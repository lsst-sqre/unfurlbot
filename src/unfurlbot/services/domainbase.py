"""Base class for domain unfurlers."""

from __future__ import annotations

from abc import ABC, abstractmethod

from httpx import AsyncClient
from rubin.squarebot.models.kafka import SquarebotSlackMessageValue
from structlog.stdlib import BoundLogger

from ..config import config
from ..storage.slackmessage import SlackBlockKitMessage
from ..storage.unfurleventstore import SlackUnfurlEventStore


class DomainUnfurler(ABC):
    """Base class for domain unfurlers."""

    def __init__(
        self,
        *,
        http_client: AsyncClient,
        logger: BoundLogger,
        unfurl_event_store: SlackUnfurlEventStore,
    ) -> None:
        self._http_client: AsyncClient = http_client
        self._logger: BoundLogger = logger
        self._unfurl_event_store = unfurl_event_store

    @abstractmethod
    async def process_slack(self, message: SquarebotSlackMessageValue) -> None:
        """Process a Slack message and unfurl it if appropriate."""
        raise NotImplementedError

    async def send_reply(
        self, message: SlackBlockKitMessage, token: str, token_type: str
    ) -> None:
        """Send an unfurl for a Slack message.

        Parameters
        ----------
        message
            The message to send.
        token
            The token string that triggered the unfurl. For example, the Jira
            issue key or the document handle.
        token_type
            The type of token. For example, "jira". This is used for logging
            purposes.
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
            self._logger.info(
                "Sent unfurl",
                channel=message.channel,
                thread_ts=message.thread_ts,
                token=token,
                token_type=token_type,
            )
        else:
            self._logger.error(
                "Failed to send Slack message",
                response=resp_json,
                status_code=r.status_code,
                reply_message=body.pop("token"),
            )

        # Add the event to the store
        if message.channel:
            # for typing; the channel should be present
            await self._unfurl_event_store.add_event(
                channel=message.channel,
                thread_ts=message.thread_ts,
                token=token,
            )

    async def is_recently_unfurled(
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
