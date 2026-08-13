"""Tests for the unfurlbot.handlers.kafka module and Kafka router."""

from __future__ import annotations

import pytest
from faststream_fastapi import FastStreamAPI

from unfurlbot.handlers.kafka import kafka_broker


@pytest.mark.asyncio
async def test_kafka_broker_started(app: FastStreamAPI) -> None:
    """The Kafka broker is connected while the app lifespan is active.

    The ``app`` fixture drives the application lifespan via
    ``LifespanManager``. This exercises the FastStream broker lifecycle: the
    broker must be started during lifespan startup so that the consumer is
    connected to Kafka.
    """
    connected = await kafka_broker.ping(timeout=10.0)
    assert connected is True
