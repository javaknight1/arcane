"""Milestone model - a major phase or deliverable.

A Milestone represents a major phase or deliverable in the project
that contains multiple Epics.
"""

from pydantic import computed_field

from .base import BaseItem
from .epic import Epic


class Milestone(BaseItem):
    """A major phase or deliverable. Contains multiple Epics.

    Milestones represent significant, demonstrable achievements with
    clear, measurable goals.
    """

    goal: str
    target_date: str | None = None
    epics: list[Epic] = []

    @computed_field
    @property
    def estimated_hours(self) -> int:
        """Total estimated hours from all epics."""
        return sum(e.estimated_hours for e in self.epics)
