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
from .domainbase import DomainUnfurler


class JiraUnfurler(DomainUnfurler):
    """Unfurl Jira issue handles."""

    def __init__(
        self,
        jira_client: JiraIssueClient,
        http_client: AsyncClient,
        logger: BoundLogger,
    ) -> None:
        super().__init__(http_client=http_client, logger=logger)
        self._jira_client = jira_client
        self._jira_host = config.jira_root_url

    async def process_slack(self, message: SquarebotSlackMessageValue) -> None:
        """Process a Slack message and unfurl it if appropriate."""
        issue_keys = await self.extract_issues(message.text)
        # Consider making this async
        for issue_key in issue_keys:
            await self.unfurl_issue(message, issue_key)

    async def unfurl_issue(
        self, message: SquarebotSlackMessageValue, issue_key: str
    ) -> None:
        """Reply to a message with info about a Jira issue."""
        # - Check with the redis cache to see if we've already unfurled this

        # - Fetch the issue from the Jira API
        issue = await self._jira_client.get_issue(issue_key)

        # Create and send a Slack reply
        # Re-add support for thread_ts when rubin-squarebot is released
        reply_message = self.format_slack_message(
            issue=issue, channel=message.channel, thread_ts=message.thread_ts
        )
        self._logger.debug(
            "Formatted Jira unfurl", reply_message=reply_message.to_slack()
        )
        await self.send_reply(reply_message)

    async def extract_issues(self, text: str) -> list[str]:
        """Extract issue keys from a Slack message."""
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

        projects = await self.get_projects()
        key_pattern = rf"((?:{'|'.join(projects)})-\d+)"
        matches = re.findall(key_pattern, text)
        return [str(m) for m in matches]

    async def get_projects(self) -> list[str]:
        """Get a list of Jira projects."""
        # This is a shim for either external configuration or an API-driven
        # approach to getting the list of projects in the Rubin Slack.
        return [
            "ADMIN",
            "CCB",
            "CAP",
            "COMCAM",
            "COMT",
            "DM",
            "EPO",
            "FRACAS",
            "IAM",
            "IHS",
            "IT",
            "ITRFC",
            "LOVE",
            "LASD",
            "LIT",
            "LOPS",
            "LVV",
            "M1M3V",
            "OPSIM",
            "PHOSIM",
            "PST",
            "PSV",
            "PUB",
            "RFC",
            "RM",
            "SAFE",
            "SIM",
            "SPP",
            "SBTT",
            "SE",
            "TSAIV",
            "TCT",
            "SECMVERIF",
            "TMDC",
            "TPC",
            "TSEIA",
            "TAS",
            "TELV",
            "TSSAL",
            "TSS",
            "TSSPP",
            "WMP",
            "PREOPS",
            "OBS",
            "SITCOM",
            "BLOCK",
        ]

    def format_slack_message(
        self,
        *,
        issue: JiraIssueSummary,
        channel: str,
        thread_ts: str | None = None,
    ) -> SlackBlockKitMessage:
        """Format a Slack message describing the Jira issue."""
        main_block = SlackTextSectionBlock(
            text=(f"> <{issue.homepage}|*{issue.key}*> {issue.summary}"),
            fields=[],
        )

        assignee = issue.assignee_name or "Unassigned"
        # Consider using a natural language date formatter
        created_date = issue.date_created.strftime("%Y-%m-%d")
        context_block = SlackContextBlock(
            elements=[
                SlackTextObject(
                    text=(
                        f"{assignee} | {issue.status_label} | "
                        f"Created {created_date}"
                    )
                )
            ]
        )
        return SlackBlockKitMessage(
            text=f"{issue.key} ({issue.status_label}) {issue.summary}",
            blocks=[main_block, context_block],
            channel=channel,
            thread_ts=thread_ts,
        )
