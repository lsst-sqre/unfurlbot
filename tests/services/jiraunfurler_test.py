"""Tests for the JiraUnfurler service."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from unfurlbot.services.jiraunfurler import JiraUnfurler
from unfurlbot.storage.jiraissues import JiraIssueClient


@pytest.mark.asyncio
async def test_key_extraction() -> None:
    """Test that issue keys are extracted from Slack messages."""
    http_client = AsyncClient()
    jira_unfurler = JiraUnfurler(
        jira_client=JiraIssueClient(
            proxy_url="https://example.com/jira-data-proxy",
            http_client=http_client,
            token="gt-123",
        ),
        http_client=http_client,
    )
    text = "DM-1234 DM-5678\nRFC-1"
    keys = await jira_unfurler.extract_issues(text)
    assert keys == ["DM-1234", "DM-5678", "RFC-1"]

    # Test that URLs are removed, but Jira URLs are preserved
    text = (
        "DM-1234 https://jira.lsstcorp.org/browse/DM-5678 "
        "https://example.com/RFC-1"
    )
    keys = await jira_unfurler.extract_issues(text)
    assert keys == ["DM-1234", "DM-5678"]

    # Test that code blocks are removed
    text = "DM-1234\n```DM-5678```\n\n`RFC-1`"
    keys = await jira_unfurler.extract_issues(text)
    assert keys == ["DM-1234"]

    await http_client.aclose()
