"""Milestone class - Major phase in the project roadmap."""

from typing import Optional
from .base import Item


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

    def add_epic(self, epic: 'Epic') -> None:
        """Add an epic to this milestone."""
        self.add_child(epic)