"""Application settings."""

from __future__ import annotations

from datetime import timedelta

from pydantic import Field, RedisDsn, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from safir.kafka import KafkaConnectionSettings
from safir.logging import LogLevel, Profile
from safir.pydantic import HumanTimedelta

__all__ = ["Config", "config"]


class Config(BaseSettings):
    """Configuration for unfurlbot."""

    model_config = SettingsConfigDict(
        env_prefix="UNFURLBOT_", case_sensitive=False
    )

    name: str = Field("unfurlbot", title="Name of application")

    path_prefix: str = Field("/unfurlbot", title="URL prefix for application")

    profile: Profile = Field(
        Profile.development,
        title="Application logging profile",
    )

    log_level: LogLevel = Field(
        LogLevel.INFO,
        title="Log level of the application's logger",
    )

    environment_url: str = Field(
        ...,
        title="Environment URL",
        examples=["https://roundtable.lsst.cloud"],
    )

    kafka: KafkaConnectionSettings = Field(
        default_factory=KafkaConnectionSettings,
        title="Kafka connection configuration.",
    )

    redis_url: RedisDsn = Field(
        default_factory=lambda: RedisDsn(
            "redis://localhost:6379/0",
        ),
        description=("URL for the redis instance, used for caching."),
    )

    slack_token: SecretStr = Field(title="Slack bot token")

    slack_app_id: str = Field(title="Slack app ID")

    slack_debounce_time: int = Field(
        5 * 60,
        description=(
            "The number of seconds before the same token can be unfurled to "
            "the same Slack channel."
        ),
    )

    jira_proxy_path: str = Field(
        "/jira-data-proxy",
        title="Jira Data Proxy URL path",
        description=(
            "The URL path to the Jira Data Proxy within the environment."
        ),
        examples=[
            "/jira-data-proxy",
        ],
    )

    jira_root_url: str = Field(
        "https://jira.lsstcorp.org",
        title="Jira root URL",
        examples=["https://jira.lsstcorp.org"],
        description=(
            "The root URL for the Jira instance for detecting Jira links."
        ),
    )

    jira_projects: str = Field(
        "DM,RFC",
        title="Jira issue keys",
        description=(
            "A comma-separated list of Jira issue keys to recognize in "
            "messages."
        ),
    )

    jira_timeout: HumanTimedelta = Field(
        timedelta(seconds=20),
        title="Jira request timeout",
        description="How long to wait for a response from the Jira server.",
        examples=["60s"],
    )

    gafaelfawr_token: SecretStr = Field(
        ...,
        title="Gafaelfawr token",
        description=(
            "The token to use for authenticating with Gafaelfawr to access "
            "the Jira Data Proxy."
        ),
        examples=["gt-1234567890abcdef"],
    )

    consumer_group_id: str = Field(
        "unfurlbot",
        title="Kafka consumer group ID",
    )

    app_mention_topic: str = Field(
        "squarebot.app_mention",
        title="app_mention Kafka topic",
        alias="UNFURLBOT_TOPIC_APP_MENTION",
        description="Kafka topic name for `app_mention` Slack events.",
    )

    message_channels_topic: str = Field(
        "squarebot.message.channels",
        title="message.channels Kafka topic",
        alias="UNFURLBOT_TOPIC_MESSAGE_CHANNELS",
        description=(
            "Kafka topic name for `message.channels` Slack events (messages "
            "in public channels)."
        ),
    )

    message_im_topic: str = Field(
        "squarebot.message.im",
        title="message.im Kafka topic",
        alias="UNFURLBOT_TOPIC_MESSAGE_IM",
        description=(
            "Kafka topic name for `message.im` Slack events (direct message "
            " channels)."
        ),
    )

    message_groups_topic: str = Field(
        "squarebot.message.groups",
        title="message.groups Kafka topic",
        alias="UNFURLBOT_TOPIC_MESSAGE_GROUPS",
        description=(
            "Kafka topic name for `message.groups` Slack events (messages in "
            "private channels)."
        ),
    )

    message_mpim_topic: str = Field(
        "squarebot.message.mpim",
        title="message.mpim Kafka topic",
        alias="UNFURLBOT_TOPIC_MESSAGE_MPIM",
        description=(
            "Kafka topic name for `message.mpim` Slack events (messages in "
            "multi-person direct messages)."
        ),
    )

    interaction_topic: str = Field(
        "squarebot.interaction",
        title="interaction Kafka topic",
        alias="UNFURLBOT_TOPIC_INTERACTION",
        description=("Kafka topic name for `interaction` Slack events"),
    )

    @property
    def jira_proxy_url(self) -> str:
        """The URL to the Jira Data Proxy."""
        env_url = self.environment_url.rstrip("/")
        proxy_path = self.jira_proxy_path.lstrip("/")
        return f"{env_url}/{proxy_path}"

    @property
    def parsed_jira_projects(self) -> list[str]:
        """The Jira projects to recognize."""
        return list({p.strip() for p in self.jira_projects.split(",")})

    @field_validator("jira_root_url")
    @classmethod
    def ensure_no_trailing_slash(cls, value: str) -> str:
        """Ensure that the Jira url does not have a trailing slash."""
        return value.rstrip("/")


config = Config()
"""Configuration for unfurlbot."""
