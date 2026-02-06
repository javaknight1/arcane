"""Jira exporter for roadmaps.

Exports roadmaps to Jira Cloud via the REST API.
This is a stub implementation - full integration coming in Sprint 9.
"""

import httpx

from arcane.items import Roadmap

from .base import BasePMClient, ExportResult


class JiraClient(BasePMClient):
    """Exports roadmap to Jira Cloud via REST API.

    Mapping:
    - Milestones -> Versions (Fix Version)
    - Epics -> Epics
    - Stories -> Stories linked to Epic
    - Tasks -> Sub-tasks

    Note: This is a stub implementation. The export() method raises
    NotImplementedError until full integration is complete.
    """

    def __init__(self, domain: str, email: str, api_token: str):
        """Initialize Jira client.

        Args:
            domain: Jira Cloud domain (e.g., 'mycompany.atlassian.net').
            email: Email address for authentication.
            api_token: Jira API token for authentication.
        """
        self.base_url = f"https://{domain}/rest/api/3"
        self.auth = (email, api_token)
        self.domain = domain

    @property
    def name(self) -> str:
        """Return the client name."""
        return "Jira Cloud"

    async def validate_credentials(self) -> bool:
        """Test that credentials are valid.

        Returns:
            True if credentials are valid and API is accessible.
        """
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{self.base_url}/myself",
                    auth=self.auth,
                )
                return resp.status_code == 200
        except httpx.RequestError:
            return False

    async def export(
        self,
        roadmap: Roadmap,
        project_key: str | None = None,
        **kwargs,
    ) -> ExportResult:
        """Export roadmap to Jira.

        Args:
            roadmap: The Roadmap to export.
            project_key: Jira project key to create items in (e.g., 'PROJ').

        Raises:
            NotImplementedError: Full integration not yet implemented.
        """
        raise NotImplementedError(
            "Jira export is coming in Sprint 9. "
            "Use CSV export for now: arcane export --to csv"
        )
