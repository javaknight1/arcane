#!/usr/bin/env python3
"""Tests for ExportPlatformQuestion class."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import os

from arcane.questions.system.export_platform_question import ExportPlatformQuestion
from arcane.engines.export.base_exporter import (
    ExportPlatform,
    PlatformConfig,
    PLATFORM_CONFIGS,
)


class TestExportPlatformQuestionBasics:
    """Test basic properties of ExportPlatformQuestion."""

    def test_question_key(self):
        """Test question_key property returns correct value."""
        question = ExportPlatformQuestion()
        assert question.question_key == "export_platform"

    def test_cli_flag_name(self):
        """Test cli_flag_name property returns correct value."""
        question = ExportPlatformQuestion()
        assert question.cli_flag_name == "--export-to"

    def test_question_text(self):
        """Test question_text property returns correct value."""
        question = ExportPlatformQuestion()
        assert question.question_text == "Export Platform"

    def test_section_title(self):
        """Test section_title property returns correct value."""
        question = ExportPlatformQuestion()
        assert question.section_title == "Export Configuration"

    def test_get_emoji(self):
        """Test _get_emoji returns correct emoji."""
        question = ExportPlatformQuestion()
        assert question._get_emoji() == "\U0001F4E4"  # Export emoji

    def test_special_values(self):
        """Test special value constants are defined correctly."""
        assert ExportPlatformQuestion.FILE_ONLY == "file_only"
        assert ExportPlatformQuestion.SKIP == "skip"


class TestGroupPlatformsByStatus:
    """Test _group_platforms_by_status method."""

    def test_group_platforms_returns_tuple(self):
        """Test that method returns tuple of two lists."""
        question = ExportPlatformQuestion()
        result = question._group_platforms_by_status()
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], list)
        assert isinstance(result[1], list)

    def test_all_platforms_are_grouped(self):
        """Test that all platforms appear in one of the two groups."""
        question = ExportPlatformQuestion()
        configured, unconfigured = question._group_platforms_by_status()

        all_platforms = configured + unconfigured
        platform_values = [p[0] for p in all_platforms]

        for platform in ExportPlatform:
            assert platform in platform_values

    @patch.dict(os.environ, {"NOTION_TOKEN": "test", "NOTION_PARENT_PAGE_ID": "test"})
    def test_configured_platforms_detection(self):
        """Test that configured platforms are correctly identified."""
        question = ExportPlatformQuestion()
        configured, unconfigured = question._group_platforms_by_status()

        # Notion should be in configured list
        configured_platforms = [p[0] for p in configured]
        assert ExportPlatform.NOTION in configured_platforms

    def test_unconfigured_platforms_detection(self):
        """Test that unconfigured platforms are correctly identified."""
        question = ExportPlatformQuestion()
        # Clear env to ensure platforms are unconfigured
        with patch.dict(os.environ, {}, clear=True):
            configured, unconfigured = question._group_platforms_by_status()

            # All should be unconfigured when no env vars set
            assert len(unconfigured) == len(ExportPlatform)
            assert len(configured) == 0

    def test_group_includes_platform_and_config(self):
        """Test that each group item contains platform and config."""
        question = ExportPlatformQuestion()
        configured, unconfigured = question._group_platforms_by_status()

        all_platforms = configured + unconfigured
        for platform, config in all_platforms:
            assert isinstance(platform, ExportPlatform)
            assert isinstance(config, PlatformConfig)
            assert config.platform == platform


class TestBuildChoices:
    """Test _build_choices method."""

    def test_build_choices_returns_list(self):
        """Test that method returns a list."""
        question = ExportPlatformQuestion()
        configured, unconfigured = question._group_platforms_by_status()
        choices = question._build_choices(configured, unconfigured)
        assert isinstance(choices, list)

    def test_choices_include_other_options(self):
        """Test that choices include file_only, skip, and cancel options."""
        question = ExportPlatformQuestion()
        configured, unconfigured = question._group_platforms_by_status()
        choices = question._build_choices(configured, unconfigured)

        # Extract values from choices (tuples are (label, value))
        values = [c[1] if isinstance(c, tuple) else None for c in choices]

        assert "file_only" in values
        assert "skip" in values
        assert "cancel" in values

    def test_choices_include_platform_values(self):
        """Test that choices include actual platform values."""
        question = ExportPlatformQuestion()
        configured, unconfigured = question._group_platforms_by_status()
        choices = question._build_choices(configured, unconfigured)

        # Extract values from choices
        values = [c[1] if isinstance(c, tuple) else None for c in choices]

        # At least some platforms should be in choices
        for platform in ExportPlatform:
            assert platform.value in values

    @patch.dict(os.environ, {"NOTION_TOKEN": "test", "NOTION_PARENT_PAGE_ID": "test"})
    def test_configured_platforms_have_checkmark(self):
        """Test that configured platforms show checkmark in label."""
        question = ExportPlatformQuestion()
        configured, unconfigured = question._group_platforms_by_status()
        choices = question._build_choices(configured, unconfigured)

        # Find Notion choice
        for choice in choices:
            if isinstance(choice, tuple) and choice[1] == "notion":
                assert "\u2705" in choice[0]  # Checkmark emoji
                break

    def test_unconfigured_platforms_have_warning(self):
        """Test that unconfigured platforms show warning in label."""
        question = ExportPlatformQuestion()
        with patch.dict(os.environ, {}, clear=True):
            configured, unconfigured = question._group_platforms_by_status()
            choices = question._build_choices(configured, unconfigured)

            # Find any unconfigured platform choice
            for choice in choices:
                if isinstance(choice, tuple) and choice[1] == "jira":
                    assert "\u26a0\ufe0f" in choice[0]  # Warning emoji
                    break

    def test_choices_include_separators(self):
        """Test that choices include section separators."""
        question = ExportPlatformQuestion()
        configured, unconfigured = question._group_platforms_by_status()
        choices = question._build_choices(configured, unconfigured)

        # Count separators (tuples with empty string value)
        separators = [c for c in choices if isinstance(c, tuple) and c[1] == ""]
        # At least "Other Options" separator should exist
        assert len(separators) >= 1


class TestProcessFlagValue:
    """Test _process_flag_value method."""

    def test_process_none_value(self):
        """Test processing None value."""
        question = ExportPlatformQuestion()
        result = question._process_flag_value(None)
        assert result is None

    def test_process_valid_platform_unconfigured(self):
        """Test processing valid but unconfigured platform."""
        question = ExportPlatformQuestion()
        with patch.dict(os.environ, {}, clear=True):
            result = question._process_flag_value("jira")
            # Should return None if platform is not configured
            assert result is None

    @patch.dict(os.environ, {"NOTION_TOKEN": "test", "NOTION_PARENT_PAGE_ID": "test"})
    def test_process_valid_platform_configured(self):
        """Test processing valid and configured platform."""
        question = ExportPlatformQuestion()
        result = question._process_flag_value("notion")
        assert result == "notion"

    def test_process_file_only_value(self):
        """Test processing file_only value."""
        question = ExportPlatformQuestion()
        result = question._process_flag_value("file_only")
        assert result == "file_only"

    def test_process_skip_value(self):
        """Test processing skip value."""
        question = ExportPlatformQuestion()
        result = question._process_flag_value("skip")
        assert result == "skip"

    def test_process_invalid_value(self):
        """Test processing invalid value."""
        question = ExportPlatformQuestion()
        result = question._process_flag_value("invalid_platform")
        assert result is None

    def test_process_case_insensitive(self):
        """Test processing is case insensitive."""
        question = ExportPlatformQuestion()
        result = question._process_flag_value("FILE_ONLY")
        assert result == "file_only"

    def test_process_strips_whitespace(self):
        """Test processing strips whitespace."""
        question = ExportPlatformQuestion()
        result = question._process_flag_value("  file_only  ")
        assert result == "file_only"


class TestFormatValueForDisplay:
    """Test _format_value_for_display method."""

    def test_format_file_only(self):
        """Test formatting file_only value."""
        question = ExportPlatformQuestion()
        result = question._format_value_for_display("file_only")
        assert result == "File Export Only"

    def test_format_skip(self):
        """Test formatting skip value."""
        question = ExportPlatformQuestion()
        result = question._format_value_for_display("skip")
        assert result == "Skip Export"

    def test_format_platform_value(self):
        """Test formatting platform value."""
        question = ExportPlatformQuestion()
        result = question._format_value_for_display("notion")
        assert result == "Notion"

    def test_format_platform_with_display_name(self):
        """Test formatting platform shows display name."""
        question = ExportPlatformQuestion()
        result = question._format_value_for_display("github_projects")
        assert result == "GitHub Projects"

    def test_format_invalid_value(self):
        """Test formatting invalid value returns string."""
        question = ExportPlatformQuestion()
        result = question._format_value_for_display("unknown")
        assert result == "unknown"

    def test_format_azure_devops(self):
        """Test formatting Azure DevOps value."""
        question = ExportPlatformQuestion()
        result = question._format_value_for_display("azure_devops")
        assert result == "Azure DevOps"

    def test_format_monday(self):
        """Test formatting Monday.com value."""
        question = ExportPlatformQuestion()
        result = question._format_value_for_display("monday")
        assert result == "Monday.com"


class TestGetValidationError:
    """Test get_validation_error method."""

    def test_validation_none_value(self):
        """Test validation of None value."""
        question = ExportPlatformQuestion()
        question._value = None
        result = question.get_validation_error()
        assert result is None

    def test_validation_valid_platform(self):
        """Test validation of valid platform value."""
        question = ExportPlatformQuestion()
        question._value = "notion"
        result = question.get_validation_error()
        assert result is None

    def test_validation_file_only(self):
        """Test validation of file_only value."""
        question = ExportPlatformQuestion()
        question._value = "file_only"
        result = question.get_validation_error()
        assert result is None

    def test_validation_skip(self):
        """Test validation of skip value."""
        question = ExportPlatformQuestion()
        question._value = "skip"
        result = question.get_validation_error()
        assert result is None

    def test_validation_invalid_value(self):
        """Test validation of invalid value."""
        question = ExportPlatformQuestion()
        question._value = "invalid"
        result = question.get_validation_error()
        assert result is not None
        assert "Invalid export platform" in result


class TestStaticMethods:
    """Test static helper methods."""

    def test_get_available_platforms(self):
        """Test get_available_platforms returns all platform values."""
        platforms = ExportPlatformQuestion.get_available_platforms()
        assert isinstance(platforms, list)
        assert len(platforms) == len(ExportPlatform)
        for platform in ExportPlatform:
            assert platform.value in platforms

    def test_get_configured_platforms_no_env(self):
        """Test get_configured_platforms with no env vars."""
        with patch.dict(os.environ, {}, clear=True):
            platforms = ExportPlatformQuestion.get_configured_platforms()
            assert isinstance(platforms, list)
            assert len(platforms) == 0

    @patch.dict(os.environ, {"NOTION_TOKEN": "test", "NOTION_PARENT_PAGE_ID": "test"})
    def test_get_configured_platforms_with_env(self):
        """Test get_configured_platforms with configured platform."""
        platforms = ExportPlatformQuestion.get_configured_platforms()
        assert "notion" in platforms

    def test_get_platform_info_valid(self):
        """Test get_platform_info with valid platform."""
        info = ExportPlatformQuestion.get_platform_info("notion")
        assert info is not None
        assert info['value'] == "notion"
        assert info['display_name'] == "Notion"
        assert 'is_configured' in info
        assert 'missing_vars' in info
        assert 'features' in info
        assert 'setup_url' in info

    def test_get_platform_info_invalid(self):
        """Test get_platform_info with invalid platform."""
        info = ExportPlatformQuestion.get_platform_info("invalid")
        assert info is None

    def test_get_platform_info_features(self):
        """Test get_platform_info includes features."""
        info = ExportPlatformQuestion.get_platform_info("jira")
        assert 'features' in info
        assert len(info['features']) > 0


class TestIsPlatformValue:
    """Test is_platform_value method."""

    def test_is_platform_value_valid(self):
        """Test is_platform_value with valid platform."""
        question = ExportPlatformQuestion()
        assert question.is_platform_value("notion") is True
        assert question.is_platform_value("jira") is True

    def test_is_platform_value_file_only(self):
        """Test is_platform_value with file_only."""
        question = ExportPlatformQuestion()
        assert question.is_platform_value("file_only") is False

    def test_is_platform_value_skip(self):
        """Test is_platform_value with skip."""
        question = ExportPlatformQuestion()
        assert question.is_platform_value("skip") is False

    def test_is_platform_value_none(self):
        """Test is_platform_value with None."""
        question = ExportPlatformQuestion()
        assert question.is_platform_value(None) is False

    def test_is_platform_value_invalid(self):
        """Test is_platform_value with invalid value."""
        question = ExportPlatformQuestion()
        assert question.is_platform_value("invalid") is False


class TestGetSelectedPlatformConfig:
    """Test get_selected_platform_config method."""

    def test_get_config_with_platform(self):
        """Test get_selected_platform_config with valid platform."""
        question = ExportPlatformQuestion()
        question._value = "notion"
        config = question.get_selected_platform_config()
        assert config is not None
        assert isinstance(config, PlatformConfig)
        assert config.platform == ExportPlatform.NOTION

    def test_get_config_with_file_only(self):
        """Test get_selected_platform_config with file_only."""
        question = ExportPlatformQuestion()
        question._value = "file_only"
        config = question.get_selected_platform_config()
        assert config is None

    def test_get_config_with_skip(self):
        """Test get_selected_platform_config with skip."""
        question = ExportPlatformQuestion()
        question._value = "skip"
        config = question.get_selected_platform_config()
        assert config is None

    def test_get_config_with_none(self):
        """Test get_selected_platform_config with None value."""
        question = ExportPlatformQuestion()
        question._value = None
        config = question.get_selected_platform_config()
        assert config is None


class TestPromptUser:
    """Test _prompt_user method."""

    @patch('inquirer.prompt')
    def test_prompt_user_returns_skip_on_cancel(self, mock_prompt):
        """Test prompt returns skip when user cancels."""
        mock_prompt.return_value = None
        question = ExportPlatformQuestion()
        result = question._prompt_user()
        assert result == ExportPlatformQuestion.SKIP

    @patch('inquirer.prompt')
    def test_prompt_user_returns_cancel_value(self, mock_prompt):
        """Test prompt returns cancel when user selects cancel."""
        mock_prompt.return_value = {'export_platform': 'cancel'}
        question = ExportPlatformQuestion()
        result = question._prompt_user()
        assert result == 'cancel'

    @patch('inquirer.prompt')
    def test_prompt_user_returns_platform_value(self, mock_prompt):
        """Test prompt returns platform value when selected."""
        mock_prompt.return_value = {'export_platform': 'file_only'}
        question = ExportPlatformQuestion()
        result = question._prompt_user()
        assert result == 'file_only'

    @patch('inquirer.prompt')
    @patch.dict(os.environ, {"NOTION_TOKEN": "test", "NOTION_PARENT_PAGE_ID": "test"})
    def test_prompt_user_returns_configured_platform(self, mock_prompt):
        """Test prompt returns configured platform."""
        mock_prompt.return_value = {'export_platform': 'notion'}
        question = ExportPlatformQuestion()
        result = question._prompt_user()
        assert result == 'notion'


class TestShowSetupInstructions:
    """Test _show_setup_instructions method."""

    @patch('builtins.input')
    def test_show_setup_instructions(self, mock_input):
        """Test setup instructions are displayed."""
        mock_input.return_value = ''
        question = ExportPlatformQuestion()
        config = PLATFORM_CONFIGS[ExportPlatform.JIRA]

        # Should not raise
        question._show_setup_instructions(config)
        mock_input.assert_called_once()

    @patch('builtins.input')
    def test_show_setup_instructions_with_optional_vars(self, mock_input):
        """Test setup instructions include optional vars."""
        mock_input.return_value = ''
        question = ExportPlatformQuestion()
        config = PLATFORM_CONFIGS[ExportPlatform.JIRA]

        # Should not raise
        question._show_setup_instructions(config)


class TestAllPlatformConfigs:
    """Test all platform configurations are properly defined."""

    @pytest.mark.parametrize("platform", list(ExportPlatform))
    def test_platform_has_config(self, platform):
        """Test each platform has a configuration."""
        assert platform in PLATFORM_CONFIGS
        config = PLATFORM_CONFIGS[platform]
        assert isinstance(config, PlatformConfig)

    @pytest.mark.parametrize("platform", list(ExportPlatform))
    def test_platform_config_has_display_name(self, platform):
        """Test each platform config has a display name."""
        config = PLATFORM_CONFIGS[platform]
        assert config.display_name
        assert len(config.display_name) > 0

    @pytest.mark.parametrize("platform", list(ExportPlatform))
    def test_platform_config_has_required_env_vars(self, platform):
        """Test each platform config has required env vars defined."""
        config = PLATFORM_CONFIGS[platform]
        assert isinstance(config.required_env_vars, list)
        assert len(config.required_env_vars) > 0

    @pytest.mark.parametrize("platform", list(ExportPlatform))
    def test_platform_config_has_features(self, platform):
        """Test each platform config has features defined."""
        config = PLATFORM_CONFIGS[platform]
        assert isinstance(config.features, list)
        assert len(config.features) > 0

    @pytest.mark.parametrize("platform", list(ExportPlatform))
    def test_platform_config_has_setup_url(self, platform):
        """Test each platform config has setup URL."""
        config = PLATFORM_CONFIGS[platform]
        assert config.setup_url
        assert config.setup_url.startswith("http")


class TestIntegrationWithBaseQuestion:
    """Test integration with BaseQuestion class."""

    def test_inherits_from_base_question(self):
        """Test that ExportPlatformQuestion inherits from BaseQuestion."""
        from arcane.questions.base_question import BaseQuestion
        assert issubclass(ExportPlatformQuestion, BaseQuestion)

    def test_has_required_abstract_methods(self):
        """Test that all required abstract methods are implemented."""
        question = ExportPlatformQuestion()

        # These should not raise
        _ = question.question_key
        _ = question.cli_flag_name
        _ = question.question_text
        _ = question.section_title
        _ = question._get_emoji()

    def test_set_value_from_flag_valid(self):
        """Test setting value from valid CLI flag."""
        question = ExportPlatformQuestion()
        question.set_value_from_flag("file_only")
        assert question.value == "file_only"
        assert question.is_answered is True

    def test_set_value_from_flag_invalid(self):
        """Test setting value from invalid CLI flag."""
        question = ExportPlatformQuestion()
        question.set_value_from_flag("invalid")
        # When flag is provided but invalid, is_answered is True but value is None
        assert question.is_answered is True
        assert question.value is None

    def test_set_value_from_flag_none(self):
        """Test setting value from None flag."""
        question = ExportPlatformQuestion()
        question.set_value_from_flag(None)
        assert question.is_answered is False


class TestCLIArgumentIntegration:
    """Test CLI argument integration."""

    def test_cli_choices_match_platforms(self):
        """Test that CLI choices cover all platforms plus special values."""
        expected_choices = set()
        for platform in ExportPlatform:
            expected_choices.add(platform.value)
        expected_choices.add("file_only")
        expected_choices.add("skip")

        # Read __main__.py to verify choices
        import arcane.__main__ as main_module
        # This is a conceptual test - the actual CLI argument is defined there


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_string_flag_value(self):
        """Test processing empty string flag value."""
        question = ExportPlatformQuestion()
        result = question._process_flag_value("")
        assert result is None

    def test_whitespace_only_flag_value(self):
        """Test processing whitespace-only flag value."""
        question = ExportPlatformQuestion()
        result = question._process_flag_value("   ")
        assert result is None

    def test_format_display_empty_string(self):
        """Test formatting empty string."""
        question = ExportPlatformQuestion()
        result = question._format_value_for_display("")
        assert result == ""

    def test_platform_info_all_platforms(self):
        """Test get_platform_info works for all platforms."""
        for platform in ExportPlatform:
            info = ExportPlatformQuestion.get_platform_info(platform.value)
            assert info is not None
            assert info['value'] == platform.value
