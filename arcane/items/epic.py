"""Epic class - Major feature area or technical component."""

from typing import Optional
from .base import Item


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

    def add_story(self, story: 'Story') -> None:
        """Add a story to this epic."""
        self.add_child(story)