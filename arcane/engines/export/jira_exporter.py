#!/usr/bin/env python3
"""Jira export implementation.

This module provides functionality to export Arcane roadmaps to Jira,
mapping the roadmap hierarchy to Jira's issue structure:
- Milestone → Epic (with Epic Link)
- Epic → Epic (linked to milestone) or Feature
- Story → Story (linked to epic)
- Task → Sub-task (under story)
"""

import os
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field

from .base_exporter import BaseExporter, ExportPlatform, ExportResult, PLATFORM_CONFIGS
from arcane.items import Roadmap, Milestone, Epic, Story, Task
from arcane.utils.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class JiraFieldConfig:
    """Configuration for Jira custom fields.

    Jira custom field IDs vary by instance, so this class
    helps manage the mapping dynamically.
    """
    epic_name_field: str = "customfield_10011"
    epic_link_field: str = "customfield_10014"
    story_points_field: str = "customfield_10016"
    sprint_field: str = "customfield_10020"

    # Additional custom fields that may be configured
    custom_fields: Dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_jira_fields(cls, fields: List[Dict[str, Any]]) -> 'JiraFieldConfig':
        """Create config by discovering fields from Jira API.

        Args:
            fields: List of field definitions from Jira API

        Returns:
            JiraFieldConfig with discovered field IDs
        """
        config = cls()

        field_name_mapping = {
            'Epic Name': 'epic_name_field',
            'Epic Link': 'epic_link_field',
            'Story Points': 'story_points_field',
            'Sprint': 'sprint_field',
        }

        for field_def in fields:
            name = field_def.get('name', '')
            field_id = field_def.get('id', '')

            if name in field_name_mapping:
                setattr(config, field_name_mapping[name], field_id)
            elif field_id.startswith('customfield_'):
                config.custom_fields[name] = field_id

        return config


class JiraRateLimiter:
    """Simple rate limiter for Jira API calls.

    Jira Cloud has rate limits that vary by endpoint.
    This helps prevent hitting those limits.
    """

    def __init__(self, requests_per_second: float = 5.0):
        """Initialize rate limiter.

        Args:
            requests_per_second: Maximum requests per second
        """
        self.min_interval = 1.0 / requests_per_second
        self.last_request_time = 0.0

    def wait(self) -> None:
        """Wait if necessary to respect rate limit."""
        now = time.time()
        elapsed = now - self.last_request_time

        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)

        self.last_request_time = time.time()


class JiraExporter(BaseExporter):
    """Export roadmap to Jira.

    This exporter creates Jira issues from Arcane roadmap items,
    preserving the hierarchical structure through Epic Links
    and parent/child relationships.

    Example:
        exporter = JiraExporter(
            jira_url="https://yourcompany.atlassian.net",
            email="your@email.com",
            api_token="your-api-token",
            project_key="PROJ"
        )

        if exporter.validate_connection():
            result = exporter.export_roadmap(roadmap)
            print(f"Created {result.items_created} issues")
    """

    # Priority mapping from Arcane to Jira
    PRIORITY_MAPPING = {
        'Critical': 'Highest',
        'High': 'High',
        'Medium': 'Medium',
        'Low': 'Low',
        'Lowest': 'Lowest',
    }

    # Reverse priority mapping for import
    PRIORITY_MAPPING_REVERSE = {v: k for k, v in PRIORITY_MAPPING.items()}

    # Work type to Jira issue type mapping
    ISSUE_TYPE_MAPPING = {
        'milestone': 'Epic',
        'epic': 'Epic',
        'story': 'Story',
        'task': 'Sub-task',
        'implementation': 'Task',
        'design': 'Task',
        'research': 'Task',
        'testing': 'Task',
        'documentation': 'Task',
        'bug': 'Bug',
    }

    # Default story point conversion (hours to points)
    HOURS_PER_STORY_POINT = 8

    def __init__(
        self,
        jira_url: Optional[str] = None,
        email: Optional[str] = None,
        api_token: Optional[str] = None,
        project_key: Optional[str] = None,
        rate_limit: float = 5.0,
        auto_discover_fields: bool = True,
    ):
        """Initialize Jira exporter.

        Args:
            jira_url: Jira instance URL (e.g., https://yourcompany.atlassian.net)
            email: Email for authentication
            api_token: Jira API token
            project_key: Default project key for creating issues
            rate_limit: Maximum API requests per second
            auto_discover_fields: Whether to auto-discover custom field IDs
        """
        self.jira_url = jira_url or os.getenv('JIRA_URL')
        self.email = email or os.getenv('JIRA_EMAIL')
        self.api_token = api_token or os.getenv('JIRA_API_TOKEN')
        self.project_key = project_key or os.getenv('JIRA_PROJECT_KEY')
        self.auto_discover_fields = auto_discover_fields

        self._client = None
        self._rate_limiter = JiraRateLimiter(rate_limit)
        self._field_config: Optional[JiraFieldConfig] = None
        self._created_issues: Dict[str, str] = {}  # item_id -> jira_key
        self._issue_type_cache: Dict[str, List[str]] = {}  # project -> issue types

    @property
    def platform(self) -> ExportPlatform:
        """Return the platform this exporter handles."""
        return ExportPlatform.JIRA

    @property
    def config(self):
        """Return platform configuration."""
        return PLATFORM_CONFIGS[ExportPlatform.JIRA]

    @property
    def created_issues(self) -> Dict[str, str]:
        """Return mapping of item IDs to Jira issue keys."""
        return self._created_issues.copy()

    def _get_client(self):
        """Get or create Jira client.

        Returns:
            JIRA client instance

        Raises:
            ImportError: If jira package is not installed
            ValueError: If required credentials are missing
        """
        if self._client is None:
            try:
                from jira import JIRA
            except ImportError:
                raise ImportError(
                    "jira package is required for Jira export. "
                    "Install it with: pip install jira"
                )

            if not all([self.jira_url, self.email, self.api_token]):
                missing = []
                if not self.jira_url:
                    missing.append('JIRA_URL')
                if not self.email:
                    missing.append('JIRA_EMAIL')
                if not self.api_token:
                    missing.append('JIRA_API_TOKEN')
                raise ValueError(f"Missing required credentials: {', '.join(missing)}")

            self._client = JIRA(
                server=self.jira_url,
                basic_auth=(self.email, self.api_token)
            )

            # Discover custom fields if enabled
            if self.auto_discover_fields:
                self._discover_fields()

        return self._client

    def _discover_fields(self) -> None:
        """Discover custom field IDs from Jira instance."""
        try:
            self._rate_limiter.wait()
            fields = self._client.fields()
            self._field_config = JiraFieldConfig.from_jira_fields(fields)
            logger.debug(f"Discovered Jira fields: epic_name={self._field_config.epic_name_field}, "
                        f"epic_link={self._field_config.epic_link_field}")
        except Exception as e:
            logger.warning(f"Could not discover Jira fields, using defaults: {e}")
            self._field_config = JiraFieldConfig()

    def _get_field_config(self) -> JiraFieldConfig:
        """Get field configuration, discovering if necessary."""
        if self._field_config is None:
            self._field_config = JiraFieldConfig()
        return self._field_config

    def validate_connection(self) -> bool:
        """Validate Jira connection.

        Returns:
            True if connection is valid and authenticated
        """
        try:
            client = self._get_client()
            self._rate_limiter.wait()
            client.myself()
            return True
        except Exception as e:
            logger.error(f"Jira connection failed: {e}")
            return False

    def get_available_projects(self) -> List[Dict[str, str]]:
        """Get list of available Jira projects.

        Returns:
            List of project dictionaries with 'key' and 'name'
        """
        try:
            client = self._get_client()
            self._rate_limiter.wait()
            projects = client.projects()
            return [{'key': p.key, 'name': p.name} for p in projects]
        except Exception as e:
            logger.error(f"Failed to get projects: {e}")
            return []

    def get_issue_types(self, project_key: str) -> List[str]:
        """Get available issue types for a project.

        Args:
            project_key: Jira project key

        Returns:
            List of issue type names
        """
        if project_key in self._issue_type_cache:
            return self._issue_type_cache[project_key]

        try:
            client = self._get_client()
            self._rate_limiter.wait()
            project = client.project(project_key)
            issue_types = [it.name for it in project.issueTypes]
            self._issue_type_cache[project_key] = issue_types
            return issue_types
        except Exception as e:
            logger.error(f"Failed to get issue types: {e}")
            return []

    def _validate_issue_type(self, project_key: str, issue_type: str) -> str:
        """Validate and possibly adjust issue type for project.

        Args:
            project_key: Jira project key
            issue_type: Desired issue type

        Returns:
            Valid issue type name (may be adjusted)
        """
        available_types = self.get_issue_types(project_key)

        if issue_type in available_types:
            return issue_type

        # Try common alternatives
        alternatives = {
            'Sub-task': ['Subtask', 'Sub Task'],
            'Story': ['User Story'],
            'Epic': ['Initiative'],
            'Task': ['Technical Task'],
        }

        for alt in alternatives.get(issue_type, []):
            if alt in available_types:
                logger.info(f"Using '{alt}' instead of '{issue_type}'")
                return alt

        # Fall back to Task if available
        if 'Task' in available_types and issue_type != 'Task':
            logger.warning(f"Issue type '{issue_type}' not available, using 'Task'")
            return 'Task'

        # Use first available type as last resort
        if available_types:
            logger.warning(f"Issue type '{issue_type}' not available, using '{available_types[0]}'")
            return available_types[0]

        return issue_type

    def export_roadmap(self, roadmap: Roadmap, **kwargs) -> ExportResult:
        """Export roadmap to Jira.

        Args:
            roadmap: Roadmap to export
            **kwargs: Additional options:
                - project_key: Override default project key
                - sprint_id: Sprint to assign stories to
                - dry_run: If True, validate but don't create issues
                - skip_existing: If True, skip items that already exist

        Returns:
            ExportResult with export details
        """
        errors = []
        warnings = []
        items_created = 0
        items_failed = 0

        # Reset created issues tracking
        self._created_issues = {}

        try:
            client = self._get_client()

            # Get or prompt for project key
            project_key = kwargs.get('project_key', self.project_key)
            if not project_key:
                project_key = self._prompt_for_project(client)

            if not project_key:
                return ExportResult(
                    success=False,
                    platform=self.platform,
                    errors=["No project key specified"],
                )

            # Validate project exists
            try:
                self._rate_limiter.wait()
                client.project(project_key)
            except Exception as e:
                return ExportResult(
                    success=False,
                    platform=self.platform,
                    errors=[f"Project '{project_key}' not found: {e}"],
                )

            dry_run = kwargs.get('dry_run', False)
            sprint_id = kwargs.get('sprint_id')

            if dry_run:
                logger.info("Dry run mode - validating only")

            # Create issues in hierarchical order
            for milestone in roadmap.milestones:
                try:
                    if not dry_run:
                        self._create_milestone_epic(client, project_key, milestone)
                    items_created += 1

                    # Get epics under this milestone
                    epics = self._get_children_by_type(milestone, Epic)
                    for epic in epics:
                        try:
                            if not dry_run:
                                self._create_epic(client, project_key, epic, milestone)
                            items_created += 1

                            # Get stories under this epic
                            stories = self._get_children_by_type(epic, Story)
                            for story in stories:
                                try:
                                    if not dry_run:
                                        story_key = self._create_story(
                                            client, project_key, story, epic, sprint_id
                                        )
                                    items_created += 1

                                    # Get tasks under this story
                                    tasks = self._get_children_by_type(story, Task)
                                    for task in tasks:
                                        try:
                                            if not dry_run:
                                                self._create_subtask(client, project_key, task, story)
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
                    errors.append(f"Failed to create milestone '{milestone.name}': {e}")
                    items_failed += 1
                    logger.error(f"Error creating milestone: {e}")

            # Get project URL
            project_url = f"{self.jira_url}/browse/{project_key}"

            return ExportResult(
                success=len(errors) == 0,
                platform=self.platform,
                project_url=project_url,
                items_created=items_created,
                items_failed=items_failed,
                errors=errors,
                warnings=warnings,
                metadata={
                    'project_key': project_key,
                    'created_issues': self._created_issues.copy(),
                    'dry_run': dry_run,
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

    def _create_milestone_epic(self, client, project_key: str, milestone: Milestone) -> str:
        """Create a Jira Epic for a milestone.

        Args:
            client: Jira client
            project_key: Project key
            milestone: Milestone to create

        Returns:
            Created issue key
        """
        field_config = self._get_field_config()
        issue_type = self._validate_issue_type(project_key, 'Epic')

        issue_dict = {
            'project': {'key': project_key},
            'summary': f"[Milestone] {milestone.name}",
            'description': self._format_description(milestone),
            'issuetype': {'name': issue_type},
        }

        # Add priority if available
        if hasattr(milestone, 'priority') and milestone.priority:
            jira_priority = self.PRIORITY_MAPPING.get(milestone.priority, 'Medium')
            issue_dict['priority'] = {'name': jira_priority}

        # Add epic name field (required for epics in most Jira configs)
        if issue_type == 'Epic':
            issue_dict[field_config.epic_name_field] = milestone.name

        # Add labels if available
        if hasattr(milestone, 'tags') and milestone.tags:
            issue_dict['labels'] = self._sanitize_labels(milestone.tags)

        self._rate_limiter.wait()
        issue = client.create_issue(fields=issue_dict)
        self._created_issues[milestone.id] = issue.key
        logger.info(f"Created Jira Epic: {issue.key} for milestone {milestone.name}")
        return issue.key

    def _create_epic(self, client, project_key: str, epic: Epic, milestone: Milestone) -> str:
        """Create a Jira Epic for an epic.

        Args:
            client: Jira client
            project_key: Project key
            epic: Epic to create
            milestone: Parent milestone

        Returns:
            Created issue key
        """
        field_config = self._get_field_config()
        parent_key = self._created_issues.get(milestone.id)
        issue_type = self._validate_issue_type(project_key, 'Epic')

        issue_dict = {
            'project': {'key': project_key},
            'summary': epic.name,
            'description': self._format_description(epic),
            'issuetype': {'name': issue_type},
        }

        # Add priority
        if hasattr(epic, 'priority') and epic.priority:
            jira_priority = self.PRIORITY_MAPPING.get(epic.priority, 'Medium')
            issue_dict['priority'] = {'name': jira_priority}

        # Add epic name
        if issue_type == 'Epic':
            issue_dict[field_config.epic_name_field] = epic.name

        # Add labels
        if hasattr(epic, 'tags') and epic.tags:
            issue_dict['labels'] = self._sanitize_labels(epic.tags)

        self._rate_limiter.wait()
        issue = client.create_issue(fields=issue_dict)
        self._created_issues[epic.id] = issue.key

        # Create link to milestone epic
        if parent_key:
            try:
                self._rate_limiter.wait()
                client.create_issue_link(
                    type="Relates",
                    inwardIssue=issue.key,
                    outwardIssue=parent_key,
                )
            except Exception as e:
                logger.warning(f"Could not link epic to milestone: {e}")

        logger.info(f"Created Jira Epic: {issue.key} for {epic.name}")
        return issue.key

    def _create_story(
        self,
        client,
        project_key: str,
        story: Story,
        epic: Epic,
        sprint_id: Optional[str] = None
    ) -> str:
        """Create a Jira Story linked to an Epic.

        Args:
            client: Jira client
            project_key: Project key
            story: Story to create
            epic: Parent epic
            sprint_id: Optional sprint to assign to

        Returns:
            Created issue key
        """
        field_config = self._get_field_config()
        epic_key = self._created_issues.get(epic.id)
        issue_type = self._validate_issue_type(project_key, 'Story')

        issue_dict = {
            'project': {'key': project_key},
            'summary': story.name,
            'description': self._format_story_description(story),
            'issuetype': {'name': issue_type},
        }

        # Add priority
        if hasattr(story, 'priority') and story.priority:
            jira_priority = self.PRIORITY_MAPPING.get(story.priority, 'Medium')
            issue_dict['priority'] = {'name': jira_priority}

        # Link to epic
        if epic_key and field_config.epic_link_field:
            issue_dict[field_config.epic_link_field] = epic_key

        # Add story points if duration is set
        if hasattr(story, 'duration_hours') and story.duration_hours:
            story_points = max(1, round(story.duration_hours / self.HOURS_PER_STORY_POINT))
            if field_config.story_points_field:
                issue_dict[field_config.story_points_field] = float(story_points)

        # Add sprint if specified
        if sprint_id and field_config.sprint_field:
            issue_dict[field_config.sprint_field] = int(sprint_id)

        # Add labels
        if hasattr(story, 'tags') and story.tags:
            issue_dict['labels'] = self._sanitize_labels(story.tags)

        self._rate_limiter.wait()
        issue = client.create_issue(fields=issue_dict)
        self._created_issues[story.id] = issue.key
        logger.info(f"Created Jira Story: {issue.key} for {story.name}")
        return issue.key

    def _create_subtask(self, client, project_key: str, task: Task, story: Story) -> str:
        """Create a Jira Sub-task under a Story.

        Args:
            client: Jira client
            project_key: Project key
            task: Task to create
            story: Parent story

        Returns:
            Created issue key or None if parent not found
        """
        parent_key = self._created_issues.get(story.id)

        if not parent_key:
            logger.warning(f"No parent story found for task {task.name}")
            raise ValueError(f"Parent story not created for task '{task.name}'")

        issue_type = self._validate_issue_type(project_key, 'Sub-task')

        issue_dict = {
            'project': {'key': project_key},
            'summary': task.name,
            'description': self._format_task_description(task),
            'issuetype': {'name': issue_type},
            'parent': {'key': parent_key},
        }

        # Add priority
        if hasattr(task, 'priority') and task.priority:
            jira_priority = self.PRIORITY_MAPPING.get(task.priority, 'Medium')
            issue_dict['priority'] = {'name': jira_priority}

        # Add time estimate if duration is set
        if hasattr(task, 'duration_hours') and task.duration_hours:
            # Jira expects time in seconds
            issue_dict['timetracking'] = {
                'originalEstimate': f"{int(task.duration_hours)}h"
            }

        # Add labels
        if hasattr(task, 'tags') and task.tags:
            issue_dict['labels'] = self._sanitize_labels(task.tags)

        self._rate_limiter.wait()
        issue = client.create_issue(fields=issue_dict)
        self._created_issues[task.id] = issue.key
        logger.info(f"Created Jira Sub-task: {issue.key} for {task.name}")
        return issue.key

    def _sanitize_labels(self, tags: List[str]) -> List[str]:
        """Sanitize tags for use as Jira labels.

        Jira labels cannot contain spaces.

        Args:
            tags: List of tags

        Returns:
            Sanitized labels
        """
        return [tag.replace(' ', '-').replace('_', '-') for tag in tags if tag]

    def _format_description(self, item) -> str:
        """Format item description for Jira.

        Args:
            item: Roadmap item

        Returns:
            Formatted description string
        """
        parts = []

        if hasattr(item, 'description') and item.description:
            parts.append(item.description)

        if hasattr(item, 'goal') and item.goal:
            parts.append(f"\n\n*Goal:*\n{item.goal}")

        if hasattr(item, 'key_deliverables') and item.key_deliverables:
            parts.append("\n\n*Key Deliverables:*")
            for d in item.key_deliverables:
                parts.append(f"* {d}")

        if hasattr(item, 'technical_requirements') and item.technical_requirements:
            parts.append("\n\n*Technical Requirements:*")
            for r in item.technical_requirements:
                parts.append(f"* {r}")

        if hasattr(item, 'dependencies') and item.dependencies:
            parts.append("\n\n*Dependencies:*")
            for dep in item.dependencies:
                parts.append(f"* {dep}")

        return "\n".join(parts) if parts else "No description provided."

    def _format_story_description(self, story: Story) -> str:
        """Format story description with acceptance criteria.

        Args:
            story: Story item

        Returns:
            Formatted description string
        """
        parts = [self._format_description(story)]

        if hasattr(story, 'acceptance_criteria') and story.acceptance_criteria:
            parts.append("\n\n*Acceptance Criteria:*")
            for ac in story.acceptance_criteria:
                parts.append(f"* {ac}")

        if hasattr(story, 'user_value') and story.user_value:
            parts.append(f"\n\n*User Value:*\n{story.user_value}")

        if hasattr(story, 'scope') and story.scope:
            if hasattr(story.scope, 'in_scope') and story.scope.in_scope:
                parts.append("\n\n*In Scope:*")
                for item in story.scope.in_scope:
                    parts.append(f"* {item}")
            if hasattr(story.scope, 'out_of_scope') and story.scope.out_of_scope:
                parts.append("\n\n*Out of Scope:*")
                for item in story.scope.out_of_scope:
                    parts.append(f"* {item}")

        return "\n".join(parts)

    def _format_task_description(self, task: Task) -> str:
        """Format task description with Claude prompt.

        Args:
            task: Task item

        Returns:
            Formatted description string
        """
        parts = [self._format_description(task)]

        if hasattr(task, 'claude_code_prompt') and task.claude_code_prompt:
            parts.append("\n\n*Implementation Guide:*")
            parts.append(f"{{code}}\n{task.claude_code_prompt}\n{{code}}")

        if hasattr(task, 'work_type') and task.work_type:
            parts.append(f"\n\n*Work Type:* {task.work_type}")

        if hasattr(task, 'files_to_modify') and task.files_to_modify:
            parts.append("\n\n*Files to Modify:*")
            for f in task.files_to_modify:
                parts.append(f"* {f}")

        return "\n".join(parts)

    def _prompt_for_project(self, client) -> Optional[str]:
        """Prompt user to select a Jira project.

        Args:
            client: Jira client

        Returns:
            Selected project key or None
        """
        try:
            self._rate_limiter.wait()
            projects = client.projects()
        except Exception as e:
            logger.error(f"Failed to get projects: {e}")
            return None

        if not projects:
            logger.error("No projects available")
            return None

        print("\nAvailable Jira Projects:")
        for i, project in enumerate(projects, 1):
            print(f"  {i}. {project.key} - {project.name}")

        while True:
            try:
                choice = input("\nEnter project number or key (or 'q' to quit): ").strip()

                if choice.lower() == 'q':
                    return None

                # Try as number
                try:
                    idx = int(choice) - 1
                    if 0 <= idx < len(projects):
                        return projects[idx].key
                except ValueError:
                    pass

                # Try as key
                if choice.upper() in [p.key for p in projects]:
                    return choice.upper()

                print("Invalid selection. Please try again.")
            except (EOFError, KeyboardInterrupt):
                return None

    def get_field_mapping(self) -> Dict[str, str]:
        """Return field mapping for Jira.

        Returns:
            Dictionary mapping Arcane fields to Jira fields
        """
        return {
            'name': 'summary',
            'description': 'description',
            'priority': 'priority',
            'duration_hours': 'timeoriginalestimate',
            'tags': 'labels',
            'acceptance_criteria': 'description (Acceptance Criteria section)',
            'claude_code_prompt': 'description (Implementation Guide section)',
            'goal': 'description (Goal section)',
            'key_deliverables': 'description (Key Deliverables section)',
            'technical_requirements': 'description (Technical Requirements section)',
            'dependencies': 'description (Dependencies section)',
        }

    def get_sprint_info(self, board_id: int) -> List[Dict[str, Any]]:
        """Get sprint information for a board.

        Args:
            board_id: Jira board ID

        Returns:
            List of sprint dictionaries
        """
        try:
            client = self._get_client()
            self._rate_limiter.wait()
            sprints = client.sprints(board_id)
            return [
                {
                    'id': s.id,
                    'name': s.name,
                    'state': s.state,
                    'startDate': getattr(s, 'startDate', None),
                    'endDate': getattr(s, 'endDate', None),
                }
                for s in sprints
            ]
        except Exception as e:
            logger.error(f"Failed to get sprints: {e}")
            return []

    def update_issue(self, issue_key: str, fields: Dict[str, Any]) -> bool:
        """Update an existing Jira issue.

        Args:
            issue_key: Jira issue key (e.g., 'PROJ-123')
            fields: Fields to update

        Returns:
            True if update succeeded
        """
        try:
            client = self._get_client()
            self._rate_limiter.wait()
            issue = client.issue(issue_key)
            issue.update(fields=fields)
            logger.info(f"Updated issue {issue_key}")
            return True
        except Exception as e:
            logger.error(f"Failed to update issue {issue_key}: {e}")
            return False

    def add_comment(self, issue_key: str, comment: str) -> bool:
        """Add a comment to a Jira issue.

        Args:
            issue_key: Jira issue key
            comment: Comment text

        Returns:
            True if comment was added
        """
        try:
            client = self._get_client()
            self._rate_limiter.wait()
            client.add_comment(issue_key, comment)
            logger.info(f"Added comment to {issue_key}")
            return True
        except Exception as e:
            logger.error(f"Failed to add comment to {issue_key}: {e}")
            return False
