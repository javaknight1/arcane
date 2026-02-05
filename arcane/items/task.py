"""Task model - the most granular unit of work.

A Task represents a single, completable piece of work that can typically
be done in 1-8 hours by one developer.
"""

from pydantic import Field

from .base import BaseItem


class Task(BaseItem):
    """The most granular unit of work. Completable in 1-40 hours.

    Tasks are the leaf nodes of the roadmap hierarchy. They contain
    specific implementation details and a ready-to-use Claude Code prompt.
    """

    estimated_hours: int = Field(ge=1, le=40)
    prerequisites: list[str] = []  # IDs of dependent tasks
    acceptance_criteria: list[str]
    implementation_notes: str
    claude_code_prompt: str  # Ready-to-use prompt for Claude Code implementation
