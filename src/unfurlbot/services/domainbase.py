"""Base class for domain unfurlers."""

from __future__ import annotations

from abc import ABC, abstractmethod

from httpx import AsyncClient
from rubin.squarebot.models.kafka import SquarebotSlackMessageValue


class DomainUnfurler(ABC):
    """Base class for domain unfurlers."""

    def __init__(self, http_client: AsyncClient) -> None:
        self._http_client: AsyncClient = http_client

    @abstractmethod
    async def process_slack(self, message: SquarebotSlackMessageValue) -> None:
        """Process a Slack message and unfurl it if appropriate."""
        raise NotImplementedError
