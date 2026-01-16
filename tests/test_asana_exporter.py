#!/usr/bin/env python3
"""Tests for AsanaExporter class."""

import pytest
from unittest.mock import Mock, MagicMock, patch, PropertyMock
import os
from dataclasses import dataclass
from datetime import datetime, timedelta

from arcane.engines.export.asana_exporter import (
    AsanaExporter,
    AsanaFieldConfig,
    AsanaRateLimiter,
)
from arcane.engines.export.base_exporter import (
    ExportPlatform,
    ExportResult,
    PlatformConfig,
    PLATFORM_CONFIGS,
)


# Mock classes for Asana items
@dataclass
class MockMilestone:
    id: str
    name: str
    description: str = ""
    priority: str = "Medium"
    tags: list = None
    goal: str = ""
    key_deliverables: list = None
    technical_requirements: list = None
    target_date: str = None
    children: list = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.key_deliverables is None:
            self.key_deliverables = []
        if self.technical_requirements is None:
            self.technical_requirements = []
        if self.children is None:
            self.children = []


@dataclass
class MockEpic:
    id: str
    name: str
    description: str = ""
    priority: str = "Medium"
    tags: list = None
    target_date: str = None
    children: list = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.children is None:
            self.children = []


@dataclass
class MockStory:
    id: str
    name: str
    description: str = ""
    priority: str = "Medium"
    tags: list = None
    duration_hours: float = None
    acceptance_criteria: list = None
    user_value: str = ""
    scope: object = None
    target_date: str = None
    dependencies: list = None
    children: list = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.acceptance_criteria is None:
            self.acceptance_criteria = []
        if self.dependencies is None:
            self.dependencies = []
        if self.children is None:
            self.children = []


@dataclass
class MockTask:
    id: str
    name: str
    description: str = ""
    priority: str = "Medium"
    tags: list = None
    duration_hours: float = None
    claude_code_prompt: str = ""
    work_type: str = ""
    files_to_modify: list = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.files_to_modify is None:
            self.files_to_modify = []


@dataclass
class MockRoadmap:
    name: str = "Test Roadmap"
    description: str = ""
    milestones: list = None

    def __post_init__(self):
        if self.milestones is None:
            self.milestones = []


class TestAsanaFieldConfig:
    """Test AsanaFieldConfig class."""

    def test_default_values(self):
        """Test default field GIDs are None."""
        config = AsanaFieldConfig()
        assert config.priority_field_gid is None
        assert config.status_field_gid is None
        assert config.duration_field_gid is None
        assert config.story_points_field_gid is None

    def test_priority_options_default(self):
        """Test priority options default to empty dict."""
        config = AsanaFieldConfig()
        assert isinstance(config.priority_options, dict)
        assert len(config.priority_options) == 0

    def test_status_options_default(self):
        """Test status options default to empty dict."""
        config = AsanaFieldConfig()
        assert isinstance(config.status_options, dict)
        assert len(config.status_options) == 0

    def test_custom_fields_default(self):
        """Test custom fields default to empty dict."""
        config = AsanaFieldConfig()
        assert isinstance(config.custom_fields, dict)
        assert len(config.custom_fields) == 0

    def test_from_asana_fields_priority(self):
        """Test field discovery for Priority."""
        fields = [
            {
                'name': 'Priority',
                'gid': '12345',
                'enum_options': [
                    {'name': 'High', 'gid': 'high-gid'},
                    {'name': 'Medium', 'gid': 'medium-gid'},
                    {'name': 'Low', 'gid': 'low-gid'},
                ]
            },
        ]
        config = AsanaFieldConfig.from_asana_fields(fields)
        assert config.priority_field_gid == "12345"
        assert config.priority_options['High'] == 'high-gid'
        assert config.priority_options['Medium'] == 'medium-gid'
        assert config.priority_options['Low'] == 'low-gid'

    def test_from_asana_fields_status(self):
        """Test field discovery for Status."""
        fields = [
            {
                'name': 'Status',
                'gid': '67890',
                'enum_options': [
                    {'name': 'Not Started', 'gid': 'ns-gid'},
                    {'name': 'In Progress', 'gid': 'ip-gid'},
                ]
            },
        ]
        config = AsanaFieldConfig.from_asana_fields(fields)
        assert config.status_field_gid == "67890"
        assert config.status_options['Not Started'] == 'ns-gid'
        assert config.status_options['In Progress'] == 'ip-gid'

    def test_from_asana_fields_duration(self):
        """Test field discovery for Duration."""
        fields = [
            {'name': 'Duration', 'gid': 'dur-123'},
        ]
        config = AsanaFieldConfig.from_asana_fields(fields)
        assert config.duration_field_gid == "dur-123"

    def test_from_asana_fields_story_points(self):
        """Test field discovery for Story Points."""
        fields = [
            {'name': 'Story Points', 'gid': 'sp-123'},
        ]
        config = AsanaFieldConfig.from_asana_fields(fields)
        assert config.story_points_field_gid == "sp-123"

    def test_from_asana_fields_custom(self):
        """Test custom field discovery."""
        fields = [
            {'name': 'My Custom Field', 'gid': 'custom-123'},
            {'name': 'Priority', 'gid': 'pri-123'},  # Standard field
        ]
        config = AsanaFieldConfig.from_asana_fields(fields)
        assert 'My Custom Field' in config.custom_fields
        assert config.custom_fields['My Custom Field'] == 'custom-123'
        assert 'Priority' not in config.custom_fields


class TestAsanaRateLimiter:
    """Test AsanaRateLimiter class."""

    def test_default_rate(self):
        """Test default rate limit."""
        limiter = AsanaRateLimiter()
        assert limiter.min_interval == 0.05  # 20 requests per second

    def test_custom_rate(self):
        """Test custom rate limit."""
        limiter = AsanaRateLimiter(requests_per_second=10.0)
        assert limiter.min_interval == 0.1

    def test_wait_first_call(self):
        """Test first call doesn't wait significantly."""
        limiter = AsanaRateLimiter(requests_per_second=1000.0)
        import time
        start = time.time()
        limiter.wait()
        elapsed = time.time() - start
        assert elapsed < 0.1  # Should be nearly instant

    def test_get_request_count(self):
        """Test request counting."""
        limiter = AsanaRateLimiter(requests_per_second=1000.0)
        assert limiter.get_request_count() == 0
        limiter.wait()
        assert limiter.get_request_count() == 1
        limiter.wait()
        assert limiter.get_request_count() == 2

    def test_reset_window(self):
        """Test window reset."""
        limiter = AsanaRateLimiter(requests_per_second=1000.0)
        limiter.wait()
        limiter.wait()
        assert limiter.get_request_count() == 2
        limiter.reset_window()
        assert limiter.get_request_count() == 0


class TestAsanaExporterBasics:
    """Test basic AsanaExporter properties."""

    def test_platform_property(self):
        """Test platform returns ASANA."""
        exporter = AsanaExporter()
        assert exporter.platform == ExportPlatform.ASANA

    def test_config_property(self):
        """Test config returns correct platform config."""
        exporter = AsanaExporter()
        config = exporter.config
        assert isinstance(config, PlatformConfig)
        assert config.platform == ExportPlatform.ASANA

    def test_priority_mapping(self):
        """Test priority mapping constants."""
        assert AsanaExporter.PRIORITY_MAPPING['Critical'] == 'High'
        assert AsanaExporter.PRIORITY_MAPPING['High'] == 'High'
        assert AsanaExporter.PRIORITY_MAPPING['Medium'] == 'Medium'
        assert AsanaExporter.PRIORITY_MAPPING['Low'] == 'Low'

    def test_status_mapping(self):
        """Test status mapping constants."""
        assert AsanaExporter.STATUS_MAPPING['Not Started'] == 'Not Started'
        assert AsanaExporter.STATUS_MAPPING['In Progress'] == 'In Progress'
        assert AsanaExporter.STATUS_MAPPING['Completed'] == 'Completed'

    def test_hours_per_day(self):
        """Test hours per day constant."""
        assert AsanaExporter.HOURS_PER_DAY == 8

    def test_init_with_env_vars(self):
        """Test initialization with environment variables."""
        with patch.dict(os.environ, {
            'ASANA_ACCESS_TOKEN': 'test-token',
            'ASANA_WORKSPACE_ID': 'ws-123',
            'ASANA_PROJECT_ID': 'proj-456',
        }):
            exporter = AsanaExporter()
            assert exporter.access_token == 'test-token'
            assert exporter.workspace_id == 'ws-123'
            assert exporter.project_id == 'proj-456'

    def test_init_with_params(self):
        """Test initialization with explicit parameters."""
        exporter = AsanaExporter(
            access_token='custom-token',
            workspace_id='custom-ws',
            project_id='custom-proj',
        )
        assert exporter.access_token == 'custom-token'
        assert exporter.workspace_id == 'custom-ws'
        assert exporter.project_id == 'custom-proj'

    def test_created_items_property(self):
        """Test created_items returns copy."""
        exporter = AsanaExporter()
        exporter._created_items = {'item1': 'gid-1'}
        items = exporter.created_items
        assert items == {'item1': 'gid-1'}
        # Should be a copy
        items['item2'] = 'gid-2'
        assert 'item2' not in exporter._created_items


class TestAsanaExporterClient:
    """Test Asana client handling."""

    @patch.dict('sys.modules', {'asana': MagicMock()})
    def test_get_client_missing_token(self):
        """Test error when token is missing."""
        exporter = AsanaExporter(access_token=None)
        with pytest.raises(ValueError) as exc_info:
            exporter._get_client()
        assert 'ASANA_ACCESS_TOKEN' in str(exc_info.value)

    def test_get_client_creates_once(self):
        """Test client is created only once."""
        mock_asana_module = MagicMock()
        mock_configuration = MagicMock()
        mock_api_client = MagicMock()
        mock_asana_module.Configuration.return_value = mock_configuration
        mock_asana_module.ApiClient.return_value = mock_api_client

        with patch.dict('sys.modules', {'asana': mock_asana_module}):
            exporter = AsanaExporter(access_token='test-token')
            exporter._get_client()
            exporter._get_client()
            # Should only create once
            assert mock_asana_module.ApiClient.call_count == 1


class TestAsanaExporterValidation:
    """Test connection validation."""

    @patch('arcane.engines.export.asana_exporter.AsanaExporter._get_users_api')
    @patch('arcane.engines.export.asana_exporter.AsanaExporter._get_client')
    def test_validate_connection_success(self, mock_get_client, mock_get_users_api):
        """Test successful connection validation."""
        mock_users_api = Mock()
        mock_users_api.get_user.return_value = {'name': 'Test User'}
        mock_get_users_api.return_value = mock_users_api

        exporter = AsanaExporter(access_token='test-token')
        assert exporter.validate_connection() is True

    @patch('arcane.engines.export.asana_exporter.AsanaExporter._get_users_api')
    @patch('arcane.engines.export.asana_exporter.AsanaExporter._get_client')
    def test_validate_connection_failure(self, mock_get_client, mock_get_users_api):
        """Test failed connection validation."""
        mock_users_api = Mock()
        mock_users_api.get_user.side_effect = Exception("Connection failed")
        mock_get_users_api.return_value = mock_users_api

        exporter = AsanaExporter(access_token='test-token')
        assert exporter.validate_connection() is False


class TestAsanaExporterWorkspaces:
    """Test workspace handling."""

    @patch('arcane.engines.export.asana_exporter.AsanaExporter._get_users_api')
    @patch('arcane.engines.export.asana_exporter.AsanaExporter._get_client')
    def test_get_available_workspaces(self, mock_get_client, mock_get_users_api):
        """Test getting available workspaces."""
        mock_users_api = Mock()
        mock_users_api.get_user.return_value = {
            'workspaces': [
                {'gid': 'ws-1', 'name': 'Workspace 1'},
                {'gid': 'ws-2', 'name': 'Workspace 2'},
            ]
        }
        mock_get_users_api.return_value = mock_users_api

        exporter = AsanaExporter(access_token='test-token')
        workspaces = exporter.get_available_workspaces()

        assert len(workspaces) == 2
        assert workspaces[0] == {'gid': 'ws-1', 'name': 'Workspace 1'}

    @patch('arcane.engines.export.asana_exporter.AsanaExporter._get_users_api')
    @patch('arcane.engines.export.asana_exporter.AsanaExporter._get_client')
    def test_get_available_workspaces_error(self, mock_get_client, mock_get_users_api):
        """Test error handling for workspaces."""
        mock_users_api = Mock()
        mock_users_api.get_user.side_effect = Exception("API error")
        mock_get_users_api.return_value = mock_users_api

        exporter = AsanaExporter(access_token='test-token')
        workspaces = exporter.get_available_workspaces()

        assert workspaces == []


class TestAsanaExporterProjects:
    """Test project handling."""

    @patch('arcane.engines.export.asana_exporter.AsanaExporter._get_projects_api')
    @patch('arcane.engines.export.asana_exporter.AsanaExporter._get_client')
    def test_get_available_projects(self, mock_get_client, mock_get_projects_api):
        """Test getting available projects."""
        mock_projects_api = Mock()
        mock_projects_api.get_projects.return_value = [
            {'gid': 'proj-1', 'name': 'Project 1', 'archived': False},
            {'gid': 'proj-2', 'name': 'Project 2', 'archived': False},
            {'gid': 'proj-3', 'name': 'Archived', 'archived': True},
        ]
        mock_get_projects_api.return_value = mock_projects_api

        exporter = AsanaExporter(access_token='test-token', workspace_id='ws-1')
        projects = exporter.get_available_projects()

        assert len(projects) == 2
        assert projects[0] == {'gid': 'proj-1', 'name': 'Project 1'}

    @patch('arcane.engines.export.asana_exporter.AsanaExporter._get_projects_api')
    @patch('arcane.engines.export.asana_exporter.AsanaExporter._get_client')
    def test_create_project(self, mock_get_client, mock_get_projects_api):
        """Test creating a project."""
        mock_projects_api = Mock()
        mock_projects_api.create_project.return_value = {'gid': 'new-proj-123'}
        mock_get_projects_api.return_value = mock_projects_api

        exporter = AsanaExporter(access_token='test-token', workspace_id='ws-1')
        project_gid = exporter.create_project('New Project', notes='Description')

        assert project_gid == 'new-proj-123'
        mock_projects_api.create_project.assert_called_once()


class TestAsanaExporterFormatting:
    """Test description formatting."""

    def test_format_description_basic(self):
        """Test basic description formatting."""
        exporter = AsanaExporter()
        item = MockMilestone(
            id='m1',
            name='Test Milestone',
            description='A test milestone',
        )
        result = exporter._format_description(item)
        assert 'A test milestone' in result

    def test_format_description_with_goal(self):
        """Test description with goal."""
        exporter = AsanaExporter()
        item = MockMilestone(
            id='m1',
            name='Test',
            description='Description',
            goal='The goal',
        )
        result = exporter._format_description(item)
        assert 'Goal:' in result
        assert 'The goal' in result

    def test_format_description_with_deliverables(self):
        """Test description with deliverables."""
        exporter = AsanaExporter()
        item = MockMilestone(
            id='m1',
            name='Test',
            key_deliverables=['Deliverable 1', 'Deliverable 2'],
        )
        result = exporter._format_description(item)
        assert 'Key Deliverables:' in result
        assert 'Deliverable 1' in result
        assert 'Deliverable 2' in result

    def test_format_story_description(self):
        """Test story description formatting."""
        exporter = AsanaExporter()
        story = MockStory(
            id='s1',
            name='Test Story',
            description='Story description',
            acceptance_criteria=['AC 1', 'AC 2'],
            user_value='User value here',
        )
        result = exporter._format_story_description(story)
        assert 'Acceptance Criteria:' in result
        assert 'AC 1' in result
        assert 'User Value:' in result
        assert 'User value here' in result

    def test_format_task_description(self):
        """Test task description formatting."""
        exporter = AsanaExporter()
        task = MockTask(
            id='t1',
            name='Test Task',
            description='Task description',
            claude_code_prompt='Use Claude to implement this',
            work_type='implementation',
            duration_hours=8.0,
            files_to_modify=['file1.py', 'file2.py'],
        )
        result = exporter._format_task_description(task)
        assert 'Implementation Guide:' in result
        assert 'Use Claude to implement this' in result
        assert 'Work Type:' in result
        assert 'Files to Modify:' in result
        assert 'Estimated Duration:' in result


class TestAsanaExporterDateFormatting:
    """Test date formatting."""

    def test_format_date_string(self):
        """Test formatting date string."""
        exporter = AsanaExporter()
        result = exporter._format_date('2024-06-15')
        assert result == '2024-06-15'

    def test_format_date_iso_string(self):
        """Test formatting ISO date string."""
        exporter = AsanaExporter()
        result = exporter._format_date('2024-06-15T10:30:00Z')
        assert result == '2024-06-15'

    def test_format_date_datetime(self):
        """Test formatting datetime object."""
        exporter = AsanaExporter()
        dt = datetime(2024, 6, 15, 10, 30, 0)
        result = exporter._format_date(dt)
        assert result == '2024-06-15'


class TestAsanaExporterCustomFields:
    """Test custom field building."""

    def test_build_custom_fields_priority(self):
        """Test building priority custom field."""
        exporter = AsanaExporter()
        exporter._field_config = AsanaFieldConfig(
            priority_field_gid='pri-123',
            priority_options={'High': 'high-gid', 'Medium': 'med-gid'}
        )

        item = MockEpic(id='e1', name='Epic', priority='High')
        fields = exporter._build_custom_fields(item)

        assert 'pri-123' in fields
        assert fields['pri-123'] == 'high-gid'

    def test_build_custom_fields_duration(self):
        """Test building duration custom field."""
        exporter = AsanaExporter()
        exporter._field_config = AsanaFieldConfig(
            duration_field_gid='dur-123',
            story_points_field_gid='sp-123'
        )

        item = MockStory(id='s1', name='Story', duration_hours=16.0)
        fields = exporter._build_custom_fields(item)

        assert 'dur-123' in fields
        assert fields['dur-123'] == '16.0'
        assert 'sp-123' in fields
        assert fields['sp-123'] == '2'  # 16 hours / 8 hours per day = 2 points

    def test_build_custom_fields_empty(self):
        """Test building custom fields with no config."""
        exporter = AsanaExporter()
        exporter._field_config = AsanaFieldConfig()

        item = MockEpic(id='e1', name='Epic', priority='High')
        fields = exporter._build_custom_fields(item)

        assert fields == {}


class TestAsanaExporterFieldMapping:
    """Test field mapping."""

    def test_get_field_mapping(self):
        """Test field mapping returns expected fields."""
        exporter = AsanaExporter()
        mapping = exporter.get_field_mapping()

        assert mapping['name'] == 'name'
        assert mapping['description'] == 'notes'
        assert 'priority' in mapping
        assert 'duration_hours' in mapping
        assert 'tags' in mapping
        assert 'target_date' in mapping
        assert 'dependencies' in mapping


class TestAsanaExporterExport:
    """Test roadmap export."""

    @patch('arcane.engines.export.asana_exporter.AsanaExporter._get_client')
    def test_export_no_workspace(self, mock_get_client):
        """Test export fails without workspace."""
        exporter = AsanaExporter(access_token='token', workspace_id=None)
        exporter._discover_workspace = Mock(return_value=None)

        roadmap = MockRoadmap()
        result = exporter.export_roadmap(roadmap)

        assert result.success is False
        assert 'workspace' in result.errors[0].lower()

    @patch('arcane.engines.export.asana_exporter.AsanaExporter._get_client')
    @patch('arcane.engines.export.asana_exporter.AsanaExporter.create_project')
    def test_export_project_creation_fails(self, mock_create_project, mock_get_client):
        """Test export fails when project creation fails."""
        mock_create_project.return_value = None

        exporter = AsanaExporter(access_token='token', workspace_id='ws-1')
        roadmap = MockRoadmap()
        result = exporter.export_roadmap(roadmap)

        assert result.success is False
        assert 'Failed to create project' in result.errors[0]

    @patch('arcane.engines.export.asana_exporter.AsanaExporter._get_client')
    def test_export_dry_run(self, mock_get_client):
        """Test dry run doesn't create items."""
        exporter = AsanaExporter(access_token='token', workspace_id='ws-1')
        exporter._discover_fields = Mock()

        roadmap = MockRoadmap(milestones=[
            MockMilestone(id='m1', name='Milestone 1'),
        ])

        result = exporter.export_roadmap(roadmap, project_gid='proj-1', dry_run=True)

        assert result.success is True
        assert result.items_created == 1
        assert result.metadata['dry_run'] is True

    @patch('arcane.engines.export.asana_exporter.AsanaExporter._get_client')
    @patch('arcane.engines.export.asana_exporter.AsanaExporter._get_sections_api')
    @patch('arcane.engines.export.asana_exporter.AsanaExporter._get_tasks_api')
    def test_export_creates_section(self, mock_tasks_api, mock_sections_api, mock_get_client):
        """Test export creates section for milestone."""
        mock_section = Mock()
        mock_section.create_section_for_project.return_value = {'gid': 'section-1'}
        mock_sections_api.return_value = mock_section

        exporter = AsanaExporter(access_token='token', workspace_id='ws-1')
        exporter._discover_fields = Mock()
        exporter._field_config = AsanaFieldConfig()

        roadmap = MockRoadmap(milestones=[
            MockMilestone(id='m1', name='Milestone 1'),
        ])

        result = exporter.export_roadmap(roadmap, project_gid='proj-1')

        assert result.success is True
        assert 'section-1' in exporter._created_items.values()

    @patch('arcane.engines.export.asana_exporter.AsanaExporter._get_client')
    @patch('arcane.engines.export.asana_exporter.AsanaExporter._get_sections_api')
    @patch('arcane.engines.export.asana_exporter.AsanaExporter._get_tasks_api')
    def test_export_creates_hierarchy(self, mock_tasks_api, mock_sections_api, mock_get_client):
        """Test export creates full hierarchy."""
        mock_section = Mock()
        mock_section.create_section_for_project.return_value = {'gid': 'section-1'}
        mock_sections_api.return_value = mock_section

        item_counter = [0]
        def create_task(data, opts):
            item_counter[0] += 1
            return {'gid': f'task-{item_counter[0]}'}

        def create_subtask(parent_gid, data, opts):
            item_counter[0] += 1
            return {'gid': f'subtask-{item_counter[0]}'}

        mock_tasks = Mock()
        mock_tasks.create_task.side_effect = create_task
        mock_tasks.create_subtask_for_task.side_effect = create_subtask
        mock_tasks_api.return_value = mock_tasks

        exporter = AsanaExporter(access_token='token', workspace_id='ws-1')
        exporter._discover_fields = Mock()
        exporter._field_config = AsanaFieldConfig()

        # Create hierarchy
        task = MockTask(id='t1', name='Task 1')
        story = MockStory(id='s1', name='Story 1', children=[task])
        epic = MockEpic(id='e1', name='Epic 1', children=[story])
        milestone = MockMilestone(id='m1', name='Milestone 1', children=[epic])

        roadmap = MockRoadmap(milestones=[milestone])

        # Mock _get_children_by_type
        from arcane.items import Epic, Story, Task

        def mock_get_children(parent, child_type):
            if not hasattr(parent, 'children'):
                return []
            type_map = {Epic: MockEpic, Story: MockStory, Task: MockTask}
            mock_type = type_map.get(child_type, child_type)
            return [c for c in parent.children if isinstance(c, mock_type)]

        exporter._get_children_by_type = mock_get_children

        result = exporter.export_roadmap(roadmap, project_gid='proj-1', create_dependencies=False)

        assert result.success is True
        assert result.items_created == 4  # milestone + epic + story + task


class TestAsanaExporterUpdateMethods:
    """Test update methods."""

    @patch('arcane.engines.export.asana_exporter.AsanaExporter._get_tasks_api')
    @patch('arcane.engines.export.asana_exporter.AsanaExporter._get_client')
    def test_update_task_success(self, mock_get_client, mock_get_tasks_api):
        """Test successful task update."""
        mock_tasks_api = Mock()
        mock_get_tasks_api.return_value = mock_tasks_api

        exporter = AsanaExporter(access_token='token')
        result = exporter.update_task('task-123', {'name': 'New name'})

        assert result is True
        mock_tasks_api.update_task.assert_called_once()

    @patch('arcane.engines.export.asana_exporter.AsanaExporter._get_tasks_api')
    @patch('arcane.engines.export.asana_exporter.AsanaExporter._get_client')
    def test_update_task_failure(self, mock_get_client, mock_get_tasks_api):
        """Test failed task update."""
        mock_tasks_api = Mock()
        mock_tasks_api.update_task.side_effect = Exception("API error")
        mock_get_tasks_api.return_value = mock_tasks_api

        exporter = AsanaExporter(access_token='token')
        result = exporter.update_task('task-123', {'name': 'New name'})

        assert result is False

    @patch('arcane.engines.export.asana_exporter.AsanaExporter.update_task')
    def test_complete_task(self, mock_update_task):
        """Test completing a task."""
        mock_update_task.return_value = True

        exporter = AsanaExporter(access_token='token')
        result = exporter.complete_task('task-123')

        assert result is True
        mock_update_task.assert_called_once_with('task-123', {'completed': True})

    @patch('arcane.engines.export.asana_exporter.AsanaExporter._get_client')
    def test_add_comment_success(self, mock_get_client):
        """Test adding a comment."""
        mock_asana = MagicMock()
        mock_stories_api = Mock()
        mock_asana.StoriesApi.return_value = mock_stories_api

        with patch.dict('sys.modules', {'asana': mock_asana}):
            exporter = AsanaExporter(access_token='token')
            exporter._client = Mock()  # Pre-set client
            result = exporter.add_comment('task-123', 'Test comment')

            assert result is True

    @patch('arcane.engines.export.asana_exporter.AsanaExporter._get_tasks_api')
    @patch('arcane.engines.export.asana_exporter.AsanaExporter._get_client')
    def test_get_task(self, mock_get_client, mock_get_tasks_api):
        """Test getting a task."""
        mock_tasks_api = Mock()
        mock_tasks_api.get_task.return_value = {'gid': 'task-123', 'name': 'Test'}
        mock_get_tasks_api.return_value = mock_tasks_api

        exporter = AsanaExporter(access_token='token')
        task = exporter.get_task('task-123')

        assert task is not None
        assert task['gid'] == 'task-123'


class TestAsanaExporterFactoryRegistration:
    """Test factory registration."""

    def test_asana_exporter_registered(self):
        """Test AsanaExporter is registered with factory."""
        from arcane.engines.export import ExporterFactory, ExportPlatform

        assert ExporterFactory.is_registered(ExportPlatform.ASANA)

    def test_create_asana_exporter(self):
        """Test creating AsanaExporter via factory."""
        from arcane.engines.export import ExporterFactory

        exporter = ExporterFactory.create('asana')
        assert isinstance(exporter, AsanaExporter)


class TestAsanaExporterEdgeCases:
    """Test edge cases and error handling."""

    def test_get_children_by_type_no_children(self):
        """Test getting children when none exist."""
        exporter = AsanaExporter()

        class NoChildren:
            pass

        item = NoChildren()
        result = exporter._get_children_by_type(item, MockEpic)
        assert result == []

    def test_get_children_by_type_empty_children(self):
        """Test getting children when list is empty."""
        exporter = AsanaExporter()

        class EmptyChildren:
            children = []

        item = EmptyChildren()
        result = exporter._get_children_by_type(item, MockEpic)
        assert result == []

    @patch('arcane.engines.export.asana_exporter.AsanaExporter._get_tasks_api')
    @patch('arcane.engines.export.asana_exporter.AsanaExporter._get_client')
    def test_create_story_subtask_no_parent(self, mock_get_client, mock_get_tasks_api):
        """Test creating subtask without parent raises error."""
        exporter = AsanaExporter(access_token='token')

        story = MockStory(id='s1', name='Story')

        with pytest.raises(ValueError) as exc_info:
            exporter._create_story_subtask(None, story)

        assert 'Parent task not created' in str(exc_info.value)

    @patch('arcane.engines.export.asana_exporter.AsanaExporter._get_tasks_api')
    @patch('arcane.engines.export.asana_exporter.AsanaExporter._get_client')
    def test_create_task_subtask_no_parent(self, mock_get_client, mock_get_tasks_api):
        """Test creating task subtask without parent raises error."""
        exporter = AsanaExporter(access_token='token')

        task = MockTask(id='t1', name='Task')

        with pytest.raises(ValueError) as exc_info:
            exporter._create_task_subtask(None, task)

        assert 'Parent task not created' in str(exc_info.value)

    def test_get_or_create_tags_returns_empty(self):
        """Test get_or_create_tags returns empty list."""
        exporter = AsanaExporter()
        result = exporter._get_or_create_tags(['tag1', 'tag2'])
        assert result == []
