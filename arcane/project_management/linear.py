"""Linear exporter for roadmaps.

Exports roadmaps to Linear via the GraphQL API.
This is a stub implementation - full integration coming in Sprint 9.
"""

import httpx

from arcane.items import Roadmap

from .base import BasePMClient, ExportResult


class LinearClient(BasePMClient):
    """Exports roadmap to Linear via GraphQL API.

    Mapping:
    - Milestones -> Projects
    - Epics -> Issues with 'epic' label
    - Stories -> Issues linked to epic
    - Tasks -> Sub-issues

    Note: This is a stub implementation. The export() method raises
    NotImplementedError until full integration is complete.
    """

    GRAPHQL_URL = "https://api.linear.app/graphql"

    def __init__(self, api_key: str):
        """Initialize Linear client.

        Args:
            api_key: Linear API key for authentication.
        """
        self.api_key = api_key
        self.headers = {
            "Authorization": api_key,
            "Content-Type": "application/json",
        }

    @property
    def name(self) -> str:
        """Return the client name."""
        return "Linear"

    async def validate_credentials(self) -> bool:
        """Test that API key is valid.

        Returns:
            True if credentials are valid and API is accessible.
        """
        query = {"query": "{ viewer { id name } }"}

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    self.GRAPHQL_URL,
                    headers=self.headers,
                    json=query,
                )
                return resp.status_code == 200
        except httpx.RequestError:
            return False

    async def export(
        self,
        roadmap: Roadmap,
        team_id: str | None = None,
        **kwargs,
    ) -> ExportResult:
        """Export roadmap to Linear.

        Args:
            roadmap: The Roadmap to export.
            team_id: Linear team ID to create items in.

        Raises:
            NotImplementedError: Full integration not yet implemented.
        """
        raise NotImplementedError(
            "Linear export is coming in Sprint 9. "
            "Use CSV export for now: arcane export --to csv"
        )
