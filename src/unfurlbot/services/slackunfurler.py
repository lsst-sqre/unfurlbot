"""Service for Unfurling Slack messages."""

from __future__ import annotations

import json

from rubin.squarebot.models.kafka import SquarebotSlackMessageValue
from structlog.stdlib import BoundLogger

from .domainbase import DomainUnfurler


class SlackUnfurlService:
    """A service for unfurling Slack messages."""

    def __init__(
        self, *, unfurlers: list[DomainUnfurler], logger: BoundLogger
    ) -> None:
        """Initialize the service."""
        self._domain_unfurlers: list[DomainUnfurler] = unfurlers
        self._logger = logger

    async def process_message(
        self, message: SquarebotSlackMessageValue
    ) -> None:
        """Process a message, sending it to unfurl handlers."""
        # Ignore messages from bots
        # Get bot_id from parsed message when rubin-squarebot is released
        original_message = json.loads(message.slack_event)
        message_event = original_message["event"]
        if "bot_id" in message_event and message_event["bot_id"] is not None:
            self._logger.info("Ignoring message from bot")
            return

        for unfurler in self._domain_unfurlers:
            await unfurler.process_slack(message)
