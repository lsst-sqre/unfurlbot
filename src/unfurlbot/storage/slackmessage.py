"""Formatting and sending a Slack message."""

from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import Annotated, Any

from pydantic import BaseModel, Field


class SlackTextObject(BaseModel):
    """A text object in a Slack message.

    https://api.slack.com/reference/messaging/composition-objects#text
    """

    text: Annotated[str, Field(description="The text content of the block.")]

    type: Annotated[
        str, Field(description="The type of text object.")
    ] = "mrkdwn"

    verbatim: Annotated[
        bool,
        Field(
            description=(
                "Indicates if the text is verbatim. When False, links "
                "are linkified and mentions parsed. Only applied to "
                "mrkdwn type."
            )
        ),
    ] = False

    def to_slack(self, max_length: int = 3000) -> dict[str, Any]:
        """Convert to a text object in the Slack message payload."""
        truncated_text = _format_and_truncate_at_end(self.text, max_length)
        data: dict[str, Any] = {"type": self.type, "text": truncated_text}
        if self.type == "mrkdwn":
            data["verbatim"] = self.verbatim
        return data


class SlackBaseBlock(BaseModel, metaclass=ABCMeta):
    """Base class for any Slack Block Kit block."""

    @abstractmethod
    def to_slack(self) -> dict[str, Any]:
        """Convert to a Slack Block Kit block.

        Returns
        -------
        dict
            A Slack Block Kit block suitable for including in the ``fields``
            or ``text`` section of a ``blocks`` element.
        """


class SlackTextSectionBlock(SlackBaseBlock):
    """A block of text in a Slack message, with markdown formatting."""

    text: Annotated[str, Field(description="The text content of the block.")]

    fields: Annotated[
        list[SlackTextObject],
        Field(
            description="Additional text arranged in twocolumns",
            default_factory=list,
        ),
    ]

    format: Annotated[str, Field(description="Format of the text.")] = "mrkdwn"

    def to_slack(self) -> dict[str, Any]:
        """Convert to a Slack Block Kit block.

        Returns
        -------
        dict
            A Slack Block Kit block suitable for including in the ``fields``
            or ``text`` section of a ``blocks`` element.
        """
        text = SlackTextObject(text=self.text, type=self.format)
        payload: dict[str, Any] = {"type": "section", "text": text.to_slack()}
        if self.fields:
            payload["fields"] = [
                field.to_slack(max_length=2000) for field in self.fields
            ]
        return payload


class SlackContextBlock(SlackBaseBlock):
    """A context block in a Slack message."""

    # Text content in the block. Note that image elements can also be supported
    elements: Annotated[
        list[SlackTextObject],
        Field(description="The elements of block.", max_length=10),
    ]

    def to_slack(self) -> dict[str, Any]:
        """Convert to a Slack Block Kit block.

        Returns
        -------
        dict
            A Slack Block Kit block suitable for including in the ``fields``
            or ``text`` section of a ``blocks`` element.
        """
        return {
            "type": "context",
            "elements": [element.to_slack() for element in self.elements],
        }


class SlackBlockKitMessage(BaseModel):
    """A message in Block Kit format."""

    text: Annotated[
        str,
        Field(
            description=(
                "The message's text. When blocks are used this becomes a "
                "fallback for notifications. This may be markdown is `mrkdwn` "
                "is true."
            )
        ),
    ]

    blocks: Annotated[
        list[SlackBaseBlock],
        Field(
            description=("An array of layout blocks. Maximum of 50 blocks. "),
            default_factory=list,
            max_length=50,  # limit for messages, but not app surfaces/modals
        ),
    ]

    mrkdwn: Annotated[
        bool, Field(description="Indicates if the text is markdown.")
    ] = True

    # Used for threading messages
    thread_ts: Annotated[
        str | None, Field(description="The timestamp of the parent message.")
    ] = None

    # Used for sending messages with the web API
    channel: Annotated[
        str | None, Field(description="The channel to send the message to.")
    ] = None

    def to_slack(self) -> dict[str, Any]:
        """Convert to a Slack message payload.

        Returns
        -------
        dict
            A Slack Block Kit message suitable for use in a Slack API call.
        """
        payload: dict[str, Any] = {
            "text": _format_and_truncate_at_end(self.text, 3000),
            "mrkdwn": self.mrkdwn,
            "blocks": [],
        }
        if self.thread_ts:
            payload["thread_ts"] = self.thread_ts
        if self.channel:
            payload["channel"] = self.channel

        for block in self.blocks:
            block_payload = block.to_slack()
            payload["blocks"].append(block_payload)

        return payload


def _format_and_truncate_at_end(string: str, max_length: int) -> str:
    """Format a string for Slack, truncating at the end.

    Slack prohibits text blocks longer than a varying number of characters
    depending on where they are in the message. If this constraint is not met,
    the whole mesage is rejected with an HTTP error. Truncate a potentially
    long message at the end.

    Parameters
    ----------
    string
        String to truncate.
    max_length
        Maximum allowed length.

    Returns
    -------
    str
        The truncated string with special characters escaped.
    """
    string = (
        string.strip()
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
    if len(string) <= max_length:
        return string
    truncated = " [...]"
    last_newline = string.rfind("\n", 0, max_length - len(truncated))
    if last_newline == -1:
        return string[: max_length - len(truncated)] + truncated
    else:
        return string[:last_newline] + truncated
