#!/usr/bin/env python3
"""Linear export implementation.

This module provides functionality to export Arcane roadmaps to Linear,
mapping the roadmap hierarchy to Linear's project structure:
- Roadmap → Project (with roadmap view)
- Milestone → Cycle (for time-based planning)
- Epic → Parent Issue (with sub-issues)
- Story → Issue (linked to parent)
- Task → Sub-issue
"""

import os
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json

from .base_exporter import BaseExporter, ExportPlatform, ExportResult, PLATFORM_CONFIGS
from arcane.items import Roadmap, Milestone, Epic, Story, Task
from arcane.utils.logging_config import get_logger

logger = get_logger(__name__)


# GraphQL query and mutation templates
GRAPHQL_VIEWER = """
query Viewer {
    viewer {
        id
        name
        email
    }
}
"""

GRAPHQL_TEAMS = """
query Teams {
    teams {
        nodes {
            id
            name
            key
        }
    }
}
"""

GRAPHQL_TEAM_STATES = """
query TeamStates($teamId: String!) {
    team(id: $teamId) {
        states {
            nodes {
                id
                name
                type
            }
        }
    }
}
"""

GRAPHQL_TEAM_LABELS = """
query TeamLabels($teamId: String!) {
    team(id: $teamId) {
        labels {
            nodes {
                id
                name
                color
            }
        }
    }
}
"""

GRAPHQL_PROJECTS = """
query Projects($teamId: String) {
    projects(filter: { team: { id: { eq: $teamId } } }) {
        nodes {
            id
            name
            state
            slugId
        }
    }
}
"""

GRAPHQL_CYCLES = """
query Cycles($teamId: String!) {
    cycles(filter: { team: { id: { eq: $teamId } } }) {
        nodes {
            id
            name
            number
            startsAt
            endsAt
        }
    }
}
"""

GRAPHQL_CREATE_PROJECT = """
mutation CreateProject($input: ProjectCreateInput!) {
    projectCreate(input: $input) {
        success
        project {
            id
            name
            slugId
        }
    }
}
"""

GRAPHQL_CREATE_CYCLE = """
mutation CreateCycle($input: CycleCreateInput!) {
    cycleCreate(input: $input) {
        success
        cycle {
            id
            name
            number
        }
    }
}
"""

GRAPHQL_CREATE_ISSUE = """
mutation CreateIssue($input: IssueCreateInput!) {
    issueCreate(input: $input) {
        success
        issue {
            id
            identifier
            title
            url
        }
    }
}
"""

GRAPHQL_UPDATE_ISSUE = """
mutation UpdateIssue($id: String!, $input: IssueUpdateInput!) {
    issueUpdate(id: $id, input: $input) {
        success
        issue {
            id
            identifier
        }
    }
}
"""

GRAPHQL_CREATE_COMMENT = """
mutation CreateComment($input: CommentCreateInput!) {
    commentCreate(input: $input) {
        success
        comment {
            id
        }
    }
}
"""

GRAPHQL_CREATE_LABEL = """
mutation CreateLabel($input: IssueLabelCreateInput!) {
    issueLabelCreate(input: $input) {
        success
        issueLabel {
            id
            name
        }
    }
}
"""

GRAPHQL_ADD_ISSUE_RELATION = """
mutation AddIssueRelation($input: IssueRelationCreateInput!) {
    issueRelationCreate(input: $input) {
        success
        issueRelation {
            id
        }
    }
}
"""


@dataclass
class LinearTeamConfig:
    """Configuration for a Linear team.

    Stores team-specific information like workflow states and labels.
    """
    team_id: str
    team_name: str
    team_key: str

    # Workflow states
    states: Dict[str, str] = field(default_factory=dict)  # state_name -> state_id
    state_types: Dict[str, str] = field(default_factory=dict)  # state_id -> type

    # Labels
    labels: Dict[str, str] = field(default_factory=dict)  # label_name -> label_id

    def get_state_id(self, state_name: str) -> Optional[str]:
        """Get state ID by name."""
        return self.states.get(state_name)

    def get_backlog_state_id(self) -> Optional[str]:
        """Get the backlog state ID."""
        for state_id, state_type in self.state_types.items():
            if state_type == 'backlog':
                return state_id
        return None

    def get_todo_state_id(self) -> Optional[str]:
        """Get the todo/unstarted state ID."""
        for state_id, state_type in self.state_types.items():
            if state_type == 'unstarted':
                return state_id
        return None


class LinearRateLimiter:
    """Rate limiter for Linear API calls.

    Linear has rate limits based on complexity points.
    This simple limiter helps prevent hitting those limits.
    """

    def __init__(self, requests_per_second: float = 10.0):
        """Initialize rate limiter.

        Args:
            requests_per_second: Maximum requests per second (default 10)
        """
        self.min_interval = 1.0 / requests_per_second
        self.last_request_time = 0.0
        self._request_count = 0
        self._complexity_used = 0

    def wait(self) -> None:
        """Wait if necessary to respect rate limit."""
        now = time.time()
        elapsed = now - self.last_request_time

        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)

        self.last_request_time = time.time()
        self._request_count += 1

    def add_complexity(self, points: int) -> None:
        """Track complexity points used."""
        self._complexity_used += points

    def get_stats(self) -> Dict[str, int]:
        """Get rate limiter stats."""
        return {
            'request_count': self._request_count,
            'complexity_used': self._complexity_used,
        }

    def reset(self) -> None:
        """Reset counters."""
        self._request_count = 0
        self._complexity_used = 0


class LinearExporter(BaseExporter):
    """Export roadmap to Linear.

    This exporter creates Linear projects, cycles, and issues from
    Arcane roadmap items, preserving the hierarchical structure through
    parent issues and sub-issues.

    Example:
        exporter = LinearExporter(api_key="lin_api_xxx")

        if exporter.validate_connection():
            result = exporter.export_roadmap(roadmap, team_id="team-id")
            print(f"Created {result.items_created} items")
    """

    API_URL = "https://api.linear.app/graphql"

    # Priority mapping from Arcane to Linear
    # Linear priorities: 0=No Priority, 1=Urgent, 2=High, 3=Normal, 4=Low
    PRIORITY_MAPPING = {
        'Critical': 1,  # Urgent
        'High': 2,      # High
        'Medium': 3,    # Normal
        'Low': 4,       # Low
        'Lowest': 4,    # Low
    }

    # Reverse priority mapping
    PRIORITY_NAMES = {
        0: 'No Priority',
        1: 'Urgent',
        2: 'High',
        3: 'Normal',
        4: 'Low',
    }

    # Estimate mapping (story points to Linear estimates)
    # Linear uses Fibonacci-like estimates: 0, 1, 2, 3, 5, 8, 13, 21
    ESTIMATE_MAPPING = {
        1: 1,
        2: 2,
        3: 3,
        4: 5,
        5: 5,
        6: 8,
        7: 8,
        8: 8,
        9: 13,
        10: 13,
    }

    # Default hours per story point
    HOURS_PER_POINT = 8

    def __init__(
        self,
        api_key: Optional[str] = None,
        team_id: Optional[str] = None,
        rate_limit: float = 10.0,
    ):
        """Initialize Linear exporter.

        Args:
            api_key: Linear API key
            team_id: Default team ID
            rate_limit: Maximum API requests per second
        """
        self.api_key = api_key or os.getenv('LINEAR_API_KEY')
        self.team_id = team_id or os.getenv('LINEAR_TEAM_ID')

        self._rate_limiter = LinearRateLimiter(rate_limit)
        self._team_config: Optional[LinearTeamConfig] = None
        self._created_items: Dict[str, str] = {}  # item_id -> linear_id
        self._issue_identifiers: Dict[str, str] = {}  # item_id -> issue identifier (e.g., "ENG-123")
        self._label_cache: Dict[str, str] = {}  # label_name -> label_id

    @property
    def platform(self) -> ExportPlatform:
        """Return the platform this exporter handles."""
        return ExportPlatform.LINEAR

    @property
    def config(self):
        """Return platform configuration."""
        return PLATFORM_CONFIGS[ExportPlatform.LINEAR]

    @property
    def created_items(self) -> Dict[str, str]:
        """Return mapping of item IDs to Linear IDs."""
        return self._created_items.copy()

    @property
    def issue_identifiers(self) -> Dict[str, str]:
        """Return mapping of item IDs to Linear issue identifiers."""
        return self._issue_identifiers.copy()

    def _make_request(
        self,
        query: str,
        variables: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make a GraphQL request to Linear API.

        Args:
            query: GraphQL query or mutation
            variables: Query variables

        Returns:
            Response data

        Raises:
            ImportError: If requests package is not installed
            ValueError: If API key is missing
            Exception: If API request fails
        """
        try:
            import requests
        except ImportError:
            raise ImportError(
                "requests package is required for Linear export. "
                "Install it with: pip install requests"
            )

        if not self.api_key:
            raise ValueError("Missing required credential: LINEAR_API_KEY")

        headers = {
            'Authorization': self.api_key,
            'Content-Type': 'application/json',
        }

        payload = {'query': query}
        if variables:
            payload['variables'] = variables

        self._rate_limiter.wait()

        response = requests.post(
            self.API_URL,
            headers=headers,
            json=payload,
            timeout=30
        )

        if response.status_code != 200:
            raise Exception(f"Linear API error: {response.status_code} - {response.text}")

        result = response.json()

        if 'errors' in result:
            errors = result['errors']
            error_messages = [e.get('message', str(e)) for e in errors]
            raise Exception(f"Linear GraphQL errors: {'; '.join(error_messages)}")

        return result.get('data', {})

    def validate_connection(self) -> bool:
        """Validate Linear connection.

        Returns:
            True if connection is valid and authenticated
        """
        try:
            data = self._make_request(GRAPHQL_VIEWER)
            viewer = data.get('viewer', {})
            logger.info(f"Connected as: {viewer.get('name')} ({viewer.get('email')})")
            return True
        except Exception as e:
            logger.error(f"Linear connection failed: {e}")
            return False

    def get_available_teams(self) -> List[Dict[str, str]]:
        """Get list of available Linear teams.

        Returns:
            List of team dictionaries with 'id', 'name', and 'key'
        """
        try:
            data = self._make_request(GRAPHQL_TEAMS)
            teams = data.get('teams', {}).get('nodes', [])
            return [
                {'id': t.get('id'), 'name': t.get('name'), 'key': t.get('key')}
                for t in teams
            ]
        except Exception as e:
            logger.error(f"Failed to get teams: {e}")
            return []

    def get_team_config(self, team_id: str) -> Optional[LinearTeamConfig]:
        """Get team configuration including states and labels.

        Args:
            team_id: Team ID

        Returns:
            LinearTeamConfig or None
        """
        try:
            # Get states
            states_data = self._make_request(GRAPHQL_TEAM_STATES, {'teamId': team_id})
            states = states_data.get('team', {}).get('states', {}).get('nodes', [])

            state_map = {}
            state_types = {}
            for state in states:
                state_map[state.get('name')] = state.get('id')
                state_types[state.get('id')] = state.get('type')

            # Get labels
            labels_data = self._make_request(GRAPHQL_TEAM_LABELS, {'teamId': team_id})
            labels = labels_data.get('team', {}).get('labels', {}).get('nodes', [])

            label_map = {}
            for label in labels:
                label_map[label.get('name')] = label.get('id')

            # Get team info
            teams = self.get_available_teams()
            team_info = next((t for t in teams if t['id'] == team_id), None)

            if not team_info:
                return None

            return LinearTeamConfig(
                team_id=team_id,
                team_name=team_info['name'],
                team_key=team_info['key'],
                states=state_map,
                state_types=state_types,
                labels=label_map,
            )
        except Exception as e:
            logger.error(f"Failed to get team config: {e}")
            return None

    def get_available_projects(self, team_id: Optional[str] = None) -> List[Dict[str, str]]:
        """Get list of available Linear projects.

        Args:
            team_id: Filter by team (optional)

        Returns:
            List of project dictionaries
        """
        try:
            variables = {}
            if team_id:
                variables['teamId'] = team_id

            data = self._make_request(GRAPHQL_PROJECTS, variables if variables else None)
            projects = data.get('projects', {}).get('nodes', [])
            return [
                {
                    'id': p.get('id'),
                    'name': p.get('name'),
                    'state': p.get('state'),
                    'slug': p.get('slugId'),
                }
                for p in projects
            ]
        except Exception as e:
            logger.error(f"Failed to get projects: {e}")
            return []

    def get_cycles(self, team_id: str) -> List[Dict[str, Any]]:
        """Get list of cycles for a team.

        Args:
            team_id: Team ID

        Returns:
            List of cycle dictionaries
        """
        try:
            data = self._make_request(GRAPHQL_CYCLES, {'teamId': team_id})
            cycles = data.get('cycles', {}).get('nodes', [])
            return [
                {
                    'id': c.get('id'),
                    'name': c.get('name'),
                    'number': c.get('number'),
                    'starts_at': c.get('startsAt'),
                    'ends_at': c.get('endsAt'),
                }
                for c in cycles
            ]
        except Exception as e:
            logger.error(f"Failed to get cycles: {e}")
            return []

    def create_project(
        self,
        name: str,
        team_ids: List[str],
        description: Optional[str] = None,
        **kwargs
    ) -> Optional[str]:
        """Create a new Linear project.

        Args:
            name: Project name
            team_ids: List of team IDs to associate with project
            description: Project description
            **kwargs: Additional project options

        Returns:
            Created project ID or None
        """
        try:
            input_data = {
                'name': name,
                'teamIds': team_ids,
            }

            if description:
                input_data['description'] = description

            # Add optional fields
            if kwargs.get('color'):
                input_data['color'] = kwargs['color']
            if kwargs.get('icon'):
                input_data['icon'] = kwargs['icon']
            if kwargs.get('targetDate'):
                input_data['targetDate'] = kwargs['targetDate']

            data = self._make_request(GRAPHQL_CREATE_PROJECT, {'input': input_data})
            result = data.get('projectCreate', {})

            if result.get('success'):
                project = result.get('project', {})
                project_id = project.get('id')
                logger.info(f"Created Linear project: {name} ({project_id})")
                return project_id

            return None
        except Exception as e:
            logger.error(f"Failed to create project: {e}")
            return None

    def create_cycle(
        self,
        team_id: str,
        name: Optional[str] = None,
        starts_at: Optional[str] = None,
        ends_at: Optional[str] = None,
        **kwargs
    ) -> Optional[str]:
        """Create a new Linear cycle.

        Args:
            team_id: Team ID
            name: Cycle name (optional, Linear auto-generates)
            starts_at: Start date (ISO format)
            ends_at: End date (ISO format)
            **kwargs: Additional cycle options

        Returns:
            Created cycle ID or None
        """
        try:
            input_data = {
                'teamId': team_id,
            }

            if name:
                input_data['name'] = name
            if starts_at:
                input_data['startsAt'] = starts_at
            if ends_at:
                input_data['endsAt'] = ends_at

            data = self._make_request(GRAPHQL_CREATE_CYCLE, {'input': input_data})
            result = data.get('cycleCreate', {})

            if result.get('success'):
                cycle = result.get('cycle', {})
                cycle_id = cycle.get('id')
                logger.info(f"Created Linear cycle: {name or cycle.get('number')} ({cycle_id})")
                return cycle_id

            return None
        except Exception as e:
            logger.error(f"Failed to create cycle: {e}")
            return None

    def export_roadmap(self, roadmap: Roadmap, **kwargs) -> ExportResult:
        """Export roadmap to Linear.

        Args:
            roadmap: Roadmap to export
            **kwargs: Additional options:
                - team_id: Team to create issues in
                - project_id: Existing project to use
                - project_name: Name for new project
                - create_cycles: If True, create cycles for milestones
                - dry_run: If True, validate but don't create items

        Returns:
            ExportResult with export details
        """
        errors = []
        warnings = []
        items_created = 0
        items_failed = 0

        # Reset tracking
        self._created_items = {}
        self._issue_identifiers = {}

        try:
            # Get team ID
            team_id = kwargs.get('team_id', self.team_id)
            if not team_id:
                team_id = self._prompt_for_team()

            if not team_id:
                return ExportResult(
                    success=False,
                    platform=self.platform,
                    errors=["No team specified. Set LINEAR_TEAM_ID or provide team_id."],
                )

            dry_run = kwargs.get('dry_run', False)
            create_cycles = kwargs.get('create_cycles', True)

            if dry_run:
                logger.info("Dry run mode - validating only")

            # Get team configuration
            if not dry_run:
                self._team_config = self.get_team_config(team_id)
                if not self._team_config:
                    return ExportResult(
                        success=False,
                        platform=self.platform,
                        errors=[f"Failed to get configuration for team {team_id}"],
                    )

            # Create or use existing project
            project_id = kwargs.get('project_id')
            if not project_id and not dry_run:
                project_name = kwargs.get('project_name')
                if not project_name:
                    project_name = getattr(roadmap, 'name', None) or 'Arcane Roadmap'

                project_id = self.create_project(
                    name=project_name,
                    team_ids=[team_id],
                    description=getattr(roadmap, 'description', ''),
                )
                if not project_id:
                    warnings.append("Failed to create project, issues will not be linked to a project")

            # Process milestones
            for milestone in roadmap.milestones:
                try:
                    cycle_id = None

                    # Create cycle for milestone if requested
                    if create_cycles and not dry_run:
                        cycle_id = self._create_milestone_cycle(team_id, milestone)
                        if cycle_id:
                            items_created += 1

                    # Get epics under this milestone
                    epics = self._get_children_by_type(milestone, Epic)
                    for epic in epics:
                        try:
                            parent_issue_id = None
                            if not dry_run:
                                parent_issue_id = self._create_epic_issue(
                                    team_id, project_id, cycle_id, epic
                                )
                            items_created += 1

                            # Get stories under this epic
                            stories = self._get_children_by_type(epic, Story)
                            for story in stories:
                                try:
                                    issue_id = None
                                    if not dry_run:
                                        issue_id = self._create_story_issue(
                                            team_id, project_id, cycle_id,
                                            story, parent_issue_id
                                        )
                                    items_created += 1

                                    # Get tasks under this story
                                    tasks = self._get_children_by_type(story, Task)
                                    for task in tasks:
                                        try:
                                            if not dry_run:
                                                self._create_task_issue(
                                                    team_id, project_id, cycle_id,
                                                    task, issue_id
                                                )
                                            items_created += 1
                                        except Exception as e:
                                            errors.append(f"Failed to create task '{task.name}': {e}")
                                            items_failed += 1
                                            logger.error(f"Error creating task: {e}")

                                except Exception as e:
                                    errors.append(f"Failed to create story '{story.name}': {e}")
                                    items_failed += 1
                                    logger.error(f"Error creating story: {e}")

                        except Exception as e:
                            errors.append(f"Failed to create epic '{epic.name}': {e}")
                            items_failed += 1
                            logger.error(f"Error creating epic: {e}")

                except Exception as e:
                    errors.append(f"Failed to process milestone '{milestone.name}': {e}")
                    items_failed += 1
                    logger.error(f"Error processing milestone: {e}")

            # Build project URL
            project_url = None
            if project_id and not dry_run:
                # Linear project URLs use the team key
                if self._team_config:
                    project_url = f"https://linear.app/{self._team_config.team_key}/project/{project_id}"

            return ExportResult(
                success=len(errors) == 0,
                platform=self.platform,
                project_url=project_url,
                items_created=items_created,
                items_failed=items_failed,
                errors=errors,
                warnings=warnings,
                metadata={
                    'team_id': team_id,
                    'project_id': project_id,
                    'created_items': self._created_items.copy(),
                    'issue_identifiers': self._issue_identifiers.copy(),
                    'dry_run': dry_run,
                    'api_stats': self._rate_limiter.get_stats(),
                }
            )

        except Exception as e:
            logger.exception(f"Export failed: {e}")
            return ExportResult(
                success=False,
                platform=self.platform,
                items_created=items_created,
                items_failed=items_failed + 1,
                errors=[str(e)] + errors,
            )

    def _get_children_by_type(self, parent, child_type) -> List:
        """Get children of a specific type from parent.

        Args:
            parent: Parent item
            child_type: Type class to filter by

        Returns:
            List of children matching the type
        """
        if hasattr(parent, 'children'):
            return [c for c in parent.children if isinstance(c, child_type)]
        return []

    def _create_milestone_cycle(self, team_id: str, milestone: Milestone) -> Optional[str]:
        """Create a Linear cycle for a milestone.

        Args:
            team_id: Team ID
            milestone: Milestone to create cycle for

        Returns:
            Created cycle ID or None
        """
        # Calculate cycle dates
        starts_at = None
        ends_at = None

        if hasattr(milestone, 'start_date') and milestone.start_date:
            starts_at = self._format_date(milestone.start_date)
        if hasattr(milestone, 'target_date') and milestone.target_date:
            ends_at = self._format_date(milestone.target_date)

        # Default to 2-week cycle if no dates
        if not starts_at:
            starts_at = datetime.now().strftime('%Y-%m-%d')
        if not ends_at:
            end_date = datetime.now() + timedelta(days=14)
            ends_at = end_date.strftime('%Y-%m-%d')

        cycle_id = self.create_cycle(
            team_id=team_id,
            name=milestone.name,
            starts_at=starts_at,
            ends_at=ends_at,
        )

        if cycle_id:
            self._created_items[milestone.id] = cycle_id

        return cycle_id

    def _create_epic_issue(
        self,
        team_id: str,
        project_id: Optional[str],
        cycle_id: Optional[str],
        epic: Epic
    ) -> Optional[str]:
        """Create a Linear issue for an epic (parent issue).

        Args:
            team_id: Team ID
            project_id: Project ID
            cycle_id: Cycle ID
            epic: Epic to create issue for

        Returns:
            Created issue ID or None
        """
        input_data = {
            'teamId': team_id,
            'title': f"[Epic] {epic.name}",
            'description': self._format_description(epic),
        }

        # Add project
        if project_id:
            input_data['projectId'] = project_id

        # Add cycle
        if cycle_id:
            input_data['cycleId'] = cycle_id

        # Add priority
        if hasattr(epic, 'priority') and epic.priority:
            input_data['priority'] = self.PRIORITY_MAPPING.get(epic.priority, 3)

        # Add state (use backlog or todo)
        if self._team_config:
            state_id = self._team_config.get_backlog_state_id()
            if state_id:
                input_data['stateId'] = state_id

        # Add labels
        if hasattr(epic, 'tags') and epic.tags:
            label_ids = self._get_or_create_labels(team_id, epic.tags)
            if label_ids:
                input_data['labelIds'] = label_ids

        # Add due date
        if hasattr(epic, 'target_date') and epic.target_date:
            input_data['dueDate'] = self._format_date(epic.target_date)

        data = self._make_request(GRAPHQL_CREATE_ISSUE, {'input': input_data})
        result = data.get('issueCreate', {})

        if result.get('success'):
            issue = result.get('issue', {})
            issue_id = issue.get('id')
            identifier = issue.get('identifier')

            self._created_items[epic.id] = issue_id
            self._issue_identifiers[epic.id] = identifier

            logger.info(f"Created Linear issue for epic: {identifier} - {epic.name}")
            return issue_id

        return None

    def _create_story_issue(
        self,
        team_id: str,
        project_id: Optional[str],
        cycle_id: Optional[str],
        story: Story,
        parent_id: Optional[str]
    ) -> Optional[str]:
        """Create a Linear issue for a story.

        Args:
            team_id: Team ID
            project_id: Project ID
            cycle_id: Cycle ID
            story: Story to create issue for
            parent_id: Parent issue ID (epic)

        Returns:
            Created issue ID or None
        """
        input_data = {
            'teamId': team_id,
            'title': story.name,
            'description': self._format_story_description(story),
        }

        # Add parent
        if parent_id:
            input_data['parentId'] = parent_id

        # Add project
        if project_id:
            input_data['projectId'] = project_id

        # Add cycle
        if cycle_id:
            input_data['cycleId'] = cycle_id

        # Add priority
        if hasattr(story, 'priority') and story.priority:
            input_data['priority'] = self.PRIORITY_MAPPING.get(story.priority, 3)

        # Add estimate (story points)
        if hasattr(story, 'duration_hours') and story.duration_hours:
            points = max(1, round(story.duration_hours / self.HOURS_PER_POINT))
            estimate = self.ESTIMATE_MAPPING.get(points, min(points, 21))
            input_data['estimate'] = estimate

        # Add state
        if self._team_config:
            state_id = self._team_config.get_todo_state_id()
            if state_id:
                input_data['stateId'] = state_id

        # Add labels
        if hasattr(story, 'tags') and story.tags:
            label_ids = self._get_or_create_labels(team_id, story.tags)
            if label_ids:
                input_data['labelIds'] = label_ids

        # Add due date
        if hasattr(story, 'target_date') and story.target_date:
            input_data['dueDate'] = self._format_date(story.target_date)

        data = self._make_request(GRAPHQL_CREATE_ISSUE, {'input': input_data})
        result = data.get('issueCreate', {})

        if result.get('success'):
            issue = result.get('issue', {})
            issue_id = issue.get('id')
            identifier = issue.get('identifier')

            self._created_items[story.id] = issue_id
            self._issue_identifiers[story.id] = identifier

            logger.info(f"Created Linear issue for story: {identifier} - {story.name}")
            return issue_id

        return None

    def _create_task_issue(
        self,
        team_id: str,
        project_id: Optional[str],
        cycle_id: Optional[str],
        task: Task,
        parent_id: Optional[str]
    ) -> Optional[str]:
        """Create a Linear sub-issue for a task.

        Args:
            team_id: Team ID
            project_id: Project ID
            cycle_id: Cycle ID
            task: Task to create issue for
            parent_id: Parent issue ID (story)

        Returns:
            Created issue ID or None
        """
        if not parent_id:
            raise ValueError(f"Parent issue not created for task '{task.name}'")

        input_data = {
            'teamId': team_id,
            'title': task.name,
            'description': self._format_task_description(task),
            'parentId': parent_id,
        }

        # Add project
        if project_id:
            input_data['projectId'] = project_id

        # Add cycle
        if cycle_id:
            input_data['cycleId'] = cycle_id

        # Add priority
        if hasattr(task, 'priority') and task.priority:
            input_data['priority'] = self.PRIORITY_MAPPING.get(task.priority, 3)

        # Add estimate
        if hasattr(task, 'duration_hours') and task.duration_hours:
            points = max(1, round(task.duration_hours / self.HOURS_PER_POINT))
            estimate = self.ESTIMATE_MAPPING.get(points, min(points, 21))
            input_data['estimate'] = estimate

        # Add state
        if self._team_config:
            state_id = self._team_config.get_todo_state_id()
            if state_id:
                input_data['stateId'] = state_id

        data = self._make_request(GRAPHQL_CREATE_ISSUE, {'input': input_data})
        result = data.get('issueCreate', {})

        if result.get('success'):
            issue = result.get('issue', {})
            issue_id = issue.get('id')
            identifier = issue.get('identifier')

            self._created_items[task.id] = issue_id
            self._issue_identifiers[task.id] = identifier

            logger.info(f"Created Linear sub-issue for task: {identifier} - {task.name}")
            return issue_id

        return None

    def _get_or_create_labels(self, team_id: str, tag_names: List[str]) -> List[str]:
        """Get or create labels and return their IDs.

        Args:
            team_id: Team ID
            tag_names: List of tag/label names

        Returns:
            List of label IDs
        """
        label_ids = []

        for name in tag_names:
            if not name:
                continue

            # Check cache first
            if name in self._label_cache:
                label_ids.append(self._label_cache[name])
                continue

            # Check team config
            if self._team_config and name in self._team_config.labels:
                label_id = self._team_config.labels[name]
                self._label_cache[name] = label_id
                label_ids.append(label_id)
                continue

            # Create new label
            try:
                input_data = {
                    'name': name,
                    'teamId': team_id,
                }

                data = self._make_request(GRAPHQL_CREATE_LABEL, {'input': input_data})
                result = data.get('issueLabelCreate', {})

                if result.get('success'):
                    label = result.get('issueLabel', {})
                    label_id = label.get('id')
                    self._label_cache[name] = label_id
                    label_ids.append(label_id)
                    logger.debug(f"Created label: {name}")
            except Exception as e:
                logger.warning(f"Could not create label '{name}': {e}")

        return label_ids

    def _format_date(self, date_value) -> str:
        """Format a date value for Linear API.

        Args:
            date_value: Date as string or datetime

        Returns:
            Date string in YYYY-MM-DD format
        """
        if isinstance(date_value, str):
            try:
                dt = datetime.fromisoformat(date_value.replace('Z', '+00:00'))
                return dt.strftime('%Y-%m-%d')
            except ValueError:
                return date_value
        elif isinstance(date_value, datetime):
            return date_value.strftime('%Y-%m-%d')
        return str(date_value)

    def _format_description(self, item) -> str:
        """Format item description for Linear.

        Linear supports Markdown formatting.

        Args:
            item: Roadmap item

        Returns:
            Formatted description string
        """
        parts = []

        if hasattr(item, 'description') and item.description:
            parts.append(item.description)

        if hasattr(item, 'goal') and item.goal:
            parts.append(f"\n\n## Goal\n{item.goal}")

        if hasattr(item, 'key_deliverables') and item.key_deliverables:
            parts.append("\n\n## Key Deliverables")
            for d in item.key_deliverables:
                parts.append(f"- {d}")

        if hasattr(item, 'technical_requirements') and item.technical_requirements:
            parts.append("\n\n## Technical Requirements")
            for r in item.technical_requirements:
                parts.append(f"- {r}")

        if hasattr(item, 'dependencies') and item.dependencies:
            parts.append("\n\n## Dependencies")
            for dep in item.dependencies:
                parts.append(f"- {dep}")

        return "\n".join(parts) if parts else ""

    def _format_story_description(self, story: Story) -> str:
        """Format story description with acceptance criteria.

        Args:
            story: Story item

        Returns:
            Formatted description string
        """
        parts = [self._format_description(story)]

        if hasattr(story, 'acceptance_criteria') and story.acceptance_criteria:
            parts.append("\n\n## Acceptance Criteria")
            for ac in story.acceptance_criteria:
                parts.append(f"- [ ] {ac}")

        if hasattr(story, 'user_value') and story.user_value:
            parts.append(f"\n\n## User Value\n{story.user_value}")

        if hasattr(story, 'scope') and story.scope:
            if hasattr(story.scope, 'in_scope') and story.scope.in_scope:
                parts.append("\n\n## In Scope")
                for item in story.scope.in_scope:
                    parts.append(f"- {item}")
            if hasattr(story.scope, 'out_of_scope') and story.scope.out_of_scope:
                parts.append("\n\n## Out of Scope")
                for item in story.scope.out_of_scope:
                    parts.append(f"- ~~{item}~~")

        return "\n".join(parts)

    def _format_task_description(self, task: Task) -> str:
        """Format task description with implementation details.

        Args:
            task: Task item

        Returns:
            Formatted description string
        """
        parts = [self._format_description(task)]

        if hasattr(task, 'claude_code_prompt') and task.claude_code_prompt:
            parts.append("\n\n## Implementation Guide")
            parts.append(f"```\n{task.claude_code_prompt}\n```")

        if hasattr(task, 'work_type') and task.work_type:
            parts.append(f"\n\n**Work Type:** {task.work_type}")

        if hasattr(task, 'files_to_modify') and task.files_to_modify:
            parts.append("\n\n## Files to Modify")
            for f in task.files_to_modify:
                parts.append(f"- `{f}`")

        if hasattr(task, 'duration_hours') and task.duration_hours:
            parts.append(f"\n\n**Estimated Duration:** {task.duration_hours} hours")

        return "\n".join(parts)

    def _prompt_for_team(self) -> Optional[str]:
        """Prompt user to select a team.

        Returns:
            Selected team ID or None
        """
        teams = self.get_available_teams()

        if not teams:
            logger.error("No teams available")
            return None

        if len(teams) == 1:
            return teams[0]['id']

        print("\nAvailable Linear Teams:")
        for i, team in enumerate(teams, 1):
            print(f"  {i}. {team['name']} ({team['key']})")

        while True:
            try:
                choice = input("\nEnter team number (or 'q' to quit): ").strip()

                if choice.lower() == 'q':
                    return None

                idx = int(choice) - 1
                if 0 <= idx < len(teams):
                    return teams[idx]['id']

                print("Invalid selection. Please try again.")
            except (ValueError, EOFError, KeyboardInterrupt):
                return None

    def get_field_mapping(self) -> Dict[str, str]:
        """Return field mapping for Linear.

        Returns:
            Dictionary mapping Arcane fields to Linear fields
        """
        return {
            'name': 'title',
            'description': 'description',
            'priority': 'priority',
            'duration_hours': 'estimate',
            'tags': 'labelIds',
            'acceptance_criteria': 'description (Acceptance Criteria section)',
            'claude_code_prompt': 'description (Implementation Guide section)',
            'goal': 'description (Goal section)',
            'target_date': 'dueDate',
            'dependencies': 'description (Dependencies section)',
        }

    def update_issue(self, issue_id: str, fields: Dict[str, Any]) -> bool:
        """Update an existing Linear issue.

        Args:
            issue_id: Linear issue ID
            fields: Fields to update

        Returns:
            True if update succeeded
        """
        try:
            data = self._make_request(
                GRAPHQL_UPDATE_ISSUE,
                {'id': issue_id, 'input': fields}
            )
            result = data.get('issueUpdate', {})
            success = result.get('success', False)

            if success:
                logger.info(f"Updated issue {issue_id}")
            return success
        except Exception as e:
            logger.error(f"Failed to update issue {issue_id}: {e}")
            return False

    def add_comment(self, issue_id: str, comment: str) -> bool:
        """Add a comment to a Linear issue.

        Args:
            issue_id: Linear issue ID
            comment: Comment text (supports Markdown)

        Returns:
            True if comment was added
        """
        try:
            input_data = {
                'issueId': issue_id,
                'body': comment,
            }

            data = self._make_request(GRAPHQL_CREATE_COMMENT, {'input': input_data})
            result = data.get('commentCreate', {})
            success = result.get('success', False)

            if success:
                logger.info(f"Added comment to issue {issue_id}")
            return success
        except Exception as e:
            logger.error(f"Failed to add comment to {issue_id}: {e}")
            return False

    def create_issue_relation(
        self,
        issue_id: str,
        related_issue_id: str,
        relation_type: str = "related"
    ) -> bool:
        """Create a relation between two issues.

        Args:
            issue_id: First issue ID
            related_issue_id: Related issue ID
            relation_type: Type of relation (related, blocks, duplicate)

        Returns:
            True if relation was created
        """
        try:
            input_data = {
                'issueId': issue_id,
                'relatedIssueId': related_issue_id,
                'type': relation_type,
            }

            data = self._make_request(GRAPHQL_ADD_ISSUE_RELATION, {'input': input_data})
            result = data.get('issueRelationCreate', {})
            success = result.get('success', False)

            if success:
                logger.info(f"Created {relation_type} relation: {issue_id} -> {related_issue_id}")
            return success
        except Exception as e:
            logger.error(f"Failed to create relation: {e}")
            return False

    def get_issue(self, issue_id: str) -> Optional[Dict[str, Any]]:
        """Get issue details.

        Args:
            issue_id: Linear issue ID

        Returns:
            Issue data dictionary or None
        """
        query = """
        query GetIssue($id: String!) {
            issue(id: $id) {
                id
                identifier
                title
                description
                priority
                estimate
                state {
                    id
                    name
                }
                project {
                    id
                    name
                }
                cycle {
                    id
                    name
                }
                labels {
                    nodes {
                        id
                        name
                    }
                }
                parent {
                    id
                    identifier
                }
                children {
                    nodes {
                        id
                        identifier
                    }
                }
                url
            }
        }
        """
        try:
            data = self._make_request(query, {'id': issue_id})
            return data.get('issue')
        except Exception as e:
            logger.error(f"Failed to get issue {issue_id}: {e}")
            return None
