"""Base class for all export platform integrations."""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
import os

from arcane.items import Roadmap


class ExportPlatform(Enum):
    """Supported export platforms."""
    NOTION = "notion"
    JIRA = "jira"
    ASANA = "asana"
    LINEAR = "linear"
    TRELLO = "trello"
    GITHUB_PROJECTS = "github_projects"
    AZURE_DEVOPS = "azure_devops"
    MONDAY = "monday"
    CLICKUP = "clickup"

    @classmethod
    def from_string(cls, value: str) -> 'ExportPlatform':
        """Create ExportPlatform from string value.

        Args:
            value: String representation of platform

        Returns:
            ExportPlatform enum member

        Raises:
            ValueError: If platform is not supported
        """
        value = value.lower().strip()
        try:
            return cls(value)
        except ValueError:
            valid = ', '.join(p.value for p in cls)
            raise ValueError(f"Unknown platform: {value}. Valid platforms: {valid}")


@dataclass
class ExportResult:
    """Result of an export operation."""
    success: bool
    platform: ExportPlatform
    project_url: Optional[str] = None
    items_created: int = 0
    items_updated: int = 0
    items_failed: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def total_items(self) -> int:
        """Get total number of items processed."""
        return self.items_created + self.items_updated + self.items_failed

    @property
    def success_rate(self) -> float:
        """Get success rate as percentage."""
        if self.total_items == 0:
            return 100.0
        return ((self.items_created + self.items_updated) / self.total_items) * 100

    def add_error(self, error: str) -> None:
        """Add an error message."""
        self.errors.append(error)

    def add_warning(self, warning: str) -> None:
        """Add a warning message."""
        self.warnings.append(warning)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'success': self.success,
            'platform': self.platform.value,
            'project_url': self.project_url,
            'items_created': self.items_created,
            'items_updated': self.items_updated,
            'items_failed': self.items_failed,
            'total_items': self.total_items,
            'success_rate': self.success_rate,
            'errors': self.errors,
            'warnings': self.warnings,
            'metadata': self.metadata,
        }


@dataclass
class PlatformConfig:
    """Configuration for an export platform."""
    platform: ExportPlatform
    display_name: str
    required_env_vars: List[str]
    optional_env_vars: List[str] = field(default_factory=list)
    setup_url: str = ""
    features: List[str] = field(default_factory=list)
    description: str = ""
    item_type_mapping: Dict[str, str] = field(default_factory=dict)

    def is_configured(self) -> bool:
        """Check if all required environment variables are set.

        Returns:
            True if all required env vars are set
        """
        return all(os.getenv(var) for var in self.required_env_vars)

    def get_missing_vars(self) -> List[str]:
        """Get list of missing required environment variables.

        Returns:
            List of missing environment variable names
        """
        return [var for var in self.required_env_vars if not os.getenv(var)]

    def get_configured_vars(self) -> List[str]:
        """Get list of configured environment variables.

        Returns:
            List of configured environment variable names
        """
        return [var for var in self.required_env_vars if os.getenv(var)]

    def get_env_value(self, var_name: str) -> Optional[str]:
        """Get value of an environment variable.

        Args:
            var_name: Name of environment variable

        Returns:
            Value if set, None otherwise
        """
        return os.getenv(var_name)

    def supports_feature(self, feature: str) -> bool:
        """Check if platform supports a specific feature.

        Args:
            feature: Feature name to check

        Returns:
            True if feature is supported
        """
        return feature.lower() in [f.lower() for f in self.features]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'platform': self.platform.value,
            'display_name': self.display_name,
            'required_env_vars': self.required_env_vars,
            'optional_env_vars': self.optional_env_vars,
            'setup_url': self.setup_url,
            'features': self.features,
            'description': self.description,
            'is_configured': self.is_configured(),
            'missing_vars': self.get_missing_vars(),
        }


class BaseExporter(ABC):
    """Abstract base class for all platform exporters.

    All platform-specific exporters should inherit from this class and
    implement the required abstract methods.

    Example:
        class JiraExporter(BaseExporter):
            @property
            def platform(self) -> ExportPlatform:
                return ExportPlatform.JIRA

            @property
            def config(self) -> PlatformConfig:
                return PLATFORM_CONFIGS[ExportPlatform.JIRA]

            def validate_connection(self) -> bool:
                # Check Jira connection
                ...

            def export_roadmap(self, roadmap, **kwargs) -> ExportResult:
                # Export to Jira
                ...

            def get_field_mapping(self) -> Dict[str, str]:
                return {'name': 'summary', 'description': 'description', ...}
    """

    @property
    @abstractmethod
    def platform(self) -> ExportPlatform:
        """Return the platform this exporter handles.

        Returns:
            ExportPlatform enum value
        """
        pass

    @property
    @abstractmethod
    def config(self) -> PlatformConfig:
        """Return platform configuration.

        Returns:
            PlatformConfig for this platform
        """
        pass

    @abstractmethod
    def validate_connection(self) -> bool:
        """Validate that the platform connection is working.

        Returns:
            True if connection is valid, False otherwise
        """
        pass

    @abstractmethod
    def export_roadmap(self, roadmap: Roadmap, **kwargs) -> ExportResult:
        """Export a roadmap to the platform.

        Args:
            roadmap: Roadmap to export
            **kwargs: Platform-specific options

        Returns:
            ExportResult with details of the export
        """
        pass

    @abstractmethod
    def get_field_mapping(self) -> Dict[str, str]:
        """Return mapping of roadmap fields to platform fields.

        Returns:
            Dictionary mapping roadmap field names to platform field names
        """
        pass

    def supports_feature(self, feature: str) -> bool:
        """Check if platform supports a specific feature.

        Args:
            feature: Feature name to check

        Returns:
            True if feature is supported
        """
        return self.config.supports_feature(feature)

    def is_configured(self) -> bool:
        """Check if exporter is properly configured.

        Returns:
            True if all required env vars are set
        """
        return self.config.is_configured()

    def get_setup_instructions(self) -> str:
        """Get setup instructions for this platform.

        Returns:
            String with setup instructions
        """
        config = self.config
        missing = config.get_missing_vars()

        if not missing:
            return f"{config.display_name} is fully configured."

        lines = [
            f"To configure {config.display_name}:",
            "",
            "Set the following environment variables:",
        ]

        for var in missing:
            lines.append(f"  - {var}")

        if config.setup_url:
            lines.append("")
            lines.append(f"Setup guide: {config.setup_url}")

        return "\n".join(lines)


# Platform configurations
PLATFORM_CONFIGS: Dict[ExportPlatform, PlatformConfig] = {
    ExportPlatform.NOTION: PlatformConfig(
        platform=ExportPlatform.NOTION,
        display_name="Notion",
        required_env_vars=["NOTION_TOKEN", "NOTION_PARENT_PAGE_ID"],
        setup_url="https://developers.notion.com/",
        features=["hierarchical", "rich_text", "relations", "databases", "views", "pages"],
        description="Export to Notion workspace with full database and page support",
        item_type_mapping={
            "milestone": "page",
            "epic": "page",
            "story": "database_item",
            "task": "database_item",
        },
    ),
    ExportPlatform.JIRA: PlatformConfig(
        platform=ExportPlatform.JIRA,
        display_name="Jira",
        required_env_vars=["JIRA_URL", "JIRA_EMAIL", "JIRA_API_TOKEN"],
        optional_env_vars=["JIRA_PROJECT_KEY"],
        setup_url="https://support.atlassian.com/atlassian-account/docs/manage-api-tokens-for-your-atlassian-account/",
        features=["sprints", "epics", "stories", "subtasks", "workflows", "boards", "versions"],
        description="Export to Jira with epic/story/task hierarchy and sprint support",
        item_type_mapping={
            "milestone": "version",
            "epic": "epic",
            "story": "story",
            "task": "subtask",
        },
    ),
    ExportPlatform.ASANA: PlatformConfig(
        platform=ExportPlatform.ASANA,
        display_name="Asana",
        required_env_vars=["ASANA_ACCESS_TOKEN"],
        optional_env_vars=["ASANA_WORKSPACE_ID", "ASANA_PROJECT_ID"],
        setup_url="https://developers.asana.com/docs/personal-access-token",
        features=["projects", "sections", "tasks", "subtasks", "custom_fields", "milestones"],
        description="Export to Asana with project/section/task structure",
        item_type_mapping={
            "milestone": "milestone",
            "epic": "section",
            "story": "task",
            "task": "subtask",
        },
    ),
    ExportPlatform.LINEAR: PlatformConfig(
        platform=ExportPlatform.LINEAR,
        display_name="Linear",
        required_env_vars=["LINEAR_API_KEY"],
        optional_env_vars=["LINEAR_TEAM_ID"],
        setup_url="https://linear.app/settings/api",
        features=["projects", "cycles", "issues", "labels", "roadmaps", "milestones"],
        description="Export to Linear with project/cycle/issue structure",
        item_type_mapping={
            "milestone": "project",
            "epic": "project",
            "story": "issue",
            "task": "sub_issue",
        },
    ),
    ExportPlatform.TRELLO: PlatformConfig(
        platform=ExportPlatform.TRELLO,
        display_name="Trello",
        required_env_vars=["TRELLO_API_KEY", "TRELLO_TOKEN"],
        optional_env_vars=["TRELLO_BOARD_ID"],
        setup_url="https://trello.com/app-key",
        features=["boards", "lists", "cards", "checklists", "labels", "attachments"],
        description="Export to Trello with board/list/card structure",
        item_type_mapping={
            "milestone": "board",
            "epic": "list",
            "story": "card",
            "task": "checklist_item",
        },
    ),
    ExportPlatform.GITHUB_PROJECTS: PlatformConfig(
        platform=ExportPlatform.GITHUB_PROJECTS,
        display_name="GitHub Projects",
        required_env_vars=["GITHUB_TOKEN"],
        optional_env_vars=["GITHUB_OWNER", "GITHUB_REPO"],
        setup_url="https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens",
        features=["projects_v2", "issues", "milestones", "labels", "iterations", "custom_fields"],
        description="Export to GitHub Projects (v2) with issues and milestones",
        item_type_mapping={
            "milestone": "milestone",
            "epic": "issue",
            "story": "issue",
            "task": "task_list_item",
        },
    ),
    ExportPlatform.AZURE_DEVOPS: PlatformConfig(
        platform=ExportPlatform.AZURE_DEVOPS,
        display_name="Azure DevOps",
        required_env_vars=["AZURE_DEVOPS_ORG", "AZURE_DEVOPS_PAT"],
        optional_env_vars=["AZURE_DEVOPS_PROJECT"],
        setup_url="https://learn.microsoft.com/en-us/azure/devops/organizations/accounts/use-personal-access-tokens-to-authenticate",
        features=["epics", "features", "user_stories", "tasks", "sprints", "boards", "iterations"],
        description="Export to Azure DevOps with full work item hierarchy",
        item_type_mapping={
            "milestone": "epic",
            "epic": "feature",
            "story": "user_story",
            "task": "task",
        },
    ),
    ExportPlatform.MONDAY: PlatformConfig(
        platform=ExportPlatform.MONDAY,
        display_name="Monday.com",
        required_env_vars=["MONDAY_API_TOKEN"],
        optional_env_vars=["MONDAY_BOARD_ID"],
        setup_url="https://support.monday.com/hc/en-us/articles/360005144659-API-Tokens",
        features=["boards", "groups", "items", "subitems", "columns", "automations"],
        description="Export to Monday.com with board/group/item structure",
        item_type_mapping={
            "milestone": "group",
            "epic": "group",
            "story": "item",
            "task": "subitem",
        },
    ),
    ExportPlatform.CLICKUP: PlatformConfig(
        platform=ExportPlatform.CLICKUP,
        display_name="ClickUp",
        required_env_vars=["CLICKUP_API_TOKEN"],
        optional_env_vars=["CLICKUP_WORKSPACE_ID", "CLICKUP_SPACE_ID"],
        setup_url="https://clickup.com/api",
        features=["spaces", "folders", "lists", "tasks", "subtasks", "custom_fields", "goals"],
        description="Export to ClickUp with space/folder/list/task hierarchy",
        item_type_mapping={
            "milestone": "folder",
            "epic": "list",
            "story": "task",
            "task": "subtask",
        },
    ),
}


def get_platform_config(platform: Union[str, ExportPlatform]) -> PlatformConfig:
    """Get configuration for a platform.

    Args:
        platform: Platform name or enum

    Returns:
        PlatformConfig for the platform

    Raises:
        ValueError: If platform is not supported
    """
    if isinstance(platform, str):
        platform = ExportPlatform.from_string(platform)
    return PLATFORM_CONFIGS[platform]


def get_all_platforms() -> List[ExportPlatform]:
    """Get list of all supported platforms.

    Returns:
        List of all ExportPlatform enum values
    """
    return list(ExportPlatform)


def get_configured_platforms() -> List[ExportPlatform]:
    """Get list of platforms that are fully configured.

    Returns:
        List of platforms with all required env vars set
    """
    return [p for p in ExportPlatform if PLATFORM_CONFIGS[p].is_configured()]
