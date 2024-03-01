"""Tests for the JiraUnfurler service."""

from __future__ import annotations

import pytest
from structlog import get_logger

from unfurlbot.factory import Factory, ProcessContext


@pytest.mark.asyncio
async def test_key_extraction() -> None:
    """Test that issue keys are extracted from Slack messages."""
    process_contact = await ProcessContext.create()
    factory = Factory(
        logger=get_logger("unfurlbot"),
        process_context=process_contact,
    )

    jira_unfurler = factory.get_jira_domain_unfurler()
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

    await process_contact.aclose()
