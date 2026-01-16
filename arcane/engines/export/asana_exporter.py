#!/usr/bin/env python3
"""Asana export implementation.

This module provides functionality to export Arcane roadmaps to Asana,
mapping the roadmap hierarchy to Asana's project structure:
- Roadmap → Project
- Milestone → Section
- Epic → Task (with subtasks)
- Story → Subtask
- Task → Subtask of subtask (or checklist item via description)
"""

import os
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from .base_exporter import BaseExporter, ExportPlatform, ExportResult, PLATFORM_CONFIGS
from arcane.items import Roadmap, Milestone, Epic, Story, Task
from arcane.utils.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class AsanaFieldConfig:
    """Configuration for Asana custom fields.

    Asana custom field GIDs vary by workspace, so this class
    helps manage the mapping dynamically.
    """
    priority_field_gid: Optional[str] = None
    status_field_gid: Optional[str] = None
    duration_field_gid: Optional[str] = None
    story_points_field_gid: Optional[str] = None

    # Mapping of priority values to custom field enum option GIDs
    priority_options: Dict[str, str] = field(default_factory=dict)

    # Mapping of status values to custom field enum option GIDs
    status_options: Dict[str, str] = field(default_factory=dict)

    # Additional custom fields that may be configured
    custom_fields: Dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_asana_fields(cls, custom_fields: List[Dict[str, Any]]) -> 'AsanaFieldConfig':
        """Create config by discovering fields from Asana API.

        Args:
            custom_fields: List of custom field definitions from Asana API

        Returns:
            AsanaFieldConfig with discovered field GIDs
        """
        config = cls()

        field_name_mapping = {
            'Priority': 'priority_field_gid',
            'Status': 'status_field_gid',
            'Duration': 'duration_field_gid',
            'Story Points': 'story_points_field_gid',
        }

        for field_def in custom_fields:
            name = field_def.get('name', '')
            gid = field_def.get('gid', '')

            if name in field_name_mapping:
                setattr(config, field_name_mapping[name], gid)

                # Extract enum options if this is an enum field
                if field_def.get('enum_options'):
                    options = {}
                    for opt in field_def['enum_options']:
                        options[opt.get('name', '')] = opt.get('gid', '')

                    if name == 'Priority':
                        config.priority_options = options
                    elif name == 'Status':
                        config.status_options = options
            else:
                config.custom_fields[name] = gid

        return config


class AsanaRateLimiter:
    """Rate limiter for Asana API calls.

    Asana has rate limits of approximately 1500 requests per minute.
    This helps prevent hitting those limits.
    """

    def __init__(self, requests_per_second: float = 20.0):
        """Initialize rate limiter.

        Args:
            requests_per_second: Maximum requests per second (default 20)
        """
        self.min_interval = 1.0 / requests_per_second
        self.last_request_time = 0.0
        self._request_count = 0
        self._window_start = time.time()

    def wait(self) -> None:
        """Wait if necessary to respect rate limit."""
        now = time.time()
        elapsed = now - self.last_request_time

        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)

        self.last_request_time = time.time()
        self._request_count += 1

    def get_request_count(self) -> int:
        """Get number of requests made since window start."""
        return self._request_count

    def reset_window(self) -> None:
        """Reset the request counting window."""
        self._request_count = 0
        self._window_start = time.time()


class AsanaExporter(BaseExporter):
    """Export roadmap to Asana.

    This exporter creates Asana projects, sections, and tasks from
    Arcane roadmap items, preserving the hierarchical structure through
    sections and parent/subtask relationships.

    Example:
        exporter = AsanaExporter(
            access_token="your-personal-access-token",
            workspace_id="your-workspace-id"
        )

        if exporter.validate_connection():
            result = exporter.export_roadmap(roadmap)
            print(f"Created {result.items_created} items")
    """

    # Priority mapping from Arcane to Asana
    PRIORITY_MAPPING = {
        'Critical': 'High',
        'High': 'High',
        'Medium': 'Medium',
        'Low': 'Low',
        'Lowest': 'Low',
    }

    # Reverse priority mapping for import
    PRIORITY_MAPPING_REVERSE = {v: k for k, v in PRIORITY_MAPPING.items()}

    # Status mapping
    STATUS_MAPPING = {
        'Not Started': 'Not Started',
        'In Progress': 'In Progress',
        'Completed': 'Completed',
        'Blocked': 'On Hold',
    }

    # Default hours per day for duration calculation
    HOURS_PER_DAY = 8

    def __init__(
        self,
        access_token: Optional[str] = None,
        workspace_id: Optional[str] = None,
        project_id: Optional[str] = None,
        rate_limit: float = 20.0,
        auto_discover_fields: bool = True,
    ):
        """Initialize Asana exporter.

        Args:
            access_token: Asana personal access token
            workspace_id: Asana workspace GID
            project_id: Default project GID for creating tasks
            rate_limit: Maximum API requests per second
            auto_discover_fields: Whether to auto-discover custom field GIDs
        """
        self.access_token = access_token or os.getenv('ASANA_ACCESS_TOKEN')
        self.workspace_id = workspace_id or os.getenv('ASANA_WORKSPACE_ID')
        self.project_id = project_id or os.getenv('ASANA_PROJECT_ID')
        self.auto_discover_fields = auto_discover_fields

        self._client = None
        self._rate_limiter = AsanaRateLimiter(rate_limit)
        self._field_config: Optional[AsanaFieldConfig] = None
        self._created_items: Dict[str, str] = {}  # item_id -> asana_gid
        self._section_cache: Dict[str, str] = {}  # section_name -> section_gid

    @property
    def platform(self) -> ExportPlatform:
        """Return the platform this exporter handles."""
        return ExportPlatform.ASANA

    @property
    def config(self):
        """Return platform configuration."""
        return PLATFORM_CONFIGS[ExportPlatform.ASANA]

    @property
    def created_items(self) -> Dict[str, str]:
        """Return mapping of item IDs to Asana GIDs."""
        return self._created_items.copy()

    def _get_client(self):
        """Get or create Asana client.

        Returns:
            Asana client instance

        Raises:
            ImportError: If asana package is not installed
            ValueError: If required credentials are missing
        """
        if self._client is None:
            try:
                import asana
            except ImportError:
                raise ImportError(
                    "asana package is required for Asana export. "
                    "Install it with: pip install asana"
                )

            if not self.access_token:
                raise ValueError("Missing required credential: ASANA_ACCESS_TOKEN")

            # Create client with personal access token
            configuration = asana.Configuration()
            configuration.access_token = self.access_token
            self._client = asana.ApiClient(configuration)

        return self._client

    def _get_tasks_api(self):
        """Get Tasks API instance."""
        import asana
        return asana.TasksApi(self._get_client())

    def _get_projects_api(self):
        """Get Projects API instance."""
        import asana
        return asana.ProjectsApi(self._get_client())

    def _get_sections_api(self):
        """Get Sections API instance."""
        import asana
        return asana.SectionsApi(self._get_client())

    def _get_workspaces_api(self):
        """Get Workspaces API instance."""
        import asana
        return asana.WorkspacesApi(self._get_client())

    def _get_users_api(self):
        """Get Users API instance."""
        import asana
        return asana.UsersApi(self._get_client())

    def _get_custom_fields_api(self):
        """Get Custom Fields API instance."""
        import asana
        return asana.CustomFieldsApi(self._get_client())

    def _discover_workspace(self) -> Optional[str]:
        """Discover workspace ID if not set.

        Returns:
            Workspace GID or None
        """
        if self.workspace_id:
            return self.workspace_id

        try:
            users_api = self._get_users_api()
            self._rate_limiter.wait()
            me = users_api.get_user("me", {})
            workspaces = me.get('workspaces', [])
            if workspaces:
                self.workspace_id = workspaces[0].get('gid')
                logger.info(f"Using workspace: {workspaces[0].get('name')}")
                return self.workspace_id
        except Exception as e:
            logger.error(f"Failed to discover workspace: {e}")

        return None

    def _discover_fields(self, project_gid: str) -> None:
        """Discover custom field GIDs from project.

        Args:
            project_gid: Project GID to get custom fields from
        """
        try:
            projects_api = self._get_projects_api()
            self._rate_limiter.wait()
            project = projects_api.get_project(project_gid, {
                'opt_fields': 'custom_field_settings.custom_field'
            })

            custom_fields = []
            settings = project.get('custom_field_settings', [])
            for setting in settings:
                cf = setting.get('custom_field', {})
                if cf:
                    custom_fields.append(cf)

            self._field_config = AsanaFieldConfig.from_asana_fields(custom_fields)
            logger.debug(f"Discovered {len(custom_fields)} custom fields")
        except Exception as e:
            logger.warning(f"Could not discover Asana fields: {e}")
            self._field_config = AsanaFieldConfig()

    def _get_field_config(self) -> AsanaFieldConfig:
        """Get field configuration."""
        if self._field_config is None:
            self._field_config = AsanaFieldConfig()
        return self._field_config

    def validate_connection(self) -> bool:
        """Validate Asana connection.

        Returns:
            True if connection is valid and authenticated
        """
        try:
            users_api = self._get_users_api()
            self._rate_limiter.wait()
            me = users_api.get_user("me", {})
            logger.info(f"Connected as: {me.get('name')}")
            return True
        except Exception as e:
            logger.error(f"Asana connection failed: {e}")
            return False

    def get_available_workspaces(self) -> List[Dict[str, str]]:
        """Get list of available Asana workspaces.

        Returns:
            List of workspace dictionaries with 'gid' and 'name'
        """
        try:
            users_api = self._get_users_api()
            self._rate_limiter.wait()
            me = users_api.get_user("me", {})
            return [
                {'gid': w.get('gid'), 'name': w.get('name')}
                for w in me.get('workspaces', [])
            ]
        except Exception as e:
            logger.error(f"Failed to get workspaces: {e}")
            return []

    def get_available_projects(self, workspace_gid: Optional[str] = None) -> List[Dict[str, str]]:
        """Get list of available Asana projects.

        Args:
            workspace_gid: Workspace GID (uses default if not provided)

        Returns:
            List of project dictionaries with 'gid' and 'name'
        """
        workspace = workspace_gid or self.workspace_id
        if not workspace:
            workspace = self._discover_workspace()

        if not workspace:
            logger.error("No workspace available")
            return []

        try:
            projects_api = self._get_projects_api()
            self._rate_limiter.wait()
            projects = projects_api.get_projects({
                'workspace': workspace,
                'opt_fields': 'name,archived'
            })
            return [
                {'gid': p.get('gid'), 'name': p.get('name')}
                for p in projects
                if not p.get('archived', False)
            ]
        except Exception as e:
            logger.error(f"Failed to get projects: {e}")
            return []

    def create_project(
        self,
        name: str,
        workspace_gid: Optional[str] = None,
        **kwargs
    ) -> Optional[str]:
        """Create a new Asana project.

        Args:
            name: Project name
            workspace_gid: Workspace GID (uses default if not provided)
            **kwargs: Additional project options (notes, color, etc.)

        Returns:
            Created project GID or None
        """
        workspace = workspace_gid or self.workspace_id
        if not workspace:
            workspace = self._discover_workspace()

        if not workspace:
            logger.error("No workspace available for project creation")
            return None

        try:
            projects_api = self._get_projects_api()

            project_data = {
                'name': name,
                'workspace': workspace,
                'default_view': 'list',
            }

            # Add optional fields
            if kwargs.get('notes'):
                project_data['notes'] = kwargs['notes']
            if kwargs.get('color'):
                project_data['color'] = kwargs['color']
            if kwargs.get('due_date'):
                project_data['due_date'] = kwargs['due_date']

            self._rate_limiter.wait()
            project = projects_api.create_project({'data': project_data}, {})
            project_gid = project.get('gid')
            logger.info(f"Created Asana project: {name} ({project_gid})")
            return project_gid
        except Exception as e:
            logger.error(f"Failed to create project: {e}")
            return None

    def export_roadmap(self, roadmap: Roadmap, **kwargs) -> ExportResult:
        """Export roadmap to Asana.

        Args:
            roadmap: Roadmap to export
            **kwargs: Additional options:
                - project_gid: Use existing project instead of creating new
                - project_name: Name for new project (default: roadmap name)
                - workspace_gid: Workspace to use
                - dry_run: If True, validate but don't create items
                - create_dependencies: If True, create task dependencies

        Returns:
            ExportResult with export details
        """
        errors = []
        warnings = []
        items_created = 0
        items_failed = 0

        # Reset tracking
        self._created_items = {}
        self._section_cache = {}

        try:
            # Ensure we have a client
            self._get_client()

            # Get or create project
            project_gid = kwargs.get('project_gid', self.project_id)
            workspace_gid = kwargs.get('workspace_gid', self.workspace_id)

            if not workspace_gid:
                workspace_gid = self._discover_workspace()

            if not workspace_gid:
                return ExportResult(
                    success=False,
                    platform=self.platform,
                    errors=["No workspace available. Set ASANA_WORKSPACE_ID or provide workspace_gid."],
                )

            dry_run = kwargs.get('dry_run', False)
            create_dependencies = kwargs.get('create_dependencies', True)

            if dry_run:
                logger.info("Dry run mode - validating only")

            # Create or use existing project
            if not project_gid:
                project_name = kwargs.get('project_name')
                if not project_name:
                    project_name = getattr(roadmap, 'name', None) or 'Arcane Roadmap'

                if not dry_run:
                    project_gid = self.create_project(
                        name=project_name,
                        workspace_gid=workspace_gid,
                        notes=getattr(roadmap, 'description', ''),
                    )
                    if not project_gid:
                        return ExportResult(
                            success=False,
                            platform=self.platform,
                            errors=["Failed to create project"],
                        )
                else:
                    project_gid = "dry-run-project"

            # Discover custom fields if enabled
            if self.auto_discover_fields and not dry_run:
                self._discover_fields(project_gid)

            # Process milestones as sections
            for milestone in roadmap.milestones:
                try:
                    section_gid = None
                    if not dry_run:
                        section_gid = self._create_section(project_gid, milestone)
                    items_created += 1

                    # Get epics under this milestone
                    epics = self._get_children_by_type(milestone, Epic)
                    for epic in epics:
                        try:
                            epic_task_gid = None
                            if not dry_run:
                                epic_task_gid = self._create_epic_task(
                                    project_gid, section_gid, epic
                                )
                            items_created += 1

                            # Get stories under this epic
                            stories = self._get_children_by_type(epic, Story)
                            for story in stories:
                                try:
                                    story_task_gid = None
                                    if not dry_run:
                                        story_task_gid = self._create_story_subtask(
                                            epic_task_gid, story
                                        )
                                    items_created += 1

                                    # Get tasks under this story
                                    tasks = self._get_children_by_type(story, Task)
                                    for task in tasks:
                                        try:
                                            if not dry_run:
                                                self._create_task_subtask(
                                                    story_task_gid, task
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
                    errors.append(f"Failed to create milestone section '{milestone.name}': {e}")
                    items_failed += 1
                    logger.error(f"Error creating milestone section: {e}")

            # Create dependencies if requested
            if create_dependencies and not dry_run:
                dep_errors = self._create_dependencies(roadmap)
                warnings.extend(dep_errors)

            # Build project URL
            project_url = None
            if project_gid and not dry_run:
                project_url = f"https://app.asana.com/0/{project_gid}/list"

            return ExportResult(
                success=len(errors) == 0,
                platform=self.platform,
                project_url=project_url,
                items_created=items_created,
                items_failed=items_failed,
                errors=errors,
                warnings=warnings,
                metadata={
                    'project_gid': project_gid,
                    'workspace_gid': workspace_gid,
                    'created_items': self._created_items.copy(),
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

    def _create_section(self, project_gid: str, milestone: Milestone) -> str:
        """Create an Asana section for a milestone.

        Args:
            project_gid: Project GID
            milestone: Milestone to create section for

        Returns:
            Created section GID
        """
        sections_api = self._get_sections_api()

        section_data = {
            'name': milestone.name,
        }

        self._rate_limiter.wait()
        section = sections_api.create_section_for_project(
            project_gid,
            {'data': section_data},
            {}
        )

        section_gid = section.get('gid')
        self._created_items[milestone.id] = section_gid
        self._section_cache[milestone.name] = section_gid
        logger.info(f"Created Asana section: {milestone.name} ({section_gid})")
        return section_gid

    def _create_epic_task(
        self,
        project_gid: str,
        section_gid: Optional[str],
        epic: Epic
    ) -> str:
        """Create an Asana task for an epic.

        Args:
            project_gid: Project GID
            section_gid: Section GID to add task to
            epic: Epic to create task for

        Returns:
            Created task GID
        """
        tasks_api = self._get_tasks_api()

        task_data = {
            'name': f"[Epic] {epic.name}",
            'notes': self._format_description(epic),
            'projects': [project_gid],
        }

        # Add to section if available
        if section_gid:
            task_data['memberships'] = [{
                'project': project_gid,
                'section': section_gid
            }]

        # Add due date if available
        if hasattr(epic, 'target_date') and epic.target_date:
            task_data['due_on'] = self._format_date(epic.target_date)

        # Add custom fields
        custom_fields = self._build_custom_fields(epic)
        if custom_fields:
            task_data['custom_fields'] = custom_fields

        # Add tags if available
        if hasattr(epic, 'tags') and epic.tags:
            task_data['tags'] = self._get_or_create_tags(epic.tags)

        self._rate_limiter.wait()
        task = tasks_api.create_task({'data': task_data}, {})

        task_gid = task.get('gid')
        self._created_items[epic.id] = task_gid
        logger.info(f"Created Asana task for epic: {epic.name} ({task_gid})")
        return task_gid

    def _create_story_subtask(self, parent_task_gid: str, story: Story) -> str:
        """Create an Asana subtask for a story.

        Args:
            parent_task_gid: Parent task GID
            story: Story to create subtask for

        Returns:
            Created subtask GID
        """
        if not parent_task_gid:
            raise ValueError(f"Parent task not created for story '{story.name}'")

        tasks_api = self._get_tasks_api()

        task_data = {
            'name': story.name,
            'notes': self._format_story_description(story),
        }

        # Add due date if available
        if hasattr(story, 'target_date') and story.target_date:
            task_data['due_on'] = self._format_date(story.target_date)

        # Add custom fields
        custom_fields = self._build_custom_fields(story)
        if custom_fields:
            task_data['custom_fields'] = custom_fields

        self._rate_limiter.wait()
        subtask = tasks_api.create_subtask_for_task(
            parent_task_gid,
            {'data': task_data},
            {}
        )

        subtask_gid = subtask.get('gid')
        self._created_items[story.id] = subtask_gid
        logger.info(f"Created Asana subtask for story: {story.name} ({subtask_gid})")
        return subtask_gid

    def _create_task_subtask(self, parent_task_gid: str, task: Task) -> str:
        """Create an Asana subtask for a task.

        Note: Asana only supports one level of subtasks natively.
        For deeper nesting, we add tasks to the description as a checklist.

        Args:
            parent_task_gid: Parent task GID
            task: Task to create subtask for

        Returns:
            Created subtask GID
        """
        if not parent_task_gid:
            raise ValueError(f"Parent task not created for task '{task.name}'")

        tasks_api = self._get_tasks_api()

        task_data = {
            'name': task.name,
            'notes': self._format_task_description(task),
        }

        # Add due date based on duration
        if hasattr(task, 'duration_hours') and task.duration_hours:
            days = max(1, int(task.duration_hours / self.HOURS_PER_DAY))
            due_date = datetime.now() + timedelta(days=days)
            task_data['due_on'] = due_date.strftime('%Y-%m-%d')

        # Add custom fields
        custom_fields = self._build_custom_fields(task)
        if custom_fields:
            task_data['custom_fields'] = custom_fields

        self._rate_limiter.wait()
        subtask = tasks_api.create_subtask_for_task(
            parent_task_gid,
            {'data': task_data},
            {}
        )

        subtask_gid = subtask.get('gid')
        self._created_items[task.id] = subtask_gid
        logger.info(f"Created Asana subtask for task: {task.name} ({subtask_gid})")
        return subtask_gid

    def _build_custom_fields(self, item) -> Dict[str, Any]:
        """Build custom fields dictionary for an item.

        Args:
            item: Roadmap item

        Returns:
            Dictionary of custom field GID to value
        """
        field_config = self._get_field_config()
        custom_fields = {}

        # Add priority
        if hasattr(item, 'priority') and item.priority:
            asana_priority = self.PRIORITY_MAPPING.get(item.priority, 'Medium')
            if field_config.priority_field_gid and asana_priority in field_config.priority_options:
                custom_fields[field_config.priority_field_gid] = \
                    field_config.priority_options[asana_priority]

        # Add duration/story points
        if hasattr(item, 'duration_hours') and item.duration_hours:
            if field_config.duration_field_gid:
                custom_fields[field_config.duration_field_gid] = str(item.duration_hours)
            if field_config.story_points_field_gid:
                story_points = max(1, round(item.duration_hours / self.HOURS_PER_DAY))
                custom_fields[field_config.story_points_field_gid] = str(story_points)

        return custom_fields

    def _get_or_create_tags(self, tag_names: List[str]) -> List[str]:
        """Get or create tags and return their GIDs.

        Args:
            tag_names: List of tag names

        Returns:
            List of tag GIDs
        """
        # For simplicity, we don't create tags here
        # Tags need to be pre-created in Asana
        # This would require additional API calls to search/create tags
        return []

    def _create_dependencies(self, roadmap: Roadmap) -> List[str]:
        """Create task dependencies based on roadmap item dependencies.

        Args:
            roadmap: Roadmap with dependency information

        Returns:
            List of warning messages for failed dependencies
        """
        warnings = []
        tasks_api = self._get_tasks_api()

        # Iterate through all items and create dependencies
        for milestone in roadmap.milestones:
            for epic in self._get_children_by_type(milestone, Epic):
                for story in self._get_children_by_type(epic, Story):
                    if hasattr(story, 'dependencies') and story.dependencies:
                        story_gid = self._created_items.get(story.id)
                        if not story_gid:
                            continue

                        for dep_id in story.dependencies:
                            dep_gid = self._created_items.get(dep_id)
                            if dep_gid:
                                try:
                                    self._rate_limiter.wait()
                                    tasks_api.add_dependencies_for_task(
                                        story_gid,
                                        {'data': {'dependencies': [dep_gid]}},
                                        {}
                                    )
                                except Exception as e:
                                    warnings.append(
                                        f"Could not create dependency {dep_id} -> {story.id}: {e}"
                                    )

        return warnings

    def _format_date(self, date_value) -> str:
        """Format a date value for Asana API.

        Args:
            date_value: Date as string or datetime

        Returns:
            Date string in YYYY-MM-DD format
        """
        if isinstance(date_value, str):
            # Try to parse and reformat
            try:
                dt = datetime.fromisoformat(date_value.replace('Z', '+00:00'))
                return dt.strftime('%Y-%m-%d')
            except ValueError:
                return date_value
        elif isinstance(date_value, datetime):
            return date_value.strftime('%Y-%m-%d')
        return str(date_value)

    def _format_description(self, item) -> str:
        """Format item description for Asana.

        Args:
            item: Roadmap item

        Returns:
            Formatted description string
        """
        parts = []

        if hasattr(item, 'description') and item.description:
            parts.append(item.description)

        if hasattr(item, 'goal') and item.goal:
            parts.append(f"\n\nGoal:\n{item.goal}")

        if hasattr(item, 'key_deliverables') and item.key_deliverables:
            parts.append("\n\nKey Deliverables:")
            for d in item.key_deliverables:
                parts.append(f"• {d}")

        if hasattr(item, 'technical_requirements') and item.technical_requirements:
            parts.append("\n\nTechnical Requirements:")
            for r in item.technical_requirements:
                parts.append(f"• {r}")

        if hasattr(item, 'dependencies') and item.dependencies:
            parts.append("\n\nDependencies:")
            for dep in item.dependencies:
                parts.append(f"• {dep}")

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
            parts.append("\n\nAcceptance Criteria:")
            for i, ac in enumerate(story.acceptance_criteria, 1):
                parts.append(f"☐ {ac}")

        if hasattr(story, 'user_value') and story.user_value:
            parts.append(f"\n\nUser Value:\n{story.user_value}")

        if hasattr(story, 'scope') and story.scope:
            if hasattr(story.scope, 'in_scope') and story.scope.in_scope:
                parts.append("\n\nIn Scope:")
                for item in story.scope.in_scope:
                    parts.append(f"✓ {item}")
            if hasattr(story.scope, 'out_of_scope') and story.scope.out_of_scope:
                parts.append("\n\nOut of Scope:")
                for item in story.scope.out_of_scope:
                    parts.append(f"✗ {item}")

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
            parts.append("\n\n📋 Implementation Guide:")
            parts.append(task.claude_code_prompt)

        if hasattr(task, 'work_type') and task.work_type:
            parts.append(f"\n\nWork Type: {task.work_type}")

        if hasattr(task, 'files_to_modify') and task.files_to_modify:
            parts.append("\n\nFiles to Modify:")
            for f in task.files_to_modify:
                parts.append(f"• {f}")

        if hasattr(task, 'duration_hours') and task.duration_hours:
            parts.append(f"\n\nEstimated Duration: {task.duration_hours} hours")

        return "\n".join(parts)

    def _prompt_for_workspace(self) -> Optional[str]:
        """Prompt user to select a workspace.

        Returns:
            Selected workspace GID or None
        """
        workspaces = self.get_available_workspaces()

        if not workspaces:
            logger.error("No workspaces available")
            return None

        if len(workspaces) == 1:
            return workspaces[0]['gid']

        print("\nAvailable Asana Workspaces:")
        for i, ws in enumerate(workspaces, 1):
            print(f"  {i}. {ws['name']}")

        while True:
            try:
                choice = input("\nEnter workspace number (or 'q' to quit): ").strip()

                if choice.lower() == 'q':
                    return None

                idx = int(choice) - 1
                if 0 <= idx < len(workspaces):
                    return workspaces[idx]['gid']

                print("Invalid selection. Please try again.")
            except (ValueError, EOFError, KeyboardInterrupt):
                return None

    def _prompt_for_project(self, workspace_gid: str) -> Optional[str]:
        """Prompt user to select or create a project.

        Args:
            workspace_gid: Workspace GID

        Returns:
            Selected/created project GID or None
        """
        projects = self.get_available_projects(workspace_gid)

        print("\nAvailable Asana Projects:")
        print("  0. Create new project")
        for i, proj in enumerate(projects, 1):
            print(f"  {i}. {proj['name']}")

        while True:
            try:
                choice = input("\nEnter project number (or 'q' to quit): ").strip()

                if choice.lower() == 'q':
                    return None

                idx = int(choice)
                if idx == 0:
                    name = input("Enter new project name: ").strip()
                    if name:
                        return self.create_project(name, workspace_gid)
                    print("Project name cannot be empty.")
                elif 1 <= idx <= len(projects):
                    return projects[idx - 1]['gid']
                else:
                    print("Invalid selection. Please try again.")
            except (ValueError, EOFError, KeyboardInterrupt):
                return None

    def get_field_mapping(self) -> Dict[str, str]:
        """Return field mapping for Asana.

        Returns:
            Dictionary mapping Arcane fields to Asana fields
        """
        return {
            'name': 'name',
            'description': 'notes',
            'priority': 'custom_fields.Priority',
            'duration_hours': 'custom_fields.Duration',
            'tags': 'tags',
            'acceptance_criteria': 'notes (Acceptance Criteria section)',
            'claude_code_prompt': 'notes (Implementation Guide section)',
            'goal': 'notes (Goal section)',
            'key_deliverables': 'notes (Key Deliverables section)',
            'target_date': 'due_on',
            'dependencies': 'dependencies',
        }

    def update_task(self, task_gid: str, fields: Dict[str, Any]) -> bool:
        """Update an existing Asana task.

        Args:
            task_gid: Asana task GID
            fields: Fields to update

        Returns:
            True if update succeeded
        """
        try:
            tasks_api = self._get_tasks_api()
            self._rate_limiter.wait()
            tasks_api.update_task(task_gid, {'data': fields}, {})
            logger.info(f"Updated task {task_gid}")
            return True
        except Exception as e:
            logger.error(f"Failed to update task {task_gid}: {e}")
            return False

    def complete_task(self, task_gid: str) -> bool:
        """Mark a task as completed.

        Args:
            task_gid: Asana task GID

        Returns:
            True if update succeeded
        """
        return self.update_task(task_gid, {'completed': True})

    def add_comment(self, task_gid: str, comment: str) -> bool:
        """Add a comment to an Asana task.

        Args:
            task_gid: Asana task GID
            comment: Comment text

        Returns:
            True if comment was added
        """
        try:
            import asana
            stories_api = asana.StoriesApi(self._get_client())
            self._rate_limiter.wait()
            stories_api.create_story_for_task(
                task_gid,
                {'data': {'text': comment}},
                {}
            )
            logger.info(f"Added comment to {task_gid}")
            return True
        except Exception as e:
            logger.error(f"Failed to add comment to {task_gid}: {e}")
            return False

    def get_task(self, task_gid: str) -> Optional[Dict[str, Any]]:
        """Get task details.

        Args:
            task_gid: Asana task GID

        Returns:
            Task data dictionary or None
        """
        try:
            tasks_api = self._get_tasks_api()
            self._rate_limiter.wait()
            return tasks_api.get_task(task_gid, {})
        except Exception as e:
            logger.error(f"Failed to get task {task_gid}: {e}")
            return None
