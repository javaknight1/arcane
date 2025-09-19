"""Project class - Root level of the roadmap hierarchy."""

import re
from typing import Optional
from .base import Item


class Project(Item):
    """Project represents the root level of the roadmap hierarchy."""

    def __init__(
        self,
        name: str,
        description: Optional[str] = None,
        project_type: Optional[str] = None,
        tech_stack: Optional[str] = None,
        estimated_duration: Optional[str] = None,
        team_size: Optional[str] = None,
        benefits: Optional[str] = None,
        prerequisites: Optional[str] = None,
        technical_requirements: Optional[str] = None,
        claude_code_prompt: Optional[str] = None
    ):
        super().__init__(
            name=name,
            item_type='Project',
            parent=None,  # Projects have no parent
            duration=None,
            priority='Critical',
            status='Not Started',
            description=description,
            benefits=benefits,
            prerequisites=prerequisites,
            technical_requirements=technical_requirements,
            claude_code_prompt=claude_code_prompt
        )

        # Additional project-specific fields
        self.project_type = project_type or ''
        self.tech_stack = tech_stack or ''
        self.estimated_duration = estimated_duration or ''
        self.team_size = team_size or ''
        self.id = "PROJECT"  # Projects have a fixed ID

    def add_milestone(self, milestone: 'Milestone') -> None:
        """Add a milestone to this project."""
        self.add_child(milestone)

    def validate_id(self) -> bool:
        """Project IDs are always valid (fixed as 'PROJECT')."""
        return self.id == "PROJECT"

    def get_id_pattern(self) -> str:
        """Return the regex pattern for valid Project IDs."""
        return r'^PROJECT$'

    def generate_prompt(self, project_context: str, parent_context: Optional[str] = None, roadmap_context: Optional[str] = None) -> str:
        """Generate prompt for project overview generation (if needed)."""
        # Projects typically don't need content generation as they're containers
        # But we implement this for completeness
        return f"""Generate a brief project overview for: {self.name}

Project Context: {project_context}
Roadmap Context: {roadmap_context or 'Not provided'}

Generate a 2-3 sentence project summary."""

    def parse_content(self, llm_response: str) -> None:
        """Parse LLM response and update project fields."""
        # Store the raw response
        self.content = llm_response

        # Projects are mainly containers, so minimal parsing is needed
        # Just store the response as the description if no description exists
        if not self.description and llm_response:
            self.description = llm_response.strip()