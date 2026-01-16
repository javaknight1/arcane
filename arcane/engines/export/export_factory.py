"""Factory for creating platform exporters."""

from typing import Optional, List, Dict, Any, Type, Union
import logging

from .base_exporter import (
    BaseExporter,
    ExportPlatform,
    ExportResult,
    PlatformConfig,
    PLATFORM_CONFIGS,
)

logger = logging.getLogger(__name__)


class ExporterFactory:
    """Factory for creating platform-specific exporters.

    This factory manages registration and creation of platform exporters.
    Exporters can be registered at runtime and created by platform name.

    Example:
        # Register a custom exporter
        ExporterFactory.register(ExportPlatform.JIRA, JiraExporter)

        # Create an exporter
        exporter = ExporterFactory.create('jira')

        # Export a roadmap
        result = exporter.export_roadmap(roadmap)
    """

    _exporters: Dict[ExportPlatform, Type[BaseExporter]] = {}

    @classmethod
    def register(cls, platform: ExportPlatform, exporter_class: Type[BaseExporter]) -> None:
        """Register an exporter class for a platform.

        Args:
            platform: Platform enum value
            exporter_class: Class that extends BaseExporter
        """
        if not issubclass(exporter_class, BaseExporter):
            raise TypeError(
                f"Exporter class must inherit from BaseExporter, "
                f"got {exporter_class.__name__}"
            )
        cls._exporters[platform] = exporter_class
        logger.debug(f"Registered exporter for {platform.value}: {exporter_class.__name__}")

    @classmethod
    def unregister(cls, platform: ExportPlatform) -> bool:
        """Unregister an exporter for a platform.

        Args:
            platform: Platform to unregister

        Returns:
            True if exporter was unregistered, False if not found
        """
        if platform in cls._exporters:
            del cls._exporters[platform]
            return True
        return False

    @classmethod
    def create(cls, platform: Union[str, ExportPlatform], **kwargs) -> BaseExporter:
        """Create an exporter for the specified platform.

        Args:
            platform: Platform name or enum value
            **kwargs: Arguments to pass to exporter constructor

        Returns:
            Configured exporter instance

        Raises:
            ValueError: If no exporter is registered for the platform
        """
        if isinstance(platform, str):
            platform = ExportPlatform.from_string(platform)

        if platform not in cls._exporters:
            available = ', '.join(p.value for p in cls._exporters.keys())
            raise ValueError(
                f"No exporter registered for {platform.value}. "
                f"Available exporters: {available or 'none'}"
            )

        exporter_class = cls._exporters[platform]
        return exporter_class(**kwargs)

    @classmethod
    def is_registered(cls, platform: Union[str, ExportPlatform]) -> bool:
        """Check if an exporter is registered for a platform.

        Args:
            platform: Platform name or enum value

        Returns:
            True if exporter is registered
        """
        if isinstance(platform, str):
            try:
                platform = ExportPlatform.from_string(platform)
            except ValueError:
                return False
        return platform in cls._exporters

    @classmethod
    def get_available_platforms(cls) -> List[ExportPlatform]:
        """Get list of platforms with registered exporters.

        Returns:
            List of platforms that have registered exporters
        """
        return list(cls._exporters.keys())

    @classmethod
    def get_configured_platforms(cls) -> List[ExportPlatform]:
        """Get list of platforms that are fully configured.

        A platform is considered configured if:
        1. An exporter is registered for it
        2. All required environment variables are set

        Returns:
            List of fully configured platforms
        """
        return [
            platform for platform in cls._exporters.keys()
            if PLATFORM_CONFIGS[platform].is_configured()
        ]

    @classmethod
    def get_unconfigured_platforms(cls) -> List[ExportPlatform]:
        """Get list of platforms that have exporters but are not configured.

        Returns:
            List of platforms with missing configuration
        """
        return [
            platform for platform in cls._exporters.keys()
            if not PLATFORM_CONFIGS[platform].is_configured()
        ]

    @classmethod
    def get_platform_config(cls, platform: Union[str, ExportPlatform]) -> PlatformConfig:
        """Get configuration for a platform.

        Args:
            platform: Platform name or enum value

        Returns:
            PlatformConfig for the platform

        Raises:
            ValueError: If platform is not supported
        """
        if isinstance(platform, str):
            platform = ExportPlatform.from_string(platform)
        return PLATFORM_CONFIGS[platform]

    @classmethod
    def get_all_platform_configs(cls) -> Dict[ExportPlatform, PlatformConfig]:
        """Get all platform configurations.

        Returns:
            Dictionary mapping platforms to their configs
        """
        return PLATFORM_CONFIGS.copy()

    @classmethod
    def get_platform_status(cls) -> Dict[str, Dict[str, Any]]:
        """Get status of all platforms.

        Returns:
            Dictionary with status information for each platform
        """
        status = {}
        for platform in ExportPlatform:
            config = PLATFORM_CONFIGS[platform]
            status[platform.value] = {
                'display_name': config.display_name,
                'has_exporter': platform in cls._exporters,
                'is_configured': config.is_configured(),
                'missing_vars': config.get_missing_vars(),
                'features': config.features,
            }
        return status

    @classmethod
    def clear_registrations(cls) -> None:
        """Clear all registered exporters.

        Useful for testing.
        """
        cls._exporters = {}


class NotionExporterAdapter(BaseExporter):
    """Adapter to make NotionImporter compatible with BaseExporter interface.

    This adapter wraps the existing NotionImporter to provide the
    BaseExporter interface for use with the ExporterFactory.
    """

    def __init__(self, **kwargs):
        """Initialize the Notion exporter adapter.

        Args:
            **kwargs: Arguments passed to NotionImporter
        """
        from arcane.engines.importers.notion import NotionImporter
        self._importer = NotionImporter(**kwargs)

    @property
    def platform(self) -> ExportPlatform:
        """Return the platform this exporter handles."""
        return ExportPlatform.NOTION

    @property
    def config(self) -> PlatformConfig:
        """Return platform configuration."""
        return PLATFORM_CONFIGS[ExportPlatform.NOTION]

    def validate_connection(self) -> bool:
        """Validate that the Notion connection is working.

        Returns:
            True if connection is valid
        """
        try:
            self._importer.notion.users.me()
            return True
        except Exception as e:
            logger.warning(f"Notion connection validation failed: {e}")
            return False

    def export_roadmap(self, roadmap, **kwargs) -> ExportResult:
        """Export a roadmap to Notion.

        Args:
            roadmap: Roadmap to export
            **kwargs: Additional options

        Returns:
            ExportResult with export details
        """
        try:
            result = self._importer.import_roadmap(roadmap)

            # Build project URL
            container_id = result.get('container_page_id', '')
            project_url = None
            if container_id:
                clean_id = container_id.replace('-', '')
                project_url = f"https://notion.so/{clean_id}"

            return ExportResult(
                success=True,
                platform=self.platform,
                project_url=project_url,
                items_created=len(self._importer.page_mapping),
                metadata={
                    'container_page_id': result.get('container_page_id'),
                    'database_id': result.get('database_id'),
                    **{k: v for k, v in result.items()
                       if k not in ['container_page_id', 'database_id']},
                },
            )
        except Exception as e:
            logger.error(f"Notion export failed: {e}")
            return ExportResult(
                success=False,
                platform=self.platform,
                errors=[str(e)],
            )

    def get_field_mapping(self) -> Dict[str, str]:
        """Return mapping of roadmap fields to Notion fields.

        Returns:
            Field mapping dictionary
        """
        return self._importer.field_mapper.get_field_mapping()


def _register_notion_exporter() -> bool:
    """Register the Notion exporter adapter.

    Returns:
        True if registration succeeded, False otherwise
    """
    try:
        # Check if NotionImporter is available
        from arcane.engines.importers.notion import NotionImporter
        ExporterFactory.register(ExportPlatform.NOTION, NotionExporterAdapter)
        logger.debug("Notion exporter registered successfully")
        return True
    except ImportError as e:
        logger.debug(f"Could not register Notion exporter: {e}")
        return False


def _register_jira_exporter() -> bool:
    """Register the Jira exporter.

    Returns:
        True if registration succeeded, False otherwise
    """
    try:
        from .jira_exporter import JiraExporter
        ExporterFactory.register(ExportPlatform.JIRA, JiraExporter)
        logger.debug("Jira exporter registered successfully")
        return True
    except ImportError as e:
        logger.debug(f"Could not register Jira exporter: {e}")
        return False


def _register_asana_exporter() -> bool:
    """Register the Asana exporter.

    Returns:
        True if registration succeeded, False otherwise
    """
    try:
        from .asana_exporter import AsanaExporter
        ExporterFactory.register(ExportPlatform.ASANA, AsanaExporter)
        logger.debug("Asana exporter registered successfully")
        return True
    except ImportError as e:
        logger.debug(f"Could not register Asana exporter: {e}")
        return False


def _register_linear_exporter() -> bool:
    """Register the Linear exporter.

    Returns:
        True if registration succeeded, False otherwise
    """
    try:
        from .linear_exporter import LinearExporter
        ExporterFactory.register(ExportPlatform.LINEAR, LinearExporter)
        logger.debug("Linear exporter registered successfully")
        return True
    except ImportError as e:
        logger.debug(f"Could not register Linear exporter: {e}")
        return False


def _auto_register_exporters() -> Dict[str, bool]:
    """Auto-register all available exporters.

    Returns:
        Dictionary mapping platform names to registration success
    """
    results = {}

    # Register Notion
    results['notion'] = _register_notion_exporter()

    # Register Jira
    results['jira'] = _register_jira_exporter()

    # Register Asana
    results['asana'] = _register_asana_exporter()

    # Register Linear
    results['linear'] = _register_linear_exporter()

    return results


# Auto-register exporters on module import
_registration_results = _auto_register_exporters()


def get_exporter(platform: Union[str, ExportPlatform], **kwargs) -> BaseExporter:
    """Convenience function to create an exporter.

    Args:
        platform: Platform name or enum value
        **kwargs: Arguments to pass to exporter constructor

    Returns:
        Configured exporter instance

    Raises:
        ValueError: If no exporter is registered for the platform
    """
    return ExporterFactory.create(platform, **kwargs)


def list_available_exporters() -> List[str]:
    """Get list of available exporter platform names.

    Returns:
        List of platform names with registered exporters
    """
    return [p.value for p in ExporterFactory.get_available_platforms()]


def list_configured_exporters() -> List[str]:
    """Get list of configured exporter platform names.

    Returns:
        List of platform names that are fully configured
    """
    return [p.value for p in ExporterFactory.get_configured_platforms()]
