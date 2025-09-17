"""Roadmap class - Container for the entire roadmap structure."""

from typing import List, Dict, Any, Optional
from .project import Project
from .milestone import Milestone
from .epic import Epic
from .story import Story
from .task import Task
from .base import Item


class Roadmap:
    """Container for the entire roadmap structure."""

    def __init__(self, project: Project):
        self.project = project

    def get_all_items(self) -> List[Item]:
        """Get all items in the roadmap as a flat list."""
        items = []
        self._collect_items(self.project, items)
        return items

    def _collect_items(self, item: Item, items_list: List[Item]) -> None:
        """Recursively collect all items in the hierarchy."""
        items_list.append(item)
        for child in item.children:
            self._collect_items(child, items_list)

    def to_dict_list(self) -> List[Dict[str, Any]]:
        """Convert roadmap to list of dictionaries for export."""
        return [item.to_dict() for item in self.get_all_items()]

    def get_milestones(self) -> List[Milestone]:
        """Get all milestones in the roadmap."""
        return [item for item in self.project.children if isinstance(item, Milestone)]

    def get_epics(self) -> List[Epic]:
        """Get all epics in the roadmap."""
        epics = []
        for milestone in self.get_milestones():
            epics.extend([item for item in milestone.children if isinstance(item, Epic)])
        return epics

    def get_stories(self) -> List[Story]:
        """Get all stories in the roadmap."""
        stories = []
        for epic in self.get_epics():
            stories.extend([item for item in epic.children if isinstance(item, Story)])
        return stories

    def get_tasks(self) -> List[Task]:
        """Get all tasks in the roadmap."""
        tasks = []
        for story in self.get_stories():
            tasks.extend([item for item in story.children if isinstance(item, Task)])
        return tasks

    def find_item_by_name(self, name: str) -> Optional[Item]:
        """Find an item by its name."""
        for item in self.get_all_items():
            if item.name == name:
                return item
        return None

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the roadmap."""
        all_items = self.get_all_items()
        return {
            'total_items': len(all_items),
            'milestones': len(self.get_milestones()),
            'epics': len(self.get_epics()),
            'stories': len(self.get_stories()),
            'tasks': len(self.get_tasks()),
            'total_duration_hours': self.project.calculate_total_duration(),
            'completion_percentage': self.project.get_completion_percentage(),
            'status_breakdown': self._get_status_breakdown(all_items)
        }

    def _get_status_breakdown(self, items: List[Item]) -> Dict[str, int]:
        """Get breakdown of items by status."""
        breakdown = {'Not Started': 0, 'In Progress': 0, 'Completed': 0, 'Blocked': 0, 'Cancelled': 0}
        for item in items:
            if item.status in breakdown:
                breakdown[item.status] += 1
        return breakdown

    def __repr__(self) -> str:
        stats = self.get_statistics()
        return (f"Roadmap(project='{self.project.name}', "
                f"milestones={stats['milestones']}, "
                f"epics={stats['epics']}, "
                f"stories={stats['stories']}, "
                f"tasks={stats['tasks']})")