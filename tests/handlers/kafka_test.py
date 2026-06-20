"""Tests for the unfurlbot.handlers.kafka module and Kafka router."""

from __future__ import annotations

import pytest
from fastapi import FastAPI

from unfurlbot.handlers.kafka import kafka_router


@pytest.mark.asyncio
async def test_kafka_broker_started(app: FastAPI) -> None:
    """The Kafka broker is connected while the app lifespan is active.

    The ``app`` fixture drives the application lifespan via
    ``LifespanManager``. This exercises the FastStream router lifecycle that
    changed between FastStream 0.5 and 0.7: the broker must be started during
    lifespan startup so that the consumer is connected to Kafka.
    """
    connected = await kafka_router.broker.ping(timeout=10.0)
    assert connected is True
