"""Application settings."""

from __future__ import annotations

import ssl
from enum import Enum
from pathlib import Path

from pydantic import (
    DirectoryPath,
    Field,
    FilePath,
    RedisDsn,
    SecretStr,
    field_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict
from safir.logging import LogLevel, Profile

__all__ = ["Config", "config"]


class KafkaSecurityProtocol(str, Enum):
    """Kafka security protocols understood by aiokafka."""

    PLAINTEXT = "PLAINTEXT"
    """Plain-text connection."""

    SSL = "SSL"
    """TLS-encrypted connection."""


class KafkaSaslMechanism(str, Enum):
    """Kafka SASL mechanisms understood by aiokafka."""

    PLAIN = "PLAIN"
    """Plain-text SASL mechanism."""

    SCRAM_SHA_256 = "SCRAM-SHA-256"
    """SCRAM-SHA-256 SASL mechanism."""

    SCRAM_SHA_512 = "SCRAM-SHA-512"
    """SCRAM-SHA-512 SASL mechanism."""


class KafkaConnectionSettings(BaseSettings):
    """Settings for connecting to Kafka."""

    bootstrap_servers: str = Field(
        ...,
        title="Kafka bootstrap servers",
        description=(
            "A comma-separated list of Kafka brokers to connect to. "
            "This should be a list of hostnames or IP addresses, "
            "each optionally followed by a port number, separated by "
            "commas. "
            "For example: `kafka-1:9092,kafka-2:9092,kafka-3:9092`."
        ),
    )

    security_protocol: KafkaSecurityProtocol = Field(
        KafkaSecurityProtocol.PLAINTEXT,
        description="The security protocol to use when connecting to Kafka.",
    )

    cert_temp_dir: DirectoryPath | None = Field(
        None,
        description=(
            "Temporary writable directory for concatenating certificates."
        ),
    )

    cluster_ca_path: FilePath | None = Field(
        None,
        title="Path to CA certificate file",
        description=(
            "The path to the CA certificate file to use for verifying the "
            "broker's certificate. "
            "This is only needed if the broker's certificate is not signed "
            "by a CA trusted by the operating system."
        ),
    )

    client_ca_path: FilePath | None = Field(
        None,
        title="Path to client CA certificate file",
        description=(
            "The path to the client CA certificate file to use for "
            "authentication. "
            "This is only needed when the client certificate needs to be"
            "concatenated with the client CA certificate, which is common"
            "for Strimzi installations."
        ),
    )

    client_cert_path: FilePath | None = Field(
        None,
        title="Path to client certificate file",
        description=(
            "The path to the client certificate file to use for "
            "authentication. "
            "This is only needed if the broker is configured to require "
            "SSL client authentication."
        ),
    )

    client_key_path: FilePath | None = Field(
        None,
        title="Path to client key file",
        description=(
            "The path to the client key file to use for authentication. "
            "This is only needed if the broker is configured to require "
            "SSL client authentication."
        ),
    )

    client_key_password: SecretStr | None = Field(
        None,
        title="Password for client key file",
        description=(
            "The password to use for decrypting the client key file. "
            "This is only needed if the client key file is encrypted."
        ),
    )

    sasl_mechanism: KafkaSaslMechanism | None = Field(
        KafkaSaslMechanism.PLAIN,
        title="SASL mechanism",
        description=(
            "The SASL mechanism to use for authentication. "
            "This is only needed if SASL authentication is enabled."
        ),
    )

    sasl_username: str | None = Field(
        None,
        title="SASL username",
        description=(
            "The username to use for SASL authentication. "
            "This is only needed if SASL authentication is enabled."
        ),
    )

    sasl_password: SecretStr | None = Field(
        None,
        title="SASL password",
        description=(
            "The password to use for SASL authentication. "
            "This is only needed if SASL authentication is enabled."
        ),
    )

    model_config = SettingsConfigDict(
        env_prefix="KAFKA_",
        case_sensitive=False,
    )

    @property
    def ssl_context(self) -> ssl.SSLContext | None:
        """An SSL context for connecting to Kafka with aiokafka, if the
        Kafka connection is configured to use SSL.
        """
        if (
            self.security_protocol != KafkaSecurityProtocol.SSL
            or self.cluster_ca_path is None
            or self.client_cert_path is None
            or self.client_key_path is None
        ):
            return None

        client_cert_path = Path(self.client_cert_path)

        if self.client_ca_path is not None:
            # Need to contatenate the client cert and CA certificates. This is
            # typical for Strimzi-based Kafka clusters.
            if self.cert_temp_dir is None:
                raise RuntimeError(
                    "KAFKIT_KAFKA_CERT_TEMP_DIR must be set when "
                    "a client CA certificate is provided.",
                )
            client_ca = Path(self.client_ca_path).read_text()
            client_cert = Path(self.client_cert_path).read_text()
            sep = "" if client_ca.endswith("\n") else "\n"
            new_client_cert = sep.join([client_cert, client_ca])
            new_client_cert_path = Path(self.cert_temp_dir) / "client.crt"
            new_client_cert_path.write_text(new_client_cert)
            client_cert_path = Path(new_client_cert_path)

        # Create an SSL context on the basis that we're the client
        # authenticating the server (the Kafka broker).
        ssl_context = ssl.create_default_context(
            purpose=ssl.Purpose.SERVER_AUTH,
            cafile=str(self.cluster_ca_path),
        )
        # Add the certificates that the Kafka broker uses to authenticate us.
        ssl_context.load_cert_chain(
            certfile=str(client_cert_path),
            keyfile=str(self.client_key_path),
        )

        return ssl_context


class Config(BaseSettings):
    """Configuration for unfurlbot."""

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

    model_config = SettingsConfigDict(
        env_prefix="UNFURLBOT_",
        case_sensitive=False,
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
