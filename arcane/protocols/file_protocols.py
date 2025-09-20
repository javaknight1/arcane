"""Protocol definitions for file operations and template loading."""

from typing import Protocol, Optional, Dict, Any
from pathlib import Path


class FileOperationsProtocol(Protocol):
    """Protocol for file operation functionality."""

    @property
    def save_outputs(self) -> bool:
        """Whether file outputs should be saved."""
        ...

    @property
    def output_dir(self) -> Optional[Path]:
        """Output directory for saving files."""
        ...

    def extract_project_name(self, content: str) -> str:
        """Extract project name from content."""
        ...

    def save_outline(self, outline: str, project_name: str) -> str:
        """Save outline to file."""
        ...

    def save_complete_roadmap(self, content: str, project_name: str) -> str:
        """Save complete roadmap to file."""
        ...

    def get_progress_filepath(self, project_name: str) -> str:
        """Get filepath for saving progress."""
        ...


class TemplateLoaderProtocol(Protocol):
    """Protocol for template loading functionality."""

    def load_template(self, template_name: str) -> str:
        """Load a template by name."""
        ...

    def get_available_templates(self) -> list[str]:
        """Get list of available template names."""
        ...

    def clear_cache(self) -> None:
        """Clear the template cache."""
        ...


class ConfigurationProtocol(Protocol):
    """Protocol for configuration management."""

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        ...

    def set(self, key: str, value: Any) -> None:
        """Set configuration value."""
        ...

    def load_from_file(self, filepath: str) -> None:
        """Load configuration from file."""
        ...

    def save_to_file(self, filepath: str) -> None:
        """Save configuration to file."""
        ...

    def get_environment_config(self) -> Dict[str, Any]:
        """Get environment-specific configuration."""
        ...

    def validate_config(self) -> list[str]:
        """Validate configuration and return any issues."""
        ...


class ExportProtocol(Protocol):
    """Protocol for export functionality."""

    def export_to_format(
        self,
        content: Any,
        format_type: str,
        output_path: Optional[str] = None
    ) -> str:
        """Export content to specified format."""
        ...

    def get_supported_formats(self) -> list[str]:
        """Get list of supported export formats."""
        ...

    def validate_format(self, format_type: str) -> bool:
        """Validate if format is supported."""
        ...