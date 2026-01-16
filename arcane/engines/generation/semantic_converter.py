"""Converts semantic outline items to Item objects."""

from typing import List, Dict, Optional
from arcane.models.outline_item import (
    SemanticOutline,
    SemanticOutlineItem,
    OutlineItemType,
)
from arcane.items.milestone import Milestone
from arcane.items.epic import Epic
from arcane.items.story import Story
from arcane.items.task import Task
from arcane.items.base import Item, ItemStatus
from arcane.utils.logging_config import get_logger

logger = get_logger(__name__)


class SemanticToItemConverter:
    """Converts SemanticOutlineItems to Arcane Item objects.

    This converter transforms the semantic outline structure (with descriptions
    and dependencies) into the Item object hierarchy used for content generation.
    """

    def __init__(self):
        self.item_lookup: Dict[str, Item] = {}

    def convert_outline(self, semantic_outline: SemanticOutline) -> List[Milestone]:
        """Convert entire semantic outline to Item hierarchy.

        Args:
            semantic_outline: The parsed semantic outline

        Returns:
            List of Milestone objects with full hierarchy
        """
        self.item_lookup = {}
        milestones = []

        for sem_milestone in semantic_outline.milestones:
            milestone = self._convert_milestone(sem_milestone)
            milestones.append(milestone)

        # Link dependencies after all items are created
        self._link_dependencies(semantic_outline)

        logger.info(
            f"Converted semantic outline: {len(milestones)} milestones, "
            f"{len(self.item_lookup)} total items"
        )

        return milestones

    def _convert_milestone(self, sem_item: SemanticOutlineItem) -> Milestone:
        """Convert a semantic milestone to Milestone object."""
        # Extract title without "Milestone N:" prefix if present
        title = sem_item.title
        display_name = f"Milestone {sem_item.id}: {title}"

        milestone = Milestone(
            name=display_name,
            number=sem_item.id
        )
        milestone.id = sem_item.id
        milestone.update_generation_status(ItemStatus.PENDING)

        # Transfer semantic description
        self._transfer_semantic_fields(milestone, sem_item)

        # Register in lookup
        self.item_lookup[sem_item.id] = milestone

        # Convert children (epics)
        for sem_epic in sem_item.children:
            epic = self._convert_epic(sem_epic, milestone)
            milestone.add_child(epic)

        return milestone

    def _convert_epic(self, sem_item: SemanticOutlineItem, parent: Milestone) -> Epic:
        """Convert a semantic epic to Epic object."""
        title = sem_item.title
        display_name = f"Epic {sem_item.id}: {title}"

        epic = Epic(
            name=display_name,
            number=sem_item.id,
            parent=parent
        )
        epic.id = sem_item.id
        epic.update_generation_status(ItemStatus.PENDING)

        # Transfer semantic description
        self._transfer_semantic_fields(epic, sem_item)

        # Register in lookup
        self.item_lookup[sem_item.id] = epic

        # Convert children (stories)
        for sem_story in sem_item.children:
            story = self._convert_story(sem_story, epic)
            epic.add_child(story)

        return epic

    def _convert_story(self, sem_item: SemanticOutlineItem, parent: Epic) -> Story:
        """Convert a semantic story to Story object."""
        title = sem_item.title
        display_name = f"Story {sem_item.id}: {title}"

        story = Story(
            name=display_name,
            number=sem_item.id,
            parent=parent
        )
        story.id = sem_item.id
        story.update_generation_status(ItemStatus.PENDING)

        # Transfer semantic description
        self._transfer_semantic_fields(story, sem_item)

        # Register in lookup
        self.item_lookup[sem_item.id] = story

        # Convert children (tasks)
        for sem_task in sem_item.children:
            task = self._convert_task(sem_task, story)
            story.add_child(task)

        return story

    def _convert_task(self, sem_item: SemanticOutlineItem, parent: Story) -> Task:
        """Convert a semantic task to Task object."""
        title = sem_item.title
        display_name = f"Task {sem_item.id}: {title}"

        task = Task(
            name=display_name,
            number=sem_item.id,
            parent=parent
        )
        task.id = sem_item.id
        task.update_generation_status(ItemStatus.PENDING)

        # Transfer semantic description
        self._transfer_semantic_fields(task, sem_item)

        # Register in lookup
        self.item_lookup[sem_item.id] = task

        return task

    def _transfer_semantic_fields(self, item: Item, sem_item: SemanticOutlineItem) -> None:
        """Transfer semantic description fields from outline item to Item object."""
        item.outline_description = sem_item.description.full_text
        item.outline_what = sem_item.description.what
        item.outline_why = sem_item.description.why
        item.dependency_ids = [d.item_id for d in sem_item.dependencies]

    def _link_dependencies(self, semantic_outline: SemanticOutline) -> None:
        """Link dependency references to actual Item objects."""
        for item_id, item in self.item_lookup.items():
            if item.dependency_ids:
                item.depends_on_items = []
                for dep_id in item.dependency_ids:
                    dep_item = self.item_lookup.get(dep_id)
                    if dep_item:
                        item.depends_on_items.append(dep_item)
                    else:
                        logger.warning(
                            f"Item {item_id} references unknown dependency: {dep_id}"
                        )

    def get_item_by_id(self, item_id: str) -> Optional[Item]:
        """Get an Item by its ID.

        Args:
            item_id: The hierarchical ID (e.g., "1.0.1")

        Returns:
            The Item object or None if not found
        """
        return self.item_lookup.get(item_id)

    def get_generation_order(self) -> List[Item]:
        """Get items in dependency-respecting order for generation.

        Returns items in an order that respects dependencies, so items
        are generated after their dependencies.

        Returns:
            List of Item objects in generation order
        """
        result = []
        visited = set()

        def visit(item_id: str):
            if item_id in visited or item_id not in self.item_lookup:
                return
            visited.add(item_id)

            item = self.item_lookup[item_id]
            # Visit dependencies first
            for dep_id in item.dependency_ids:
                visit(dep_id)

            result.append(item)

        # Visit all items
        for item_id in self.item_lookup:
            visit(item_id)

        return result

    def get_statistics(self) -> Dict[str, int]:
        """Get statistics about the converted items.

        Returns:
            Dictionary with counts by type
        """
        stats = {
            'milestones': 0,
            'epics': 0,
            'stories': 0,
            'tasks': 0,
            'total': len(self.item_lookup),
            'items_with_semantic_context': 0,
            'items_with_dependencies': 0,
        }

        for item in self.item_lookup.values():
            if item.item_type == 'Milestone':
                stats['milestones'] += 1
            elif item.item_type == 'Epic':
                stats['epics'] += 1
            elif item.item_type == 'Story':
                stats['stories'] += 1
            elif item.item_type == 'Task':
                stats['tasks'] += 1

            if item.has_semantic_context():
                stats['items_with_semantic_context'] += 1

            if item.dependency_ids:
                stats['items_with_dependencies'] += 1

        return stats
