"""Story model - a user-facing capability.

A Story represents a user-facing capability or developer deliverable
that contains multiple Tasks.
"""

from pydantic import computed_field

from .base import BaseItem
from .task import Task


class Story(BaseItem):
    """A user-facing capability. Contains multiple Tasks.

    Stories are completable in 1-5 days by one developer and have
    clear acceptance criteria.
    """

    acceptance_criteria: list[str]
    tasks: list[Task] = []

    @computed_field
    @property
    def estimated_hours(self) -> int:
        """Total estimated hours from all tasks."""
        return sum(t.estimated_hours for t in self.tasks)
