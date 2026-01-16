"""Task class - Specific implementation work."""

import re
from typing import Optional, List, Dict, Any
from .base import Item, ItemStatus
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class Task(Item):
    """Task represents specific implementation work."""

    # Field markers for parsing structured LLM output
    FIELD_MARKERS = [
        'GOAL_DESCRIPTION',
        'BENEFITS',
        'TECHNICAL_REQUIREMENTS',
        'PREREQUISITES',
        'CLAUDE_CODE_PROMPT',
        'WORK_TYPE',
        'COMPLEXITY',
        'DURATION_HOURS',
        'PRIORITY',
        'TAGS'
    ]

    def __init__(
        self,
        name: str,
        number: str,  # e.g., "1.0.1.1", "1.0.1.2", etc.
        parent: Optional[Item] = None,
        duration: Optional[int] = None,
        priority: str = 'Medium',
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
            name=f"Task {number}: {name}" if not name.startswith("Task") else name,
            item_type='Task',
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
            raise ValueError(f"Invalid Task ID: {self.id}")

        # Task-specific fields
        self.what_to_do = []
        self.success_criteria = []

    def validate_id(self) -> bool:
        """Task IDs must be number.number.number.number (1.0.1.1, 2.3.4.5, etc.)."""
        return bool(re.match(r'^[1-9]\d*\.\d+\.\d+\.\d+$', self.id))

    def get_id_pattern(self) -> str:
        """Return the regex pattern for valid Task IDs."""
        return r'^[1-9]\d*\.\d+\.\d+\.\d+$'

    def generate_prompt(self, project_context: str, parent_context: Optional[str] = None, roadmap_context: Optional[str] = None) -> str:
        """Generate prompt for task generation (usually handled by story generation)."""
        from arcane.prompts.roadmap_prompt_builder import RoadmapPromptBuilder
        builder = RoadmapPromptBuilder()

        story_context = parent_context or ""
        if self.parent:
            story_context = f"Story {self.parent.id}: {self.parent.name.split(': ', 1)[-1] if ': ' in self.parent.name else self.parent.name}"

        return builder.build_custom_prompt(
            'task_generation_individual',
            task_number=self.id,
            task_title=self.name.split(': ', 1)[-1] if ': ' in self.name else self.name,
            project_context=project_context,
            story_context=story_context,
            roadmap_context=roadmap_context or ""
        )

    def parse_content(self, llm_response: str) -> None:
        """Parse structured LLM response into task fields."""
        self.content = llm_response

        # Try new structured format first
        if ':::GOAL_DESCRIPTION:::' in llm_response:
            self._parse_structured_format(llm_response)
        else:
            # Fall back to legacy format for backward compatibility
            self._parse_legacy_format(llm_response)

        self.update_generation_status(ItemStatus.GENERATED)

    def _parse_structured_format(self, llm_response: str) -> None:
        """Parse the new structured format with ::: markers."""
        # Extract each field using markers
        fields = self._extract_all_fields(llm_response)

        # Map to task attributes
        self.description = fields.get('GOAL_DESCRIPTION', '').strip()
        self.benefits = fields.get('BENEFITS', '').strip()
        self.technical_requirements = fields.get('TECHNICAL_REQUIREMENTS', '').strip()
        self.prerequisites = fields.get('PREREQUISITES', '').strip()
        self.claude_code_prompt = fields.get('CLAUDE_CODE_PROMPT', '').strip()
        self.work_type = self._normalize_work_type(fields.get('WORK_TYPE', ''))
        self.complexity = self._normalize_complexity(fields.get('COMPLEXITY', ''))
        self.priority = self._normalize_priority(fields.get('PRIORITY', 'Medium'))
        self.tags = self._parse_tags(fields.get('TAGS', ''))

        # Parse duration
        duration_str = fields.get('DURATION_HOURS', '0')
        try:
            match = re.search(r'\d+', duration_str)
            if match:
                self.duration = int(match.group())
            else:
                self.duration = 4  # Default to 4 hours
        except (AttributeError, ValueError):
            self.duration = 4  # Default to 4 hours

        # Validate required fields were populated
        self._validate_parsed_fields()

    def _extract_all_fields(self, response: str) -> dict:
        """Extract all fields using markers."""
        fields = {}

        for i, marker in enumerate(self.FIELD_MARKERS):
            start_pattern = f":::{marker}:::"

            # Find start position
            start_match = re.search(re.escape(start_pattern), response)
            if not start_match:
                continue

            start_pos = start_match.end()

            # Find end position (next marker or end of string)
            end_pos = len(response)
            for next_marker in self.FIELD_MARKERS[i+1:]:
                next_pattern = f":::{next_marker}:::"
                next_match = re.search(re.escape(next_pattern), response[start_pos:])
                if next_match:
                    end_pos = start_pos + next_match.start()
                    break

            # Extract content
            content = response[start_pos:end_pos].strip()
            fields[marker] = content

        return fields

    def _normalize_work_type(self, value: str) -> str:
        """Normalize work type to valid option."""
        valid_types = ['implementation', 'design', 'research', 'testing',
                       'documentation', 'configuration', 'deployment']
        value_lower = value.lower().strip()

        for valid in valid_types:
            if valid in value_lower:
                return valid
        return 'implementation'  # Default

    def _normalize_complexity(self, value: str) -> str:
        """Normalize complexity to valid option."""
        value_lower = value.lower().strip()
        if 'simple' in value_lower:
            return 'simple'
        elif 'complex' in value_lower:
            return 'complex'
        return 'moderate'  # Default

    def _normalize_priority(self, value: str) -> str:
        """Normalize priority to valid option."""
        value_lower = value.lower().strip()
        if 'critical' in value_lower:
            return 'Critical'
        elif 'high' in value_lower:
            return 'High'
        elif 'low' in value_lower:
            return 'Low'
        return 'Medium'  # Default

    def _parse_tags(self, value: str) -> List[str]:
        """Parse comma-separated tags."""
        if not value:
            return []
        tags = [t.strip() for t in value.split(',')]
        return [t for t in tags if t]  # Remove empty strings

    def _validate_parsed_fields(self) -> None:
        """Log warnings for any fields that weren't populated."""
        required_fields = [
            ('description', 'Goal/Description'),
            ('benefits', 'Benefits'),
            ('claude_code_prompt', 'Claude Code Prompt'),
            ('work_type', 'Work Type'),
            ('complexity', 'Complexity'),
        ]

        for attr, display_name in required_fields:
            if not getattr(self, attr, None):
                logger.warning(f"Task {self.id}: {display_name} field is empty after parsing")

    def _parse_legacy_format(self, llm_response: str) -> None:
        """Parse legacy markdown format for backward compatibility."""
        # Extract duration if present
        duration_match = re.search(r'\*\*Duration:\*\*\s*(\d+)\s*hours?', llm_response)
        if duration_match:
            self.duration = int(duration_match.group(1))

        # Extract priority if present
        priority_match = re.search(r'\*\*Priority:\*\*\s*(.+?)(?:\n|$)', llm_response)
        if priority_match:
            self.priority = priority_match.group(1).strip()

        # Extract "What to do" as list
        what_to_do_match = re.search(r'\*\*What to [Dd]o:\*\*\n((?:(?:\d+\. |- ).+?\n?)+)', llm_response, re.DOTALL)
        if what_to_do_match:
            self.what_to_do = [line.strip() for line in what_to_do_match.group(1).strip().split('\n') if line.strip()]
            # Also set as description for compatibility
            self.description = '\n'.join(self.what_to_do)

        # Extract success criteria
        success_match = re.search(r'\*\*Success Criteria:\*\*\n((?:- .+?\n)+)', llm_response)
        if success_match:
            self.success_criteria = [s.strip('- ').strip()
                                   for s in success_match.group(1).split('\n') if s.strip()]

        # Extract Benefits if present
        benefits_match = re.search(r'\*\*Benefits:\*\*\n((?:- .+?\n)+)', llm_response)
        if benefits_match:
            self.benefits = benefits_match.group(1).strip()

        # Extract Prerequisites if present
        prereq_match = re.search(r'\*\*Prerequisites:\*\*\n(.+?)(?:\n\n|\*\*|$)', llm_response, re.DOTALL)
        if prereq_match:
            self.prerequisites = prereq_match.group(1).strip()

        # Extract Technical Requirements if present
        tech_req_match = re.search(r'\*\*Technical Requirements:\*\*\n(.+?)(?:\n\n|\*\*|$)', llm_response, re.DOTALL)
        if tech_req_match:
            self.technical_requirements = tech_req_match.group(1).strip()

        # Extract Work Type if present
        work_type_match = re.search(r'\*\*Work Type:\*\*\s*(.+?)(?:\n|$)', llm_response)
        if work_type_match:
            self.work_type = work_type_match.group(1).strip().lower()

        # Extract Complexity if present
        complexity_match = re.search(r'\*\*Complexity:\*\*\s*(.+?)(?:\n|$)', llm_response)
        if complexity_match:
            self.complexity = complexity_match.group(1).strip().lower()

        # Extract Tags if present
        tags_match = re.search(r'\*\*Tags:\*\*\s*(.+?)(?:\n|$)', llm_response)
        if tags_match:
            tags_str = tags_match.group(1).strip()
            # Split by comma and clean up each tag
            self.tags = [tag.strip().lower() for tag in tags_str.split(',') if tag.strip()]

        # Extract Claude Code prompt
        claude_prompt_match = re.search(r'\*\*Claude Code Prompt:\*\*\n```\n?(.+?)```',
                                       llm_response, re.DOTALL)
        if claude_prompt_match:
            self.claude_code_prompt = claude_prompt_match.group(1).strip()

    def parse_structured_content(self, data: Dict[str, Any]) -> None:
        """Parse from structured tool output (JSON from Claude's tool use).

        This method parses structured data returned from Claude's tool use
        feature, which provides more reliable output than text parsing.

        Args:
            data: Dictionary containing structured task data from tool use
        """
        # Store raw data as content for reference
        import json
        self.content = json.dumps(data, indent=2)

        # Extract title if different from current name
        if 'title' in data:
            title = data['title']
            if not self.name.endswith(title):
                self.name = f"Task {self.id}: {title}"

        # Primary fields
        self.description = data.get('goal_description', data.get('description', ''))

        # List fields - convert to formatted strings
        benefits_list = data.get('benefits', [])
        if isinstance(benefits_list, list):
            self.benefits = "\n".join([f"- {b}" for b in benefits_list])
        else:
            self.benefits = str(benefits_list)

        prerequisites_list = data.get('prerequisites', [])
        if isinstance(prerequisites_list, list):
            self.prerequisites = "\n".join([f"- {p}" for p in prerequisites_list])
        else:
            self.prerequisites = str(prerequisites_list)

        tech_requirements_list = data.get('technical_requirements', [])
        if isinstance(tech_requirements_list, list):
            self.technical_requirements = "\n".join([f"- {t}" for t in tech_requirements_list])
        else:
            self.technical_requirements = str(tech_requirements_list)

        # Simple fields
        self.claude_code_prompt = data.get('claude_code_prompt', '')
        self.work_type = data.get('work_type', 'implementation')
        self.complexity = data.get('complexity', 'moderate')
        self.priority = data.get('priority', 'Medium')

        # Duration with fallback
        duration_value = data.get('duration_hours', 4)
        if isinstance(duration_value, (int, float)):
            self.duration = int(duration_value)
        else:
            try:
                self.duration = int(duration_value)
            except (ValueError, TypeError):
                self.duration = 4

        # Tags - ensure it's a list
        tags_value = data.get('tags', [])
        if isinstance(tags_value, list):
            self.tags = [str(t).lower().strip() for t in tags_value if t]
        elif isinstance(tags_value, str):
            self.tags = [t.strip().lower() for t in tags_value.split(',') if t.strip()]
        else:
            self.tags = []

        # Update generation status
        self.update_generation_status(ItemStatus.GENERATED)

        logger.debug(f"Task {self.id}: Parsed structured content - "
                    f"work_type={self.work_type}, complexity={self.complexity}, "
                    f"duration={self.duration}h")

    @staticmethod
    def get_structured_schema() -> Dict[str, Any]:
        """Get the JSON schema for structured task generation.

        Returns:
            JSON schema dictionary for use with Claude's tool use
        """
        from arcane.clients.claude import TASK_SCHEMA
        return TASK_SCHEMA
