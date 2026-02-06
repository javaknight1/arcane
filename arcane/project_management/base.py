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
        items_created: Number of items exported.
        errors: List of error messages if any occurred.
        url: URL or path to the exported result, if applicable.
    """

    success: bool
    target: str
    items_created: int
    errors: list[str] = []
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
