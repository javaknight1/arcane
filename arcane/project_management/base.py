"""Base interface for project management tool clients.

All PM tool exporters (CSV, Linear, Jira, Notion) implement this interface
so they can be used interchangeably by the CLI export command.
"""

from abc import ABC, abstractmethod

from pydantic import BaseModel

from arcane.items import Roadmap


class ExportResult(BaseModel):
    """Result of an export operation.

    Attributes:
        success: Whether the export completed successfully.
        target: Name of the export target (e.g., "CSV", "Linear").
        items_created: Total number of items exported.
        items_by_type: Breakdown of items created by type
            (e.g., {"milestones": 3, "epics": 9, ...}).
        id_mapping: Mapping of Arcane item IDs to PM tool IDs
            (e.g., {"task-01HQ...": "LIN-123"}).
        errors: List of fatal error messages if any occurred.
        warnings: List of non-fatal issues encountered during export
            (e.g., "Could not set status for task-01HQ...").
        url: URL or path to the exported result, if applicable.
    """

    success: bool
    target: str
    items_created: int
    items_by_type: dict[str, int] = {}
    id_mapping: dict[str, str] = {}
    errors: list[str] = []
    warnings: list[str] = []
    url: str | None = None


class BasePMClient(ABC):
    """Abstract base class for project management tool clients.

    All PM exporters must implement this interface to provide
    consistent export behavior across different tools.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name of the PM tool (e.g., 'Linear', 'Jira')."""
        pass

    @abstractmethod
    async def export(self, roadmap: Roadmap, **kwargs) -> ExportResult:
        """Export a roadmap to the PM tool.

        Args:
            roadmap: The Roadmap to export.
            **kwargs: Tool-specific options (e.g., workspace, project_key).

        Returns:
            ExportResult with success status and details.
        """
        pass

    @abstractmethod
    async def validate_credentials(self) -> bool:
        """Test that credentials are valid and the API is reachable.

        Returns:
            True if credentials are valid and API is accessible.
        """
        pass
