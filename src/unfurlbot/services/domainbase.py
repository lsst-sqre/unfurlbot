"""Base class for domain unfurlers."""

from __future__ import annotations

from abc import ABC, abstractmethod

from httpx import AsyncClient
from rubin.squarebot.models.kafka import SquarebotSlackMessageValue
from structlog.stdlib import BoundLogger

from ..config import config
from ..storage.slackmessage import SlackBlockKitMessage


class DomainUnfurler(ABC):
    """Base class for domain unfurlers."""

    def __init__(
        self, *, http_client: AsyncClient, logger: BoundLogger
    ) -> None:
        self._http_client: AsyncClient = http_client
        self._logger: BoundLogger = logger

    @abstractmethod
    async def process_slack(self, message: SquarebotSlackMessageValue) -> None:
        """Process a Slack message and unfurl it if appropriate."""
        raise NotImplementedError

    async def send_reply(
        self,
        message: SlackBlockKitMessage,
    ) -> None:
        """Send a reply to a Slack message."""
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
        if not resp_json["ok"]:
            self._logger.error(
                "Failed to send Slack message",
                response=resp_json,
                status_code=r.status_code,
                reply_message=body.pop("token"),
            )
