"""Task class - Specific implementation work."""

from typing import Optional
from .base import Item


class Task(Item):
    """Task represents specific implementation work."""

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
        claude_code_prompt: Optional[str] = None
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
            claude_code_prompt=claude_code_prompt
        )