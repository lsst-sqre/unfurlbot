"""Test fixtures for unfurlbot tests."""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest_asyncio
from asgi_lifespan import LifespanManager
from faststream_fastapi import FastStreamAPI
from httpx import ASGITransport, AsyncClient

from unfurlbot import main


@pytest_asyncio.fixture
async def app() -> AsyncIterator[FastStreamAPI]:
    """Return a configured test application.

    Wraps the application in a lifespan manager so that startup and shutdown
    events are sent during test execution. This also starts and stops the
    Kafka broker, inside the app's own lifespan.
    """
    async with LifespanManager(main.app, startup_timeout=30):
        yield main.app


@pytest_asyncio.fixture
async def client(app: FastStreamAPI) -> AsyncIterator[AsyncClient]:
    """Return an ``httpx.AsyncClient`` configured to talk to the test app."""
    async with AsyncClient(
        base_url="https://example.com/", transport=ASGITransport(app=app)
    ) as client:
        yield client
