"""Epic class - Major feature area or technical component."""

import re
from typing import Optional, List, Dict
from .base import Item, ItemStatus
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class Epic(Item):
    """Epic represents a major feature area or technical component."""

    # Field markers for parsing structured LLM output
    FIELD_MARKERS = [
        'EPIC_DESCRIPTION',
        'EPIC_GOALS',
        'BENEFITS',
        'TECHNICAL_REQUIREMENTS',
        'PREREQUISITES',
        'SUCCESS_METRICS',
        'RISKS_AND_MITIGATIONS',
        'WORK_TYPE',
        'COMPLEXITY',
        'PRIORITY',
        'DURATION_HOURS',
        'TAGS'
    ]

    def __init__(
        self,
        name: str,
        number: str,  # e.g., "1.0", "1.1", etc.
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
            name=f"Epic {number}: {name}" if not name.startswith("Epic") else name,
            item_type='Epic',
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
            raise ValueError(f"Invalid Epic ID: {self.id}")

        # Epic-specific fields
        self.goals: List[str] = []
        self.success_metrics: List[str] = []
        self.risks_and_mitigations: str = ''

    def add_story(self, story: 'Story') -> None:
        """Add a story to this epic."""
        self.add_child(story)

    def validate_id(self) -> bool:
        """Epic IDs must be number.number (1.0, 1.1, 2.3, etc.)."""
        return bool(re.match(r'^[1-9]\d*\.\d+$', self.id))

    def get_id_pattern(self) -> str:
        """Return the regex pattern for valid Epic IDs."""
        return r'^[1-9]\d*\.\d+$'

    def generate_prompt(self, project_context: str, parent_context: Optional[str] = None, roadmap_context: Optional[str] = None) -> str:
        """Generate prompt for epic generation."""
        from arcane.prompts.roadmap_prompt_builder import RoadmapPromptBuilder
        builder = RoadmapPromptBuilder()

        # Build expected structure from children
        expected_stories = "\n".join([f"- Story {child.id}: {child.name.split(': ', 1)[-1] if ': ' in child.name else child.name}"
                                     for child in self.get_children_by_type('Story')])

        milestone_context = parent_context or ""
        if self.parent:
            milestone_context = f"Milestone {self.parent.id}: {self.parent.name.split(': ', 1)[-1] if ': ' in self.parent.name else self.parent.name}"

        return builder.build_custom_prompt(
            'epic_generation_individual',
            epic_number=self.id,
            epic_title=self.name.split(': ', 1)[-1] if ': ' in self.name else self.name,
            project_context=project_context,
            milestone_context=milestone_context,
            expected_stories=expected_stories,
            roadmap_context=roadmap_context or ""
        )

    def parse_content(self, llm_response: str) -> None:
        """Parse epic content from LLM response."""
        self.content = llm_response

        # Check if this is the new structured format
        if ':::EPIC_DESCRIPTION:::' in llm_response:
            self._parse_structured_format(llm_response)
        else:
            # Fall back to legacy format
            self._parse_legacy_format(llm_response)

        self.update_generation_status(ItemStatus.GENERATED)

    def _parse_structured_format(self, llm_response: str) -> None:
        """Parse the new structured format with ::: markers."""
        fields = self._extract_all_fields(llm_response)

        # Map to epic attributes
        self.description = fields.get('EPIC_DESCRIPTION', '').strip()
        self.benefits = fields.get('BENEFITS', '').strip()
        self.technical_requirements = fields.get('TECHNICAL_REQUIREMENTS', '').strip()
        self.prerequisites = fields.get('PREREQUISITES', '').strip()
        self.risks_and_mitigations = fields.get('RISKS_AND_MITIGATIONS', '').strip()

        # Parse list fields
        self.goals = self._parse_list_field(fields.get('EPIC_GOALS', ''))
        self.success_metrics = self._parse_list_field(fields.get('SUCCESS_METRICS', ''))

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
            # Remove "Goal N:" or "Metric N:" prefixes
            line = re.sub(r'^(Goal|Metric)\s*\d+:\s*', '', line, flags=re.IGNORECASE)

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
            return int(match.group()) if match else 40
        except (AttributeError, ValueError):
            return 40  # Default for epics

    def _validate_parsed_content(self) -> None:
        """Validate that critical fields were populated."""
        issues = []

        if not self.description:
            issues.append("description")
        if not self.benefits:
            issues.append("benefits")

        if issues:
            logger.warning(f"Epic {self.id} has unpopulated fields: {', '.join(issues)}")

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

        # Extract description from "What it is and why we need it" section
        desc_match = re.search(r'#### \*\*What it is and why we need it:\*\*\n(.+?)(?:\n####|\n\*\*|$)',
                              llm_response, re.DOTALL)
        if desc_match:
            self.description = desc_match.group(1).strip()

        # Extract benefits
        benefits_match = re.search(r'#### \*\*Benefits:\*\*\n((?:- .+?\n)+)', llm_response)
        if benefits_match:
            self.benefits = benefits_match.group(1).strip()

        # Extract prerequisites
        prereq_match = re.search(r'#### \*\*Prerequisites:\*\*\n((?:- .+?\n)+)', llm_response)
        if prereq_match:
            self.prerequisites = prereq_match.group(1).strip()

        # Extract technical requirements
        tech_match = re.search(r'#### \*\*Technical Requirements:\*\*\n((?:- .+?\n)+)', llm_response)
        if tech_match:
            self.technical_requirements = tech_match.group(1).strip()

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
