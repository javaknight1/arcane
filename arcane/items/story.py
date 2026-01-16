"""Story class - User-facing functionality or major technical work."""

import re
from typing import Optional, List, Dict, Any
from .base import Item, ItemStatus
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class Story(Item):
    """Story represents user-facing functionality or major technical work."""

    # Field markers for parsing structured LLM output
    STORY_FIELD_MARKERS = [
        'STORY_DESCRIPTION',
        'USER_VALUE',
        'ACCEPTANCE_CRITERIA',
        'TECHNICAL_REQUIREMENTS',
        'PREREQUISITES',
        'BENEFITS',
        'WORK_TYPE',
        'COMPLEXITY',
        'PRIORITY',
        'DURATION_HOURS',
        'TAGS'
    ]

    TASK_FIELD_MARKERS = [
        'TASK_TITLE',
        'TASK_GOAL',
        'TASK_BENEFITS',
        'TASK_TECHNICAL_REQUIREMENTS',
        'TASK_PREREQUISITES',
        'TASK_CLAUDE_CODE_PROMPT',
        'TASK_WORK_TYPE',
        'TASK_COMPLEXITY',
        'TASK_DURATION_HOURS',
        'TASK_PRIORITY',
        'TASK_TAGS'
    ]

    def __init__(
        self,
        name: str,
        number: str,  # e.g., "1.0.1", "1.0.2", etc.
        parent: Optional[Item] = None,
        duration: Optional[int] = None,
        priority: str = 'High',
        status: str = 'Not Started',
        description: Optional[str] = None,
        benefits: Optional[str] = None,
        prerequisites: Optional[str] = None,
        technical_requirements: Optional[str] = None,
        claude_code_prompt: Optional[str] = None,
        tags: Optional[List[str]] = None,
        work_type: Optional[str] = None,
        complexity: Optional[str] = None
    ):
        self.number = number
        super().__init__(
            name=f"Story {number}: {name}" if not name.startswith("Story") else name,
            item_type='Story',
            parent=parent,
            duration=duration,
            priority=priority,
            status=status,
            description=description,
            benefits=benefits,
            prerequisites=prerequisites,
            technical_requirements=technical_requirements,
            claude_code_prompt=claude_code_prompt,
            tags=tags,
            work_type=work_type,
            complexity=complexity
        )
        self.id = number
        if not self.validate_id():
            raise ValueError(f"Invalid Story ID: {self.id}")

        # Story-specific fields
        self.user_value: str = ''
        self.acceptance_criteria: List[str] = []
        self.technical_outline: List[str] = []
        self.success_criteria: List[str] = []

        # Two-pass generation fields
        self.technical_considerations: str = ''
        self.scope_in: List[str] = []
        self.scope_out: List[str] = []

        # Two-pass generation tracking
        self.pass1_complete: bool = False
        self.pass2_complete: bool = False

    def add_task(self, task: 'Task') -> None:
        """Add a task to this story."""
        self.add_child(task)

    def validate_id(self) -> bool:
        """Story IDs must be number.number.number (1.0.1, 2.3.4, etc.)."""
        return bool(re.match(r'^[1-9]\d*\.\d+\.\d+$', self.id))

    def get_id_pattern(self) -> str:
        """Return the regex pattern for valid Story IDs."""
        return r'^[1-9]\d*\.\d+\.\d+$'

    def generate_prompt(self, project_context: str, parent_context: Optional[str] = None, roadmap_context: Optional[str] = None) -> str:
        """Generate prompt for story generation (with all tasks)."""
        from arcane.prompts.roadmap_prompt_builder import RoadmapPromptBuilder
        builder = RoadmapPromptBuilder()

        # Build list of expected tasks
        task_list = "\n".join([f"- Task {child.id}: {child.name.split(': ', 1)[-1] if ': ' in child.name else child.name}"
                              for child in self.get_children_by_type('Task')])

        epic_context = parent_context or ""
        if self.parent:
            epic_context = f"Epic {self.parent.id}: {self.parent.name.split(': ', 1)[-1] if ': ' in self.parent.name else self.parent.name}"

        return builder.build_custom_prompt(
            'story_with_tasks_generation',
            story_number=self.id,
            story_title=self.name.split(': ', 1)[-1] if ': ' in self.name else self.name,
            project_context=project_context,
            epic_context=epic_context,
            expected_tasks=task_list,
            roadmap_context=roadmap_context or ""
        )

    # =====================================================
    # Two-Pass Generation Methods
    # =====================================================

    def generate_description_prompt(
        self,
        project_context: str,
        epic_context: str,
        cascading_context: str,
        roadmap_overview: str = "",
        semantic_description: str = ""
    ) -> str:
        """Generate Pass 1 prompt for description and acceptance criteria only.

        Args:
            project_context: Project-level context
            epic_context: Parent epic context
            cascading_context: Context from previously generated items
            roadmap_overview: Overview of roadmap generation status
            semantic_description: Semantic outline description

        Returns:
            Prompt string for Pass 1 generation
        """
        from arcane.prompts.roadmap_prompt_builder import RoadmapPromptBuilder
        # Use no compression for internal prompt generation
        builder = RoadmapPromptBuilder(compression_level='none')

        return builder.build_custom_prompt(
            'story_description_generation',
            story_number=self.id,
            story_title=self._get_title(),
            project_context=project_context,
            epic_context=epic_context,
            cascading_context=cascading_context,
            roadmap_overview=roadmap_overview,
            semantic_description=semantic_description or self.outline_description
        )

    def generate_tasks_prompt(
        self,
        cascading_context: str,
        sibling_context: str,
        roadmap_overview: str = ""
    ) -> str:
        """Generate Pass 2 prompt for tasks with full story context.

        Args:
            cascading_context: Context from previously generated items
            sibling_context: Context from sibling stories
            roadmap_overview: Overview of roadmap generation status

        Returns:
            Prompt string for Pass 2 generation
        """
        from arcane.prompts.roadmap_prompt_builder import RoadmapPromptBuilder
        # Use no compression for internal prompt generation
        builder = RoadmapPromptBuilder(compression_level='none')

        # Build expected tasks list from children
        expected_tasks = "\n".join([
            f"- Task {t.id}: {t.name.split(': ', 1)[-1] if ': ' in t.name else t.name}"
            for t in self.get_children_by_type('Task')
        ])

        # Format acceptance criteria with AC numbers
        ac_formatted = "\n".join([
            f"- [ ] AC{i+1}: {ac}"
            for i, ac in enumerate(self.acceptance_criteria)
        ])

        # Format scope boundaries
        scope_formatted = self._format_scope()

        return builder.build_custom_prompt(
            'story_tasks_generation',
            story_number=self.id,
            story_title=self._get_title(),
            story_description=self.description,
            user_value=self.user_value,
            acceptance_criteria=ac_formatted,
            technical_considerations=self.technical_considerations or self.technical_requirements,
            scope_boundaries=scope_formatted,
            sibling_stories=sibling_context,
            cascading_context=cascading_context,
            roadmap_overview=roadmap_overview,
            expected_tasks=expected_tasks,
            duration_hours=str(self.duration or 8)
        )

    def parse_description_content(self, response: str) -> None:
        """Parse Pass 1 response (description and acceptance criteria only).

        Args:
            response: LLM response from Pass 1
        """
        fields = self._extract_fields(response, self.STORY_FIELD_MARKERS + [
            'TECHNICAL_CONSIDERATIONS', 'SCOPE_BOUNDARIES'
        ])

        self.description = fields.get('STORY_DESCRIPTION', '').strip()
        self.user_value = fields.get('USER_VALUE', '').strip()
        self.technical_considerations = fields.get('TECHNICAL_CONSIDERATIONS', '').strip()
        self.benefits = fields.get('BENEFITS', '').strip()
        self.prerequisites = fields.get('PREREQUISITES', '').strip()

        # Normalize select fields
        self.work_type = self._normalize_select_field(
            fields.get('WORK_TYPE', 'implementation'),
            ['implementation', 'design', 'research', 'testing', 'documentation', 'configuration', 'deployment'],
            'implementation'
        )
        self.complexity = self._normalize_select_field(
            fields.get('COMPLEXITY', 'moderate'),
            ['simple', 'moderate', 'complex'],
            'moderate'
        )
        self.priority = self._normalize_select_field(
            fields.get('PRIORITY', 'Medium'),
            ['Critical', 'High', 'Medium', 'Low'],
            'Medium'
        )

        # Parse duration
        self.duration = self._parse_duration(fields.get('DURATION_HOURS', '8'))

        # Parse tags
        self.tags = self._parse_comma_list(fields.get('TAGS', ''))

        # Parse acceptance criteria
        ac_raw = fields.get('ACCEPTANCE_CRITERIA', '')
        self.acceptance_criteria = self._parse_acceptance_criteria(ac_raw)
        self.success_criteria = self.acceptance_criteria  # Backward compatibility

        # Parse scope boundaries
        scope_raw = fields.get('SCOPE_BOUNDARIES', '')
        self.scope_in, self.scope_out = self._parse_scope(scope_raw)

        self.pass1_complete = True
        logger.info(f"Story {self.id} Pass 1 complete: {len(self.acceptance_criteria)} acceptance criteria")

    def parse_tasks_content(self, response: str) -> None:
        """Parse Pass 2 response (tasks).

        Args:
            response: LLM response from Pass 2
        """
        # Parse task blocks using the new format
        task_pattern = r'###TASK_START###\s*(\S+)(.*?)###TASK_END###'
        matches = re.findall(task_pattern, response, re.DOTALL)

        tasks_updated = 0
        tasks_created = 0

        for task_id, task_content in matches:
            task_id = task_id.strip()

            # Find existing task or create new one
            existing_task = self._find_task_by_id(task_id)
            if existing_task:
                self._populate_task_from_content(existing_task, task_content)
                tasks_updated += 1
            else:
                # Create new task from content
                new_task = self._create_task_from_content(task_id, task_content)
                if new_task:
                    self.add_child(new_task)
                    tasks_created += 1

        # Parse AC coverage if present
        self._parse_ac_coverage(response)

        self.pass2_complete = True
        logger.info(f"Story {self.id} Pass 2 complete: {tasks_updated} tasks updated, {tasks_created} tasks created")

    def _get_title(self) -> str:
        """Get clean title without prefix."""
        if ': ' in self.name:
            return self.name.split(': ', 1)[-1]
        return self.name

    def _parse_acceptance_criteria(self, raw: str) -> List[str]:
        """Parse acceptance criteria list from raw text."""
        criteria = []
        for line in raw.split('\n'):
            line = line.strip()
            # Remove checkbox and AC prefix patterns
            line = re.sub(r'^-?\s*\[[ x]?\]\s*', '', line)
            line = re.sub(r'^AC\d+:\s*', '', line, flags=re.IGNORECASE)
            line = re.sub(r'^-?\s*', '', line)
            if line and len(line) > 5:
                criteria.append(line)
        return criteria

    def _parse_scope(self, raw: str) -> tuple:
        """Parse scope boundaries into in/out lists."""
        scope_in = []
        scope_out = []
        current_section = None

        for line in raw.split('\n'):
            line = line.strip()
            upper_line = line.upper()

            if 'IN SCOPE' in upper_line:
                current_section = 'in'
            elif 'OUT OF SCOPE' in upper_line or 'OUT SCOPE' in upper_line:
                current_section = 'out'
            elif line.startswith('-') or line.startswith('*'):
                item = re.sub(r'^[-*]\s*', '', line).strip()
                if item and len(item) > 3:
                    if current_section == 'in':
                        scope_in.append(item)
                    elif current_section == 'out':
                        scope_out.append(item)

        return scope_in, scope_out

    def _format_scope(self) -> str:
        """Format scope boundaries for prompt injection."""
        lines = []

        if self.scope_in:
            lines.append("IN SCOPE:")
            for item in self.scope_in:
                lines.append(f"- {item}")

        if self.scope_out:
            lines.append("\nOUT OF SCOPE:")
            for item in self.scope_out:
                lines.append(f"- {item}")

        return "\n".join(lines) if lines else "Scope not defined"

    def _find_task_by_id(self, task_id: str) -> Optional['Task']:
        """Find a child task by ID."""
        for child in self.get_children_by_type('Task'):
            if child.id == task_id:
                return child
        return None

    def _populate_task_from_content(self, task: 'Task', content: str) -> None:
        """Populate an existing task with parsed content from Pass 2."""
        fields = self._extract_fields(content, self.TASK_FIELD_MARKERS + ['TASK_SATISFIES_AC'])

        # Update task title if provided
        title = fields.get('TASK_TITLE', '').strip()
        if title:
            task.name = f"Task {task.id}: {title}"

        task.description = fields.get('TASK_GOAL', '').strip()
        task.claude_code_prompt = fields.get('TASK_CLAUDE_CODE_PROMPT', '').strip()
        task.technical_requirements = fields.get('TASK_TECHNICAL_REQUIREMENTS', '').strip()
        task.prerequisites = fields.get('TASK_PREREQUISITES', '').strip()
        task.benefits = fields.get('TASK_BENEFITS', '').strip()

        # Store which ACs this task satisfies
        task.satisfies_criteria = fields.get('TASK_SATISFIES_AC', '').strip()

        task.work_type = self._normalize_select_field(
            fields.get('TASK_WORK_TYPE', 'implementation'),
            ['implementation', 'design', 'research', 'testing', 'documentation', 'configuration', 'deployment'],
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

    def _create_task_from_content(self, task_id: str, content: str) -> Optional['Task']:
        """Create a new task from content if it doesn't exist."""
        from .task import Task

        fields = self._extract_fields(content, self.TASK_FIELD_MARKERS + ['TASK_SATISFIES_AC'])
        title = fields.get('TASK_TITLE', 'Untitled Task').strip()

        try:
            new_task = Task(
                name=title,
                number=task_id,
                parent=self
            )

            # Populate fields
            new_task.description = fields.get('TASK_GOAL', '').strip()
            new_task.claude_code_prompt = fields.get('TASK_CLAUDE_CODE_PROMPT', '').strip()
            new_task.technical_requirements = fields.get('TASK_TECHNICAL_REQUIREMENTS', '').strip()
            new_task.prerequisites = fields.get('TASK_PREREQUISITES', '').strip()
            new_task.satisfies_criteria = fields.get('TASK_SATISFIES_AC', '').strip()

            new_task.work_type = self._normalize_select_field(
                fields.get('TASK_WORK_TYPE', 'implementation'),
                ['implementation', 'design', 'research', 'testing', 'documentation', 'configuration', 'deployment'],
                'implementation'
            )
            new_task.complexity = self._normalize_select_field(
                fields.get('TASK_COMPLEXITY', 'moderate'),
                ['simple', 'moderate', 'complex'],
                'moderate'
            )
            new_task.duration = self._parse_duration(fields.get('TASK_DURATION_HOURS', '4'))

            new_task.update_generation_status(ItemStatus.GENERATED)

            return new_task
        except ValueError as e:
            logger.warning(f"Could not create task {task_id}: {e}")
            return None

    def _parse_ac_coverage(self, response: str) -> None:
        """Parse AC coverage summary from response."""
        # Look for the AC_COVERAGE section
        coverage_match = re.search(r':::AC_COVERAGE:::(.*?)(?=:::|\Z)', response, re.DOTALL)
        if coverage_match:
            coverage_text = coverage_match.group(1).strip()
            logger.debug(f"Story {self.id} AC coverage: {coverage_text[:100]}...")

        # Check for uncovered ACs
        uncovered_match = re.search(r':::UNCOVERED_AC:::(.*?)(?=:::|\Z)', response, re.DOTALL)
        if uncovered_match:
            uncovered = uncovered_match.group(1).strip()
            if uncovered and 'none' not in uncovered.lower():
                logger.warning(f"Story {self.id} has uncovered acceptance criteria: {uncovered}")

    def is_two_pass_complete(self) -> bool:
        """Check if two-pass generation is complete."""
        return self.pass1_complete and self.pass2_complete

    def parse_content(self, llm_response: str) -> None:
        """Parse structured story response and extract tasks."""
        self.content = llm_response

        # Check if this is the new structured format
        if ':::STORY_DESCRIPTION:::' in llm_response:
            self._parse_structured_format(llm_response)
        else:
            # Fall back to legacy format
            self._parse_legacy_format(llm_response)

        self.update_generation_status(ItemStatus.GENERATED)

    def _parse_structured_format(self, llm_response: str) -> None:
        """Parse the new structured format with ::: markers."""
        # Split response into story section and tasks section
        story_section, tasks_section = self._split_story_and_tasks(llm_response)

        # Parse story fields
        self._parse_story_fields(story_section)

        # Parse and update task objects
        self._parse_tasks(tasks_section)

        # Validate
        self._validate_parsed_content()

    def _split_story_and_tasks(self, response: str) -> tuple:
        """Split response into story and tasks sections."""
        # Find first task marker
        task_start = response.find('###TASK_START###')

        if task_start == -1:
            # Try legacy task marker
            task_start = response.find('###### Task')
            if task_start == -1:
                return response, ""

        return response[:task_start], response[task_start:]

    def _parse_story_fields(self, story_section: str) -> None:
        """Extract story-level fields from structured format."""
        fields = self._extract_fields(story_section, self.STORY_FIELD_MARKERS)

        self.description = fields.get('STORY_DESCRIPTION', '').strip()
        self.user_value = fields.get('USER_VALUE', '').strip()
        self.technical_requirements = fields.get('TECHNICAL_REQUIREMENTS', '').strip()
        self.prerequisites = fields.get('PREREQUISITES', '').strip()
        self.benefits = fields.get('BENEFITS', '').strip()

        # Normalize select fields
        self.work_type = self._normalize_select_field(
            fields.get('WORK_TYPE', 'implementation'),
            ['implementation', 'design', 'research', 'testing', 'documentation', 'configuration', 'deployment'],
            'implementation'
        )
        self.complexity = self._normalize_select_field(
            fields.get('COMPLEXITY', 'moderate'),
            ['simple', 'moderate', 'complex'],
            'moderate'
        )
        self.priority = self._normalize_select_field(
            fields.get('PRIORITY', 'Medium'),
            ['Critical', 'High', 'Medium', 'Low'],
            'Medium'
        )

        # Parse tags
        self.tags = self._parse_comma_list(fields.get('TAGS', ''))

        # Parse acceptance criteria as list
        ac_raw = fields.get('ACCEPTANCE_CRITERIA', '')
        self.acceptance_criteria = self._parse_criteria_list(ac_raw)
        # Also set success_criteria for backward compatibility
        self.success_criteria = self.acceptance_criteria

        # Parse duration
        self.duration = self._parse_duration(fields.get('DURATION_HOURS', '0'))

    def _parse_tasks(self, tasks_section: str) -> None:
        """Parse task blocks and update corresponding Task objects."""
        if not tasks_section:
            return

        # Try new format first: ###TASK_START### {task_id}
        task_pattern = r'###TASK_START###\s*(\d+\.\d+\.\d+\.\d+)(.*?)###TASK_END###'
        task_matches = re.findall(task_pattern, tasks_section, re.DOTALL)

        if task_matches:
            for task_id, task_content in task_matches:
                self._update_task_from_structured_content(task_id, task_content)
        else:
            # Fall back to legacy format: ###### Task {task_id}: {title}
            legacy_pattern = r'###### Task (\d+\.\d+\.\d+\.\d+): (.+?)\n(.*?)(?=###### Task |$)'
            legacy_matches = re.findall(legacy_pattern, tasks_section, re.DOTALL)

            for task_id, task_title, task_content in legacy_matches:
                # Find corresponding task child and update its content
                for task in self.get_children_by_type('Task'):
                    if task.id == task_id:
                        full_task_content = f"###### Task {task_id}: {task_title}\n{task_content}"
                        task.parse_content(full_task_content)
                        break

    def _update_task_from_structured_content(self, task_id: str, task_content: str) -> None:
        """Update a task object with structured content."""
        # Find the corresponding task child
        task = None
        for child in self.get_children_by_type('Task'):
            if child.id == task_id:
                task = child
                break

        if not task:
            logger.warning(f"Task {task_id} not found in story {self.id} children")
            return

        # Extract task fields
        fields = self._extract_fields(task_content, self.TASK_FIELD_MARKERS)

        # Update task attributes
        task.description = fields.get('TASK_GOAL', '').strip()
        task.benefits = fields.get('TASK_BENEFITS', '').strip()
        task.technical_requirements = fields.get('TASK_TECHNICAL_REQUIREMENTS', '').strip()
        task.prerequisites = fields.get('TASK_PREREQUISITES', '').strip()
        task.claude_code_prompt = fields.get('TASK_CLAUDE_CODE_PROMPT', '').strip()

        task.work_type = self._normalize_select_field(
            fields.get('TASK_WORK_TYPE', 'implementation'),
            ['implementation', 'design', 'research', 'testing', 'documentation', 'configuration', 'deployment'],
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
        task.duration = self._parse_duration(fields.get('TASK_DURATION_HOURS', '0'))
        task.tags = self._parse_comma_list(fields.get('TASK_TAGS', ''))

        # Mark as generated
        task.update_generation_status(ItemStatus.GENERATED)

    def _extract_fields(self, text: str, markers: List[str]) -> Dict[str, str]:
        """Extract fields using ::: markers."""
        fields = {}

        for marker in markers:
            start_pattern = f":::{marker}:::"

            # Find start position
            start_match = re.search(re.escape(start_pattern), text)
            if not start_match:
                continue

            start_pos = start_match.end()

            # Find end position - look for the CLOSEST next marker (any marker)
            end_pos = len(text)

            # Search for any ::: marker pattern after current position
            next_marker_match = re.search(r':::([A-Z_]+):::', text[start_pos:])
            if next_marker_match:
                end_pos = start_pos + next_marker_match.start()

            # Also check for task block marker
            task_block = re.search(r'###TASK', text[start_pos:])
            if task_block and start_pos + task_block.start() < end_pos:
                end_pos = start_pos + task_block.start()

            # Extract content
            content = text[start_pos:end_pos].strip()
            fields[marker] = content

        return fields

    def _parse_criteria_list(self, raw: str) -> List[str]:
        """Parse acceptance criteria into list."""
        criteria = []
        lines = raw.split('\n')

        for line in lines:
            line = line.strip()
            # Remove checkbox markers
            line = re.sub(r'^-?\s*\[[ x]?\]\s*', '', line)
            # Remove leading dash or bullet
            line = re.sub(r'^[-•*]\s*', '', line)
            # Remove "Criterion N:" prefix
            line = re.sub(r'^Criterion\s*\d+:\s*', '', line, flags=re.IGNORECASE)

            if line and len(line) > 5:  # Filter out empty/tiny lines
                criteria.append(line)

        return criteria

    def _normalize_select_field(self, value: str, valid_options: List[str], default: str) -> str:
        """Normalize a select field to valid option."""
        value_lower = value.lower().strip()

        for option in valid_options:
            if option.lower() in value_lower:
                return option

        return default

    def _parse_comma_list(self, value: str) -> List[str]:
        """Parse comma-separated list."""
        if not value:
            return []
        items = [item.strip() for item in value.split(',')]
        return [item for item in items if item]

    def _parse_duration(self, value: str) -> int:
        """Parse duration string to integer hours."""
        try:
            match = re.search(r'\d+', str(value))
            return int(match.group()) if match else 8
        except (AttributeError, ValueError):
            return 8  # Default

    def _validate_parsed_content(self) -> None:
        """Validate that critical fields were populated."""
        issues = []

        if not self.description:
            issues.append("description")
        if not self.acceptance_criteria:
            issues.append("acceptance_criteria")

        if issues:
            logger.warning(f"Story {self.id} has unpopulated fields: {', '.join(issues)}")

    def _parse_legacy_format(self, llm_response: str) -> None:
        """Parse legacy markdown format for backward compatibility."""
        # Parse story section (before the first task)
        story_section = llm_response.split('###### Task')[0] if '###### Task' in llm_response else llm_response

        # Extract duration if present
        duration_match = re.search(r'\*\*Duration:\*\*\s*(\d+)\s*hours?', story_section)
        if duration_match:
            self.duration = int(duration_match.group(1))

        # Extract priority if present
        priority_match = re.search(r'\*\*Priority:\*\*\s*(.+?)(?:\n|$)', story_section)
        if priority_match:
            self.priority = priority_match.group(1).strip()

        # Extract "What it is" as description
        what_match = re.search(r'\*\*What it is:\*\*\s*(.+?)(?:\n\*\*|$)', story_section, re.DOTALL)
        if what_match:
            self.description = what_match.group(1).strip()

        # Extract benefits
        benefits_match = re.search(r'\*\*Benefits:\*\*\n((?:- .+?\n)+)', story_section)
        if benefits_match:
            self.benefits = benefits_match.group(1).strip()

        # Extract prerequisites
        prereq_match = re.search(r'\*\*Prerequisites:\*\*\n((?:- .+?\n)+)', story_section)
        if prereq_match:
            self.prerequisites = prereq_match.group(1).strip()

        # Extract technical outline
        tech_outline_match = re.search(r'\*\*Technical Outline:\*\*\n((?:\d+\. .+?\n?)+)', story_section)
        if tech_outline_match:
            self.technical_outline = [line.strip() for line in tech_outline_match.group(1).strip().split('\n') if line.strip()]

        # Extract success criteria
        success_match = re.search(r'\*\*Success Criteria:\*\*\n((?:- .+?\n)+)', story_section)
        if success_match:
            self.success_criteria = [s.strip('- ').strip()
                                   for s in success_match.group(1).split('\n') if s.strip()]

        # Extract Work Type if present
        work_type_match = re.search(r'\*\*Work Type:\*\*\s*(.+?)(?:\n|$)', story_section)
        if work_type_match:
            self.work_type = work_type_match.group(1).strip().lower()

        # Extract Complexity if present
        complexity_match = re.search(r'\*\*Complexity:\*\*\s*(.+?)(?:\n|$)', story_section)
        if complexity_match:
            self.complexity = complexity_match.group(1).strip().lower()

        # Extract Tags if present
        tags_match = re.search(r'\*\*Tags:\*\*\s*(.+?)(?:\n|$)', story_section)
        if tags_match:
            tags_str = tags_match.group(1).strip()
            self.tags = [tag.strip().lower() for tag in tags_str.split(',') if tag.strip()]

        # Now parse each task section and update corresponding task objects
        task_pattern = r'###### Task (\d+\.\d+\.\d+\.\d+): (.+?)\n(.*?)(?=###### Task |$)'
        task_matches = re.findall(task_pattern, llm_response, re.DOTALL)

        for task_id, task_title, task_content in task_matches:
            # Find corresponding task child and update its content
            for task in self.get_children_by_type('Task'):
                if task.id == task_id:
                    # Reconstruct full task content for parsing
                    full_task_content = f"###### Task {task_id}: {task_title}\n{task_content}"
                    task.parse_content(full_task_content)
                    break

    def parse_structured_content(self, data: Dict[str, Any]) -> None:
        """Parse from structured tool output (JSON from Claude's tool use).

        This method parses structured data returned from Claude's tool use
        feature, which provides more reliable output than text parsing.

        Args:
            data: Dictionary containing structured story data from tool use
        """
        import json
        # Store raw data as content for reference
        self.content = json.dumps(data, indent=2)

        # Extract title if different from current name
        if 'title' in data:
            title = data['title']
            if not self.name.endswith(title):
                self.name = f"Story {self.id}: {title}"

        # Primary description fields
        self.description = data.get('description', '')
        self.user_value = data.get('user_value', '')

        # Acceptance criteria - always a list
        ac_list = data.get('acceptance_criteria', [])
        if isinstance(ac_list, list):
            self.acceptance_criteria = [str(ac) for ac in ac_list if ac]
        else:
            self.acceptance_criteria = [str(ac_list)]
        self.success_criteria = self.acceptance_criteria  # Backward compatibility

        # Scope boundaries
        scope_in_list = data.get('scope_in', [])
        if isinstance(scope_in_list, list):
            self.scope_in = [str(s) for s in scope_in_list if s]
        else:
            self.scope_in = [str(scope_in_list)] if scope_in_list else []

        scope_out_list = data.get('scope_out', [])
        if isinstance(scope_out_list, list):
            self.scope_out = [str(s) for s in scope_out_list if s]
        else:
            self.scope_out = [str(scope_out_list)] if scope_out_list else []

        # List fields - convert to formatted strings
        benefits_list = data.get('benefits', [])
        if isinstance(benefits_list, list):
            self.benefits = "\n".join([f"- {b}" for b in benefits_list])
        else:
            self.benefits = str(benefits_list)

        tech_requirements_list = data.get('technical_requirements', [])
        if isinstance(tech_requirements_list, list):
            self.technical_requirements = "\n".join([f"- {t}" for t in tech_requirements_list])
        else:
            self.technical_requirements = str(tech_requirements_list)

        prerequisites_list = data.get('prerequisites', [])
        if isinstance(prerequisites_list, list):
            self.prerequisites = "\n".join([f"- {p}" for p in prerequisites_list])
        else:
            self.prerequisites = str(prerequisites_list)

        # Simple fields with normalization
        self.work_type = data.get('work_type', 'feature')
        self.complexity = data.get('complexity', 'moderate')
        self.priority = data.get('priority', 'High')

        # Duration with fallback
        duration_value = data.get('duration_hours', 8)
        if isinstance(duration_value, (int, float)):
            self.duration = int(duration_value)
        else:
            try:
                self.duration = int(duration_value)
            except (ValueError, TypeError):
                self.duration = 8

        # Tags - ensure it's a list
        tags_value = data.get('tags', [])
        if isinstance(tags_value, list):
            self.tags = [str(t).lower().strip() for t in tags_value if t]
        elif isinstance(tags_value, str):
            self.tags = [t.strip().lower() for t in tags_value.split(',') if t.strip()]
        else:
            self.tags = []

        # Mark Pass 1 as complete
        self.pass1_complete = True

        # Update generation status
        self.update_generation_status(ItemStatus.GENERATED)

        logger.debug(f"Story {self.id}: Parsed structured content - "
                    f"{len(self.acceptance_criteria)} acceptance criteria, "
                    f"work_type={self.work_type}, duration={self.duration}h")

    @staticmethod
    def get_structured_schema() -> Dict[str, Any]:
        """Get the JSON schema for structured story generation.

        Returns:
            JSON schema dictionary for use with Claude's tool use
        """
        from arcane.clients.claude import STORY_SCHEMA
        return STORY_SCHEMA
