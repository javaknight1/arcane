"""Parser for semantic outlines with descriptions and dependencies."""

import re
from typing import List, Optional, Set
from arcane.models.outline_item import (
    SemanticOutline,
    SemanticOutlineItem,
    OutlineItemType,
    OutlineItemDescription,
    OutlineDependency
)
from arcane.utils.logging_config import get_logger

logger = get_logger(__name__)


class SemanticOutlineParser:
    """Parses semantic outlines into structured data with descriptions and dependencies."""

    # Regex patterns for parsing item headers
    MILESTONE_PATTERN = re.compile(r'^##\s*Milestone\s+(\d+):\s*(.+)$')
    EPIC_PATTERN = re.compile(r'^###\s*Epic\s+(\d+\.\d+):\s*(.+)$')
    STORY_PATTERN = re.compile(r'^####\s*Story\s+(\d+\.\d+\.\d+):\s*(.+)$')
    TASK_PATTERN = re.compile(r'^#####\s*Task\s+(\d+\.\d+\.\d+\.\d+):\s*(.+)$')

    # Pattern for description lines (start with "> " but not dependencies)
    DESCRIPTION_PATTERN = re.compile(r'^>\s*(?!Dependencies?:)(.+)$')

    # Pattern for dependency lines
    DEPENDENCY_PATTERN = re.compile(r'^>\s*Dependencies?:\s*(.+)$', re.IGNORECASE)

    # Pattern for extracting item IDs with type prefix
    ITEM_ID_WITH_TYPE_PATTERN = re.compile(r'(?:Milestone|Epic|Story|Task)\s+(\d+(?:\.\d+)*)')

    # Pattern for raw item IDs (including single-digit milestone IDs)
    RAW_ID_PATTERN = re.compile(r'\b(\d+(?:\.\d+)*)\b')

    # Project metadata patterns
    PROJECT_NAME_PATTERN = re.compile(r'PROJECT_NAME:\s*(.+)$', re.MULTILINE)
    PROJECT_TYPE_PATTERN = re.compile(r'PROJECT_TYPE:\s*(.+)$', re.MULTILINE)
    TECH_STACK_PATTERN = re.compile(r'TECH_STACK:\s*(.+)$', re.MULTILINE)
    PROJECT_DESCRIPTION_PATTERN = re.compile(r'DESCRIPTION:\s*(.+)$', re.MULTILINE)

    def __init__(self):
        self.parse_errors: List[str] = []
        self.parse_warnings: List[str] = []

    def parse(self, outline_text: str) -> SemanticOutline:
        """Parse a semantic outline into structured format.

        Args:
            outline_text: The raw outline text to parse

        Returns:
            SemanticOutline object with all parsed items
        """
        self.parse_errors = []
        self.parse_warnings = []

        outline = SemanticOutline()

        # Parse project metadata
        self._parse_metadata(outline, outline_text)

        # Parse all items
        self._parse_items(outline, outline_text)

        # Validate the parsed outline
        self._validate_outline(outline)

        return outline

    def _parse_metadata(self, outline: SemanticOutline, text: str) -> None:
        """Parse project metadata from the outline."""
        name_match = self.PROJECT_NAME_PATTERN.search(text)
        if name_match:
            outline.project_name = name_match.group(1).strip()

        type_match = self.PROJECT_TYPE_PATTERN.search(text)
        if type_match:
            outline.project_type = type_match.group(1).strip()

        stack_match = self.TECH_STACK_PATTERN.search(text)
        if stack_match:
            outline.tech_stack = stack_match.group(1).strip()

        desc_match = self.PROJECT_DESCRIPTION_PATTERN.search(text)
        if desc_match:
            outline.project_description = desc_match.group(1).strip()

    def _parse_items(self, outline: SemanticOutline, text: str) -> None:
        """Parse all outline items from text."""
        lines = text.split('\n')

        current_milestone: Optional[SemanticOutlineItem] = None
        current_epic: Optional[SemanticOutlineItem] = None
        current_story: Optional[SemanticOutlineItem] = None
        current_item: Optional[SemanticOutlineItem] = None

        description_buffer: List[str] = []

        for line_num, line in enumerate(lines, 1):
            line = line.rstrip()

            # Skip empty lines
            if not line.strip():
                continue

            # Check for item headers
            milestone_match = self.MILESTONE_PATTERN.match(line)
            epic_match = self.EPIC_PATTERN.match(line)
            story_match = self.STORY_PATTERN.match(line)
            task_match = self.TASK_PATTERN.match(line)

            # Process buffered description for previous item
            if any([milestone_match, epic_match, story_match, task_match]):
                if current_item and description_buffer:
                    self._parse_description_buffer(current_item, description_buffer)
                    description_buffer = []

            if milestone_match:
                item_id = milestone_match.group(1)
                title = milestone_match.group(2).strip()

                current_milestone = SemanticOutlineItem(
                    id=item_id,
                    title=title,
                    item_type=OutlineItemType.MILESTONE,
                    description=OutlineItemDescription(),
                    line_number=line_num
                )
                outline.add_item(current_milestone)
                current_item = current_milestone
                current_epic = None
                current_story = None

            elif epic_match:
                item_id = epic_match.group(1)
                title = epic_match.group(2).strip()

                if not current_milestone:
                    self.parse_errors.append(f"Line {line_num}: Epic {item_id} has no parent milestone")
                    continue

                current_epic = SemanticOutlineItem(
                    id=item_id,
                    title=title,
                    item_type=OutlineItemType.EPIC,
                    description=OutlineItemDescription(),
                    line_number=line_num
                )
                current_milestone.add_child(current_epic)
                outline.add_item(current_epic)
                current_item = current_epic
                current_story = None

            elif story_match:
                item_id = story_match.group(1)
                title = story_match.group(2).strip()

                if not current_epic:
                    self.parse_errors.append(f"Line {line_num}: Story {item_id} has no parent epic")
                    continue

                current_story = SemanticOutlineItem(
                    id=item_id,
                    title=title,
                    item_type=OutlineItemType.STORY,
                    description=OutlineItemDescription(),
                    line_number=line_num
                )
                current_epic.add_child(current_story)
                outline.add_item(current_story)
                current_item = current_story

            elif task_match:
                item_id = task_match.group(1)
                title = task_match.group(2).strip()

                if not current_story:
                    self.parse_errors.append(f"Line {line_num}: Task {item_id} has no parent story")
                    continue

                task = SemanticOutlineItem(
                    id=item_id,
                    title=title,
                    item_type=OutlineItemType.TASK,
                    description=OutlineItemDescription(),
                    line_number=line_num
                )
                current_story.add_child(task)
                outline.add_item(task)
                current_item = task

            elif line.startswith('>'):
                # Description or dependency line
                description_buffer.append(line)

        # Process final item's description buffer
        if current_item and description_buffer:
            self._parse_description_buffer(current_item, description_buffer)

    def _parse_description_buffer(self, item: SemanticOutlineItem, buffer: List[str]) -> None:
        """Parse description lines for an item."""
        description_lines = []

        for line in buffer:
            # Check if it's a dependency line
            dep_match = self.DEPENDENCY_PATTERN.match(line)
            if dep_match:
                deps_text = dep_match.group(1).strip()
                item.dependencies = self._parse_dependencies(deps_text)
            else:
                # Regular description line
                desc_match = self.DESCRIPTION_PATTERN.match(line)
                if desc_match:
                    description_lines.append(desc_match.group(1).strip())

        # Combine description lines
        if description_lines:
            full_desc = ' '.join(description_lines)
            item.description.full_text = full_desc

            # Try to split into what/why
            sentences = full_desc.split('. ')
            if len(sentences) >= 2:
                item.description.what = sentences[0] + '.'
                item.description.why = '. '.join(sentences[1:])
            else:
                item.description.what = full_desc

    def _parse_dependencies(self, deps_text: str) -> List[OutlineDependency]:
        """Parse dependency text into structured dependencies."""
        dependencies = []

        # Handle "None" case
        if deps_text.lower().strip() == 'none':
            return dependencies

        # Track seen IDs to avoid duplicates
        seen_ids: Set[str] = set()

        # Find all item ID references with type prefix
        matches = self.ITEM_ID_WITH_TYPE_PATTERN.findall(deps_text)

        for item_id in matches:
            if item_id in seen_ids:
                continue
            seen_ids.add(item_id)

            # Determine item type from ID format
            item_type = self._infer_item_type(item_id)

            dependencies.append(OutlineDependency(
                item_id=item_id,
                item_type=item_type,
                is_blocking=True
            ))

        # Also check for raw IDs without type prefix
        raw_matches = self.RAW_ID_PATTERN.findall(deps_text)

        for item_id in raw_matches:
            if item_id in seen_ids:
                continue
            seen_ids.add(item_id)

            item_type = self._infer_item_type(item_id)

            dependencies.append(OutlineDependency(
                item_id=item_id,
                item_type=item_type,
                is_blocking=True
            ))

        return dependencies

    def _infer_item_type(self, item_id: str) -> str:
        """Infer item type from its ID format."""
        parts = item_id.split('.')
        if len(parts) == 1:
            return 'Milestone'
        elif len(parts) == 2:
            return 'Epic'
        elif len(parts) == 3:
            return 'Story'
        else:
            return 'Task'

    def _validate_outline(self, outline: SemanticOutline) -> None:
        """Validate the parsed outline for issues."""

        # Check for missing dependencies
        dep_issues = outline.validate_dependencies()
        for issue in dep_issues:
            self.parse_warnings.append(issue)

        # Check for items without descriptions
        for item_id, item in outline.all_items.items():
            if not item.description.full_text:
                self.parse_warnings.append(
                    f"{item.item_type.value} {item_id} has no description"
                )

        # Check for orphan items (items without children)
        for milestone in outline.milestones:
            if not milestone.children:
                self.parse_warnings.append(
                    f"Milestone {milestone.id} has no epics"
                )

            for epic in milestone.children:
                if not epic.children:
                    self.parse_warnings.append(
                        f"Epic {epic.id} has no stories"
                    )

                for story in epic.children:
                    if not story.children:
                        self.parse_warnings.append(
                            f"Story {story.id} has no tasks"
                        )

        # Check for circular dependencies
        self._check_circular_dependencies(outline)

    def _check_circular_dependencies(self, outline: SemanticOutline) -> None:
        """Check for circular dependency chains."""

        def has_cycle(item_id: str, visited: Set[str], path: Set[str]) -> bool:
            if item_id in path:
                return True
            if item_id in visited:
                return False

            visited.add(item_id)
            path.add(item_id)

            item = outline.get_item_by_id(item_id)
            if item:
                for dep in item.dependencies:
                    if has_cycle(dep.item_id, visited, path):
                        return True

            path.remove(item_id)
            return False

        for item_id in outline.all_items:
            if has_cycle(item_id, set(), set()):
                self.parse_errors.append(
                    f"Circular dependency detected involving {item_id}"
                )

    def has_errors(self) -> bool:
        """Check if there were any parse errors."""
        return len(self.parse_errors) > 0

    def has_warnings(self) -> bool:
        """Check if there were any parse warnings."""
        return len(self.parse_warnings) > 0

    def get_parse_report(self) -> str:
        """Generate a report of parsing results."""
        lines = ["Semantic Outline Parse Report", "=" * 40]

        if self.parse_errors:
            lines.append(f"\n{len(self.parse_errors)} Errors:")
            for error in self.parse_errors:
                lines.append(f"  - {error}")

        if self.parse_warnings:
            lines.append(f"\n{len(self.parse_warnings)} Warnings:")
            for warning in self.parse_warnings:
                lines.append(f"  - {warning}")

        if not self.parse_errors and not self.parse_warnings:
            lines.append("\nNo issues found")

        return "\n".join(lines)
