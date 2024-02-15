"""Kafka router and consumers."""

from __future__ import annotations

from faststream.kafka.fastapi import KafkaMessage, KafkaRouter
from faststream.security import BaseSecurity
from rubin.squarebot.models.kafka import SquarebotSlackMessageValue
from structlog import get_logger

from ..config import config

__all__ = ["kafka_router", "handle_slack_message"]


kafka_security = BaseSecurity(ssl_context=config.kafka.ssl_context)
kafka_router = KafkaRouter(
    config.kafka.bootstrap_servers,
    security=kafka_security,
    logger=get_logger(__name__),
)


@kafka_router.subscriber(
    config.message_channels_topic,
    config.message_groups_topic,
    config.message_im_topic,
    config.message_mpim_topic,
    group_id=config.consumer_group_id,
)
async def handle_slack_message(
    message: SquarebotSlackMessageValue,
    msg: KafkaMessage,
) -> None:
    """Handle a Slack message."""
    logger = get_logger(__name__)
    record = msg.raw_message
    kafka_context = {
        "topic": record.topic,
        "offset": record.offset,
        "partition": record.partition,
    }
    logger = logger.bind(kafka=kafka_context)

    logger.info(
        "Slack message text",
        text=message.text,
    )
