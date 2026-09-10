"""Kafka router and consumers."""

from typing import Annotated

from fastapi import Depends
from faststream.kafka import KafkaBroker
from rubin.squarebot.models.kafka import SquarebotSlackMessageValue
from structlog import get_logger

from ..config import config
from ..dependencies.consumercontext import (
    ConsumerContext,
    MessageContextMiddleware,
    consumer_context_dependency,
)

__all__ = ["handle_slack_message", "kafka_broker"]


# The broker is wrapped by FastStreamAPI in main.py, which starts it inside
# the application lifespan (after the lifespan's startup code, before its
# shutdown code).
kafka_broker = KafkaBroker(
    **config.kafka.to_faststream_params(),
    logger=get_logger(__name__),
    middlewares=[MessageContextMiddleware],
)


@kafka_broker.subscriber(
    config.message_channels_topic,
    config.message_groups_topic,
    config.message_im_topic,
    config.message_mpim_topic,
    group_id=config.consumer_group_id,
)
async def handle_slack_message(
    message: SquarebotSlackMessageValue,
    context: Annotated[ConsumerContext, Depends(consumer_context_dependency)],
) -> None:
    """Handle a Slack message."""
    logger = context.logger

    logger.debug(
        "Slack message text",
        text=message.text,
    )

    factory = context.factory
    unfurl_service = factory.get_slack_unfurler()
    await unfurl_service.process_message(message)
