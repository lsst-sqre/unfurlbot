"""Storage interface for issues from the Jira API."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any, Self

from httpx import AsyncClient
from pydantic import BaseModel, Field, field_validator
from safir.pydantic import normalize_datetime

from ..config import config


class JiraIssueClient:
    """Client for fetching Jira issues.

    Parameters
    ----------
    proxy_url : str
        The base URL for the Jira Data Proxy. It should not include a trailing
        slash.
    http_client : AsyncClient
        The HTTP client to use for requests.
    token : str
        The Gafaelfawr token to use for authentication.
    """

    def __init__(
        self,
        *,
        proxy_url: str,
        http_client: AsyncClient,
        token: str,
    ) -> None:
        self._proxy_base = proxy_url
        self._http_client = http_client
        self._token = token

    async def get(self, path: str) -> dict:
        """Send a GET request to the Jira API.

        Parameters
        ----------
        path : str
            The path to request from the Jira API. It should include the
            leading slash, as well as the API version prefix (e.g.,
            `/rest/api/latest` or `/rest/api/v2`).
        """
        response = await self._http_client.get(
            f"{self._proxy_base}{path}",
            headers={"Authorization": f"Bearer {self._token}"},
            timeout=config.jira_timeout.total_seconds(),
        )
        response.raise_for_status()  # add a proper error message
        return response.json()

    async def get_issue(self, issue_key: str) -> JiraIssueSummary:
        """Get a Jira issue."""
        path = f"/rest/api/2/issue/{issue_key}"
        data = await self.get(path)
        return JiraIssueSummary.from_json(data)


class JiraIssueSummary(BaseModel):
    """Summary of a Jira issue."""

    key: Annotated[str, Field(description="The issue key.")]

    summary: Annotated[str, Field(description="The issue summary.")]

    # This is a plain-text label because statuses are site-configurable and
    # new statuses can be added.
    status_label: Annotated[
        str,
        Field(description="The label for the issue status."),
    ]

    date_created: Annotated[
        datetime,
        Field(description="The date the issue was created."),
    ]

    description: Annotated[
        str | None,
        Field(description="The issue description."),
    ] = None

    reporter_name: Annotated[
        str,
        Field(description="The name of the issue reporter."),
    ]

    homepage: Annotated[
        str,
        Field(description="The URL to the issue homepage."),
    ]

    date_resolved: Annotated[
        datetime | None,
        Field(description="The date the issue was resolved, if applicable."),
    ] = None

    assignee_name: Annotated[
        str | None,
        Field(description="The name of the issue assignee, if applicable."),
    ] = None

    _normalize_dates = field_validator(
        "date_created",
        "date_resolved",
        mode="before",
    )(normalize_datetime)

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> Self:
        """Create a JiraIssueSummary from JSON data."""
        date_created = datetime.fromisoformat(data["fields"]["created"])

        if data["fields"]["resolutiondate"]:
            date_resolved = datetime.fromisoformat(
                data["fields"]["resolutiondate"],
            )
        else:
            date_resolved = None

        if data["fields"]["assignee"]:
            assignee_name = data["fields"]["assignee"]["displayName"]
        else:
            assignee_name = None

        homepage = f"{config.jira_root_url}/browse/{data['key']}"

        return cls(
            key=data["key"],
            summary=data["fields"]["summary"],
            status_label=data["fields"]["status"]["name"],
            date_created=date_created,
            description=data["fields"]["description"],
            reporter_name=data["fields"]["reporter"]["displayName"],
            date_resolved=date_resolved,
            assignee_name=assignee_name,
            homepage=homepage,
        )
