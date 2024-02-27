"""Tests for the JiraIssues storage service."""

from __future__ import annotations

import json
from pathlib import Path

from unfurlbot.storage.jiraissues import JiraIssueSummary


def test_parsing_dm_42877() -> None:
    """Test that the DM-42877 issue can be parsed into a JiraIssueSummary."""
    p = Path(__file__).parent / "data" / "DM-42877.json"
    issue = JiraIssueSummary.from_json(json.loads(p.read_text()))

    assert issue.key == "DM-42877"
    assert issue.summary == (
        "unfurlbot: Create a ticket/identifier unfurler for squarebot/Slack"
    )
    assert issue.status_label == "In Progress"
    assert issue.date_created.isoformat() == "2024-02-13T16:23:06+00:00"
    assert issue.description.startswith(
        "This backend for Squarebot will replace"
    )
    assert issue.reporter_name == "Jonathan Sick"
    assert issue.assignee_name == "Jonathan Sick"
    assert issue.date_resolved is None
    assert issue.homepage == "https://jira.lsstcorp.org/browse/DM-42877"


def test_parsing_dm_42711() -> None:
    """Test parsing DM-42711 into a JiraIssueSummary."""
    p = Path(__file__).parent / "data" / "DM-42711.json"
    issue = JiraIssueSummary.from_json(json.loads(p.read_text()))
    assert issue.key == "DM-42711"
    assert issue.summary == (
        "Technote: Wrap code samples that don't have captions"
    )
    assert issue.status_label == "Done"
    assert issue.date_created.isoformat() == "2024-01-29T23:08:48+00:00"
    assert issue.reporter_name == "Jonathan Sick"
    assert issue.assignee_name == "Jonathan Sick"
    assert issue.date_resolved is not None
    assert issue.date_resolved.isoformat() == "2024-01-30T23:11:11+00:00"
    assert issue.homepage == "https://jira.lsstcorp.org/browse/DM-42711"


def test_parsing_rfc_880() -> None:
    """Test parsing RFC-880 into a JiraIssueSummary."""
    p = Path(__file__).parent / "data" / "RFC-880.json"
    issue = JiraIssueSummary.from_json(json.loads(p.read_text()))
    assert issue.key == "RFC-880"
    assert (
        issue.summary == "Allow package docstrings in python automodapi docs."
    )
    assert issue.status_label == "Withdrawn"
    assert issue.date_created.isoformat() == "2022-09-23T21:50:08+00:00"
    assert issue.reporter_name == "John Parejko"
    assert issue.assignee_name == "John Parejko"
    assert issue.date_resolved is not None
    assert issue.date_resolved.isoformat() == "2024-01-31T23:21:23+00:00"
    assert issue.homepage == "https://jira.lsstcorp.org/browse/RFC-880"
