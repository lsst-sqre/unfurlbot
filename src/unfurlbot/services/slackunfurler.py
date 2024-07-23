"""Service for Unfurling Slack messages."""

from __future__ import annotations

from rubin.squarebot.models.kafka import SquarebotSlackMessageValue
from structlog.stdlib import BoundLogger

from .domainbase import DomainUnfurler


class SlackUnfurlService:
    """A service for unfurling Slack messages."""

    def __init__(
        self,
        *,
        unfurlers: list[DomainUnfurler],
        logger: BoundLogger,
    ) -> None:
        """Initialize the service."""
        self._domain_unfurlers: list[DomainUnfurler] = unfurlers
        self._logger = logger

    async def process_message(
        self,
        message: SquarebotSlackMessageValue,
    ) -> None:
        """Process a message, sending it to unfurl handlers."""
        for unfurler in self._domain_unfurlers:
            await unfurler.process_slack(message)
