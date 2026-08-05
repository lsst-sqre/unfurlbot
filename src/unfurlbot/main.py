"""The main application factory for the unfurlbot service.

Notes
-----
Be aware that, following the normal pattern for FastAPI services, the app is
constructed when this module is loaded and is not deferred until a function is
called.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from importlib.metadata import metadata, version

from fastapi import FastAPI
from faststream_fastapi import FastStreamAPI
from safir.logging import configure_logging, configure_uvicorn_logging
from safir.middleware.x_forwarded import XForwardedMiddleware
from structlog import get_logger

from .config import config
from .dependencies.consumercontext import consumer_context_dependency
from .handlers.internal import internal_router
from .handlers.kafka import kafka_broker

__all__ = ["app", "config"]


@asynccontextmanager
async def lifespan(api: FastAPI) -> AsyncIterator[None]:
    """Set up and tear down the application.

    Note
    ----
    The FastStream Kafka broker is started and stopped by ``FastStreamAPI``
    around this lifespan, so by the time this runs the broker is already
    connected.
    """
    logger = get_logger(__name__)

    # Initialize ProcessContext resources (HTTP client, Redis).
    await consumer_context_dependency.initialize()

    logger.info("Unfurlbot start up complete.")

    yield

    # Clean up ProcessContext resources.
    await consumer_context_dependency.aclose()


configure_logging(
    profile=config.profile,
    log_level=config.log_level,
    name="unfurlbot",
)
configure_uvicorn_logging(config.log_level)

api = FastAPI(
    title="unfurlbot",
    description=metadata("unfurlbot")["Summary"],
    version=version("unfurlbot"),
    openapi_url=f"/{config.path_prefix}/openapi.json",
    docs_url=f"/{config.path_prefix}/docs",
    redoc_url=f"/{config.path_prefix}/redoc",
    lifespan=lifespan,
)
"""The inner FastAPI application for unfurlbot."""

# Attach the routers.
api.include_router(internal_router)

# Add middleware.
api.add_middleware(XForwardedMiddleware)

# Wrap the FastAPI app with the FastStream Kafka broker. This must come
# after all subscriber modules are imported (the `handlers.kafka` import
# above guarantees that).
app = FastStreamAPI(kafka_broker, application=api)
"""The ASGI application for unfurlbot, serving both HTTP and Kafka."""
