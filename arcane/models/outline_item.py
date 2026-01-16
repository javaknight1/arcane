"""Semantic outline data structures for roadmap generation."""

import re
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, field
from enum import Enum

from arcane.utils.logging_config import get_logger

logger = get_logger(__name__)


class OutlineItemType(Enum):
    """Types of items in a roadmap outline."""
    PROJECT = "Project"
    MILESTONE = "Milestone"
    EPIC = "Epic"
    STORY = "Story"
    TASK = "Task"


@dataclass
class OutlineDependency:
    """Represents a dependency relationship between outline items."""
    item_id: str  # The ID of the item this depends on (e.g., "1.0.1")
    item_type: str  # Type of the dependency item as string
    is_blocking: bool = True  # Whether this is a blocking dependency

    # Alias for backward compatibility
    @property
    def dependency_id(self) -> str:
        return self.item_id

    @property
    def dependency_type(self) -> OutlineItemType:
        """Get dependency type as enum."""
        type_map = {
            'Milestone': OutlineItemType.MILESTONE,
            'Epic': OutlineItemType.EPIC,
            'Story': OutlineItemType.STORY,
            'Task': OutlineItemType.TASK,
        }
        return type_map.get(self.item_type, OutlineItemType.TASK)

    def __str__(self) -> str:
        return self.item_id


@dataclass
class OutlineItemDescription:
    """Structured description for an outline item."""
    full_text: str = ""  # Complete description text
    what: str = ""  # What this item accomplishes
    why: str = ""  # Why it's needed

    def __bool__(self) -> bool:
        return bool(self.full_text)


@dataclass
class SemanticOutlineItem:
    """Represents an item in a semantic outline with description and dependencies."""
    id: str  # Hierarchical ID (e.g., "1", "1.0", "1.0.1", "1.0.1.1")
    title: str  # Item title/name
    item_type: OutlineItemType
    description: OutlineItemDescription = field(default_factory=OutlineItemDescription)
    dependencies: List[OutlineDependency] = field(default_factory=list)
    children: List['SemanticOutlineItem'] = field(default_factory=list)
    parent: Optional['SemanticOutlineItem'] = field(default=None, repr=False)
    line_number: int = 0

    # Alias for backward compatibility
    @property
    def name(self) -> str:
        return self.title

    @property
    def number(self) -> str:
        """Alias for id to match Item interface."""
        return self.id

    @property
    def parent_id(self) -> Optional[str]:
        """Get the parent item's ID based on hierarchy."""
        parts = self.id.split('.')
        if len(parts) <= 1:
            return None
        return '.'.join(parts[:-1])

    @property
    def dependency_ids(self) -> List[str]:
        """Get list of dependency IDs as strings."""
        return [str(dep) for dep in self.dependencies]

    def has_dependencies(self) -> bool:
        """Check if this item has any dependencies."""
        return len(self.dependencies) > 0

    def depends_on(self, item_id: str) -> bool:
        """Check if this item depends on the given item."""
        return item_id in self.dependency_ids

    def add_child(self, child: 'SemanticOutlineItem') -> None:
        """Add a child item."""
        child.parent = self
        self.children.append(child)

    def get_all_descendants(self) -> List['SemanticOutlineItem']:
        """Get all descendants recursively."""
        descendants = []
        for child in self.children:
            descendants.append(child)
            descendants.extend(child.get_all_descendants())
        return descendants

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'id': self.id,
            'type': self.item_type.value,
            'title': self.title,
            'name': self.title,  # Alias
            'description': self.description.full_text,
            'description_what': self.description.what,
            'description_why': self.description.why,
            'dependencies': self.dependency_ids,
            'parent_id': self.parent.id if self.parent else None,
            'children': [c.id for c in self.children],
            'line_number': self.line_number,
        }

    def __str__(self) -> str:
        deps_str = f" [deps: {', '.join(self.dependency_ids)}]" if self.dependencies else ""
        return f"{self.item_type.value} {self.id}: {self.title}{deps_str}"


class SemanticOutline:
    """Collection of semantic outline items with hierarchy and validation."""

    def __init__(self):
        self.milestones: List[SemanticOutlineItem] = []
        self.all_items: Dict[str, SemanticOutlineItem] = {}
        self.project_name: str = ""
        self.project_type: str = ""
        self.tech_stack: str = ""
        self.project_description: str = ""

    # Alias for backward compatibility
    @property
    def items(self) -> Dict[str, SemanticOutlineItem]:
        return self.all_items

    def add_item(self, item: SemanticOutlineItem) -> None:
        """Add an item to the outline."""
        self.all_items[item.id] = item
        if item.item_type == OutlineItemType.MILESTONE:
            self.milestones.append(item)

    def get_item_by_id(self, item_id: str) -> Optional[SemanticOutlineItem]:
        """Get an item by its ID."""
        return self.all_items.get(item_id)

    # Alias for backward compatibility
    def get_item(self, item_id: str) -> Optional[SemanticOutlineItem]:
        return self.get_item_by_id(item_id)

    def get_items_by_type(self, item_type: OutlineItemType) -> List[SemanticOutlineItem]:
        """Get all items of a specific type."""
        return [item for item in self.all_items.values() if item.item_type == item_type]

    def get_milestones(self) -> List[SemanticOutlineItem]:
        """Get all milestone items."""
        return self.milestones

    def get_epics(self) -> List[SemanticOutlineItem]:
        """Get all epic items."""
        return self.get_items_by_type(OutlineItemType.EPIC)

    def get_stories(self) -> List[SemanticOutlineItem]:
        """Get all story items."""
        return self.get_items_by_type(OutlineItemType.STORY)

    def get_tasks(self) -> List[SemanticOutlineItem]:
        """Get all task items."""
        return self.get_items_by_type(OutlineItemType.TASK)

    def get_children(self, parent_id: str) -> List[SemanticOutlineItem]:
        """Get all direct children of an item."""
        parent = self.get_item_by_id(parent_id)
        if parent:
            return parent.children
        return [
            item for item in self.all_items.values()
            if item.parent_id == parent_id
        ]

    def get_dependents(self, item_id: str) -> List[SemanticOutlineItem]:
        """Get all items that depend on the given item."""
        return [
            item for item in self.all_items.values()
            if item.depends_on(item_id)
        ]

    def validate_dependencies(self) -> List[str]:
        """Validate all dependency references exist."""
        issues = []
        for item_id, item in self.all_items.items():
            for dep in item.dependencies:
                if dep.item_id not in self.all_items:
                    issues.append(
                        f"{item.item_type.value} {item_id} references unknown dependency: {dep.item_id}"
                    )
        return issues

    def get_generation_order(self) -> List[SemanticOutlineItem]:
        """Get items in dependency-respecting order (topological sort)."""
        result = []
        visited: Set[str] = set()

        def visit(item_id: str):
            if item_id in visited or item_id not in self.all_items:
                return
            visited.add(item_id)

            item = self.all_items[item_id]
            # Visit dependencies first
            for dep in item.dependencies:
                visit(dep.item_id)

            result.append(item)

        # Visit all items
        for item_id in self.all_items:
            visit(item_id)

        return result

    # Alias for backward compatibility
    def get_execution_order(self) -> List[SemanticOutlineItem]:
        return self.get_generation_order()

    def get_statistics(self) -> Dict[str, Any]:
        """Get outline statistics."""
        return {
            'total_items': len(self.all_items),
            'milestones': len(self.milestones),
            'epics': len(self.get_epics()),
            'stories': len(self.get_stories()),
            'tasks': len(self.get_tasks()),
            'items_with_dependencies': sum(1 for item in self.all_items.values() if item.has_dependencies()),
            'items_with_descriptions': sum(1 for item in self.all_items.values() if item.description),
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert outline to dictionary representation."""
        return {
            'project_name': self.project_name,
            'project_type': self.project_type,
            'tech_stack': self.tech_stack,
            'project_description': self.project_description,
            'items': [item.to_dict() for item in self.all_items.values()],
            'statistics': self.get_statistics(),
        }

    def __len__(self) -> int:
        return len(self.all_items)

    def __iter__(self):
        return iter(self.all_items.values())

    def __contains__(self, item_id: str) -> bool:
        return item_id in self.all_items
