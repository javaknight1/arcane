"""Epic class - Major feature area or technical component."""

import re
from typing import Optional
from .base import Item, ItemStatus


class Epic(Item):
    """Epic represents a major feature area or technical component."""

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
        claude_code_prompt: Optional[str] = None
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
            claude_code_prompt=claude_code_prompt
        )
        self.id = number
        if not self.validate_id():
            raise ValueError(f"Invalid Epic ID: {self.id}")

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
        from arcane.prompts.prompt_builder import PromptBuilder
        builder = PromptBuilder()

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

        self.update_generation_status(ItemStatus.GENERATED)