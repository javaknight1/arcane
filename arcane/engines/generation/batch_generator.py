"""Batch task generation for efficiency."""

import re
from typing import Dict, List, Optional, Any, TYPE_CHECKING
from arcane.templates import get_template
from arcane.items.task import Task
from arcane.items.base import ItemStatus
from arcane.utils.logging_config import get_logger

if TYPE_CHECKING:
    from arcane.items.epic import Epic
    from arcane.items.story import Story

logger = get_logger(__name__)


class BatchTaskGenerator:
    """Generates all tasks for an epic's stories in a single API call."""

    # Minimum stories to trigger batch mode
    BATCH_THRESHOLD = 3

    # Field markers for parsing tasks
    TASK_FIELD_MARKERS = [
        'TASK_TITLE',
        'TASK_GOAL',
        'TASK_SATISFIES_AC',
        'TASK_CLAUDE_CODE_PROMPT',
        'TASK_TECHNICAL_REQUIREMENTS',
        'TASK_PREREQUISITES',
        'TASK_WORK_TYPE',
        'TASK_COMPLEXITY',
        'TASK_DURATION_HOURS',
        'TASK_PRIORITY',
        'TASK_TAGS'
    ]

    def __init__(self, llm_client):
        """Initialize the batch generator.

        Args:
            llm_client: LLM client to use for generation
        """
        self.llm_client = llm_client

    def should_use_batch(self, epic: 'Epic') -> bool:
        """Determine if batch generation is appropriate for this epic.

        Uses batch mode when there are 3+ stories to generate tasks for,
        as this reduces API calls and improves consistency.

        Args:
            epic: Epic to evaluate

        Returns:
            True if batch mode should be used
        """
        stories = epic.get_children_by_type('Story')
        ready_stories = [s for s in stories if self._story_ready_for_tasks(s)]
        return len(ready_stories) >= self.BATCH_THRESHOLD

    def _story_ready_for_tasks(self, story: 'Story') -> bool:
        """Check if a story has completed Pass 1 and is ready for task generation.

        Args:
            story: Story to check

        Returns:
            True if story has description and acceptance criteria
        """
        return bool(
            story.description and
            story.acceptance_criteria and
            len(story.acceptance_criteria) > 0
        )

    def generate_epic_tasks_batch(
        self,
        epic: 'Epic',
        cascading_context: str = "",
        roadmap_overview: str = ""
    ) -> Dict[str, List[Task]]:
        """Generate all tasks for all stories in an epic in a single API call.

        Args:
            epic: Epic containing stories to generate tasks for
            cascading_context: Context from previously generated items
            roadmap_overview: Overview of roadmap generation status

        Returns:
            Dictionary mapping story IDs to lists of generated tasks
        """
        stories = [s for s in epic.get_children_by_type('Story')
                   if self._story_ready_for_tasks(s)]

        if not stories:
            logger.warning(f"No stories ready for task generation in Epic {epic.id}")
            return {}

        # Build the prompt
        prompt = self._build_batch_prompt(
            epic, stories, cascading_context, roadmap_overview
        )

        logger.info(f"Generating batch tasks for {len(stories)} stories in Epic {epic.id}")

        # Generate all tasks in one call
        response = self.llm_client.generate(prompt)

        # Parse and distribute to stories
        return self._parse_batch_response(response, epic, stories)

    def _build_batch_prompt(
        self,
        epic: 'Epic',
        stories: List['Story'],
        cascading_context: str,
        roadmap_overview: str
    ) -> str:
        """Build the batch generation prompt.

        Args:
            epic: Parent epic
            stories: Stories to generate tasks for
            cascading_context: Context from previously generated items
            roadmap_overview: Overview of roadmap generation status

        Returns:
            Formatted prompt string
        """
        template = get_template('epic_tasks_batch_generation')

        # Build stories details
        stories_details = self._build_stories_context(stories)

        # Get epic title without prefix
        epic_title = epic.name
        if ': ' in epic_title:
            epic_title = epic_title.split(': ', 1)[-1]

        # Format template
        prompt = template.format(
            epic_id=epic.id,
            epic_title=epic_title,
            epic_description=epic.description or "See epic content for details",
            cascading_context=cascading_context or "No prior context available",
            roadmap_overview=roadmap_overview or "See roadmap structure",
            stories_with_details=stories_details
        )

        return prompt

    def _build_stories_context(self, stories: List['Story']) -> str:
        """Build detailed context for all stories in the epic.

        Args:
            stories: List of stories to include

        Returns:
            Formatted string with all story details
        """
        sections = []

        for story in stories:
            story_title = story.name
            if ': ' in story_title:
                story_title = story_title.split(': ', 1)[-1]

            # Format acceptance criteria
            ac_text = "\n".join([
                f"  - AC{i+1}: {ac}"
                for i, ac in enumerate(story.acceptance_criteria)
            ]) if story.acceptance_criteria else "  No acceptance criteria defined"

            # Get expected tasks from outline
            expected_tasks = "\n".join([
                f"  - Task {child.id}: {child.name.split(': ', 1)[-1] if ': ' in child.name else child.name}"
                for child in story.get_children_by_type('Task')
            ]) if story.get_children_by_type('Task') else "  Generate appropriate tasks"

            # Build scope text
            scope_text = ""
            if story.scope_in or story.scope_out:
                if story.scope_in:
                    scope_text += "IN SCOPE:\n" + "\n".join([f"  - {s}" for s in story.scope_in])
                if story.scope_out:
                    scope_text += "\nOUT OF SCOPE:\n" + "\n".join([f"  - {s}" for s in story.scope_out])
            else:
                scope_text = "  See story description"

            section = f"""
---
STORY {story.id}: {story_title}
---
Description: {story.description or 'Not specified'}

User Value: {story.user_value or 'Not specified'}

Acceptance Criteria:
{ac_text}

Technical Considerations: {story.technical_considerations or 'See parent epic'}

Scope Boundaries:
{scope_text}

Estimated Duration: {story.duration or 'Not specified'} hours

Expected Tasks (from outline):
{expected_tasks}
"""
            sections.append(section)

        return "\n".join(sections)

    def _parse_batch_response(
        self,
        response: str,
        epic: 'Epic',
        stories: List['Story']
    ) -> Dict[str, List[Task]]:
        """Parse the batch response and distribute tasks to stories.

        Args:
            response: LLM response containing all tasks
            epic: Parent epic
            stories: Stories to distribute tasks to

        Returns:
            Dictionary mapping story IDs to lists of tasks
        """
        result: Dict[str, List[Task]] = {}

        # Create story lookup
        story_lookup = {s.id: s for s in stories}

        # Parse story sections
        story_pattern = r'###STORY_TASKS_START###\s*(\d+\.\d+\.\d+)(.*?)###STORY_TASKS_END###'
        story_matches = re.findall(story_pattern, response, re.DOTALL)

        for story_id, story_content in story_matches:
            story_id = story_id.strip()

            if story_id not in story_lookup:
                logger.warning(f"Found tasks for unknown story: {story_id}")
                continue

            story = story_lookup[story_id]
            tasks = self._parse_story_tasks(story_content, story)

            result[story_id] = tasks

            # Also apply tasks to the story object
            for task in tasks:
                if not story._find_task_by_id(task.id):
                    story.add_child(task)

            # Mark story pass2 complete
            story.pass2_complete = True

            logger.info(f"Story {story_id}: generated {len(tasks)} tasks from batch")

        # Log any stories that didn't get tasks
        for story in stories:
            if story.id not in result:
                logger.warning(f"Story {story.id} did not receive tasks from batch generation")

        return result

    def _parse_story_tasks(
        self,
        content: str,
        story: 'Story'
    ) -> List[Task]:
        """Parse tasks for a single story from batch content.

        Args:
            content: Content section for this story
            story: Parent story object

        Returns:
            List of parsed Task objects
        """
        tasks = []

        # Parse task blocks
        task_pattern = r'###TASK_START###\s*(\d+\.\d+\.\d+\.\d+)(.*?)###TASK_END###'
        task_matches = re.findall(task_pattern, content, re.DOTALL)

        for task_id, task_content in task_matches:
            task_id = task_id.strip()

            # Validate task ID belongs to this story
            expected_prefix = f"{story.id}."
            if not task_id.startswith(expected_prefix):
                logger.warning(f"Task {task_id} doesn't match story {story.id}")
                continue

            task = self._create_task_from_content(task_id, task_content, story)
            if task:
                tasks.append(task)

        return tasks

    def _create_task_from_content(
        self,
        task_id: str,
        content: str,
        story: 'Story'
    ) -> Optional[Task]:
        """Create a Task object from parsed content.

        Args:
            task_id: Task ID string
            content: Raw content for this task
            story: Parent story

        Returns:
            Task object or None if creation failed
        """
        fields = self._extract_fields(content)

        title = fields.get('TASK_TITLE', 'Untitled Task').strip()

        try:
            task = Task(
                name=title,
                number=task_id,
                parent=story
            )

            # Populate fields
            task.description = fields.get('TASK_GOAL', '').strip()
            task.claude_code_prompt = fields.get('TASK_CLAUDE_CODE_PROMPT', '').strip()
            task.technical_requirements = fields.get('TASK_TECHNICAL_REQUIREMENTS', '').strip()
            task.prerequisites = fields.get('TASK_PREREQUISITES', '').strip()
            task.satisfies_criteria = fields.get('TASK_SATISFIES_AC', '').strip()

            task.work_type = self._normalize_select_field(
                fields.get('TASK_WORK_TYPE', 'implementation'),
                ['implementation', 'design', 'research', 'testing',
                 'documentation', 'configuration', 'deployment'],
                'implementation'
            )
            task.complexity = self._normalize_select_field(
                fields.get('TASK_COMPLEXITY', 'moderate'),
                ['simple', 'moderate', 'complex'],
                'moderate'
            )
            task.priority = self._normalize_select_field(
                fields.get('TASK_PRIORITY', 'Medium'),
                ['Critical', 'High', 'Medium', 'Low'],
                'Medium'
            )
            task.duration = self._parse_duration(fields.get('TASK_DURATION_HOURS', '4'))
            task.tags = self._parse_comma_list(fields.get('TASK_TAGS', ''))

            task.update_generation_status(ItemStatus.GENERATED)

            return task

        except ValueError as e:
            logger.warning(f"Could not create task {task_id}: {e}")
            return None

    def _extract_fields(self, content: str) -> Dict[str, str]:
        """Extract all fields from content using markers.

        Args:
            content: Raw content string

        Returns:
            Dictionary of field name to value
        """
        fields = {}

        for i, marker in enumerate(self.TASK_FIELD_MARKERS):
            start_pattern = f":::{marker}:::"

            start_match = re.search(re.escape(start_pattern), content)
            if not start_match:
                continue

            start_pos = start_match.end()

            # Find end position (next marker or end)
            end_pos = len(content)
            for next_marker in self.TASK_FIELD_MARKERS[i+1:]:
                next_pattern = f":::{next_marker}:::"
                next_match = re.search(re.escape(next_pattern), content[start_pos:])
                if next_match:
                    end_pos = start_pos + next_match.start()
                    break

            fields[marker] = content[start_pos:end_pos].strip()

        return fields

    def _normalize_select_field(
        self,
        value: str,
        options: List[str],
        default: str
    ) -> str:
        """Normalize a select field to valid option.

        Args:
            value: Raw value from parsing
            options: List of valid options
            default: Default value if no match

        Returns:
            Normalized value
        """
        value_lower = value.lower().strip()
        for option in options:
            if option.lower() in value_lower:
                return option
        return default

    def _parse_duration(self, value: str) -> int:
        """Parse duration value to integer hours.

        Args:
            value: Raw duration string

        Returns:
            Duration in hours
        """
        try:
            match = re.search(r'\d+', value)
            if match:
                return int(match.group())
        except (AttributeError, ValueError):
            pass
        return 4  # Default

    def _parse_comma_list(self, value: str) -> List[str]:
        """Parse comma-separated list.

        Args:
            value: Raw comma-separated string

        Returns:
            List of trimmed items
        """
        if not value:
            return []
        items = [t.strip() for t in value.split(',')]
        return [t for t in items if t]

    def get_batch_stats(
        self,
        epic: 'Epic',
        result: Dict[str, List[Task]]
    ) -> Dict[str, Any]:
        """Get statistics about the batch generation.

        Args:
            epic: Epic that was processed
            result: Result from generate_epic_tasks_batch

        Returns:
            Dictionary of statistics
        """
        total_tasks = sum(len(tasks) for tasks in result.values())
        stories_processed = len(result)

        return {
            'epic_id': epic.id,
            'stories_processed': stories_processed,
            'total_tasks_generated': total_tasks,
            'avg_tasks_per_story': total_tasks / stories_processed if stories_processed > 0 else 0,
            'api_calls_saved': max(0, stories_processed - 1)  # Would have been 1 call per story
        }
