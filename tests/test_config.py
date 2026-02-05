"""Tests for arcane.config module."""

import pytest

from arcane.config import Settings


class TestSettings:
    """Tests for the Settings configuration class."""

    def test_default_values(self):
        """Verify Settings loads defaults correctly."""
        settings = Settings(_env_file=None)

        assert settings.anthropic_api_key == ""
        assert settings.model == "claude-sonnet-4-20250514"
        assert settings.max_retries == 3
        assert settings.linear_api_key is None
        assert settings.jira_domain is None
        assert settings.jira_email is None
        assert settings.jira_api_token is None
        assert settings.notion_api_key is None
        assert settings.interactive is True
        assert settings.auto_save is True
        assert settings.output_dir == "./"

    def test_env_var_override(self, monkeypatch):
        """Verify env var override works with ARCANE_ prefix."""
        monkeypatch.setenv("ARCANE_MODEL", "claude-opus-4-20250514")
        monkeypatch.setenv("ARCANE_MAX_RETRIES", "5")
        monkeypatch.setenv("ARCANE_INTERACTIVE", "false")

        settings = Settings(_env_file=None)

        assert settings.model == "claude-opus-4-20250514"
        assert settings.max_retries == 5
        assert settings.interactive is False

    def test_arcane_prefix_applied(self, monkeypatch):
        """Verify the ARCANE_ prefix is applied to env vars."""
        # Set env var WITHOUT prefix - should not be picked up
        monkeypatch.setenv("ANTHROPIC_API_KEY", "wrong-key")
        # Set env var WITH prefix - should be picked up
        monkeypatch.setenv("ARCANE_ANTHROPIC_API_KEY", "correct-key")

        settings = Settings(_env_file=None)

        assert settings.anthropic_api_key == "correct-key"

    def test_optional_pm_settings(self, monkeypatch):
        """Verify optional project management settings can be set."""
        monkeypatch.setenv("ARCANE_LINEAR_API_KEY", "lin_api_key")
        monkeypatch.setenv("ARCANE_JIRA_DOMAIN", "mycompany.atlassian.net")
        monkeypatch.setenv("ARCANE_JIRA_EMAIL", "user@example.com")
        monkeypatch.setenv("ARCANE_JIRA_API_TOKEN", "jira_token")
        monkeypatch.setenv("ARCANE_NOTION_API_KEY", "notion_key")

        settings = Settings(_env_file=None)

        assert settings.linear_api_key == "lin_api_key"
        assert settings.jira_domain == "mycompany.atlassian.net"
        assert settings.jira_email == "user@example.com"
        assert settings.jira_api_token == "jira_token"
        assert settings.notion_api_key == "notion_key"

    def test_output_dir_override(self, monkeypatch):
        """Verify output_dir can be overridden."""
        monkeypatch.setenv("ARCANE_OUTPUT_DIR", "/custom/output/path")

        settings = Settings(_env_file=None)

        assert settings.output_dir == "/custom/output/path"
