"""Story class - User-facing functionality or major technical work."""

from typing import Optional
from .base import Item


class Story(Item):
    """Story represents user-facing functionality or major technical work."""

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
        claude_code_prompt: Optional[str] = None
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
            claude_code_prompt=claude_code_prompt
        )

    def add_task(self, task: 'Task') -> None:
        """Add a task to this story."""
        self.add_child(task)