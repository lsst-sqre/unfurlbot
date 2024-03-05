"""A Redis storage backend of tokens unfurled to Slack channels."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated

from pydantic import BaseModel, Field
from redis.asyncio import Redis
from safir.redis import PydanticRedisStorage

from ..config import config


class SlackUnfurlEventModel(BaseModel):
    """A model for a Slack unfurl event."""

    time: Annotated[
        datetime, Field(description="The time the unfurl happened.")
    ]


class SlackUnfurlEventKey:
    """A key for a Slack unfurl event."""

    def __init__(
        self, channel: str, token: str, thread_ts: str | None = None
    ) -> None:
        self.channel = channel
        self.token = token
        self.thread_ts = thread_ts

    def __str__(self) -> str:
        # base64 encode the token to avoid issues with special characters
        token = self.token.encode("utf-8").hex()
        key = f"unfurl:slack:{self.channel}:{token}"
        if self.thread_ts:
            key += f":{self.thread_ts}"
        return key


class SlackUnfurlEventStore(PydanticRedisStorage[SlackUnfurlEventModel]):
    """A Redis storage backend of Slack unfurl events."""

    def __init__(self, redis: Redis) -> None:
        super().__init__(redis=redis, datatype=SlackUnfurlEventModel)

    async def add_event(
        self, channel: str, token: str, thread_ts: str | None = None
    ) -> None:
        key = SlackUnfurlEventKey(
            channel=channel, token=token, thread_ts=thread_ts
        )
        await self.store(
            str(key),
            SlackUnfurlEventModel(time=datetime.now(tz=UTC)),
            lifetime=config.slack_debounce_time,
        )

    async def has_event(
        self, channel: str, token: str, thread_ts: str | None = None
    ) -> bool:
        key = SlackUnfurlEventKey(
            channel=channel, token=token, thread_ts=thread_ts
        )
        return await self.get(str(key)) is not None
