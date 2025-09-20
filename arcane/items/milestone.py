"""Milestone class - Major phase in the project roadmap."""

import re
from typing import Optional
from .base import Item, ItemStatus


class Milestone(Item):
    """Milestone represents a major phase in the project roadmap."""

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
        claude_code_prompt: Optional[str] = None
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
            claude_code_prompt=claude_code_prompt
        )
        self.id = number
        if not self.validate_id():
            raise ValueError(f"Invalid Milestone ID: {self.id}")

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

        # Extract duration if present
        duration_match = re.search(r'\*\*Duration:\*\*\s*(\d+)\s*hours?', llm_response)
        if duration_match:
            self.duration = int(duration_match.group(1))

        # Extract priority if present
        priority_match = re.search(r'\*\*Priority:\*\*\s*(.+?)(?:\n|$)', llm_response)
        if priority_match:
            self.priority = priority_match.group(1).strip()

        # Extract description from "What it is and why we need it" section
        desc_match = re.search(r'### \*\*What it is and why we need it:\*\*\n(.+?)(?:\n###|\n\*\*|$)',
                              llm_response, re.DOTALL)
        if desc_match:
            self.description = desc_match.group(1).strip()

        # Extract benefits
        benefits_match = re.search(r'### \*\*Benefits:\*\*\n((?:- .+?\n)+)', llm_response)
        if benefits_match:
            self.benefits = benefits_match.group(1).strip()

        self.update_generation_status(ItemStatus.GENERATED)