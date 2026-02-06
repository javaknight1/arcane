"""Notion exporter for roadmaps.

Exports roadmaps to Notion via the API.
This is a stub implementation - full integration coming in Sprint 9.
"""

import httpx

from arcane.items import Roadmap

from .base import BasePMClient, ExportResult


class NotionClient(BasePMClient):
    """Exports roadmap to Notion via API.

    Mapping:
    - Creates a database for roadmap items
    - Uses nested pages for hierarchy
    - Includes all metadata as properties

    Note: This is a stub implementation. The export() method raises
    NotImplementedError until full integration is complete.
    """

    API_URL = "https://api.notion.com/v1"
    NOTION_VERSION = "2022-06-28"

    def __init__(self, api_key: str):
        """Initialize Notion client.

        Args:
            api_key: Notion internal integration token.
        """
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Notion-Version": self.NOTION_VERSION,
        }

    @property
    def name(self) -> str:
        """Return the client name."""
        return "Notion"

    async def validate_credentials(self) -> bool:
        """Test that API key is valid.

        Returns:
            True if credentials are valid and API is accessible.
        """
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{self.API_URL}/users/me",
                    headers=self.headers,
                )
                return resp.status_code == 200
        except httpx.RequestError:
            return False

    async def export(
        self,
        roadmap: Roadmap,
        parent_page_id: str | None = None,
        **kwargs,
    ) -> ExportResult:
        """Export roadmap to Notion.

        Args:
            roadmap: The Roadmap to export.
            parent_page_id: Notion page ID to create database under.

        Raises:
            NotImplementedError: Full integration not yet implemented.
        """
        raise NotImplementedError(
            "Notion export is coming in Sprint 9. "
            "Use CSV export for now: arcane export --to csv"
        )
