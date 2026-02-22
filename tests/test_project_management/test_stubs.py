"""Tests for PM client stub implementations (Linear, Jira, Notion)."""

import pytest

from arcane.core.project_management import JiraClient, LinearClient, NotionClient


class TestLinearClient:
    """Tests for LinearClient stub."""

    def test_instantiation(self):
        """LinearClient can be instantiated with API key."""
        client = LinearClient(api_key="lin_api_test123")
        assert client is not None
        assert client.api_key == "lin_api_test123"

    def test_name_property(self):
        """LinearClient has correct name."""
        client = LinearClient(api_key="test")
        assert client.name == "Linear"

    def test_graphql_url(self):
        """LinearClient has correct GraphQL URL."""
        client = LinearClient(api_key="test")
        assert client.GRAPHQL_URL == "https://api.linear.app/graphql"

    def test_headers_set_correctly(self):
        """LinearClient sets auth headers correctly."""
        client = LinearClient(api_key="lin_api_test123")
        assert client.headers["Authorization"] == "lin_api_test123"
        assert client.headers["Content-Type"] == "application/json"

    @pytest.mark.asyncio
    async def test_export_requires_team_id(self, sample_roadmap):
        """LinearClient.export() requires team_id."""
        client = LinearClient(api_key="test")
        with pytest.raises(ValueError, match="team_id is required"):
            await client.export(sample_roadmap)


class TestJiraClient:
    """Tests for JiraClient stub."""

    def test_instantiation(self):
        """JiraClient can be instantiated with credentials."""
        client = JiraClient(
            domain="test.atlassian.net",
            email="user@example.com",
            api_token="token123",
        )
        assert client is not None
        assert client.domain == "test.atlassian.net"

    def test_name_property(self):
        """JiraClient has correct name."""
        client = JiraClient(
            domain="test.atlassian.net",
            email="user@example.com",
            api_token="token123",
        )
        assert client.name == "Jira Cloud"

    def test_base_url_constructed(self):
        """JiraClient constructs correct base URL."""
        client = JiraClient(
            domain="mycompany.atlassian.net",
            email="user@example.com",
            api_token="token123",
        )
        assert client.base_url == "https://mycompany.atlassian.net/rest/api/3"

    def test_auth_tuple_set(self):
        """JiraClient sets auth tuple correctly."""
        client = JiraClient(
            domain="test.atlassian.net",
            email="user@example.com",
            api_token="token123",
        )
        assert client.auth == ("user@example.com", "token123")

    @pytest.mark.asyncio
    async def test_export_requires_project_key(self, sample_roadmap):
        """JiraClient.export() requires project_key."""
        client = JiraClient(
            domain="test.atlassian.net",
            email="user@example.com",
            api_token="token123",
        )
        with pytest.raises(ValueError, match="project_key is required"):
            await client.export(sample_roadmap)


class TestNotionClient:
    """Tests for NotionClient basics."""

    def test_instantiation(self):
        """NotionClient can be instantiated with API key."""
        client = NotionClient(api_key="secret_test123")
        assert client is not None
        assert client.api_key == "secret_test123"

    def test_name_property(self):
        """NotionClient has correct name."""
        client = NotionClient(api_key="test")
        assert client.name == "Notion"

    def test_api_url(self):
        """NotionClient has correct API URL."""
        client = NotionClient(api_key="test")
        assert client.API_URL == "https://api.notion.com/v1"

    def test_headers_set_correctly(self):
        """NotionClient sets headers correctly."""
        client = NotionClient(api_key="secret_test123")
        assert client.headers["Authorization"] == "Bearer secret_test123"
        assert client.headers["Content-Type"] == "application/json"
        assert "Notion-Version" in client.headers

    @pytest.mark.asyncio
    async def test_export_requires_parent_page_id(self, sample_roadmap):
        """NotionClient.export() raises ValueError without parent_page_id."""
        client = NotionClient(api_key="test")
        with pytest.raises(ValueError, match="parent_page_id is required"):
            await client.export(sample_roadmap)


class TestPMClientImports:
    """Tests that all clients are properly exported from package."""

    def test_import_progress_callback(self):
        """ProgressCallback type can be imported from package."""
        from arcane.core.project_management import ProgressCallback

        assert ProgressCallback is not None

    def test_import_from_package(self):
        """All clients can be imported from project_management package."""
        from arcane.core.project_management import (
            BasePMClient,
            CSVClient,
            ExportResult,
            JiraClient,
            LinearClient,
            NotionClient,
        )

        # All should be classes
        assert isinstance(CSVClient, type)
        assert isinstance(JiraClient, type)
        assert isinstance(LinearClient, type)
        assert isinstance(NotionClient, type)
        assert isinstance(BasePMClient, type)
        assert isinstance(ExportResult, type)

    def test_all_clients_inherit_from_base(self):
        """All concrete clients inherit from BasePMClient."""
        from arcane.core.project_management import (
            BasePMClient,
            CSVClient,
            JiraClient,
            LinearClient,
            NotionClient,
        )

        assert issubclass(CSVClient, BasePMClient)
        assert issubclass(JiraClient, BasePMClient)
        assert issubclass(LinearClient, BasePMClient)
        assert issubclass(NotionClient, BasePMClient)
