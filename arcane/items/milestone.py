"""Milestone class - Major phase in the project roadmap."""

import re
from typing import Optional, List, Dict
from .base import Item, ItemStatus
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class Milestone(Item):
    """Milestone represents a major phase in the project roadmap."""

    # Field markers for parsing structured LLM output
    FIELD_MARKERS = [
        'MILESTONE_DESCRIPTION',
        'MILESTONE_GOAL',
        'KEY_DELIVERABLES',
        'BENEFITS',
        'PREREQUISITES',
        'SUCCESS_CRITERIA',
        'RISKS_IF_DELAYED',
        'TECHNICAL_REQUIREMENTS',
        'WORK_TYPE',
        'COMPLEXITY',
        'PRIORITY',
        'DURATION_HOURS',
        'TAGS'
    ]

    def __init__(
        self,
        name: str,
        number: str,  # e.g., "1", "2", etc.
        parent: Optional[Item] = None,
        duration: Optional[int] = None,
        priority: str = 'Critical',
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
            name=f"Milestone {number}: {name}" if not name.startswith("Milestone") else name,
            item_type='Milestone',
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
            raise ValueError(f"Invalid Milestone ID: {self.id}")

        # Milestone-specific fields
        self.goal: str = ''
        self.key_deliverables: List[str] = []
        self.success_criteria: List[str] = []
        self.risks_if_delayed: str = ''

    def add_epic(self, epic: 'Epic') -> None:
        """Add an epic to this milestone."""
        self.add_child(epic)

    def validate_id(self) -> bool:
        """Milestone IDs must be single digits (1, 2, 3, etc.)."""
        return bool(re.match(r'^[1-9]\d*$', self.id))

    def get_id_pattern(self) -> str:
        """Return the regex pattern for valid Milestone IDs."""
        return r'^[1-9]\d*$'

    def generate_prompt(self, project_context: str, parent_context: Optional[str] = None, roadmap_context: Optional[str] = None) -> str:
        """Generate prompt for milestone header generation."""
        from arcane.prompts.roadmap_prompt_builder import RoadmapPromptBuilder
        builder = RoadmapPromptBuilder()

        # Build expected structure from children
        expected_epics = "\n".join([f"- Epic {child.id}: {child.name.split(': ', 1)[-1] if ': ' in child.name else child.name}"
                                   for child in self.get_children_by_type('Epic')])

        return builder.build_custom_prompt(
            'milestone_header_generation',
            milestone_number=self.id,
            milestone_title=self.name.split(': ', 1)[-1] if ': ' in self.name else self.name,
            project_context=project_context,
            expected_epics=expected_epics,
            roadmap_context=roadmap_context or ""
        )

    def parse_content(self, llm_response: str) -> None:
        """Parse milestone header content from LLM response."""
        self.content = llm_response

        # Check if this is the new structured format
        if ':::MILESTONE_DESCRIPTION:::' in llm_response:
            self._parse_structured_format(llm_response)
        else:
            # Fall back to legacy format
            self._parse_legacy_format(llm_response)

        self.update_generation_status(ItemStatus.GENERATED)

    def _parse_structured_format(self, llm_response: str) -> None:
        """Parse the new structured format with ::: markers."""
        fields = self._extract_all_fields(llm_response)

        # Map to milestone attributes
        self.description = fields.get('MILESTONE_DESCRIPTION', '').strip()
        self.goal = fields.get('MILESTONE_GOAL', '').strip()
        self.benefits = fields.get('BENEFITS', '').strip()
        self.technical_requirements = fields.get('TECHNICAL_REQUIREMENTS', '').strip()
        self.prerequisites = fields.get('PREREQUISITES', '').strip()
        self.risks_if_delayed = fields.get('RISKS_IF_DELAYED', '').strip()

        # Parse list fields
        self.key_deliverables = self._parse_list_field(fields.get('KEY_DELIVERABLES', ''))
        self.success_criteria = self._parse_list_field(fields.get('SUCCESS_CRITERIA', ''))

        # Normalize select fields
        self.work_type = self._normalize_select_field(
            fields.get('WORK_TYPE', 'implementation'),
            ['implementation', 'design', 'research', 'testing', 'documentation', 'configuration', 'deployment'],
            'implementation'
        )
        self.complexity = self._normalize_select_field(
            fields.get('COMPLEXITY', 'complex'),
            ['simple', 'moderate', 'complex'],
            'complex'
        )
        self.priority = self._normalize_select_field(
            fields.get('PRIORITY', 'Critical'),
            ['Critical', 'High', 'Medium', 'Low'],
            'Critical'
        )

        # Parse duration
        self.duration = self._parse_duration(fields.get('DURATION_HOURS', '0'))

        # Parse tags
        self.tags = self._parse_comma_list(fields.get('TAGS', ''))

        # Validate
        self._validate_parsed_content()

    def _extract_all_fields(self, response: str) -> Dict[str, str]:
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

    def _parse_list_field(self, raw: str) -> List[str]:
        """Parse a field with list items into a list."""
        items = []
        lines = raw.split('\n')

        for line in lines:
            line = line.strip()
            # Remove leading dash or bullet
            line = re.sub(r'^[-•*]\s*', '', line)
            # Remove "Deliverable N:" or "Criterion N:" prefixes
            line = re.sub(r'^(Deliverable|Criterion)\s*\d+:\s*', '', line, flags=re.IGNORECASE)

            if line and len(line) > 5:
                items.append(line)

        return items

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
            return int(match.group()) if match else 160
        except (AttributeError, ValueError):
            return 160  # Default for milestones

    def _validate_parsed_content(self) -> None:
        """Validate that critical fields were populated."""
        issues = []

        if not self.description:
            issues.append("description")
        if not self.goal:
            issues.append("goal")
        if not self.benefits:
            issues.append("benefits")

        if issues:
            logger.warning(f"Milestone {self.id} has unpopulated fields: {', '.join(issues)}")

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

        # Extract goal if present
        goal_match = re.search(r'\*\*Goal:\*\*\s*(.+?)(?:\n|$)', llm_response)
        if goal_match:
            self.goal = goal_match.group(1).strip()

        # Extract description from "What it is and why we need it" section
        desc_match = re.search(r'### \*\*What it is and why we need it:\*\*\n(.+?)(?:\n###|\n\*\*|$)',
                              llm_response, re.DOTALL)
        if desc_match:
            self.description = desc_match.group(1).strip()

        # Extract benefits
        benefits_match = re.search(r'### \*\*Benefits:\*\*\n((?:- .+?\n)+)', llm_response)
        if benefits_match:
            self.benefits = benefits_match.group(1).strip()

        # Extract "What happens if we don't have it" as risks
        risks_match = re.search(r'### \*\*What happens if we don\'t have it:\*\*\n((?:- .+?\n)+)', llm_response)
        if risks_match:
            self.risks_if_delayed = risks_match.group(1).strip()

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
            self.tags = [tag.strip().lower() for tag in tags_str.split(',') if tag.strip()]
