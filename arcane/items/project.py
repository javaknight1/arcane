"""Project class - Root level of the roadmap hierarchy."""

from typing import Optional
from .base import Item


class Project(Item):
    """Project represents the root level of the roadmap hierarchy."""

    def __init__(
        self,
        name: str,
        description: Optional[str] = None,
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

    def add_milestone(self, milestone: 'Milestone') -> None:
        """Add a milestone to this project."""
        self.add_child(milestone)