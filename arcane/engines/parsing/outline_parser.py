"""Outline parser to create roadmap item objects from outline text."""

import re
from typing import List, Dict, Any, Optional
from arcane.items.milestone import Milestone
from arcane.items.epic import Epic
from arcane.items.story import Story
from arcane.items.task import Task
from arcane.items.base import ItemStatus
from ...utils.logging_config import get_logger

logger = get_logger(__name__)


class OutlineParser:
    """Parses outline text and creates a tree of roadmap item objects."""

    def __init__(self):
        self.milestones: List[Milestone] = []

    def parse_outline(self, outline_content: str) -> List[Milestone]:
        """Parse outline content and return list of milestone objects with full hierarchy."""
        self.milestones = []

        # Preprocess to fix common format errors
        outline_content = self._fix_format_issues(outline_content)

        lines = outline_content.split('\n')

        current_milestone = None
        current_epic = None
        current_story = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Skip metadata and single-hash project titles
            if line.startswith('===') or (line.startswith('#') and not line.startswith('##')):
                continue

            # Parse milestone
            milestone_match = re.match(r'^## Milestone (\d+): (.+)', line)
            if milestone_match:
                milestone_number = milestone_match.group(1)
                milestone_name = milestone_match.group(2)
                current_milestone = Milestone(
                    name=milestone_name,
                    number=milestone_number
                )
                current_milestone.update_generation_status(ItemStatus.PENDING)
                self.milestones.append(current_milestone)
                current_epic = None
                current_story = None
                continue

            # Parse epic
            epic_match = re.match(r'^### Epic (\d+\.\d+): (.+)', line)
            if epic_match and current_milestone:
                epic_number = epic_match.group(1)
                epic_name = epic_match.group(2)
                current_epic = Epic(
                    name=epic_name,
                    number=epic_number,
                    parent=current_milestone
                )
                current_epic.update_generation_status(ItemStatus.PENDING)
                current_milestone.add_epic(current_epic)
                current_story = None
                continue

            # Parse story
            story_match = re.match(r'^#### Story (\d+\.\d+\.\d+): (.+)', line)
            if story_match and current_epic:
                story_number = story_match.group(1)
                story_name = story_match.group(2)
                current_story = Story(
                    name=story_name,
                    number=story_number,
                    parent=current_epic
                )
                current_story.update_generation_status(ItemStatus.PENDING)
                current_epic.add_story(current_story)
                continue

            # Parse task
            task_match = re.match(r'^##### Task (\d+\.\d+\.\d+\.\d+): (.+)', line)
            if task_match and current_story:
                task_number = task_match.group(1)
                task_name = task_match.group(2)
                task = Task(
                    name=task_name,
                    number=task_number,
                    parent=current_story
                )
                task.update_generation_status(ItemStatus.PENDING)
                current_story.add_task(task)
                continue

        return self.milestones

    def count_items(self, milestones: List[Milestone]) -> Dict[str, int]:
        """Count total items by type for cost estimation."""
        counts = {
            'milestones': len(milestones),
            'epics': 0,
            'stories': 0,
            'tasks': 0
        }

        for milestone in milestones:
            epics = milestone.get_children_by_type('Epic')
            counts['epics'] += len(epics)

            for epic in epics:
                stories = epic.get_children_by_type('Story')
                counts['stories'] += len(stories)

                for story in stories:
                    tasks = story.get_children_by_type('Task')
                    counts['tasks'] += len(tasks)

        counts['total'] = sum(counts.values())
        return counts

    def validate_structure(self, milestones: List[Milestone]) -> List[str]:
        """Validate the parsed structure and return any issues found."""
        issues = []

        for milestone in milestones:
            # Check milestone ID
            if not milestone.validate_id():
                issues.append(f"Invalid milestone ID: {milestone.id}")

            epics = milestone.get_children_by_type('Epic')
            if not epics:
                issues.append(f"Milestone {milestone.id} has no epics")

            for epic in epics:
                # Check epic ID
                if not epic.validate_id():
                    issues.append(f"Invalid epic ID: {epic.id}")

                # Check epic belongs to correct milestone
                expected_milestone = epic.id.split('.')[0]
                if expected_milestone != milestone.id:
                    issues.append(f"Epic {epic.id} should belong to milestone {expected_milestone}, not {milestone.id}")

                stories = epic.get_children_by_type('Story')
                if not stories:
                    issues.append(f"Epic {epic.id} has no stories")

                for story in stories:
                    # Check story ID
                    if not story.validate_id():
                        issues.append(f"Invalid story ID: {story.id}")

                    # Check story belongs to correct epic
                    expected_epic = '.'.join(story.id.split('.')[:2])
                    if expected_epic != epic.id:
                        issues.append(f"Story {story.id} should belong to epic {expected_epic}, not {epic.id}")

                    tasks = story.get_children_by_type('Task')
                    if not tasks:
                        issues.append(f"Story {story.id} has no tasks")

                    for task in tasks:
                        # Check task ID
                        if not task.validate_id():
                            issues.append(f"Invalid task ID: {task.id}")

                        # Check task belongs to correct story
                        expected_story = '.'.join(task.id.split('.')[:3])
                        if expected_story != story.id:
                            issues.append(f"Task {task.id} should belong to story {expected_story}, not {story.id}")

        return issues

    def get_generation_order(self, milestones: List[Milestone]) -> List[Any]:
        """Get items in the order they should be generated (depth-first)."""
        generation_order = []

        for milestone in milestones:
            generation_order.append(milestone)

            for epic in milestone.get_children_by_type('Epic'):
                generation_order.append(epic)

                for story in epic.get_children_by_type('Story'):
                    generation_order.append(story)
                    # Note: Tasks are generated with their stories, so we don't add them separately

        return generation_order

    def find_item_by_id(self, milestones: List[Milestone], item_id: str) -> Optional[Any]:
        """Find an item by its ID in the milestone tree."""
        # Check milestones
        for milestone in milestones:
            if milestone.id == item_id:
                return milestone

            # Check epics
            for epic in milestone.get_children_by_type('Epic'):
                if epic.id == item_id:
                    return epic

                # Check stories
                for story in epic.get_children_by_type('Story'):
                    if story.id == item_id:
                        return story

                    # Check tasks
                    for task in story.get_children_by_type('Task'):
                        if task.id == item_id:
                            return task

        return None

    def print_structure(self, milestones: List[Milestone]) -> None:
        """Print the parsed structure for debugging."""
        for milestone in milestones:
            logger.debug("📊 %s (ID: %s)", milestone.name, milestone.id)

            for epic in milestone.get_children_by_type('Epic'):
                logger.debug("  📁 %s (ID: %s)", epic.name, epic.id)

                for story in epic.get_children_by_type('Story'):
                    logger.debug("    📄 %s (ID: %s)", story.name, story.id)

                    for task in story.get_children_by_type('Task'):
                        logger.debug("      ✅ %s (ID: %s)", task.name, task.id)

    def _fix_format_issues(self, content: str) -> str:
        """Fix common format issues in outline content."""
        lines = content.split('\n')
        fixed_lines = []

        for line in lines:
            original_line = line
            line = line.strip()

            # Skip empty lines and metadata
            if not line or line.startswith('==='):
                fixed_lines.append(original_line)
                continue

            # Fix milestone format: "## 1. Name" -> "## Milestone 1: Name"
            milestone_fix = re.sub(r'^##\s*(\d+)\.\s*(.+)', r'## Milestone \1: \2', line)
            if milestone_fix != line:
                logger.debug(f"Fixed milestone format: '{line}' -> '{milestone_fix}'")
                fixed_lines.append(milestone_fix)
                continue

            # Fix epic format: "### 1.1. Name" -> "### Epic 1.0: Name"
            epic_fix = re.sub(r'^###\s*(\d+)\.(\d+)\.\s*(.+)', r'### Epic \1.\2: \3', line)
            if epic_fix != line:
                logger.debug(f"Fixed epic format: '{line}' -> '{epic_fix}'")
                fixed_lines.append(epic_fix)
                continue

            # Fix story format: "#### 1.1.1. Name" -> "#### Story 1.1.1: Name"
            story_fix = re.sub(r'^####\s*(\d+)\.(\d+)\.(\d+)\.\s*(.+)', r'#### Story \1.\2.\3: \4', line)
            if story_fix != line:
                logger.debug(f"Fixed story format: '{line}' -> '{story_fix}'")
                fixed_lines.append(story_fix)
                continue

            # Fix task format: "##### 1.1.1.1. Name" -> "##### Task 1.1.1.1: Name"
            task_fix = re.sub(r'^#####\s*(\d+)\.(\d+)\.(\d+)\.(\d+)\.\s*(.+)', r'##### Task \1.\2.\3.\4: \5', line)
            if task_fix != line:
                logger.debug(f"Fixed task format: '{line}' -> '{task_fix}'")
                fixed_lines.append(task_fix)
                continue

            # No changes needed
            fixed_lines.append(original_line)

        return '\n'.join(fixed_lines)