"""Tests for export platform base classes and factory."""

import pytest
import os
from unittest.mock import patch, MagicMock
from typing import Dict

from arcane.engines.export.base_exporter import (
    BaseExporter,
    ExportPlatform,
    ExportResult,
    PlatformConfig,
    PLATFORM_CONFIGS,
    get_platform_config,
    get_all_platforms,
    get_configured_platforms,
)
from arcane.engines.export.export_factory import (
    ExporterFactory,
    get_exporter,
    list_available_exporters,
    list_configured_exporters,
)


class TestExportPlatform:
    """Tests for ExportPlatform enum."""

    def test_all_platforms_defined(self):
        """Test that all expected platforms are defined."""
        platforms = [p.value for p in ExportPlatform]

        assert 'notion' in platforms
        assert 'jira' in platforms
        assert 'asana' in platforms
        assert 'linear' in platforms
        assert 'trello' in platforms
        assert 'github_projects' in platforms
        assert 'azure_devops' in platforms
        assert 'monday' in platforms
        assert 'clickup' in platforms

    def test_from_string_valid(self):
        """Test from_string with valid platform names."""
        assert ExportPlatform.from_string('notion') == ExportPlatform.NOTION
        assert ExportPlatform.from_string('JIRA') == ExportPlatform.JIRA
        assert ExportPlatform.from_string('GitHub_Projects') == ExportPlatform.GITHUB_PROJECTS

    def test_from_string_with_whitespace(self):
        """Test from_string strips whitespace."""
        assert ExportPlatform.from_string('  notion  ') == ExportPlatform.NOTION

    def test_from_string_invalid(self):
        """Test from_string raises for invalid platform."""
        with pytest.raises(ValueError) as exc_info:
            ExportPlatform.from_string('invalid_platform')

        assert 'Unknown platform' in str(exc_info.value)
        assert 'invalid_platform' in str(exc_info.value)


class TestExportResult:
    """Tests for ExportResult dataclass."""

    def test_create_success_result(self):
        """Test creating a successful export result."""
        result = ExportResult(
            success=True,
            platform=ExportPlatform.NOTION,
            project_url="https://notion.so/test",
            items_created=10,
        )

        assert result.success is True
        assert result.platform == ExportPlatform.NOTION
        assert result.project_url == "https://notion.so/test"
        assert result.items_created == 10
        assert result.items_failed == 0
        assert result.errors == []

    def test_create_failure_result(self):
        """Test creating a failed export result."""
        result = ExportResult(
            success=False,
            platform=ExportPlatform.JIRA,
            errors=["Connection failed", "API rate limited"],
        )

        assert result.success is False
        assert result.platform == ExportPlatform.JIRA
        assert len(result.errors) == 2
        assert "Connection failed" in result.errors

    def test_total_items(self):
        """Test total_items property."""
        result = ExportResult(
            success=True,
            platform=ExportPlatform.NOTION,
            items_created=5,
            items_updated=3,
            items_failed=2,
        )

        assert result.total_items == 10

    def test_success_rate(self):
        """Test success_rate property."""
        result = ExportResult(
            success=True,
            platform=ExportPlatform.NOTION,
            items_created=8,
            items_updated=0,
            items_failed=2,
        )

        assert result.success_rate == 80.0

    def test_success_rate_no_items(self):
        """Test success_rate with no items returns 100%."""
        result = ExportResult(
            success=True,
            platform=ExportPlatform.NOTION,
        )

        assert result.success_rate == 100.0

    def test_add_error(self):
        """Test add_error method."""
        result = ExportResult(
            success=False,
            platform=ExportPlatform.NOTION,
        )

        result.add_error("Error 1")
        result.add_error("Error 2")

        assert len(result.errors) == 2
        assert "Error 1" in result.errors
        assert "Error 2" in result.errors

    def test_add_warning(self):
        """Test add_warning method."""
        result = ExportResult(
            success=True,
            platform=ExportPlatform.NOTION,
        )

        result.add_warning("Warning 1")

        assert len(result.warnings) == 1
        assert "Warning 1" in result.warnings

    def test_to_dict(self):
        """Test to_dict method."""
        result = ExportResult(
            success=True,
            platform=ExportPlatform.NOTION,
            project_url="https://notion.so/test",
            items_created=10,
            items_updated=5,
            items_failed=2,
            errors=["Error 1"],
            warnings=["Warning 1"],
            metadata={'key': 'value'},
        )

        data = result.to_dict()

        assert data['success'] is True
        assert data['platform'] == 'notion'
        assert data['project_url'] == "https://notion.so/test"
        assert data['items_created'] == 10
        assert data['total_items'] == 17
        assert data['success_rate'] == pytest.approx(88.235, rel=0.01)
        assert data['errors'] == ['Error 1']
        assert data['warnings'] == ['Warning 1']
        assert data['metadata'] == {'key': 'value'}


class TestPlatformConfig:
    """Tests for PlatformConfig dataclass."""

    def test_create_config(self):
        """Test creating a platform config."""
        config = PlatformConfig(
            platform=ExportPlatform.JIRA,
            display_name="Jira",
            required_env_vars=["JIRA_URL", "JIRA_API_TOKEN"],
            optional_env_vars=["JIRA_PROJECT_KEY"],
            setup_url="https://example.com",
            features=["epics", "stories"],
        )

        assert config.platform == ExportPlatform.JIRA
        assert config.display_name == "Jira"
        assert len(config.required_env_vars) == 2
        assert "JIRA_URL" in config.required_env_vars

    @patch.dict(os.environ, {'TEST_VAR_1': 'value1', 'TEST_VAR_2': 'value2'})
    def test_is_configured_true(self):
        """Test is_configured returns True when all vars are set."""
        config = PlatformConfig(
            platform=ExportPlatform.JIRA,
            display_name="Test",
            required_env_vars=["TEST_VAR_1", "TEST_VAR_2"],
        )

        assert config.is_configured() is True

    @patch.dict(os.environ, {'TEST_VAR_1': 'value1'}, clear=True)
    def test_is_configured_false(self):
        """Test is_configured returns False when vars are missing."""
        config = PlatformConfig(
            platform=ExportPlatform.JIRA,
            display_name="Test",
            required_env_vars=["TEST_VAR_1", "TEST_VAR_2"],
        )

        assert config.is_configured() is False

    @patch.dict(os.environ, {'TEST_VAR_1': 'value1'}, clear=True)
    def test_get_missing_vars(self):
        """Test get_missing_vars returns list of missing vars."""
        config = PlatformConfig(
            platform=ExportPlatform.JIRA,
            display_name="Test",
            required_env_vars=["TEST_VAR_1", "TEST_VAR_2", "TEST_VAR_3"],
        )

        missing = config.get_missing_vars()

        assert "TEST_VAR_1" not in missing
        assert "TEST_VAR_2" in missing
        assert "TEST_VAR_3" in missing

    @patch.dict(os.environ, {'TEST_VAR_1': 'value1', 'TEST_VAR_2': 'value2'})
    def test_get_configured_vars(self):
        """Test get_configured_vars returns list of set vars."""
        config = PlatformConfig(
            platform=ExportPlatform.JIRA,
            display_name="Test",
            required_env_vars=["TEST_VAR_1", "TEST_VAR_2", "TEST_VAR_3"],
        )

        configured = config.get_configured_vars()

        assert "TEST_VAR_1" in configured
        assert "TEST_VAR_2" in configured
        assert "TEST_VAR_3" not in configured

    @patch.dict(os.environ, {'TEST_VAR': 'test_value'})
    def test_get_env_value(self):
        """Test get_env_value returns env var value."""
        config = PlatformConfig(
            platform=ExportPlatform.JIRA,
            display_name="Test",
            required_env_vars=["TEST_VAR"],
        )

        assert config.get_env_value("TEST_VAR") == "test_value"
        assert config.get_env_value("MISSING_VAR") is None

    def test_supports_feature(self):
        """Test supports_feature method."""
        config = PlatformConfig(
            platform=ExportPlatform.JIRA,
            display_name="Test",
            required_env_vars=[],
            features=["epics", "stories", "sprints"],
        )

        assert config.supports_feature("epics") is True
        assert config.supports_feature("EPICS") is True  # Case insensitive
        assert config.supports_feature("kanban") is False

    def test_to_dict(self):
        """Test to_dict method."""
        config = PlatformConfig(
            platform=ExportPlatform.JIRA,
            display_name="Jira",
            required_env_vars=["VAR1"],
            optional_env_vars=["VAR2"],
            setup_url="https://example.com",
            features=["epics"],
            description="Test description",
        )

        data = config.to_dict()

        assert data['platform'] == 'jira'
        assert data['display_name'] == 'Jira'
        assert data['required_env_vars'] == ['VAR1']
        assert data['optional_env_vars'] == ['VAR2']
        assert data['setup_url'] == 'https://example.com'
        assert data['features'] == ['epics']
        assert data['description'] == 'Test description'
        assert 'is_configured' in data
        assert 'missing_vars' in data


class TestPlatformConfigs:
    """Tests for PLATFORM_CONFIGS constant."""

    def test_all_platforms_have_configs(self):
        """Test that all platforms have configurations."""
        for platform in ExportPlatform:
            assert platform in PLATFORM_CONFIGS, f"Missing config for {platform.value}"

    def test_notion_config(self):
        """Test Notion platform config."""
        config = PLATFORM_CONFIGS[ExportPlatform.NOTION]

        assert config.display_name == "Notion"
        assert "NOTION_TOKEN" in config.required_env_vars
        assert "NOTION_PARENT_PAGE_ID" in config.required_env_vars
        assert "hierarchical" in config.features
        assert "databases" in config.features

    def test_jira_config(self):
        """Test Jira platform config."""
        config = PLATFORM_CONFIGS[ExportPlatform.JIRA]

        assert config.display_name == "Jira"
        assert "JIRA_URL" in config.required_env_vars
        assert "JIRA_EMAIL" in config.required_env_vars
        assert "JIRA_API_TOKEN" in config.required_env_vars
        assert "sprints" in config.features
        assert "epics" in config.features

    def test_github_config(self):
        """Test GitHub Projects platform config."""
        config = PLATFORM_CONFIGS[ExportPlatform.GITHUB_PROJECTS]

        assert config.display_name == "GitHub Projects"
        assert "GITHUB_TOKEN" in config.required_env_vars
        assert "projects_v2" in config.features
        assert "issues" in config.features

    def test_all_configs_have_required_fields(self):
        """Test that all configs have required fields."""
        for platform, config in PLATFORM_CONFIGS.items():
            assert config.platform == platform
            assert config.display_name
            assert isinstance(config.required_env_vars, list)
            assert isinstance(config.features, list)


class TestGetPlatformConfig:
    """Tests for get_platform_config function."""

    def test_get_by_enum(self):
        """Test getting config by enum."""
        config = get_platform_config(ExportPlatform.NOTION)
        assert config.platform == ExportPlatform.NOTION

    def test_get_by_string(self):
        """Test getting config by string."""
        config = get_platform_config('jira')
        assert config.platform == ExportPlatform.JIRA

    def test_get_invalid_platform(self):
        """Test getting config for invalid platform raises."""
        with pytest.raises(ValueError):
            get_platform_config('invalid')


class TestGetAllPlatforms:
    """Tests for get_all_platforms function."""

    def test_returns_all_platforms(self):
        """Test that all platforms are returned."""
        platforms = get_all_platforms()

        assert len(platforms) == len(ExportPlatform)
        for platform in ExportPlatform:
            assert platform in platforms


class TestGetConfiguredPlatforms:
    """Tests for get_configured_platforms function."""

    @patch.dict(os.environ, {'NOTION_TOKEN': 'test', 'NOTION_PARENT_PAGE_ID': 'test'})
    def test_returns_configured_platforms(self):
        """Test that only configured platforms are returned."""
        configured = get_configured_platforms()

        assert ExportPlatform.NOTION in configured

    @patch.dict(os.environ, {}, clear=True)
    def test_returns_empty_when_none_configured(self):
        """Test returns empty list when no platforms configured."""
        # Clear all env vars
        for var in ['NOTION_TOKEN', 'NOTION_PARENT_PAGE_ID', 'JIRA_URL']:
            os.environ.pop(var, None)

        configured = get_configured_platforms()

        # Most platforms should not be configured
        assert len(configured) < len(ExportPlatform)


class MockExporter(BaseExporter):
    """Mock exporter for testing."""

    def __init__(self, **kwargs):
        self.kwargs = kwargs

    @property
    def platform(self) -> ExportPlatform:
        return ExportPlatform.JIRA

    @property
    def config(self) -> PlatformConfig:
        return PLATFORM_CONFIGS[ExportPlatform.JIRA]

    def validate_connection(self) -> bool:
        return True

    def export_roadmap(self, roadmap, **kwargs) -> ExportResult:
        return ExportResult(
            success=True,
            platform=self.platform,
            items_created=10,
        )

    def get_field_mapping(self) -> Dict[str, str]:
        return {'name': 'summary', 'description': 'description'}


class TestExporterFactory:
    """Tests for ExporterFactory class."""

    def setup_method(self):
        """Clear factory registrations before each test."""
        # Save current registrations
        self._saved_exporters = ExporterFactory._exporters.copy()

    def teardown_method(self):
        """Restore factory registrations after each test."""
        ExporterFactory._exporters = self._saved_exporters

    def test_register_exporter(self):
        """Test registering an exporter."""
        ExporterFactory.register(ExportPlatform.JIRA, MockExporter)

        assert ExporterFactory.is_registered(ExportPlatform.JIRA)

    def test_register_invalid_class(self):
        """Test registering non-BaseExporter class raises."""
        with pytest.raises(TypeError):
            ExporterFactory.register(ExportPlatform.JIRA, dict)

    def test_create_exporter(self):
        """Test creating an exporter."""
        ExporterFactory.register(ExportPlatform.JIRA, MockExporter)

        exporter = ExporterFactory.create('jira')

        assert isinstance(exporter, MockExporter)
        assert exporter.platform == ExportPlatform.JIRA

    def test_create_with_kwargs(self):
        """Test creating exporter with kwargs."""
        ExporterFactory.register(ExportPlatform.JIRA, MockExporter)

        exporter = ExporterFactory.create('jira', project_key='TEST')

        assert exporter.kwargs.get('project_key') == 'TEST'

    def test_create_unregistered_platform(self):
        """Test creating exporter for unregistered platform raises."""
        ExporterFactory.clear_registrations()

        with pytest.raises(ValueError) as exc_info:
            ExporterFactory.create('asana')

        assert 'No exporter registered' in str(exc_info.value)

    def test_unregister_exporter(self):
        """Test unregistering an exporter."""
        ExporterFactory.register(ExportPlatform.JIRA, MockExporter)
        assert ExporterFactory.is_registered(ExportPlatform.JIRA)

        result = ExporterFactory.unregister(ExportPlatform.JIRA)

        assert result is True
        assert not ExporterFactory.is_registered(ExportPlatform.JIRA)

    def test_unregister_nonexistent(self):
        """Test unregistering non-existent exporter returns False."""
        # Use TRELLO as it's not auto-registered
        result = ExporterFactory.unregister(ExportPlatform.TRELLO)
        assert result is False

    def test_is_registered_by_string(self):
        """Test is_registered with string."""
        ExporterFactory.register(ExportPlatform.JIRA, MockExporter)

        assert ExporterFactory.is_registered('jira') is True
        # TRELLO is not auto-registered
        assert ExporterFactory.is_registered('trello') is False

    def test_is_registered_invalid_string(self):
        """Test is_registered with invalid string returns False."""
        assert ExporterFactory.is_registered('invalid') is False

    def test_get_available_platforms(self):
        """Test getting available platforms."""
        ExporterFactory.register(ExportPlatform.JIRA, MockExporter)

        available = ExporterFactory.get_available_platforms()

        assert ExportPlatform.JIRA in available

    @patch.dict(os.environ, {
        'JIRA_URL': 'https://jira.example.com',
        'JIRA_EMAIL': 'test@example.com',
        'JIRA_API_TOKEN': 'token'
    })
    def test_get_configured_platforms(self):
        """Test getting configured platforms."""
        ExporterFactory.register(ExportPlatform.JIRA, MockExporter)

        configured = ExporterFactory.get_configured_platforms()

        assert ExportPlatform.JIRA in configured

    def test_get_unconfigured_platforms(self):
        """Test getting unconfigured platforms."""
        ExporterFactory.register(ExportPlatform.JIRA, MockExporter)

        # Ensure Jira env vars are not set
        for var in ['JIRA_URL', 'JIRA_EMAIL', 'JIRA_API_TOKEN']:
            os.environ.pop(var, None)

        unconfigured = ExporterFactory.get_unconfigured_platforms()

        assert ExportPlatform.JIRA in unconfigured

    def test_get_platform_config(self):
        """Test getting platform config from factory."""
        config = ExporterFactory.get_platform_config('jira')

        assert config.platform == ExportPlatform.JIRA

    def test_get_all_platform_configs(self):
        """Test getting all platform configs."""
        configs = ExporterFactory.get_all_platform_configs()

        assert len(configs) == len(ExportPlatform)
        for platform in ExportPlatform:
            assert platform in configs

    def test_get_platform_status(self):
        """Test getting platform status."""
        ExporterFactory.register(ExportPlatform.JIRA, MockExporter)

        status = ExporterFactory.get_platform_status()

        assert 'jira' in status
        assert status['jira']['display_name'] == 'Jira'
        assert status['jira']['has_exporter'] is True
        assert 'is_configured' in status['jira']
        assert 'features' in status['jira']

    def test_clear_registrations(self):
        """Test clearing all registrations."""
        ExporterFactory.register(ExportPlatform.JIRA, MockExporter)
        assert len(ExporterFactory.get_available_platforms()) > 0

        ExporterFactory.clear_registrations()

        assert len(ExporterFactory.get_available_platforms()) == 0


class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""

    def setup_method(self):
        """Save and clear registrations."""
        self._saved_exporters = ExporterFactory._exporters.copy()

    def teardown_method(self):
        """Restore registrations."""
        ExporterFactory._exporters = self._saved_exporters

    def test_get_exporter(self):
        """Test get_exporter convenience function."""
        ExporterFactory.register(ExportPlatform.JIRA, MockExporter)

        exporter = get_exporter('jira')

        assert isinstance(exporter, MockExporter)

    def test_list_available_exporters(self):
        """Test list_available_exporters function."""
        ExporterFactory.register(ExportPlatform.JIRA, MockExporter)

        available = list_available_exporters()

        assert 'jira' in available

    @patch.dict(os.environ, {
        'JIRA_URL': 'test',
        'JIRA_EMAIL': 'test',
        'JIRA_API_TOKEN': 'test'
    })
    def test_list_configured_exporters(self):
        """Test list_configured_exporters function."""
        ExporterFactory.register(ExportPlatform.JIRA, MockExporter)

        configured = list_configured_exporters()

        assert 'jira' in configured


class TestBaseExporterInterface:
    """Tests for BaseExporter interface methods."""

    def test_supports_feature(self):
        """Test supports_feature method."""
        exporter = MockExporter()

        # Jira supports sprints
        assert exporter.supports_feature('sprints') is True
        assert exporter.supports_feature('kanban') is False

    def test_is_configured(self):
        """Test is_configured method."""
        exporter = MockExporter()

        # Without env vars, should not be configured
        for var in ['JIRA_URL', 'JIRA_EMAIL', 'JIRA_API_TOKEN']:
            os.environ.pop(var, None)

        assert exporter.is_configured() is False

    @patch.dict(os.environ, {
        'JIRA_URL': 'test',
        'JIRA_EMAIL': 'test',
        'JIRA_API_TOKEN': 'test'
    })
    def test_is_configured_true(self):
        """Test is_configured when configured."""
        exporter = MockExporter()

        assert exporter.is_configured() is True

    def test_get_setup_instructions_unconfigured(self):
        """Test get_setup_instructions when not configured."""
        for var in ['JIRA_URL', 'JIRA_EMAIL', 'JIRA_API_TOKEN']:
            os.environ.pop(var, None)

        exporter = MockExporter()

        instructions = exporter.get_setup_instructions()

        assert 'Jira' in instructions
        assert 'JIRA_URL' in instructions
        assert 'environment variables' in instructions

    @patch.dict(os.environ, {
        'JIRA_URL': 'test',
        'JIRA_EMAIL': 'test',
        'JIRA_API_TOKEN': 'test'
    })
    def test_get_setup_instructions_configured(self):
        """Test get_setup_instructions when configured."""
        exporter = MockExporter()

        instructions = exporter.get_setup_instructions()

        assert 'fully configured' in instructions


class TestNotionExporterAdapter:
    """Tests for NotionExporterAdapter if available."""

    def test_notion_adapter_properties(self):
        """Test NotionExporterAdapter basic properties."""
        try:
            from arcane.engines.export.export_factory import NotionExporterAdapter

            # This will fail without proper env vars, but we can check the class exists
            assert NotionExporterAdapter is not None
        except ImportError:
            pytest.skip("Notion client not installed")

    def test_notion_registered_if_available(self):
        """Test that Notion is registered if available."""
        # Check if Notion was auto-registered
        try:
            import notion_client
            assert ExporterFactory.is_registered(ExportPlatform.NOTION)
        except ImportError:
            # Notion client not installed, skip
            pytest.skip("Notion client not installed")


class TestIntegration:
    """Integration tests for export platform system."""

    def setup_method(self):
        """Save registrations."""
        self._saved_exporters = ExporterFactory._exporters.copy()

    def teardown_method(self):
        """Restore registrations."""
        ExporterFactory._exporters = self._saved_exporters

    def test_full_export_workflow(self):
        """Test complete export workflow."""
        # Register mock exporter
        ExporterFactory.register(ExportPlatform.JIRA, MockExporter)

        # Create exporter
        exporter = ExporterFactory.create('jira')

        # Validate connection
        assert exporter.validate_connection() is True

        # Get field mapping
        mapping = exporter.get_field_mapping()
        assert 'name' in mapping
        assert 'description' in mapping

        # Export (with mock roadmap)
        mock_roadmap = MagicMock()
        result = exporter.export_roadmap(mock_roadmap)

        assert result.success is True
        assert result.platform == ExportPlatform.JIRA
        assert result.items_created > 0

    def test_multiple_exporters(self):
        """Test registering multiple exporters."""
        ExporterFactory.register(ExportPlatform.JIRA, MockExporter)

        # Create another mock exporter for Asana
        class AsanaMockExporter(MockExporter):
            @property
            def platform(self):
                return ExportPlatform.ASANA

            @property
            def config(self):
                return PLATFORM_CONFIGS[ExportPlatform.ASANA]

        ExporterFactory.register(ExportPlatform.ASANA, AsanaMockExporter)

        # Both should be available
        assert ExporterFactory.is_registered('jira')
        assert ExporterFactory.is_registered('asana')

        # Create both
        jira = ExporterFactory.create('jira')
        asana = ExporterFactory.create('asana')

        assert jira.platform == ExportPlatform.JIRA
        assert asana.platform == ExportPlatform.ASANA
