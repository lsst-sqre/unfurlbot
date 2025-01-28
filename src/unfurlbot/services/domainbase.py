"""Base class for domain unfurlers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import ClassVar

from httpx import AsyncClient
from rubin.squarebot.models.kafka import SquarebotSlackMessageValue
from structlog.stdlib import BoundLogger

from ..config import config
from ..storage.slackmessage import SlackBlockKitMessage
from ..storage.unfurleventstore import SlackUnfurlEventStore


class DomainUnfurler(ABC):
    """Base class for domain unfurlers.

    Notes
    -----
    Classes that implement a domain unfurler should inherit from this class
    with three points of implementation:

    1. Set the `unfurler_domain` class variable to a unique string that
       identifies the domain. This domain is typically used for logging unfurl
       activity.

    2. Implement the `extract_tokens` method to extract tokens from a Slack
       message. The nature of tokens are domain-specific. For example, in the
       Jira domain, the token is the issue key. In other domains, the token
       could be a document handle or even a URL.

    3. Implement the `create_slack_message` method to create a
       `SlackBlockKitMessage`. This message acts as an unfurl for the token,
       and is send automatically by the unfurler through the `process_slack`
       entry point.

    This base class handles sending the generated unfurl messages, and ensuring
    that messages are debounced to prevent repeated unfurls of the same token,
    and that messages are only unfurled if the trigger message is recent.
    """

    unfurler_domain: ClassVar[str] = "default"

    def __init__(
        self,
        *,
        http_client: AsyncClient,
        logger: BoundLogger,
        unfurl_event_store: SlackUnfurlEventStore,
    ) -> None:
        self._http_client: AsyncClient = http_client
        self._logger: BoundLogger = logger.bind(
            token_type=self.unfurler_domain
        )
        self._unfurl_event_store = unfurl_event_store

    async def process_slack(self, message: SquarebotSlackMessageValue) -> None:
        """Process a Slack message and unfurl extracted tokens."""
        tokens = await self.extract_tokens(message)
        for token in tokens:
            # This is a logger bound to the specific token context
            token_logger = self._logger.bind(
                token=token,
                channel=message.channel,
                thread_ts=message.thread_ts,
                trigger_ts=message.ts,
            )
            if self._is_trigger_message_stale(message):
                token_logger.warning("Ignoring stale trigger message")
                continue
            if await self._is_recently_unfurled(message, token):
                token_logger.debug("Ignoring recently unfurled token")
                continue
            unfurl_slack_message = await self.create_slack_message(
                token=token, trigger_message=message, logger=token_logger
            )
            await self._send_unfurl(
                message=unfurl_slack_message, token=token, logger=token_logger
            )

    @abstractmethod
    async def extract_tokens(
        self, message: SquarebotSlackMessageValue
    ) -> list[str]:
        """Extract tokens from a Slack message."""
        raise NotImplementedError

    @abstractmethod
    async def create_slack_message(
        self,
        *,
        token: str,
        trigger_message: SquarebotSlackMessageValue,
        logger: BoundLogger,
    ) -> SlackBlockKitMessage:
        """Create a Slack message to unfurl a token.

        This method is called by `process_slack` for each detected token.

        Parameters
        ----------
        trigger_message
            The message to reply to.
        token
            The key of the issue to reply about.
        logger
            A logger bound with the token and message context.
        """
        raise NotImplementedError

    async def _send_unfurl(
        self, *, message: SlackBlockKitMessage, token: str, logger: BoundLogger
    ) -> None:
        """Send an unfurl for a Slack message.

        Parameters
        ----------
        message
            The message to send.
        token
            The token string that triggered the unfurl. For example, the Jira
            issue key or the document handle.
        logger
            A logger bound with the token and message context.
        """
        # https://api.slack.com/methods/chat.postMessage
        body = message.to_slack()
        body["token"] = config.slack_token.get_secret_value()
        r = await self._http_client.post(
            "https://slack.com/api/chat.postMessage",
            json=body,
            headers={
                "content-type": "application/json; charset=utf-8",
                "authorization": (
                    f"Bearer {config.slack_token.get_secret_value()}"
                ),
            },
        )
        resp_json = r.json()
        if resp_json["ok"]:
            logger.info(
                "Sent unfurl",
                channel=message.channel,
                thread_ts=message.thread_ts,
                token=token,
            )
        else:
            logger.error(
                "Failed to send Slack message",
                response=resp_json,
                status_code=r.status_code,
                reply_message=body.pop("token"),
                channel=message.channel,
                thread_ts=message.thread_ts,
                token=token,
            )

        # Add the event to the store
        if message.channel:
            # for typing; the channel should be present
            await self._unfurl_event_store.add_event(
                channel=message.channel,
                thread_ts=message.thread_ts,
                token=token,
            )

    async def _is_recently_unfurled(
        self,
        message: SquarebotSlackMessageValue,
        token: str,
    ) -> bool:
        """Check if a message has been recently unfurled."""
        return await self._unfurl_event_store.has_event(
            channel=message.channel,
            thread_ts=message.thread_ts,
            token=token,
        )

    def _is_trigger_message_stale(
        self,
        message: SquarebotSlackMessageValue,
    ) -> bool:
        """Check if a trigger message is stale.

        Parameters
        ----------
        message
            The message that triggered the unfurl.

        Notes
        -----
        In https://rubinobs.atlassian.net/browse/DM-48614 we observed that
        a message was repeatedly triggering unfurls. We don't know how this
        happened and its possible that either the message was being resent by
        Slack or was being re-consumed by unfurlbot. Regardless, we can
        protect against this case by only unfurl if the triggering message is
        current, within a time window defined by
        `Config.slack_trigger_message_ttl`.
        """
        trigger_datetime = datetime.fromtimestamp(float(message.ts), tz=UTC)
        age = datetime.now(tz=UTC) - trigger_datetime
        return age.total_seconds() > config.slack_trigger_message_ttl
