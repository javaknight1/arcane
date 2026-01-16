"""Incremental refinement engine for roadmap items.

Allows users to refine specific items with feedback without regenerating everything.
Tracks version history and supports reverting to previous versions.
"""

import json
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from arcane.items.base import Item
from arcane.utils.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class RefinementRecord:
    """Record of a single refinement operation.

    Tracks the before/after state of an item along with the feedback
    that prompted the refinement.
    """
    item_id: str
    version: int
    content_before: str
    content_after: str
    user_feedback: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'item_id': self.item_id,
            'version': self.version,
            'content_before': self.content_before,
            'content_after': self.content_after,
            'user_feedback': self.user_feedback,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RefinementRecord':
        """Create from dictionary."""
        return cls(
            item_id=data['item_id'],
            version=data['version'],
            content_before=data['content_before'],
            content_after=data['content_after'],
            user_feedback=data['user_feedback'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            metadata=data.get('metadata', {}),
        )


class RefinementEngine:
    """Handles incremental refinement of roadmap items.

    Allows users to provide feedback on generated content and get
    refined versions while maintaining a complete version history.
    """

    REFINEMENT_PROMPT = """
You previously generated this {item_type}:

=== PREVIOUS VERSION ===
{previous_content}

=== USER FEEDBACK ===
{user_feedback}

=== CONTEXT ===
{context}

Please regenerate this {item_type} addressing the feedback specifically.
Maintain consistency with the overall roadmap structure and style.

Important:
- Address ALL points in the user feedback
- Keep what was good in the previous version
- Maintain the same format and level of detail
- Ensure the refined version integrates well with related items
"""

    TARGETED_REFINEMENT_PROMPT = """
You previously generated this {item_type}:

=== PREVIOUS VERSION ===
{previous_content}

=== SPECIFIC SECTION TO REFINE ===
{section_name}: {section_content}

=== USER FEEDBACK ===
{user_feedback}

=== CONTEXT ===
{context}

Please regenerate ONLY the {section_name} section, keeping everything else the same.
Address the user feedback while maintaining consistency with the rest of the content.
"""

    def __init__(self, llm_client):
        """Initialize the refinement engine.

        Args:
            llm_client: LLM client for generating refinements
        """
        self.llm_client = llm_client
        self.history: Dict[str, List[RefinementRecord]] = {}
        self._item_cache: Dict[str, Item] = {}

    def refine_item(
        self,
        item: Item,
        feedback: str,
        context: str = "",
        apply_immediately: bool = True
    ) -> str:
        """Regenerate item based on user feedback.

        Args:
            item: The item to refine
            feedback: User's feedback on what to change
            context: Additional context for refinement
            apply_immediately: Whether to apply changes to item directly

        Returns:
            The refined content
        """
        if not item.content and not item.description:
            raise ValueError(f"Item {item.id} has no content to refine")

        # Use content if available, otherwise use description
        previous_content = item.content or self._serialize_item_content(item)

        # Build refinement prompt
        prompt = self.REFINEMENT_PROMPT.format(
            item_type=item.item_type,
            previous_content=previous_content,
            user_feedback=feedback,
            context=context or self._build_default_context(item)
        )

        # Generate refined content
        logger.info(f"Refining {item.item_type} {item.id} based on feedback")
        refined_content = self.llm_client.generate(prompt)

        # Record the refinement
        version = len(self.history.get(item.id, [])) + 1
        record = RefinementRecord(
            item_id=item.id,
            version=version,
            content_before=previous_content,
            content_after=refined_content,
            user_feedback=feedback,
            metadata={'context_provided': bool(context)}
        )

        if item.id not in self.history:
            self.history[item.id] = []
        self.history[item.id].append(record)

        # Cache item reference for revert operations
        self._item_cache[item.id] = item

        # Apply changes if requested
        if apply_immediately:
            self._apply_content(item, refined_content)

        logger.info(f"Refinement complete for {item.id}, now at version {version}")
        return refined_content

    def refine_section(
        self,
        item: Item,
        section_name: str,
        section_content: str,
        feedback: str,
        context: str = ""
    ) -> str:
        """Refine a specific section of an item.

        Args:
            item: The item containing the section
            section_name: Name of the section (e.g., "description", "acceptance_criteria")
            section_content: Current content of the section
            feedback: User's feedback on what to change
            context: Additional context for refinement

        Returns:
            The refined section content
        """
        previous_content = item.content or self._serialize_item_content(item)

        prompt = self.TARGETED_REFINEMENT_PROMPT.format(
            item_type=item.item_type,
            previous_content=previous_content,
            section_name=section_name,
            section_content=section_content,
            user_feedback=feedback,
            context=context or self._build_default_context(item)
        )

        logger.info(f"Refining section '{section_name}' of {item.item_type} {item.id}")
        refined_section = self.llm_client.generate(prompt)

        # Record the refinement
        version = len(self.history.get(item.id, [])) + 1
        record = RefinementRecord(
            item_id=item.id,
            version=version,
            content_before=section_content,
            content_after=refined_section,
            user_feedback=feedback,
            metadata={
                'section_name': section_name,
                'targeted_refinement': True
            }
        )

        if item.id not in self.history:
            self.history[item.id] = []
        self.history[item.id].append(record)

        return refined_section

    def revert_to_version(self, item_id: str, version: int) -> str:
        """Revert an item to a previous version.

        Args:
            item_id: ID of the item to revert
            version: Version number to revert to (0 = original)

        Returns:
            The content of the specified version

        Raises:
            ValueError: If item has no history or version is invalid
        """
        if item_id not in self.history:
            raise ValueError(f"No refinement history for item {item_id}")

        history = self.history[item_id]

        if version < 0 or version > len(history):
            raise ValueError(
                f"Invalid version {version}. Valid range: 0-{len(history)}"
            )

        # Version 0 = original content (before any refinements)
        if version == 0:
            content = history[0].content_before
        else:
            content = history[version - 1].content_after

        # Apply to cached item if available
        if item_id in self._item_cache:
            self._apply_content(self._item_cache[item_id], content)
            logger.info(f"Reverted {item_id} to version {version}")

        return content

    def get_version(self, item_id: str, version: int) -> Optional[str]:
        """Get content of a specific version without applying it.

        Args:
            item_id: ID of the item
            version: Version number (0 = original)

        Returns:
            Content of the specified version, or None if not found
        """
        if item_id not in self.history:
            return None

        history = self.history[item_id]

        if version < 0 or version > len(history):
            return None

        if version == 0:
            return history[0].content_before
        return history[version - 1].content_after

    def get_current_version(self, item_id: str) -> int:
        """Get the current version number for an item.

        Args:
            item_id: ID of the item

        Returns:
            Current version number (0 if no refinements)
        """
        if item_id not in self.history:
            return 0
        return len(self.history[item_id])

    def compare_versions(self, item_id: str) -> Optional[Dict[str, Any]]:
        """Compare all versions of an item.

        Args:
            item_id: ID of the item

        Returns:
            Dictionary with version comparison, or None if no history
        """
        if item_id not in self.history:
            return None

        versions = []
        for record in self.history[item_id]:
            versions.append({
                'version': record.version,
                'feedback': record.user_feedback,
                'timestamp': record.timestamp.isoformat(),
                'content_length_before': len(record.content_before),
                'content_length_after': len(record.content_after),
                'metadata': record.metadata,
            })

        return {
            'item_id': item_id,
            'total_versions': len(versions),
            'versions': versions,
            'original_length': len(self.history[item_id][0].content_before),
            'current_length': len(self.history[item_id][-1].content_after),
        }

    def get_version_diff(self, item_id: str, version1: int, version2: int) -> Dict[str, Any]:
        """Get a diff between two versions.

        Args:
            item_id: ID of the item
            version1: First version number
            version2: Second version number

        Returns:
            Dictionary with diff information
        """
        content1 = self.get_version(item_id, version1)
        content2 = self.get_version(item_id, version2)

        if content1 is None or content2 is None:
            raise ValueError(f"Invalid version numbers: {version1}, {version2}")

        # Calculate simple diff metrics
        lines1 = content1.split('\n')
        lines2 = content2.split('\n')

        return {
            'item_id': item_id,
            'version1': version1,
            'version2': version2,
            'content1_lines': len(lines1),
            'content2_lines': len(lines2),
            'content1_length': len(content1),
            'content2_length': len(content2),
            'length_change': len(content2) - len(content1),
            'line_change': len(lines2) - len(lines1),
        }

    def get_history(self, item_id: str) -> List[RefinementRecord]:
        """Get full refinement history for an item.

        Args:
            item_id: ID of the item

        Returns:
            List of refinement records
        """
        return self.history.get(item_id, []).copy()

    def get_feedback_summary(self, item_id: str) -> List[str]:
        """Get summary of all feedback for an item.

        Args:
            item_id: ID of the item

        Returns:
            List of feedback strings in chronological order
        """
        if item_id not in self.history:
            return []
        return [r.user_feedback for r in self.history[item_id]]

    def clear_history(self, item_id: Optional[str] = None) -> int:
        """Clear refinement history.

        Args:
            item_id: Specific item to clear, or None to clear all

        Returns:
            Number of items cleared
        """
        if item_id:
            if item_id in self.history:
                del self.history[item_id]
                if item_id in self._item_cache:
                    del self._item_cache[item_id]
                return 1
            return 0
        else:
            count = len(self.history)
            self.history.clear()
            self._item_cache.clear()
            return count

    def export_history(self, filepath: str) -> None:
        """Export refinement history to JSON file.

        Args:
            filepath: Path to save history
        """
        data = {
            'exported_at': datetime.now().isoformat(),
            'items': {}
        }

        for item_id, records in self.history.items():
            data['items'][item_id] = [r.to_dict() for r in records]

        output_path = Path(filepath)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

        logger.info(f"Exported refinement history to {filepath}")

    def import_history(self, filepath: str) -> int:
        """Import refinement history from JSON file.

        Args:
            filepath: Path to load history from

        Returns:
            Number of items imported
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        count = 0
        for item_id, records in data.get('items', {}).items():
            self.history[item_id] = [
                RefinementRecord.from_dict(r) for r in records
            ]
            count += 1

        logger.info(f"Imported history for {count} items from {filepath}")
        return count

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all refinement activity.

        Returns:
            Dictionary with summary statistics
        """
        total_refinements = sum(len(records) for records in self.history.values())
        items_refined = len(self.history)

        # Calculate average refinements per item
        avg_refinements = total_refinements / items_refined if items_refined > 0 else 0

        # Find most refined item
        most_refined_id = None
        most_refined_count = 0
        for item_id, records in self.history.items():
            if len(records) > most_refined_count:
                most_refined_count = len(records)
                most_refined_id = item_id

        return {
            'total_refinements': total_refinements,
            'items_refined': items_refined,
            'average_refinements_per_item': round(avg_refinements, 2),
            'most_refined_item': most_refined_id,
            'most_refined_count': most_refined_count,
        }

    def _serialize_item_content(self, item: Item) -> str:
        """Serialize item content for storage.

        Args:
            item: The item to serialize

        Returns:
            Serialized content string
        """
        parts = [f"# {item.item_type}: {item.name}"]

        if item.description:
            parts.append(f"\n## Description\n{item.description}")

        if hasattr(item, 'acceptance_criteria') and item.acceptance_criteria:
            parts.append("\n## Acceptance Criteria")
            for i, ac in enumerate(item.acceptance_criteria, 1):
                parts.append(f"- AC{i}: {ac}")

        if item.technical_requirements:
            parts.append(f"\n## Technical Requirements\n{item.technical_requirements}")

        if item.benefits:
            parts.append(f"\n## Benefits\n{item.benefits}")

        return '\n'.join(parts)

    def _build_default_context(self, item: Item) -> str:
        """Build default context from item's position in hierarchy.

        Args:
            item: The item to build context for

        Returns:
            Context string
        """
        parts = [f"Item path: {item.get_path()}"]

        if item.parent:
            parts.append(f"Parent: {item.parent.item_type} - {item.parent.name}")

        children = item.children
        if children:
            child_types = {}
            for child in children:
                child_types[child.item_type] = child_types.get(child.item_type, 0) + 1
            parts.append(f"Children: {child_types}")

        return '\n'.join(parts)

    def _apply_content(self, item: Item, content: str) -> None:
        """Apply refined content to an item.

        Args:
            item: The item to update
            content: The new content
        """
        item.content = content
        item.updated_at = datetime.now()

        # Try to update description if it's in the content
        if hasattr(item, 'description'):
            # Extract description from structured content if possible
            import re
            desc_match = re.search(r'## Description\s*\n(.+?)(?=\n##|\Z)', content, re.DOTALL)
            if desc_match:
                item.description = desc_match.group(1).strip()
