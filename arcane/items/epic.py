"""Epic model - a feature area or system component.

An Epic represents a coherent feature area or system component
that contains multiple Stories.
"""

from pydantic import computed_field

from .base import BaseItem
from .story import Story


class Epic(BaseItem):
    """A feature area or system component. Contains multiple Stories.

    Epics represent distinct, bounded areas of work that contribute
    to a milestone's objective.
    """

    goal: str
    prerequisites: list[str] = []  # IDs of dependent epics
    stories: list[Story] = []

    @computed_field
    @property
    def estimated_hours(self) -> int:
        """Total estimated hours from all stories."""
        return sum(s.estimated_hours for s in self.stories)
