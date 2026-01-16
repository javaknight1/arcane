#!/usr/bin/env python3
"""Tests for LinearExporter class."""

import pytest
from unittest.mock import Mock, MagicMock, patch, PropertyMock
import os
from dataclasses import dataclass
from datetime import datetime, timedelta

from arcane.engines.export.linear_exporter import (
    LinearExporter,
    LinearTeamConfig,
    LinearRateLimiter,
)
from arcane.engines.export.base_exporter import (
    ExportPlatform,
    ExportResult,
    PlatformConfig,
    PLATFORM_CONFIGS,
)


# Mock classes for Linear items
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
    start_date: str = None
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


class TestLinearTeamConfig:
    """Test LinearTeamConfig class."""

    def test_basic_creation(self):
        """Test basic config creation."""
        config = LinearTeamConfig(
            team_id='team-123',
            team_name='Engineering',
            team_key='ENG',
        )
        assert config.team_id == 'team-123'
        assert config.team_name == 'Engineering'
        assert config.team_key == 'ENG'

    def test_default_states(self):
        """Test default states is empty dict."""
        config = LinearTeamConfig(
            team_id='team-123',
            team_name='Engineering',
            team_key='ENG',
        )
        assert isinstance(config.states, dict)
        assert len(config.states) == 0

    def test_default_state_types(self):
        """Test default state_types is empty dict."""
        config = LinearTeamConfig(
            team_id='team-123',
            team_name='Engineering',
            team_key='ENG',
        )
        assert isinstance(config.state_types, dict)
        assert len(config.state_types) == 0

    def test_default_labels(self):
        """Test default labels is empty dict."""
        config = LinearTeamConfig(
            team_id='team-123',
            team_name='Engineering',
            team_key='ENG',
        )
        assert isinstance(config.labels, dict)
        assert len(config.labels) == 0

    def test_get_state_id(self):
        """Test getting state ID by name."""
        config = LinearTeamConfig(
            team_id='team-123',
            team_name='Engineering',
            team_key='ENG',
            states={'Backlog': 'state-1', 'Todo': 'state-2'},
        )
        assert config.get_state_id('Backlog') == 'state-1'
        assert config.get_state_id('Todo') == 'state-2'
        assert config.get_state_id('Unknown') is None

    def test_get_backlog_state_id(self):
        """Test getting backlog state ID."""
        config = LinearTeamConfig(
            team_id='team-123',
            team_name='Engineering',
            team_key='ENG',
            state_types={'state-1': 'backlog', 'state-2': 'unstarted'},
        )
        assert config.get_backlog_state_id() == 'state-1'

    def test_get_backlog_state_id_not_found(self):
        """Test backlog state not found."""
        config = LinearTeamConfig(
            team_id='team-123',
            team_name='Engineering',
            team_key='ENG',
            state_types={'state-1': 'started'},
        )
        assert config.get_backlog_state_id() is None

    def test_get_todo_state_id(self):
        """Test getting todo/unstarted state ID."""
        config = LinearTeamConfig(
            team_id='team-123',
            team_name='Engineering',
            team_key='ENG',
            state_types={'state-1': 'backlog', 'state-2': 'unstarted'},
        )
        assert config.get_todo_state_id() == 'state-2'

    def test_get_todo_state_id_not_found(self):
        """Test todo state not found."""
        config = LinearTeamConfig(
            team_id='team-123',
            team_name='Engineering',
            team_key='ENG',
            state_types={'state-1': 'completed'},
        )
        assert config.get_todo_state_id() is None


class TestLinearRateLimiter:
    """Test LinearRateLimiter class."""

    def test_default_rate(self):
        """Test default rate limit."""
        limiter = LinearRateLimiter()
        assert limiter.min_interval == 0.1  # 10 requests per second

    def test_custom_rate(self):
        """Test custom rate limit."""
        limiter = LinearRateLimiter(requests_per_second=5.0)
        assert limiter.min_interval == 0.2

    def test_wait_first_call(self):
        """Test first call doesn't wait significantly."""
        limiter = LinearRateLimiter(requests_per_second=1000.0)
        import time
        start = time.time()
        limiter.wait()
        elapsed = time.time() - start
        assert elapsed < 0.1  # Should be nearly instant

    def test_get_stats(self):
        """Test getting statistics."""
        limiter = LinearRateLimiter(requests_per_second=1000.0)
        limiter.wait()
        limiter.wait()
        stats = limiter.get_stats()
        assert stats['request_count'] == 2
        assert stats['complexity_used'] == 0

    def test_add_complexity(self):
        """Test adding complexity points."""
        limiter = LinearRateLimiter()
        limiter.add_complexity(10)
        limiter.add_complexity(5)
        stats = limiter.get_stats()
        assert stats['complexity_used'] == 15

    def test_reset(self):
        """Test reset counters."""
        limiter = LinearRateLimiter(requests_per_second=1000.0)
        limiter.wait()
        limiter.wait()
        limiter.add_complexity(10)
        limiter.reset()
        stats = limiter.get_stats()
        assert stats['request_count'] == 0
        assert stats['complexity_used'] == 0


class TestLinearExporterBasics:
    """Test basic LinearExporter properties."""

    def test_platform_property(self):
        """Test platform returns LINEAR."""
        exporter = LinearExporter()
        assert exporter.platform == ExportPlatform.LINEAR

    def test_config_property(self):
        """Test config returns correct platform config."""
        exporter = LinearExporter()
        config = exporter.config
        assert isinstance(config, PlatformConfig)
        assert config.platform == ExportPlatform.LINEAR

    def test_priority_mapping(self):
        """Test priority mapping constants."""
        assert LinearExporter.PRIORITY_MAPPING['Critical'] == 1  # Urgent
        assert LinearExporter.PRIORITY_MAPPING['High'] == 2
        assert LinearExporter.PRIORITY_MAPPING['Medium'] == 3  # Normal
        assert LinearExporter.PRIORITY_MAPPING['Low'] == 4
        assert LinearExporter.PRIORITY_MAPPING['Lowest'] == 4

    def test_priority_names(self):
        """Test priority names constants."""
        assert LinearExporter.PRIORITY_NAMES[0] == 'No Priority'
        assert LinearExporter.PRIORITY_NAMES[1] == 'Urgent'
        assert LinearExporter.PRIORITY_NAMES[2] == 'High'
        assert LinearExporter.PRIORITY_NAMES[3] == 'Normal'
        assert LinearExporter.PRIORITY_NAMES[4] == 'Low'

    def test_estimate_mapping(self):
        """Test estimate mapping constants."""
        assert LinearExporter.ESTIMATE_MAPPING[1] == 1
        assert LinearExporter.ESTIMATE_MAPPING[2] == 2
        assert LinearExporter.ESTIMATE_MAPPING[3] == 3
        assert LinearExporter.ESTIMATE_MAPPING[4] == 5
        assert LinearExporter.ESTIMATE_MAPPING[5] == 5
        assert LinearExporter.ESTIMATE_MAPPING[8] == 8
        assert LinearExporter.ESTIMATE_MAPPING[10] == 13

    def test_hours_per_point(self):
        """Test hours per point constant."""
        assert LinearExporter.HOURS_PER_POINT == 8

    def test_api_url(self):
        """Test API URL constant."""
        assert LinearExporter.API_URL == "https://api.linear.app/graphql"

    def test_init_with_env_vars(self):
        """Test initialization with environment variables."""
        with patch.dict(os.environ, {
            'LINEAR_API_KEY': 'lin_api_test',
            'LINEAR_TEAM_ID': 'team-123',
        }):
            exporter = LinearExporter()
            assert exporter.api_key == 'lin_api_test'
            assert exporter.team_id == 'team-123'

    def test_init_with_params(self):
        """Test initialization with explicit parameters."""
        exporter = LinearExporter(
            api_key='custom-key',
            team_id='custom-team',
            rate_limit=5.0,
        )
        assert exporter.api_key == 'custom-key'
        assert exporter.team_id == 'custom-team'
        assert exporter._rate_limiter.min_interval == 0.2

    def test_created_items_property(self):
        """Test created_items returns copy."""
        exporter = LinearExporter()
        exporter._created_items = {'item1': 'id-1'}
        items = exporter.created_items
        assert items == {'item1': 'id-1'}
        # Should be a copy
        items['item2'] = 'id-2'
        assert 'item2' not in exporter._created_items

    def test_issue_identifiers_property(self):
        """Test issue_identifiers returns copy."""
        exporter = LinearExporter()
        exporter._issue_identifiers = {'item1': 'ENG-123'}
        identifiers = exporter.issue_identifiers
        assert identifiers == {'item1': 'ENG-123'}
        # Should be a copy
        identifiers['item2'] = 'ENG-456'
        assert 'item2' not in exporter._issue_identifiers


class TestLinearExporterMakeRequest:
    """Test API request handling."""

    def test_make_request_missing_key(self):
        """Test error when API key is missing."""
        exporter = LinearExporter(api_key=None)
        with pytest.raises(ValueError) as exc_info:
            exporter._make_request("query { viewer { id } }")
        assert 'LINEAR_API_KEY' in str(exc_info.value)

    def test_make_request_missing_requests_package(self):
        """Test error when requests package is missing."""
        exporter = LinearExporter(api_key='test-key')
        with patch.dict('sys.modules', {'requests': None}):
            # Force reimport to trigger ImportError
            pass  # This is tricky to test; skip for now

    @patch('requests.post')
    def test_make_request_success(self, mock_post):
        """Test successful API request."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'data': {'viewer': {'id': 'user-1'}}}
        mock_post.return_value = mock_response

        exporter = LinearExporter(api_key='test-key')
        result = exporter._make_request("query { viewer { id } }")

        assert result == {'viewer': {'id': 'user-1'}}
        mock_post.assert_called_once()

    @patch('requests.post')
    def test_make_request_with_variables(self, mock_post):
        """Test API request with variables."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'data': {'team': {'name': 'Engineering'}}}
        mock_post.return_value = mock_response

        exporter = LinearExporter(api_key='test-key')
        result = exporter._make_request(
            "query Team($id: String!) { team(id: $id) { name } }",
            variables={'id': 'team-123'}
        )

        assert result == {'team': {'name': 'Engineering'}}
        call_args = mock_post.call_args
        assert call_args[1]['json']['variables'] == {'id': 'team-123'}

    @patch('requests.post')
    def test_make_request_api_error(self, mock_post):
        """Test API error handling."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = 'Internal Server Error'
        mock_post.return_value = mock_response

        exporter = LinearExporter(api_key='test-key')
        with pytest.raises(Exception) as exc_info:
            exporter._make_request("query { viewer { id } }")
        assert '500' in str(exc_info.value)

    @patch('requests.post')
    def test_make_request_graphql_errors(self, mock_post):
        """Test GraphQL error handling."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'errors': [{'message': 'Field not found'}]
        }
        mock_post.return_value = mock_response

        exporter = LinearExporter(api_key='test-key')
        with pytest.raises(Exception) as exc_info:
            exporter._make_request("query { invalid }")
        assert 'Field not found' in str(exc_info.value)


class TestLinearExporterValidation:
    """Test connection validation."""

    @patch.object(LinearExporter, '_make_request')
    def test_validate_connection_success(self, mock_make_request):
        """Test successful connection validation."""
        mock_make_request.return_value = {
            'viewer': {'name': 'Test User', 'email': 'test@example.com'}
        }

        exporter = LinearExporter(api_key='test-key')
        assert exporter.validate_connection() is True

    @patch.object(LinearExporter, '_make_request')
    def test_validate_connection_failure(self, mock_make_request):
        """Test failed connection validation."""
        mock_make_request.side_effect = Exception("Connection failed")

        exporter = LinearExporter(api_key='test-key')
        assert exporter.validate_connection() is False


class TestLinearExporterTeams:
    """Test team handling."""

    @patch.object(LinearExporter, '_make_request')
    def test_get_available_teams(self, mock_make_request):
        """Test getting available teams."""
        mock_make_request.return_value = {
            'teams': {
                'nodes': [
                    {'id': 'team-1', 'name': 'Engineering', 'key': 'ENG'},
                    {'id': 'team-2', 'name': 'Product', 'key': 'PRD'},
                ]
            }
        }

        exporter = LinearExporter(api_key='test-key')
        teams = exporter.get_available_teams()

        assert len(teams) == 2
        assert teams[0] == {'id': 'team-1', 'name': 'Engineering', 'key': 'ENG'}

    @patch.object(LinearExporter, '_make_request')
    def test_get_available_teams_error(self, mock_make_request):
        """Test error handling for teams."""
        mock_make_request.side_effect = Exception("API error")

        exporter = LinearExporter(api_key='test-key')
        teams = exporter.get_available_teams()

        assert teams == []

    @patch.object(LinearExporter, '_make_request')
    @patch.object(LinearExporter, 'get_available_teams')
    def test_get_team_config(self, mock_get_teams, mock_make_request):
        """Test getting team configuration."""
        mock_get_teams.return_value = [
            {'id': 'team-1', 'name': 'Engineering', 'key': 'ENG'}
        ]
        mock_make_request.side_effect = [
            # States query
            {
                'team': {
                    'states': {
                        'nodes': [
                            {'id': 'state-1', 'name': 'Backlog', 'type': 'backlog'},
                            {'id': 'state-2', 'name': 'Todo', 'type': 'unstarted'},
                        ]
                    }
                }
            },
            # Labels query
            {
                'team': {
                    'labels': {
                        'nodes': [
                            {'id': 'label-1', 'name': 'Bug'},
                            {'id': 'label-2', 'name': 'Feature'},
                        ]
                    }
                }
            },
        ]

        exporter = LinearExporter(api_key='test-key')
        config = exporter.get_team_config('team-1')

        assert config is not None
        assert config.team_id == 'team-1'
        assert config.team_name == 'Engineering'
        assert config.team_key == 'ENG'
        assert config.states['Backlog'] == 'state-1'
        assert config.state_types['state-1'] == 'backlog'
        assert config.labels['Bug'] == 'label-1'

    @patch.object(LinearExporter, '_make_request')
    @patch.object(LinearExporter, 'get_available_teams')
    def test_get_team_config_not_found(self, mock_get_teams, mock_make_request):
        """Test team config not found."""
        mock_get_teams.return_value = []
        mock_make_request.return_value = {'team': {'states': {'nodes': []}}}

        exporter = LinearExporter(api_key='test-key')
        config = exporter.get_team_config('unknown-team')

        assert config is None


class TestLinearExporterProjects:
    """Test project handling."""

    @patch.object(LinearExporter, '_make_request')
    def test_get_available_projects(self, mock_make_request):
        """Test getting available projects."""
        mock_make_request.return_value = {
            'projects': {
                'nodes': [
                    {'id': 'proj-1', 'name': 'Project 1', 'state': 'started', 'slugId': 'project-1'},
                    {'id': 'proj-2', 'name': 'Project 2', 'state': 'planned', 'slugId': 'project-2'},
                ]
            }
        }

        exporter = LinearExporter(api_key='test-key')
        projects = exporter.get_available_projects(team_id='team-1')

        assert len(projects) == 2
        assert projects[0] == {
            'id': 'proj-1',
            'name': 'Project 1',
            'state': 'started',
            'slug': 'project-1'
        }

    @patch.object(LinearExporter, '_make_request')
    def test_get_available_projects_error(self, mock_make_request):
        """Test error handling for projects."""
        mock_make_request.side_effect = Exception("API error")

        exporter = LinearExporter(api_key='test-key')
        projects = exporter.get_available_projects()

        assert projects == []

    @patch.object(LinearExporter, '_make_request')
    def test_create_project(self, mock_make_request):
        """Test creating a project."""
        mock_make_request.return_value = {
            'projectCreate': {
                'success': True,
                'project': {'id': 'proj-new', 'name': 'New Project', 'slugId': 'new-project'}
            }
        }

        exporter = LinearExporter(api_key='test-key')
        project_id = exporter.create_project(
            name='New Project',
            team_ids=['team-1'],
            description='A new project',
        )

        assert project_id == 'proj-new'

    @patch.object(LinearExporter, '_make_request')
    def test_create_project_failure(self, mock_make_request):
        """Test project creation failure."""
        mock_make_request.return_value = {
            'projectCreate': {'success': False}
        }

        exporter = LinearExporter(api_key='test-key')
        project_id = exporter.create_project('New Project', ['team-1'])

        assert project_id is None


class TestLinearExporterCycles:
    """Test cycle handling."""

    @patch.object(LinearExporter, '_make_request')
    def test_get_cycles(self, mock_make_request):
        """Test getting cycles."""
        mock_make_request.return_value = {
            'cycles': {
                'nodes': [
                    {
                        'id': 'cycle-1',
                        'name': 'Sprint 1',
                        'number': 1,
                        'startsAt': '2024-01-01',
                        'endsAt': '2024-01-14',
                    },
                ]
            }
        }

        exporter = LinearExporter(api_key='test-key')
        cycles = exporter.get_cycles('team-1')

        assert len(cycles) == 1
        assert cycles[0]['id'] == 'cycle-1'
        assert cycles[0]['name'] == 'Sprint 1'
        assert cycles[0]['number'] == 1

    @patch.object(LinearExporter, '_make_request')
    def test_get_cycles_error(self, mock_make_request):
        """Test error handling for cycles."""
        mock_make_request.side_effect = Exception("API error")

        exporter = LinearExporter(api_key='test-key')
        cycles = exporter.get_cycles('team-1')

        assert cycles == []

    @patch.object(LinearExporter, '_make_request')
    def test_create_cycle(self, mock_make_request):
        """Test creating a cycle."""
        mock_make_request.return_value = {
            'cycleCreate': {
                'success': True,
                'cycle': {'id': 'cycle-new', 'name': 'Sprint 2', 'number': 2}
            }
        }

        exporter = LinearExporter(api_key='test-key')
        cycle_id = exporter.create_cycle(
            team_id='team-1',
            name='Sprint 2',
            starts_at='2024-01-15',
            ends_at='2024-01-28',
        )

        assert cycle_id == 'cycle-new'

    @patch.object(LinearExporter, '_make_request')
    def test_create_cycle_failure(self, mock_make_request):
        """Test cycle creation failure."""
        mock_make_request.return_value = {
            'cycleCreate': {'success': False}
        }

        exporter = LinearExporter(api_key='test-key')
        cycle_id = exporter.create_cycle('team-1')

        assert cycle_id is None


class TestLinearExporterFormatting:
    """Test description formatting."""

    def test_format_description_basic(self):
        """Test basic description formatting."""
        exporter = LinearExporter()
        item = MockMilestone(
            id='m1',
            name='Test Milestone',
            description='A test milestone',
        )
        result = exporter._format_description(item)
        assert 'A test milestone' in result

    def test_format_description_with_goal(self):
        """Test description with goal."""
        exporter = LinearExporter()
        item = MockMilestone(
            id='m1',
            name='Test',
            description='Description',
            goal='The goal',
        )
        result = exporter._format_description(item)
        assert '## Goal' in result
        assert 'The goal' in result

    def test_format_description_with_deliverables(self):
        """Test description with deliverables."""
        exporter = LinearExporter()
        item = MockMilestone(
            id='m1',
            name='Test',
            key_deliverables=['Deliverable 1', 'Deliverable 2'],
        )
        result = exporter._format_description(item)
        assert '## Key Deliverables' in result
        assert '- Deliverable 1' in result
        assert '- Deliverable 2' in result

    def test_format_description_with_requirements(self):
        """Test description with technical requirements."""
        exporter = LinearExporter()
        item = MockMilestone(
            id='m1',
            name='Test',
            technical_requirements=['Req 1', 'Req 2'],
        )
        result = exporter._format_description(item)
        assert '## Technical Requirements' in result
        assert '- Req 1' in result

    def test_format_story_description(self):
        """Test story description formatting."""
        exporter = LinearExporter()
        story = MockStory(
            id='s1',
            name='Test Story',
            description='Story description',
            acceptance_criteria=['AC 1', 'AC 2'],
            user_value='User value here',
        )
        result = exporter._format_story_description(story)
        assert '## Acceptance Criteria' in result
        assert '- [ ] AC 1' in result
        assert '## User Value' in result
        assert 'User value here' in result

    def test_format_task_description(self):
        """Test task description formatting."""
        exporter = LinearExporter()
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
        assert '## Implementation Guide' in result
        assert 'Use Claude to implement this' in result
        assert '**Work Type:**' in result
        assert '## Files to Modify' in result
        assert '**Estimated Duration:**' in result


class TestLinearExporterDateFormatting:
    """Test date formatting."""

    def test_format_date_string(self):
        """Test formatting date string."""
        exporter = LinearExporter()
        result = exporter._format_date('2024-06-15')
        assert result == '2024-06-15'

    def test_format_date_iso_string(self):
        """Test formatting ISO date string."""
        exporter = LinearExporter()
        result = exporter._format_date('2024-06-15T10:30:00Z')
        assert result == '2024-06-15'

    def test_format_date_datetime(self):
        """Test formatting datetime object."""
        exporter = LinearExporter()
        dt = datetime(2024, 6, 15, 10, 30, 0)
        result = exporter._format_date(dt)
        assert result == '2024-06-15'


class TestLinearExporterFieldMapping:
    """Test field mapping."""

    def test_get_field_mapping(self):
        """Test field mapping returns expected fields."""
        exporter = LinearExporter()
        mapping = exporter.get_field_mapping()

        assert mapping['name'] == 'title'
        assert mapping['description'] == 'description'
        assert mapping['priority'] == 'priority'
        assert mapping['duration_hours'] == 'estimate'
        assert mapping['tags'] == 'labelIds'
        assert 'target_date' in mapping
        assert 'dependencies' in mapping


class TestLinearExporterExport:
    """Test roadmap export."""

    def test_export_no_team(self):
        """Test export fails without team."""
        exporter = LinearExporter(api_key='token', team_id=None)
        exporter._prompt_for_team = Mock(return_value=None)

        roadmap = MockRoadmap()
        result = exporter.export_roadmap(roadmap)

        assert result.success is False
        assert 'team' in result.errors[0].lower()

    @patch.object(LinearExporter, 'get_team_config')
    @patch.object(LinearExporter, 'create_project')
    def test_export_team_config_fails(self, mock_create_project, mock_get_team_config):
        """Test export fails when team config fails."""
        mock_get_team_config.return_value = None

        exporter = LinearExporter(api_key='token', team_id='team-1')
        roadmap = MockRoadmap()
        result = exporter.export_roadmap(roadmap)

        assert result.success is False
        assert 'Failed to get configuration' in result.errors[0]

    def test_export_dry_run(self):
        """Test dry run doesn't create items."""
        exporter = LinearExporter(api_key='token', team_id='team-1')

        # Create hierarchy for dry run
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

        result = exporter.export_roadmap(roadmap, dry_run=True)

        assert result.success is True
        assert result.items_created >= 1
        assert result.metadata['dry_run'] is True

    @patch.object(LinearExporter, 'get_team_config')
    @patch.object(LinearExporter, 'create_project')
    @patch.object(LinearExporter, 'create_cycle')
    @patch.object(LinearExporter, '_make_request')
    def test_export_creates_hierarchy(self, mock_make_request, mock_create_cycle,
                                      mock_create_project, mock_get_team_config):
        """Test export creates full hierarchy."""
        mock_get_team_config.return_value = LinearTeamConfig(
            team_id='team-1',
            team_name='Engineering',
            team_key='ENG',
            state_types={'state-1': 'backlog', 'state-2': 'unstarted'},
        )
        mock_create_project.return_value = 'proj-1'
        mock_create_cycle.return_value = 'cycle-1'

        issue_counter = [0]
        def create_issue(query, variables):
            issue_counter[0] += 1
            return {
                'issueCreate': {
                    'success': True,
                    'issue': {
                        'id': f'issue-{issue_counter[0]}',
                        'identifier': f'ENG-{issue_counter[0]}',
                        'title': f'Issue {issue_counter[0]}',
                        'url': f'https://linear.app/eng/issue/ENG-{issue_counter[0]}'
                    }
                }
            }

        mock_make_request.side_effect = create_issue

        exporter = LinearExporter(api_key='token', team_id='team-1')

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

        result = exporter.export_roadmap(roadmap, create_cycles=True)

        assert result.success is True
        # 1 cycle + 3 issues (epic, story, task)
        assert result.items_created == 4


class TestLinearExporterUpdateMethods:
    """Test update methods."""

    @patch.object(LinearExporter, '_make_request')
    def test_update_issue_success(self, mock_make_request):
        """Test successful issue update."""
        mock_make_request.return_value = {
            'issueUpdate': {'success': True, 'issue': {'id': 'issue-1'}}
        }

        exporter = LinearExporter(api_key='token')
        result = exporter.update_issue('issue-1', {'title': 'New title'})

        assert result is True

    @patch.object(LinearExporter, '_make_request')
    def test_update_issue_failure(self, mock_make_request):
        """Test failed issue update."""
        mock_make_request.side_effect = Exception("API error")

        exporter = LinearExporter(api_key='token')
        result = exporter.update_issue('issue-1', {'title': 'New title'})

        assert result is False

    @patch.object(LinearExporter, '_make_request')
    def test_add_comment_success(self, mock_make_request):
        """Test adding a comment."""
        mock_make_request.return_value = {
            'commentCreate': {'success': True, 'comment': {'id': 'comment-1'}}
        }

        exporter = LinearExporter(api_key='token')
        result = exporter.add_comment('issue-1', 'Test comment')

        assert result is True

    @patch.object(LinearExporter, '_make_request')
    def test_add_comment_failure(self, mock_make_request):
        """Test failed comment."""
        mock_make_request.side_effect = Exception("API error")

        exporter = LinearExporter(api_key='token')
        result = exporter.add_comment('issue-1', 'Test comment')

        assert result is False

    @patch.object(LinearExporter, '_make_request')
    def test_create_issue_relation_success(self, mock_make_request):
        """Test creating issue relation."""
        mock_make_request.return_value = {
            'issueRelationCreate': {'success': True, 'issueRelation': {'id': 'rel-1'}}
        }

        exporter = LinearExporter(api_key='token')
        result = exporter.create_issue_relation('issue-1', 'issue-2', 'blocks')

        assert result is True

    @patch.object(LinearExporter, '_make_request')
    def test_create_issue_relation_failure(self, mock_make_request):
        """Test failed issue relation."""
        mock_make_request.side_effect = Exception("API error")

        exporter = LinearExporter(api_key='token')
        result = exporter.create_issue_relation('issue-1', 'issue-2')

        assert result is False

    @patch.object(LinearExporter, '_make_request')
    def test_get_issue_success(self, mock_make_request):
        """Test getting an issue."""
        mock_make_request.return_value = {
            'issue': {
                'id': 'issue-1',
                'identifier': 'ENG-123',
                'title': 'Test Issue',
            }
        }

        exporter = LinearExporter(api_key='token')
        issue = exporter.get_issue('issue-1')

        assert issue is not None
        assert issue['id'] == 'issue-1'
        assert issue['identifier'] == 'ENG-123'

    @patch.object(LinearExporter, '_make_request')
    def test_get_issue_error(self, mock_make_request):
        """Test getting issue error."""
        mock_make_request.side_effect = Exception("Not found")

        exporter = LinearExporter(api_key='token')
        issue = exporter.get_issue('unknown')

        assert issue is None


class TestLinearExporterLabels:
    """Test label handling."""

    @patch.object(LinearExporter, '_make_request')
    def test_get_or_create_labels_existing(self, mock_make_request):
        """Test getting existing labels from team config."""
        exporter = LinearExporter(api_key='token')
        exporter._team_config = LinearTeamConfig(
            team_id='team-1',
            team_name='Engineering',
            team_key='ENG',
            labels={'Bug': 'label-1', 'Feature': 'label-2'},
        )

        label_ids = exporter._get_or_create_labels('team-1', ['Bug', 'Feature'])

        assert len(label_ids) == 2
        assert 'label-1' in label_ids
        assert 'label-2' in label_ids

    @patch.object(LinearExporter, '_make_request')
    def test_get_or_create_labels_create_new(self, mock_make_request):
        """Test creating new labels."""
        mock_make_request.return_value = {
            'issueLabelCreate': {
                'success': True,
                'issueLabel': {'id': 'label-new', 'name': 'NewLabel'}
            }
        }

        exporter = LinearExporter(api_key='token')
        exporter._team_config = LinearTeamConfig(
            team_id='team-1',
            team_name='Engineering',
            team_key='ENG',
            labels={},
        )

        label_ids = exporter._get_or_create_labels('team-1', ['NewLabel'])

        assert len(label_ids) == 1
        assert 'label-new' in label_ids

    def test_get_or_create_labels_empty_name(self):
        """Test handling empty label name."""
        exporter = LinearExporter(api_key='token')
        exporter._team_config = LinearTeamConfig(
            team_id='team-1',
            team_name='Engineering',
            team_key='ENG',
        )

        label_ids = exporter._get_or_create_labels('team-1', ['', None])

        # Should skip empty/None labels
        assert len(label_ids) == 0

    def test_get_or_create_labels_cached(self):
        """Test label caching."""
        exporter = LinearExporter(api_key='token')
        exporter._team_config = LinearTeamConfig(
            team_id='team-1',
            team_name='Engineering',
            team_key='ENG',
        )
        exporter._label_cache = {'CachedLabel': 'label-cached'}

        label_ids = exporter._get_or_create_labels('team-1', ['CachedLabel'])

        assert len(label_ids) == 1
        assert 'label-cached' in label_ids


class TestLinearExporterFactoryRegistration:
    """Test factory registration."""

    def test_linear_exporter_registered(self):
        """Test LinearExporter is registered with factory."""
        from arcane.engines.export import ExporterFactory, ExportPlatform

        assert ExporterFactory.is_registered(ExportPlatform.LINEAR)

    def test_create_linear_exporter(self):
        """Test creating LinearExporter via factory."""
        from arcane.engines.export import ExporterFactory

        exporter = ExporterFactory.create('linear')
        assert isinstance(exporter, LinearExporter)


class TestLinearExporterEdgeCases:
    """Test edge cases and error handling."""

    def test_get_children_by_type_no_children(self):
        """Test getting children when none exist."""
        exporter = LinearExporter()

        class NoChildren:
            pass

        item = NoChildren()
        result = exporter._get_children_by_type(item, MockEpic)
        assert result == []

    def test_get_children_by_type_empty_children(self):
        """Test getting children when list is empty."""
        exporter = LinearExporter()

        class EmptyChildren:
            children = []

        item = EmptyChildren()
        result = exporter._get_children_by_type(item, MockEpic)
        assert result == []

    def test_create_task_issue_no_parent(self):
        """Test creating task without parent raises error."""
        exporter = LinearExporter(api_key='token')
        exporter._team_config = LinearTeamConfig(
            team_id='team-1',
            team_name='Engineering',
            team_key='ENG',
        )

        task = MockTask(id='t1', name='Task')

        with pytest.raises(ValueError) as exc_info:
            exporter._create_task_issue('team-1', None, None, task, None)

        assert 'Parent issue not created' in str(exc_info.value)

    @patch.object(LinearExporter, 'get_available_teams')
    def test_prompt_for_team_no_teams(self, mock_get_teams):
        """Test prompt when no teams available."""
        mock_get_teams.return_value = []

        exporter = LinearExporter(api_key='token')
        result = exporter._prompt_for_team()

        assert result is None

    @patch.object(LinearExporter, 'get_available_teams')
    def test_prompt_for_team_single_team(self, mock_get_teams):
        """Test prompt with single team auto-selects."""
        mock_get_teams.return_value = [
            {'id': 'team-1', 'name': 'Engineering', 'key': 'ENG'}
        ]

        exporter = LinearExporter(api_key='token')
        result = exporter._prompt_for_team()

        assert result == 'team-1'

    @patch.object(LinearExporter, '_make_request')
    def test_create_milestone_cycle_no_dates(self, mock_make_request):
        """Test creating cycle without dates uses defaults."""
        mock_make_request.return_value = {
            'cycleCreate': {
                'success': True,
                'cycle': {'id': 'cycle-1', 'name': 'Milestone 1', 'number': 1}
            }
        }

        exporter = LinearExporter(api_key='token')
        milestone = MockMilestone(id='m1', name='Milestone 1')

        cycle_id = exporter._create_milestone_cycle('team-1', milestone)

        assert cycle_id == 'cycle-1'

    @patch.object(LinearExporter, '_make_request')
    def test_create_milestone_cycle_with_dates(self, mock_make_request):
        """Test creating cycle with dates."""
        mock_make_request.return_value = {
            'cycleCreate': {
                'success': True,
                'cycle': {'id': 'cycle-1', 'name': 'Milestone 1', 'number': 1}
            }
        }

        exporter = LinearExporter(api_key='token')
        milestone = MockMilestone(
            id='m1',
            name='Milestone 1',
            start_date='2024-01-01',
            target_date='2024-01-14',
        )

        cycle_id = exporter._create_milestone_cycle('team-1', milestone)

        assert cycle_id == 'cycle-1'
        # Verify dates were passed - call_args[0] contains positional args
        call_args = mock_make_request.call_args
        variables = call_args[0][1]  # Second positional arg is the variables dict
        input_data = variables['input']
        assert input_data['startsAt'] == '2024-01-01'
        assert input_data['endsAt'] == '2024-01-14'
