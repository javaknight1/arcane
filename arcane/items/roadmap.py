"""Roadmap model - the top-level container.

The Roadmap is the complete output of Arcane, containing all milestones,
epics, stories, and tasks along with project context.
"""

from datetime import datetime

from pydantic import BaseModel, computed_field

from .context import ProjectContext
from .milestone import Milestone


class Roadmap(BaseModel):
    """Top-level container. The complete output of Arcane.

    Contains the full project roadmap with all milestones and their
    nested epics, stories, and tasks.
    """

    id: str
    project_name: str
    created_at: datetime
    updated_at: datetime
    context: ProjectContext
    milestones: list[Milestone] = []

    @computed_field
    @property
    def total_hours(self) -> int:
        """Total estimated hours from all milestones."""
        return sum(m.estimated_hours for m in self.milestones)

    @computed_field
    @property
    def total_items(self) -> dict[str, int]:
        """Count of all items by type."""
        milestones = len(self.milestones)
        epics = sum(len(m.epics) for m in self.milestones)
        stories = sum(len(e.stories) for m in self.milestones for e in m.epics)
        tasks = sum(
            len(s.tasks) for m in self.milestones for e in m.epics for s in e.stories
        )
        return {
            "milestones": milestones,
            "epics": epics,
            "stories": stories,
            "tasks": tasks,
        }
