"""Domain unfurler for Jira messages."""

from __future__ import annotations

import re

from httpx import AsyncClient
from rubin.squarebot.models.kafka import SquarebotSlackMessageValue
from structlog.stdlib import BoundLogger

from ..config import config
from ..storage.jiraissues import JiraIssueClient, JiraIssueSummary
from ..storage.slackmessage import (
    SlackBlockKitMessage,
    SlackContextBlock,
    SlackTextObject,
    SlackTextSectionBlock,
)
from ..storage.unfurleventstore import SlackUnfurlEventStore
from .domainbase import DomainUnfurler


class JiraUnfurler(DomainUnfurler):
    """Unfurls Jira issue keys found in Slack messages."""

    unfurler_domain = "jira"

    def __init__(
        self,
        *,
        jira_client: JiraIssueClient,
        http_client: AsyncClient,
        logger: BoundLogger,
        unfurl_event_store: SlackUnfurlEventStore,
    ) -> None:
        super().__init__(
            http_client=http_client,
            logger=logger,
            unfurl_event_store=unfurl_event_store,
        )
        self._jira_client = jira_client
        self._jira_host = config.jira_root_url

    async def extract_tokens(
        self, message: SquarebotSlackMessageValue
    ) -> list[str]:
        """Extract Jira issue tokens from a Slack message.

        Implements the abstract method from the base class.

        Parameters
        ----------
        message
            The Slack message to process, containing text content.

        Returns
        -------
        list
            A list of Jira issue tokens found in the message text.
        """
        return await self._extract_issues(message.text)

    async def _extract_issues(self, text: str) -> list[str]:
        """Extract issue keys from a Slack message.

        Parameters
        ----------
        text
            The text content of the original Slack message.

        Returns
        -------
        list
            A list of issue keys (`str` type) found in the message. For
            example, ``["DM-123", "DM-456"]``. The list is empty if no issue
            keys are found.
        """
        # This algorithm is based on the original sqrbot implementation

        # Remove markdown fenced code blocks from the text
        text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)

        # Remove inline code from the text
        text = re.sub(r"`.*?`", "", text)

        # Protect issue keys in Jira URLs by removing the surrounding URL
        text = re.sub(rf"{self._jira_host}/browse/", "", text)

        # Protect "tickets/DM-" (only) when not part of a URL or path
        text = re.sub(r"tickets/DM-", "DM-", text)

        # Remove URLs from the text
        text = re.sub(r"https?://\S+", "", text)

        projects = await self._get_projects()
        key_pattern = rf"\b((?:{'|'.join(projects)})-\d+)"
        matches = re.findall(key_pattern, text)
        matches = list({str(m) for m in matches})  # Deduplicate
        return sorted(matches)

    async def _get_projects(self) -> list[str]:
        """Get a list of Jira projects."""
        # This is a shim for an API-driven approach to getting the list of
        # projects in the Rubin Jira.
        return config.parsed_jira_projects

    async def create_slack_message(
        self,
        *,
        trigger_message: SquarebotSlackMessageValue,
        token: str,
    ) -> SlackBlockKitMessage:
        """Create an unfurl message with info about a Jira issue.

        This method is called by `process_slack` for each detected issue key.

        Parameters
        ----------
        message
            The message to reply to.
        issue_key
            The key of the issue to reply about.
        """
        # - Fetch the issue from the Jira API
        issue = await self._jira_client.get_issue(token)

        # Create and send a Slack reply
        reply_message = self._format_slack_message(
            issue=issue,
            channel=trigger_message.channel,
            thread_ts=trigger_message.thread_ts,
        )
        self._logger.debug(
            "Formatted Jira unfurl",
            reply_message=reply_message.to_slack(),
            token=token,
            channel=trigger_message.channel,
            thread_ts=trigger_message.thread_ts,
        )
        return reply_message

    def _format_slack_message(
        self,
        *,
        issue: JiraIssueSummary,
        channel: str,
        thread_ts: str | None = None,
    ) -> SlackBlockKitMessage:
        """Format a Slack message describing the Jira issue.

        Parameters
        ----------
        issue
            The issue to describe.
        channel
            The ID of the Slack channel to send the message to.
        thread_ts
            The timestamp of the message to thread this message onto. This is
            the ``thread_id`` or the original message. If the original message
            was more threaded, this is ``None``.
        """
        # Text that's used for notifications
        fallback_text = f"{issue.key} ({issue.status_label}) {issue.summary}"

        # The main section block
        main_block = SlackTextSectionBlock(
            text=(f"<{issue.homepage}|*{issue.key}*> {issue.summary}"),
            fields=[],
        )

        # Prepare a context block with the assignee, status, and date
        assignee = issue.assignee_name or "Unassigned"
        # The date is either the resolved date or the created date
        if issue.date_resolved:
            ts = int(issue.date_resolved.timestamp())
            ts_label = "Resolved"
            date_fallback = issue.date_resolved.strftime("%Y-%m-%d")
        else:
            ts = int(issue.date_created.timestamp())
            ts_label = "Created"
            date_fallback = issue.date_created.strftime("%Y-%m-%d")
        # Use Slack date formatting to make the date human-readable and
        # be localized to the user's timezone
        date_text = (
            f"<!date^{ts}^{ts_label} {{date_pretty}} {{time}}"
            f"|{ts_label} {date_fallback}>"
        )

        context_block = SlackContextBlock(
            elements=[
                SlackTextObject(
                    text=f"{assignee} | {issue.status_label} | {date_text}",
                ),
            ],
        )
        return SlackBlockKitMessage(
            text=fallback_text,
            blocks=[main_block, context_block],
            channel=channel,
            thread_ts=thread_ts,
        )
