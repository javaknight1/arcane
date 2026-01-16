"""Base Item class for all roadmap components."""

import re
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class ItemStatus(Enum):
    """Status of roadmap item generation."""
    NOT_STARTED = "Not Started"
    PENDING = "Pending"  # Ready for generation
    GENERATING = "Generating"  # Currently being generated
    GENERATED = "Generated"  # Successfully generated
    FAILED = "Failed"  # Generation failed
    SKIPPED = "Skipped"  # User chose to skip
    COMPLETED = "Completed"  # Work completed
    IN_PROGRESS = "In Progress"  # Work in progress
    BLOCKED = "Blocked"  # Blocked by dependencies
    CANCELLED = "Cancelled"  # Cancelled


class Item(ABC):
    """Base class for all roadmap items (Project, Milestone, Epic, Story, Task)."""

    def __init__(
        self,
        name: str,
        item_type: str,
        parent: Optional['Item'] = None,
        duration: Optional[int] = None,  # in hours
        priority: str = 'Medium',
        status: str = 'Not Started',
        description: Optional[str] = None,
        benefits: Optional[str] = None,
        prerequisites: Optional[str] = None,
        technical_requirements: Optional[str] = None,
        claude_code_prompt: Optional[str] = None,
        tags: Optional[List[str]] = None,
        work_type: Optional[str] = None,
        complexity: Optional[str] = None
    ):
        self.name = name
        self.item_type = item_type
        self.parent = parent
        self.duration = duration
        self.priority = priority
        self.status = status
        self.description = description or ''
        self.benefits = benefits or ''
        self.prerequisites = prerequisites or ''
        self.technical_requirements = technical_requirements or ''
        self.claude_code_prompt = claude_code_prompt or ''
        self.tags = tags or []
        self.work_type = work_type or ''
        self.complexity = complexity or ''
        self.children: List['Item'] = []
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

        # Generation-specific fields
        self.id = None  # Will be set by subclasses
        self.content = None  # Raw LLM response
        self.generation_status = ItemStatus.NOT_STARTED

        # Semantic outline fields
        self.outline_description: str = ''  # Brief description from semantic outline
        self.outline_what: str = ''  # What this item accomplishes
        self.outline_why: str = ''  # Why it's needed / its purpose
        self.dependency_ids: List[str] = []  # IDs of items this depends on
        self.depends_on_items: List['Item'] = []  # Linked dependency Item objects

        # If this item has a parent, add it to parent's children
        if parent:
            parent.add_child(self)

    def add_child(self, child: 'Item') -> None:
        """Add a child item to this item."""
        if child not in self.children:
            self.children.append(child)
            child.parent = self

    def remove_child(self, child: 'Item') -> None:
        """Remove a child item from this item."""
        if child in self.children:
            self.children.remove(child)
            child.parent = None

    def get_path(self) -> str:
        """Get the full hierarchical path to this item."""
        if self.parent:
            return f"{self.parent.get_path()} > {self.name}"
        return self.name

    def get_parent_name(self) -> str:
        """Get the parent's name or empty string if no parent."""
        return self.parent.name if self.parent else ''

    def to_dict(self) -> Dict[str, Any]:
        """Convert item to dictionary format for CSV/JSON export."""
        return {
            'Name': self.name,
            'Type': self.item_type,
            'Parent': self.get_parent_name(),
            'Duration': self.duration or '',
            'Priority': self.priority,
            'Status': self.status,
            'Goal/Description': self.description,
            'Benefits': self.benefits,
            'Prerequisites': self.prerequisites,
            'Technical Requirements': self.technical_requirements,
            'Claude Code Prompt': self.claude_code_prompt,
            'Work Type': self.work_type,
            'Complexity': self.complexity,
            'Tags': ', '.join(self.tags) if self.tags else ''
        }

    def update_status(self, new_status: str) -> None:
        """Update the status of this item."""
        valid_statuses = ['Not Started', 'In Progress', 'Completed', 'Blocked', 'Cancelled']
        if new_status in valid_statuses:
            self.status = new_status
            self.updated_at = datetime.now()
        else:
            raise ValueError(f"Invalid status: {new_status}. Must be one of {valid_statuses}")

    def update_generation_status(self, new_status: ItemStatus) -> None:
        """Update the generation status of this item."""
        self.generation_status = new_status
        self.updated_at = datetime.now()

    @abstractmethod
    def validate_id(self) -> bool:
        """Validate that the ID follows the correct pattern for this item type."""
        pass

    @abstractmethod
    def get_id_pattern(self) -> str:
        """Return the regex pattern for valid IDs of this type."""
        pass

    @abstractmethod
    def generate_prompt(self, project_context: str, parent_context: Optional[str] = None, roadmap_context: Optional[str] = None) -> str:
        """Generate the LLM prompt for this item."""
        pass

    @abstractmethod
    def parse_content(self, llm_response: str) -> None:
        """Parse LLM response and update item fields."""
        pass

    def needs_generation(self) -> bool:
        """Check if this item needs generation."""
        return self.generation_status in [ItemStatus.NOT_STARTED, ItemStatus.PENDING, ItemStatus.FAILED]

    def generate_content(self, llm_client, project_context: str, parent_context: Optional[str] = None, roadmap_context: Optional[str] = None) -> None:
        """Generate content for this item using the LLM client."""
        if not self.needs_generation():
            return

        self.update_generation_status(ItemStatus.GENERATING)

        try:
            # Generate prompt for this item
            prompt = self.generate_prompt(project_context, parent_context, roadmap_context)

            # Call LLM to generate content
            response = llm_client.generate(prompt)

            # Parse and store the response
            self.parse_content(response)

            self.update_generation_status(ItemStatus.GENERATED)

        except Exception as e:
            self.update_generation_status(ItemStatus.FAILED)
            raise e

    def get_children_by_type(self, item_type: str) -> List['Item']:
        """Get all children of a specific type."""
        return [child for child in self.children if child.item_type == item_type]

    def calculate_total_duration(self) -> int:
        """Calculate total duration including all children."""
        total = self.duration or 0
        for child in self.children:
            total += child.calculate_total_duration()
        return total

    def get_completion_percentage(self) -> float:
        """Calculate completion percentage based on children status."""
        if not self.children:
            return 100.0 if self.status == 'Completed' else 0.0

        completed_count = sum(1 for child in self.children if child.status == 'Completed')
        return (completed_count / len(self.children)) * 100.0

    def add_tag(self, tag: str) -> None:
        """Add a tag to this item if it doesn't already exist."""
        tag = tag.strip().lower()
        if tag and tag not in self.tags:
            self.tags.append(tag)
            self.updated_at = datetime.now()

    def add_tags(self, tags: List[str]) -> None:
        """Add multiple tags to this item."""
        for tag in tags:
            self.add_tag(tag)

    def remove_tag(self, tag: str) -> None:
        """Remove a tag from this item."""
        tag = tag.strip().lower()
        if tag in self.tags:
            self.tags.remove(tag)
            self.updated_at = datetime.now()

    def has_tag(self, tag: str) -> bool:
        """Check if this item has a specific tag."""
        return tag.strip().lower() in self.tags

    def has_any_tag(self, tags: List[str]) -> bool:
        """Check if this item has any of the specified tags."""
        return any(self.has_tag(tag) for tag in tags)

    def get_tags_display(self) -> str:
        """Get tags as a comma-separated string for display."""
        return ', '.join(self.tags) if self.tags else 'None'

    def get_semantic_context(self) -> str:
        """Get semantic context string for prompt injection."""
        lines = []

        if self.outline_description:
            lines.append(f"Purpose: {self.outline_description}")

        if self.outline_what:
            lines.append(f"What it does: {self.outline_what}")

        if self.outline_why:
            lines.append(f"Why it's needed: {self.outline_why}")

        if self.depends_on_items:
            dep_strs = [f"{d.item_type} {d.id}" for d in self.depends_on_items]
            lines.append(f"Dependencies: {', '.join(dep_strs)}")

        return "\n".join(lines) if lines else "No semantic context available"

    def get_dependency_context(self) -> str:
        """Get context from dependency items for prompt injection."""
        if not self.depends_on_items:
            return "No dependencies - this item can be started independently"

        contexts = []
        for dep in self.depends_on_items:
            ctx = f"{dep.item_type} {dep.id}: {dep.name}"
            if dep.outline_description:
                ctx += f"\n  → Purpose: {dep.outline_description}"
            if hasattr(dep, 'description') and dep.description:
                desc_preview = dep.description[:200] + "..." if len(dep.description) > 200 else dep.description
                ctx += f"\n  → Output: {desc_preview}"
            contexts.append(ctx)

        return "\n".join(contexts)

    def has_semantic_context(self) -> bool:
        """Check if this item has semantic context from outline."""
        return bool(self.outline_description or self.outline_what or self.outline_why)

    def get_generation_instructions(self) -> str:
        """Get generation instructions specific to this item type.

        Returns:
            Instructions string for the LLM
        """
        instructions = [f"Generate detailed content for this {self.item_type}."]

        if self.outline_description:
            instructions.append(f"Purpose: {self.outline_description}")

        if self.outline_what:
            instructions.append(f"Scope: {self.outline_what}")

        if self.outline_why:
            instructions.append(f"Rationale: {self.outline_why}")

        instructions.append(f"\nOutput requirements:")
        instructions.append(f"- Provide a clear description")
        instructions.append(f"- Include technical details where appropriate")
        instructions.append(f"- Maintain consistency with the roadmap context")

        return "\n".join(instructions)

    def __repr__(self) -> str:
        return f"{self.item_type}(name='{self.name}', status='{self.status}')"

    def __str__(self) -> str:
        return f"{self.item_type}: {self.name}"