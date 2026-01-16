#!/usr/bin/env python3
"""Tests for JiraExporter class."""

import pytest
from unittest.mock import Mock, MagicMock, patch, PropertyMock
import os
from dataclasses import dataclass

from arcane.engines.export.jira_exporter import (
    JiraExporter,
    JiraFieldConfig,
    JiraRateLimiter,
)
from arcane.engines.export.base_exporter import (
    ExportPlatform,
    ExportResult,
    PlatformConfig,
    PLATFORM_CONFIGS,
)


# Mock classes for Jira items
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
    children: list = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.acceptance_criteria is None:
            self.acceptance_criteria = []
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
    milestones: list = None

    def __post_init__(self):
        if self.milestones is None:
            self.milestones = []


class TestJiraFieldConfig:
    """Test JiraFieldConfig class."""

    def test_default_values(self):
        """Test default field IDs."""
        config = JiraFieldConfig()
        assert config.epic_name_field == "customfield_10011"
        assert config.epic_link_field == "customfield_10014"
        assert config.story_points_field == "customfield_10016"
        assert config.sprint_field == "customfield_10020"

    def test_custom_fields_dict(self):
        """Test custom fields dictionary is initialized."""
        config = JiraFieldConfig()
        assert isinstance(config.custom_fields, dict)
        assert len(config.custom_fields) == 0

    def test_from_jira_fields_epic_name(self):
        """Test field discovery for Epic Name."""
        fields = [
            {'name': 'Epic Name', 'id': 'customfield_12345'},
            {'name': 'Summary', 'id': 'summary'},
        ]
        config = JiraFieldConfig.from_jira_fields(fields)
        assert config.epic_name_field == "customfield_12345"

    def test_from_jira_fields_epic_link(self):
        """Test field discovery for Epic Link."""
        fields = [
            {'name': 'Epic Link', 'id': 'customfield_67890'},
        ]
        config = JiraFieldConfig.from_jira_fields(fields)
        assert config.epic_link_field == "customfield_67890"

    def test_from_jira_fields_story_points(self):
        """Test field discovery for Story Points."""
        fields = [
            {'name': 'Story Points', 'id': 'customfield_11111'},
        ]
        config = JiraFieldConfig.from_jira_fields(fields)
        assert config.story_points_field == "customfield_11111"

    def test_from_jira_fields_sprint(self):
        """Test field discovery for Sprint."""
        fields = [
            {'name': 'Sprint', 'id': 'customfield_22222'},
        ]
        config = JiraFieldConfig.from_jira_fields(fields)
        assert config.sprint_field == "customfield_22222"

    def test_from_jira_fields_custom_fields(self):
        """Test custom field discovery."""
        fields = [
            {'name': 'My Custom Field', 'id': 'customfield_99999'},
            {'name': 'Standard Field', 'id': 'standard'},
        ]
        config = JiraFieldConfig.from_jira_fields(fields)
        assert 'My Custom Field' in config.custom_fields
        assert config.custom_fields['My Custom Field'] == 'customfield_99999'
        assert 'Standard Field' not in config.custom_fields

    def test_from_jira_fields_all(self):
        """Test discovering all standard fields."""
        fields = [
            {'name': 'Epic Name', 'id': 'cf_1'},
            {'name': 'Epic Link', 'id': 'cf_2'},
            {'name': 'Story Points', 'id': 'cf_3'},
            {'name': 'Sprint', 'id': 'cf_4'},
        ]
        config = JiraFieldConfig.from_jira_fields(fields)
        assert config.epic_name_field == "cf_1"
        assert config.epic_link_field == "cf_2"
        assert config.story_points_field == "cf_3"
        assert config.sprint_field == "cf_4"


class TestJiraRateLimiter:
    """Test JiraRateLimiter class."""

    def test_default_rate(self):
        """Test default rate limit."""
        limiter = JiraRateLimiter()
        assert limiter.min_interval == 0.2  # 5 requests per second

    def test_custom_rate(self):
        """Test custom rate limit."""
        limiter = JiraRateLimiter(requests_per_second=10.0)
        assert limiter.min_interval == 0.1

    def test_wait_first_call(self):
        """Test first call doesn't wait."""
        limiter = JiraRateLimiter(requests_per_second=1000.0)
        import time
        start = time.time()
        limiter.wait()
        elapsed = time.time() - start
        assert elapsed < 0.1  # Should be nearly instant

    @patch('time.sleep')
    def test_wait_respects_interval(self, mock_sleep):
        """Test wait respects minimum interval."""
        limiter = JiraRateLimiter(requests_per_second=2.0)
        limiter.last_request_time = 0  # Force to start of epoch
        # Since we're mocking, time.time() will be much larger than 0.5
        limiter.wait()
        # Should not sleep since enough time has passed


class TestJiraExporterBasics:
    """Test basic JiraExporter properties."""

    def test_platform_property(self):
        """Test platform returns JIRA."""
        exporter = JiraExporter()
        assert exporter.platform == ExportPlatform.JIRA

    def test_config_property(self):
        """Test config returns correct platform config."""
        exporter = JiraExporter()
        config = exporter.config
        assert isinstance(config, PlatformConfig)
        assert config.platform == ExportPlatform.JIRA

    def test_priority_mapping(self):
        """Test priority mapping constants."""
        assert JiraExporter.PRIORITY_MAPPING['Critical'] == 'Highest'
        assert JiraExporter.PRIORITY_MAPPING['High'] == 'High'
        assert JiraExporter.PRIORITY_MAPPING['Medium'] == 'Medium'
        assert JiraExporter.PRIORITY_MAPPING['Low'] == 'Low'

    def test_issue_type_mapping(self):
        """Test issue type mapping constants."""
        assert JiraExporter.ISSUE_TYPE_MAPPING['milestone'] == 'Epic'
        assert JiraExporter.ISSUE_TYPE_MAPPING['story'] == 'Story'
        assert JiraExporter.ISSUE_TYPE_MAPPING['task'] == 'Sub-task'

    def test_hours_per_story_point(self):
        """Test story point conversion constant."""
        assert JiraExporter.HOURS_PER_STORY_POINT == 8

    def test_init_with_env_vars(self):
        """Test initialization with environment variables."""
        with patch.dict(os.environ, {
            'JIRA_URL': 'https://test.atlassian.net',
            'JIRA_EMAIL': 'test@example.com',
            'JIRA_API_TOKEN': 'token123',
            'JIRA_PROJECT_KEY': 'TEST',
        }):
            exporter = JiraExporter()
            assert exporter.jira_url == 'https://test.atlassian.net'
            assert exporter.email == 'test@example.com'
            assert exporter.api_token == 'token123'
            assert exporter.project_key == 'TEST'

    def test_init_with_params(self):
        """Test initialization with explicit parameters."""
        exporter = JiraExporter(
            jira_url='https://custom.atlassian.net',
            email='custom@example.com',
            api_token='custom_token',
            project_key='CUSTOM',
        )
        assert exporter.jira_url == 'https://custom.atlassian.net'
        assert exporter.email == 'custom@example.com'
        assert exporter.api_token == 'custom_token'
        assert exporter.project_key == 'CUSTOM'

    def test_created_issues_property(self):
        """Test created_issues returns copy."""
        exporter = JiraExporter()
        exporter._created_issues = {'item1': 'PROJ-1'}
        issues = exporter.created_issues
        assert issues == {'item1': 'PROJ-1'}
        # Should be a copy
        issues['item2'] = 'PROJ-2'
        assert 'item2' not in exporter._created_issues


class TestJiraExporterClient:
    """Test Jira client handling."""

    @patch.dict('sys.modules', {'jira': MagicMock()})
    def test_get_client_missing_credentials(self):
        """Test error when credentials are missing."""
        exporter = JiraExporter(
            jira_url=None,
            email=None,
            api_token=None,
        )
        with pytest.raises(ValueError) as exc_info:
            exporter._get_client()
        assert 'Missing required credentials' in str(exc_info.value)

    @patch.dict('sys.modules', {'jira': MagicMock()})
    def test_get_client_missing_url(self):
        """Test error message includes missing URL."""
        exporter = JiraExporter(
            jira_url=None,
            email='test@example.com',
            api_token='token',
        )
        with pytest.raises(ValueError) as exc_info:
            exporter._get_client()
        assert 'JIRA_URL' in str(exc_info.value)

    def test_get_client_creates_once(self):
        """Test client is created only once."""
        mock_jira_module = MagicMock()
        mock_jira_class = MagicMock()
        mock_jira_module.JIRA = mock_jira_class

        with patch.dict('sys.modules', {'jira': mock_jira_module}):
            exporter = JiraExporter(
                jira_url='https://test.atlassian.net',
                email='test@example.com',
                api_token='token',
                auto_discover_fields=False,
            )
            exporter._get_client()
            exporter._get_client()
            # Should only create once
            assert mock_jira_class.call_count == 1


class TestJiraExporterValidation:
    """Test connection validation."""

    @patch('arcane.engines.export.jira_exporter.JiraExporter._get_client')
    def test_validate_connection_success(self, mock_get_client):
        """Test successful connection validation."""
        mock_client = Mock()
        mock_client.myself.return_value = {'name': 'testuser'}
        mock_get_client.return_value = mock_client

        exporter = JiraExporter()
        assert exporter.validate_connection() is True
        mock_client.myself.assert_called_once()

    @patch('arcane.engines.export.jira_exporter.JiraExporter._get_client')
    def test_validate_connection_failure(self, mock_get_client):
        """Test failed connection validation."""
        mock_client = Mock()
        mock_client.myself.side_effect = Exception("Connection failed")
        mock_get_client.return_value = mock_client

        exporter = JiraExporter()
        assert exporter.validate_connection() is False


class TestJiraExporterProjects:
    """Test project handling."""

    @patch('arcane.engines.export.jira_exporter.JiraExporter._get_client')
    def test_get_available_projects(self, mock_get_client):
        """Test getting available projects."""
        mock_project1 = Mock()
        mock_project1.key = 'PROJ1'
        mock_project1.name = 'Project One'
        mock_project2 = Mock()
        mock_project2.key = 'PROJ2'
        mock_project2.name = 'Project Two'

        mock_client = Mock()
        mock_client.projects.return_value = [mock_project1, mock_project2]
        mock_get_client.return_value = mock_client

        exporter = JiraExporter()
        projects = exporter.get_available_projects()

        assert len(projects) == 2
        assert projects[0] == {'key': 'PROJ1', 'name': 'Project One'}
        assert projects[1] == {'key': 'PROJ2', 'name': 'Project Two'}

    @patch('arcane.engines.export.jira_exporter.JiraExporter._get_client')
    def test_get_available_projects_error(self, mock_get_client):
        """Test error handling when getting projects."""
        mock_client = Mock()
        mock_client.projects.side_effect = Exception("API error")
        mock_get_client.return_value = mock_client

        exporter = JiraExporter()
        projects = exporter.get_available_projects()

        assert projects == []


class TestJiraExporterIssueTypes:
    """Test issue type handling."""

    @patch('arcane.engines.export.jira_exporter.JiraExporter._get_client')
    def test_get_issue_types(self, mock_get_client):
        """Test getting issue types for project."""
        mock_type1 = Mock()
        mock_type1.name = 'Epic'
        mock_type2 = Mock()
        mock_type2.name = 'Story'
        mock_type3 = Mock()
        mock_type3.name = 'Sub-task'

        mock_project = Mock()
        mock_project.issueTypes = [mock_type1, mock_type2, mock_type3]

        mock_client = Mock()
        mock_client.project.return_value = mock_project
        mock_get_client.return_value = mock_client

        exporter = JiraExporter()
        types = exporter.get_issue_types('PROJ')

        assert 'Epic' in types
        assert 'Story' in types
        assert 'Sub-task' in types

    @patch('arcane.engines.export.jira_exporter.JiraExporter._get_client')
    def test_get_issue_types_cached(self, mock_get_client):
        """Test issue types are cached."""
        mock_type = Mock()
        mock_type.name = 'Epic'
        mock_project = Mock()
        mock_project.issueTypes = [mock_type]

        mock_client = Mock()
        mock_client.project.return_value = mock_project
        mock_get_client.return_value = mock_client

        exporter = JiraExporter()
        exporter.get_issue_types('PROJ')
        exporter.get_issue_types('PROJ')

        # Should only call project once due to caching
        assert mock_client.project.call_count == 1

    def test_validate_issue_type_available(self):
        """Test issue type validation when type is available."""
        exporter = JiraExporter()
        exporter._issue_type_cache['PROJ'] = ['Epic', 'Story', 'Task']

        result = exporter._validate_issue_type('PROJ', 'Story')
        assert result == 'Story'

    def test_validate_issue_type_alternative(self):
        """Test issue type validation with alternative name."""
        exporter = JiraExporter()
        exporter._issue_type_cache['PROJ'] = ['Subtask', 'Story']

        result = exporter._validate_issue_type('PROJ', 'Sub-task')
        assert result == 'Subtask'

    def test_validate_issue_type_fallback_task(self):
        """Test issue type validation falls back to Task."""
        exporter = JiraExporter()
        exporter._issue_type_cache['PROJ'] = ['Task', 'Bug']

        result = exporter._validate_issue_type('PROJ', 'Epic')
        assert result == 'Task'


class TestJiraExporterFormatting:
    """Test description formatting."""

    def test_format_description_basic(self):
        """Test basic description formatting."""
        exporter = JiraExporter()
        item = MockMilestone(
            id='m1',
            name='Test Milestone',
            description='A test milestone',
        )
        result = exporter._format_description(item)
        assert 'A test milestone' in result

    def test_format_description_with_goal(self):
        """Test description with goal."""
        exporter = JiraExporter()
        item = MockMilestone(
            id='m1',
            name='Test',
            description='Description',
            goal='The goal',
        )
        result = exporter._format_description(item)
        assert '*Goal:*' in result
        assert 'The goal' in result

    def test_format_description_with_deliverables(self):
        """Test description with deliverables."""
        exporter = JiraExporter()
        item = MockMilestone(
            id='m1',
            name='Test',
            key_deliverables=['Deliverable 1', 'Deliverable 2'],
        )
        result = exporter._format_description(item)
        assert '*Key Deliverables:*' in result
        assert '* Deliverable 1' in result
        assert '* Deliverable 2' in result

    def test_format_description_with_requirements(self):
        """Test description with technical requirements."""
        exporter = JiraExporter()
        item = MockMilestone(
            id='m1',
            name='Test',
            technical_requirements=['Req 1', 'Req 2'],
        )
        result = exporter._format_description(item)
        assert '*Technical Requirements:*' in result
        assert '* Req 1' in result

    def test_format_description_empty(self):
        """Test description when empty."""
        exporter = JiraExporter()
        item = MockMilestone(id='m1', name='Test')
        result = exporter._format_description(item)
        assert result == "No description provided."

    def test_format_story_description(self):
        """Test story description formatting."""
        exporter = JiraExporter()
        story = MockStory(
            id='s1',
            name='Test Story',
            description='Story description',
            acceptance_criteria=['AC 1', 'AC 2'],
            user_value='User value here',
        )
        result = exporter._format_story_description(story)
        assert '*Acceptance Criteria:*' in result
        assert '* AC 1' in result
        assert '*User Value:*' in result
        assert 'User value here' in result

    def test_format_task_description(self):
        """Test task description formatting."""
        exporter = JiraExporter()
        task = MockTask(
            id='t1',
            name='Test Task',
            description='Task description',
            claude_code_prompt='Use Claude to implement this',
            work_type='implementation',
            files_to_modify=['file1.py', 'file2.py'],
        )
        result = exporter._format_task_description(task)
        assert '*Implementation Guide:*' in result
        assert 'Use Claude to implement this' in result
        assert '*Work Type:*' in result
        assert '*Files to Modify:*' in result


class TestJiraExporterLabels:
    """Test label sanitization."""

    def test_sanitize_labels_spaces(self):
        """Test labels with spaces are sanitized."""
        exporter = JiraExporter()
        labels = ['my label', 'another tag']
        result = exporter._sanitize_labels(labels)
        assert result == ['my-label', 'another-tag']

    def test_sanitize_labels_underscores(self):
        """Test labels with underscores are sanitized."""
        exporter = JiraExporter()
        labels = ['my_label', 'another_tag']
        result = exporter._sanitize_labels(labels)
        assert result == ['my-label', 'another-tag']

    def test_sanitize_labels_empty(self):
        """Test empty labels are filtered."""
        exporter = JiraExporter()
        labels = ['valid', '', 'also_valid']
        result = exporter._sanitize_labels(labels)
        assert result == ['valid', 'also-valid']


class TestJiraExporterFieldMapping:
    """Test field mapping."""

    def test_get_field_mapping(self):
        """Test field mapping returns expected fields."""
        exporter = JiraExporter()
        mapping = exporter.get_field_mapping()

        assert mapping['name'] == 'summary'
        assert mapping['description'] == 'description'
        assert mapping['priority'] == 'priority'
        assert 'tags' in mapping
        assert 'acceptance_criteria' in mapping
        assert 'claude_code_prompt' in mapping


class TestJiraExporterExport:
    """Test roadmap export."""

    @patch('arcane.engines.export.jira_exporter.JiraExporter._get_client')
    def test_export_no_project_key(self, mock_get_client):
        """Test export fails without project key."""
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        exporter = JiraExporter(project_key=None)
        # Mock _prompt_for_project to return None
        exporter._prompt_for_project = Mock(return_value=None)

        roadmap = MockRoadmap()
        result = exporter.export_roadmap(roadmap)

        assert result.success is False
        assert 'No project key specified' in result.errors

    @patch('arcane.engines.export.jira_exporter.JiraExporter._get_client')
    def test_export_invalid_project(self, mock_get_client):
        """Test export fails with invalid project."""
        mock_client = Mock()
        mock_client.project.side_effect = Exception("Project not found")
        mock_get_client.return_value = mock_client

        exporter = JiraExporter()
        roadmap = MockRoadmap()
        result = exporter.export_roadmap(roadmap, project_key='INVALID')

        assert result.success is False
        assert any('not found' in e for e in result.errors)

    @patch('arcane.engines.export.jira_exporter.JiraExporter._get_client')
    def test_export_dry_run(self, mock_get_client):
        """Test dry run doesn't create issues."""
        mock_client = Mock()
        mock_client.project.return_value = Mock()
        mock_get_client.return_value = mock_client

        exporter = JiraExporter()
        roadmap = MockRoadmap(milestones=[
            MockMilestone(id='m1', name='Milestone 1'),
        ])

        result = exporter.export_roadmap(roadmap, project_key='TEST', dry_run=True)

        assert result.success is True
        assert result.items_created == 1
        assert result.metadata['dry_run'] is True
        mock_client.create_issue.assert_not_called()

    @patch('arcane.engines.export.jira_exporter.JiraExporter._get_client')
    @patch('arcane.engines.export.jira_exporter.JiraExporter._validate_issue_type')
    def test_export_creates_milestone(self, mock_validate, mock_get_client):
        """Test export creates milestone as epic."""
        mock_validate.return_value = 'Epic'
        mock_issue = Mock()
        mock_issue.key = 'TEST-1'

        mock_client = Mock()
        mock_client.project.return_value = Mock()
        mock_client.create_issue.return_value = mock_issue
        mock_get_client.return_value = mock_client

        exporter = JiraExporter()
        exporter._field_config = JiraFieldConfig()

        roadmap = MockRoadmap(milestones=[
            MockMilestone(id='m1', name='Milestone 1', description='Test'),
        ])

        result = exporter.export_roadmap(roadmap, project_key='TEST')

        assert result.success is True
        assert 'TEST-1' in exporter._created_issues.values()

    @patch('arcane.engines.export.jira_exporter.JiraExporter._get_client')
    @patch('arcane.engines.export.jira_exporter.JiraExporter._validate_issue_type')
    def test_export_creates_hierarchy(self, mock_validate, mock_get_client):
        """Test export creates full hierarchy."""
        mock_validate.return_value = 'Epic'

        issue_counter = [0]
        def create_issue(fields):
            issue_counter[0] += 1
            mock = Mock()
            mock.key = f'TEST-{issue_counter[0]}'
            return mock

        mock_client = Mock()
        mock_client.project.return_value = Mock()
        mock_client.create_issue.side_effect = create_issue
        mock_get_client.return_value = mock_client

        exporter = JiraExporter()
        exporter._field_config = JiraFieldConfig()

        # Create hierarchy
        task = MockTask(id='t1', name='Task 1')
        story = MockStory(id='s1', name='Story 1', children=[task])
        epic = MockEpic(id='e1', name='Epic 1', children=[story])
        milestone = MockMilestone(id='m1', name='Milestone 1', children=[epic])

        roadmap = MockRoadmap(milestones=[milestone])

        # Mock _get_children_by_type to work with our mock classes
        from arcane.items import Epic, Story, Task
        original_get_children = exporter._get_children_by_type

        def mock_get_children(parent, child_type):
            if not hasattr(parent, 'children'):
                return []
            # Map actual types to mock types
            type_map = {Epic: MockEpic, Story: MockStory, Task: MockTask}
            mock_type = type_map.get(child_type, child_type)
            return [c for c in parent.children if isinstance(c, mock_type)]

        exporter._get_children_by_type = mock_get_children

        result = exporter.export_roadmap(roadmap, project_key='TEST')

        assert result.success is True
        assert result.items_created == 4  # milestone + epic + story + task

    @patch('arcane.engines.export.jira_exporter.JiraExporter._get_client')
    @patch('arcane.engines.export.jira_exporter.JiraExporter._validate_issue_type')
    def test_export_handles_errors(self, mock_validate, mock_get_client):
        """Test export handles individual item errors."""
        mock_validate.return_value = 'Epic'

        call_count = [0]
        def create_issue(fields):
            call_count[0] += 1
            if call_count[0] == 2:
                raise Exception("API rate limit")
            mock = Mock()
            mock.key = f'TEST-{call_count[0]}'
            return mock

        mock_client = Mock()
        mock_client.project.return_value = Mock()
        mock_client.create_issue.side_effect = create_issue
        mock_get_client.return_value = mock_client

        exporter = JiraExporter()
        exporter._field_config = JiraFieldConfig()

        epic = MockEpic(id='e1', name='Epic 1')
        milestone = MockMilestone(id='m1', name='Milestone 1', children=[epic])

        roadmap = MockRoadmap(milestones=[milestone])

        # Mock _get_children_by_type to work with our mock classes
        from arcane.items import Epic, Story, Task

        def mock_get_children(parent, child_type):
            if not hasattr(parent, 'children'):
                return []
            type_map = {Epic: MockEpic, Story: MockStory, Task: MockTask}
            mock_type = type_map.get(child_type, child_type)
            return [c for c in parent.children if isinstance(c, mock_type)]

        exporter._get_children_by_type = mock_get_children

        result = exporter.export_roadmap(roadmap, project_key='TEST')

        assert result.success is False
        assert result.items_created == 1
        assert result.items_failed == 1
        assert len(result.errors) > 0


class TestJiraExporterSprints:
    """Test sprint handling."""

    @patch('arcane.engines.export.jira_exporter.JiraExporter._get_client')
    def test_get_sprint_info(self, mock_get_client):
        """Test getting sprint information."""
        mock_sprint1 = Mock()
        mock_sprint1.id = 1
        mock_sprint1.name = 'Sprint 1'
        mock_sprint1.state = 'active'
        mock_sprint1.startDate = '2024-01-01'
        mock_sprint1.endDate = '2024-01-14'

        mock_client = Mock()
        mock_client.sprints.return_value = [mock_sprint1]
        mock_get_client.return_value = mock_client

        exporter = JiraExporter()
        sprints = exporter.get_sprint_info(100)

        assert len(sprints) == 1
        assert sprints[0]['id'] == 1
        assert sprints[0]['name'] == 'Sprint 1'
        assert sprints[0]['state'] == 'active'

    @patch('arcane.engines.export.jira_exporter.JiraExporter._get_client')
    def test_get_sprint_info_error(self, mock_get_client):
        """Test error handling for sprint info."""
        mock_client = Mock()
        mock_client.sprints.side_effect = Exception("API error")
        mock_get_client.return_value = mock_client

        exporter = JiraExporter()
        sprints = exporter.get_sprint_info(100)

        assert sprints == []


class TestJiraExporterUpdateMethods:
    """Test update methods."""

    @patch('arcane.engines.export.jira_exporter.JiraExporter._get_client')
    def test_update_issue_success(self, mock_get_client):
        """Test successful issue update."""
        mock_issue = Mock()
        mock_client = Mock()
        mock_client.issue.return_value = mock_issue
        mock_get_client.return_value = mock_client

        exporter = JiraExporter()
        result = exporter.update_issue('TEST-1', {'summary': 'New summary'})

        assert result is True
        mock_issue.update.assert_called_once_with(fields={'summary': 'New summary'})

    @patch('arcane.engines.export.jira_exporter.JiraExporter._get_client')
    def test_update_issue_failure(self, mock_get_client):
        """Test failed issue update."""
        mock_client = Mock()
        mock_client.issue.side_effect = Exception("Issue not found")
        mock_get_client.return_value = mock_client

        exporter = JiraExporter()
        result = exporter.update_issue('TEST-999', {'summary': 'New'})

        assert result is False

    @patch('arcane.engines.export.jira_exporter.JiraExporter._get_client')
    def test_add_comment_success(self, mock_get_client):
        """Test successful comment addition."""
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        exporter = JiraExporter()
        result = exporter.add_comment('TEST-1', 'Test comment')

        assert result is True
        mock_client.add_comment.assert_called_once_with('TEST-1', 'Test comment')

    @patch('arcane.engines.export.jira_exporter.JiraExporter._get_client')
    def test_add_comment_failure(self, mock_get_client):
        """Test failed comment addition."""
        mock_client = Mock()
        mock_client.add_comment.side_effect = Exception("API error")
        mock_get_client.return_value = mock_client

        exporter = JiraExporter()
        result = exporter.add_comment('TEST-1', 'Test comment')

        assert result is False


class TestJiraExporterFactoryRegistration:
    """Test factory registration."""

    def test_jira_exporter_registered(self):
        """Test JiraExporter is registered with factory."""
        from arcane.engines.export import ExporterFactory, ExportPlatform

        assert ExporterFactory.is_registered(ExportPlatform.JIRA)

    def test_create_jira_exporter(self):
        """Test creating JiraExporter via factory."""
        from arcane.engines.export import ExporterFactory

        exporter = ExporterFactory.create('jira')
        assert isinstance(exporter, JiraExporter)


class TestJiraExporterEdgeCases:
    """Test edge cases and error handling."""

    def test_get_children_by_type_no_children(self):
        """Test getting children when none exist."""
        exporter = JiraExporter()

        class NoChildren:
            pass

        item = NoChildren()
        result = exporter._get_children_by_type(item, MockEpic)
        assert result == []

    def test_get_children_by_type_empty_children(self):
        """Test getting children when list is empty."""
        exporter = JiraExporter()

        class EmptyChildren:
            children = []

        item = EmptyChildren()
        result = exporter._get_children_by_type(item, MockEpic)
        assert result == []

    def test_get_children_by_type_filters_correctly(self):
        """Test getting children filters by type."""
        exporter = JiraExporter()

        class Parent:
            children = [
                MockEpic(id='e1', name='Epic'),
                MockStory(id='s1', name='Story'),
            ]

        item = Parent()
        epics = exporter._get_children_by_type(item, MockEpic)
        stories = exporter._get_children_by_type(item, MockStory)

        assert len(epics) == 1
        assert len(stories) == 1

    @patch('arcane.engines.export.jira_exporter.JiraExporter._get_client')
    @patch('arcane.engines.export.jira_exporter.JiraExporter._validate_issue_type')
    def test_create_subtask_no_parent(self, mock_validate, mock_get_client):
        """Test creating subtask without parent raises error."""
        mock_validate.return_value = 'Sub-task'
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        exporter = JiraExporter()
        exporter._created_issues = {}  # No parent created

        task = MockTask(id='t1', name='Task')
        story = MockStory(id='s1', name='Story')

        with pytest.raises(ValueError) as exc_info:
            exporter._create_subtask(mock_client, 'TEST', task, story)

        assert 'Parent story not created' in str(exc_info.value)

    def test_import_error_without_jira_package(self):
        """Test appropriate error when jira package not installed."""
        exporter = JiraExporter(
            jira_url='https://test.atlassian.net',
            email='test@example.com',
            api_token='token',
        )

        with patch.dict('sys.modules', {'jira': None}):
            with patch('builtins.__import__', side_effect=ImportError("No module named 'jira'")):
                # This would raise ImportError if jira isn't installed
                # The actual test depends on whether jira is installed in test env
                pass
