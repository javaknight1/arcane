"""Cross-reference validation for roadmap coherence."""

import re
from typing import List, Dict, Set, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
from difflib import SequenceMatcher

from arcane.items.roadmap import Roadmap
from arcane.items.base import Item
from arcane.utils.logging_config import get_logger

logger = get_logger(__name__)


class CoherenceSeverity(Enum):
    """Severity level for coherence issues."""
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


@dataclass
class CoherenceIssue:
    """A coherence-related issue found during cross-reference validation."""
    severity: CoherenceSeverity
    item_id: str
    issue_type: str
    description: str
    related_item_id: Optional[str] = None
    suggestion: Optional[str] = None
    auto_fixable: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'severity': self.severity.value,
            'item_id': self.item_id,
            'issue_type': self.issue_type,
            'description': self.description,
            'related_item_id': self.related_item_id,
            'suggestion': self.suggestion,
            'auto_fixable': self.auto_fixable,
        }


class CrossReferenceValidator:
    """Validates coherence across generated roadmap.

    Performs post-generation validation to ensure:
    - Tasks actually complete their parent stories
    - No duplicate or redundant work items
    - All dependencies reference existing items
    - Scope and naming are consistent
    """

    # Common stop words to exclude from keyword extraction
    STOP_WORDS = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
        'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
        'would', 'could', 'should', 'may', 'might', 'must', 'shall', 'can',
        'this', 'that', 'these', 'those', 'it', 'its', 'they', 'them', 'their',
        'all', 'each', 'every', 'both', 'few', 'more', 'most', 'other', 'some',
        'such', 'no', 'not', 'only', 'same', 'so', 'than', 'too', 'very',
        'just', 'also', 'now', 'new', 'first', 'last', 'one', 'two', 'three',
        'implement', 'create', 'add', 'setup', 'configure', 'build', 'develop',
        'design', 'define', 'write', 'update', 'task', 'story', 'epic',
    }

    # Minimum similarity threshold for duplicate detection
    SIMILARITY_THRESHOLD = 0.8

    # Minimum keyword overlap for task-story alignment
    MIN_KEYWORD_OVERLAP = 2

    def __init__(self):
        self.issues: List[CoherenceIssue] = []
        self._item_lookup: Dict[str, Item] = {}

    def validate_roadmap(self, roadmap: Roadmap) -> List[CoherenceIssue]:
        """Run all cross-reference validations on the roadmap.

        Args:
            roadmap: The roadmap to validate

        Returns:
            List of coherence issues found
        """
        self.issues = []
        self._build_item_lookup(roadmap)

        # Run all validations
        self.issues.extend(self._validate_task_story_alignment(roadmap))
        self.issues.extend(self._validate_no_duplicate_work(roadmap))
        self.issues.extend(self._validate_dependencies_exist(roadmap))
        self.issues.extend(self._validate_scope_consistency(roadmap))

        return self.issues

    def _build_item_lookup(self, roadmap: Roadmap) -> None:
        """Build lookup dictionary of all items by ID."""
        self._item_lookup = {}
        for item in roadmap.get_all_items():
            self._item_lookup[item.id] = item

    def _validate_task_story_alignment(self, roadmap: Roadmap) -> List[CoherenceIssue]:
        """Check that tasks actually complete their parent stories.

        Validates:
        - Every story has at least one task
        - Task names/descriptions have keyword overlap with story
        """
        issues = []

        for story in roadmap.get_stories():
            tasks = story.get_children_by_type('Task')

            # Check for missing tasks
            if not tasks:
                issues.append(CoherenceIssue(
                    severity=CoherenceSeverity.CRITICAL,
                    item_id=story.id,
                    issue_type='missing_tasks',
                    description=f"Story '{story.name}' has no tasks",
                    suggestion="Add tasks to implement this story",
                    auto_fixable=True
                ))
                continue

            # Check keyword overlap between story and tasks
            story_text = f"{story.name} {story.description or ''}"
            story_keywords = self._extract_keywords(story_text)

            task_keywords: Set[str] = set()
            for task in tasks:
                task_text = f"{task.name} {task.description or ''}"
                task_keywords.update(self._extract_keywords(task_text))

            overlap = story_keywords & task_keywords

            if len(overlap) < self.MIN_KEYWORD_OVERLAP:
                issues.append(CoherenceIssue(
                    severity=CoherenceSeverity.WARNING,
                    item_id=story.id,
                    issue_type='task_story_mismatch',
                    description=f"Tasks may not align with story intent for '{story.name}'",
                    suggestion="Review tasks to ensure they implement the story requirements",
                    auto_fixable=True
                ))

        return issues

    def _validate_no_duplicate_work(self, roadmap: Roadmap) -> List[CoherenceIssue]:
        """Check for duplicate or redundant work items.

        Uses string similarity to detect items with very similar names.
        """
        issues = []
        all_items = self._get_comparable_items(roadmap)
        seen_pairs: Set[Tuple[str, str]] = set()

        for i, (id1, name1, type1) in enumerate(all_items):
            for id2, name2, type2 in all_items[i + 1:]:
                # Skip if we've already reported this pair
                pair_key = tuple(sorted([id1, id2]))
                if pair_key in seen_pairs:
                    continue

                # Calculate similarity
                similarity = SequenceMatcher(
                    None,
                    name1.lower(),
                    name2.lower()
                ).ratio()

                if similarity > self.SIMILARITY_THRESHOLD:
                    seen_pairs.add(pair_key)
                    truncated_name = name2[:40] + '...' if len(name2) > 40 else name2
                    issues.append(CoherenceIssue(
                        severity=CoherenceSeverity.WARNING,
                        item_id=id1,
                        issue_type='potential_duplicate',
                        description=f"Similar to {type2} {id2}: '{truncated_name}' ({similarity:.0%} similar)",
                        related_item_id=id2,
                        suggestion="Consider consolidating or differentiating these items"
                    ))

        return issues

    def _validate_dependencies_exist(self, roadmap: Roadmap) -> List[CoherenceIssue]:
        """Check that all dependency references point to existing items."""
        issues = []

        for item in roadmap.get_all_items():
            # Check depends_on_items (linked Item objects)
            depends_on = getattr(item, 'depends_on_items', [])
            for dep_item in depends_on:
                dep_id = dep_item.id if hasattr(dep_item, 'id') else str(dep_item)
                if dep_id not in self._item_lookup:
                    issues.append(CoherenceIssue(
                        severity=CoherenceSeverity.CRITICAL,
                        item_id=item.id,
                        issue_type='invalid_dependency',
                        description=f"References non-existent dependency: {dep_id}",
                        related_item_id=dep_id,
                        suggestion="Remove or correct the dependency reference"
                    ))

            # Check dependency_ids (string IDs)
            dep_ids = getattr(item, 'dependency_ids', [])
            for dep_id in dep_ids:
                if dep_id not in self._item_lookup:
                    issues.append(CoherenceIssue(
                        severity=CoherenceSeverity.CRITICAL,
                        item_id=item.id,
                        issue_type='invalid_dependency',
                        description=f"References non-existent dependency: {dep_id}",
                        related_item_id=dep_id,
                        suggestion="Remove or correct the dependency reference"
                    ))

        return issues

    def _validate_scope_consistency(self, roadmap: Roadmap) -> List[CoherenceIssue]:
        """Check for scope consistency across the roadmap.

        Validates:
        - Epics have a reasonable number of stories (not too few or too many)
        - Stories have a reasonable number of tasks
        - Item names follow consistent patterns
        """
        issues = []

        # Check epic scope
        for epic in roadmap.get_epics():
            stories = epic.get_children_by_type('Story')
            story_count = len(stories)

            if story_count == 0:
                issues.append(CoherenceIssue(
                    severity=CoherenceSeverity.CRITICAL,
                    item_id=epic.id,
                    issue_type='empty_epic',
                    description=f"Epic '{epic.name}' has no stories",
                    suggestion="Add stories to break down this epic",
                    auto_fixable=True
                ))
            elif story_count == 1:
                issues.append(CoherenceIssue(
                    severity=CoherenceSeverity.INFO,
                    item_id=epic.id,
                    issue_type='single_story_epic',
                    description=f"Epic '{epic.name}' has only 1 story",
                    suggestion="Consider if this epic is appropriately scoped"
                ))
            elif story_count > 10:
                issues.append(CoherenceIssue(
                    severity=CoherenceSeverity.WARNING,
                    item_id=epic.id,
                    issue_type='oversized_epic',
                    description=f"Epic '{epic.name}' has {story_count} stories (>10)",
                    suggestion="Consider splitting into multiple epics"
                ))

        # Check story scope
        for story in roadmap.get_stories():
            tasks = story.get_children_by_type('Task')
            task_count = len(tasks)

            if task_count > 8:
                issues.append(CoherenceIssue(
                    severity=CoherenceSeverity.WARNING,
                    item_id=story.id,
                    issue_type='oversized_story',
                    description=f"Story '{story.name}' has {task_count} tasks (>8)",
                    suggestion="Consider splitting into multiple stories"
                ))

        # Check naming consistency
        issues.extend(self._check_naming_patterns(roadmap))

        return issues

    def _check_naming_patterns(self, roadmap: Roadmap) -> List[CoherenceIssue]:
        """Check for naming pattern consistency."""
        issues = []

        # Detect common prefixes in story names that might indicate poor scoping
        story_names = [s.name for s in roadmap.get_stories()]
        prefix_counts: Dict[str, int] = {}

        for name in story_names:
            # Extract potential prefix (first 2-3 words)
            words = name.split()[:3]
            if len(words) >= 2:
                prefix = ' '.join(words[:2]).lower()
                prefix_counts[prefix] = prefix_counts.get(prefix, 0) + 1

        # Flag if many stories share the same prefix
        for prefix, count in prefix_counts.items():
            if count >= 4:  # More than 4 stories with same prefix
                issues.append(CoherenceIssue(
                    severity=CoherenceSeverity.INFO,
                    item_id='roadmap',
                    issue_type='repetitive_naming',
                    description=f"{count} stories start with '{prefix}'",
                    suggestion="Consider using more descriptive, unique names"
                ))

        return issues

    def _extract_keywords(self, text: str) -> Set[str]:
        """Extract meaningful keywords from text.

        Args:
            text: Text to extract keywords from

        Returns:
            Set of lowercase keywords
        """
        # Tokenize and normalize
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())

        # Filter stop words and return unique keywords
        return {w for w in words if w not in self.STOP_WORDS}

    def _get_comparable_items(self, roadmap: Roadmap) -> List[Tuple[str, str, str]]:
        """Get all items in a format suitable for comparison.

        Returns:
            List of (id, name, type) tuples
        """
        items = []
        for item in roadmap.get_all_items():
            # Skip project-level item
            if item.item_type.lower() == 'project':
                continue
            items.append((item.id, item.name, item.item_type))
        return items

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of validation results."""
        by_severity = {s: 0 for s in CoherenceSeverity}
        by_type: Dict[str, int] = {}

        for issue in self.issues:
            by_severity[issue.severity] += 1
            by_type[issue.issue_type] = by_type.get(issue.issue_type, 0) + 1

        return {
            'total_issues': len(self.issues),
            'by_severity': {s.value: c for s, c in by_severity.items()},
            'by_type': by_type,
            'items_validated': len(self._item_lookup),
        }

    def get_critical_issues(self) -> List[CoherenceIssue]:
        """Get only critical issues."""
        return [i for i in self.issues if i.severity == CoherenceSeverity.CRITICAL]

    def has_critical_issues(self) -> bool:
        """Check if any critical issues were found."""
        return any(i.severity == CoherenceSeverity.CRITICAL for i in self.issues)

    def format_report(self) -> str:
        """Format validation results as a human-readable report."""
        lines = [
            "Cross-Reference Validation Report",
            "=" * 50,
        ]

        summary = self.get_summary()
        lines.extend([
            f"\nItems validated: {summary['items_validated']}",
            f"Total issues: {summary['total_issues']}",
            f"  Critical: {summary['by_severity']['critical']}",
            f"  Warning: {summary['by_severity']['warning']}",
            f"  Info: {summary['by_severity']['info']}",
        ])

        if self.issues:
            lines.append("\n" + "-" * 50)

            # Group by severity
            for severity in [CoherenceSeverity.CRITICAL, CoherenceSeverity.WARNING, CoherenceSeverity.INFO]:
                severity_issues = [i for i in self.issues if i.severity == severity]
                if not severity_issues:
                    continue

                icon = {
                    CoherenceSeverity.CRITICAL: "CRITICAL",
                    CoherenceSeverity.WARNING: "WARNING",
                    CoherenceSeverity.INFO: "INFO"
                }[severity]

                lines.append(f"\n{icon} ({len(severity_issues)}):")

                for issue in severity_issues:
                    lines.append(f"  [{issue.item_id}] {issue.issue_type}")
                    lines.append(f"    {issue.description}")
                    if issue.suggestion:
                        lines.append(f"    -> {issue.suggestion}")
        else:
            lines.append("\nNo coherence issues found!")

        return "\n".join(lines)

    def get_auto_fixable_issues(self) -> List[CoherenceIssue]:
        """Get all issues that can be automatically fixed."""
        return [i for i in self.issues if i.auto_fixable]


class CoherenceAutoFixer:
    """Automatically fixes coherence issues by regenerating problematic items.

    This class attempts to fix auto-fixable coherence issues by:
    - Regenerating missing tasks for stories
    - Regenerating tasks that don't align with story intent
    - Generating stories for empty epics
    """

    # Template for regenerating aligned tasks
    ALIGNED_TASK_PROMPT = """
The following story needs tasks regenerated to better align with its description and acceptance criteria.

Story: {story_name}
Description: {story_description}
Acceptance Criteria:
{acceptance_criteria}

Generate 3-5 tasks that DIRECTLY address the acceptance criteria.
Each task should:
- Have a clear, actionable title
- Directly implement part of the story
- Be specific enough to complete in 1-4 hours

Format each task as:
###TASK_START### [task_id]
TASK_TITLE: [title]
TASK_GOAL: [what this task accomplishes]
TASK_DURATION_HOURS: [1-4]
###TASK_END###
"""

    # Template for generating stories for empty epic
    EPIC_STORIES_PROMPT = """
The following epic needs stories to break down its scope.

Epic: {epic_name}
Description: {epic_description}

Generate 2-4 user stories that implement this epic.
Each story should:
- Focus on a specific piece of functionality
- Be completable in 1-2 sprints
- Have clear acceptance criteria

Format each story as:
###STORY_START### [story_id like {next_story_prefix}.1]
STORY_TITLE: [title]
STORY_DESCRIPTION: [description]
ACCEPTANCE_CRITERIA:
- [criterion 1]
- [criterion 2]
- [criterion 3]
###STORY_END###
"""

    def __init__(self, llm_client, generator=None):
        """Initialize the auto-fixer.

        Args:
            llm_client: LLM client for generating content
            generator: Optional roadmap generator for advanced fixes
        """
        self.llm_client = llm_client
        self.generator = generator
        self._item_lookup: Dict[str, Item] = {}

    def fix_issues(
        self,
        roadmap: Roadmap,
        issues: List[CoherenceIssue],
        max_fixes: int = 10
    ) -> Dict[str, Any]:
        """Attempt to fix auto-fixable issues.

        Args:
            roadmap: The roadmap to fix
            issues: List of coherence issues to fix
            max_fixes: Maximum number of fixes to attempt

        Returns:
            Dictionary with fix results:
            - fixed: Number of successfully fixed issues
            - failed: Number of failed fix attempts
            - skipped: Number of skipped (non-auto-fixable) issues
            - details: List of fix details
        """
        self._build_item_lookup(roadmap)

        results = {
            'fixed': 0,
            'failed': 0,
            'skipped': 0,
            'details': []
        }

        fixes_attempted = 0

        for issue in issues:
            if fixes_attempted >= max_fixes:
                logger.info(f"Reached max fixes limit ({max_fixes})")
                break

            if not issue.auto_fixable:
                results['skipped'] += 1
                continue

            fixes_attempted += 1
            fix_result = self._fix_issue(roadmap, issue)

            if fix_result['success']:
                results['fixed'] += 1
            else:
                results['failed'] += 1

            results['details'].append(fix_result)

        return results

    def _build_item_lookup(self, roadmap: Roadmap) -> None:
        """Build lookup dictionary of all items by ID."""
        self._item_lookup = {}
        for item in roadmap.get_all_items():
            self._item_lookup[item.id] = item

    def _fix_issue(self, roadmap: Roadmap, issue: CoherenceIssue) -> Dict[str, Any]:
        """Fix a single issue.

        Args:
            roadmap: The roadmap containing the item
            issue: The issue to fix

        Returns:
            Dictionary with fix result
        """
        result = {
            'issue_type': issue.issue_type,
            'item_id': issue.item_id,
            'success': False,
            'message': ''
        }

        try:
            if issue.issue_type == 'missing_tasks':
                success = self._regenerate_story_tasks(roadmap, issue.item_id)
                result['success'] = success
                result['message'] = "Tasks regenerated" if success else "Failed to regenerate tasks"

            elif issue.issue_type == 'task_story_mismatch':
                success = self._regenerate_aligned_tasks(roadmap, issue.item_id)
                result['success'] = success
                result['message'] = "Tasks realigned" if success else "Failed to realign tasks"

            elif issue.issue_type == 'empty_epic':
                success = self._regenerate_epic_stories(roadmap, issue.item_id)
                result['success'] = success
                result['message'] = "Stories generated" if success else "Failed to generate stories"

            else:
                result['message'] = f"Unknown issue type: {issue.issue_type}"

        except Exception as e:
            result['message'] = f"Error: {str(e)}"
            logger.error(f"Error fixing issue {issue.issue_type} for {issue.item_id}: {e}")

        return result

    def _find_item(self, roadmap: Roadmap, item_id: str) -> Optional[Item]:
        """Find an item by ID in the roadmap."""
        return self._item_lookup.get(item_id)

    def _regenerate_story_tasks(self, roadmap: Roadmap, story_id: str) -> bool:
        """Regenerate tasks for a story that has none.

        Args:
            roadmap: The roadmap containing the story
            story_id: ID of the story

        Returns:
            True if successful, False otherwise
        """
        story = self._find_item(roadmap, story_id)
        if not story:
            logger.warning(f"Story {story_id} not found")
            return False

        # Build prompt
        acceptance_criteria = getattr(story, 'acceptance_criteria', [])
        if not acceptance_criteria:
            acceptance_criteria = getattr(story, 'success_criteria', [])

        ac_text = '\n'.join(f"- {ac}" for ac in acceptance_criteria) if acceptance_criteria else "- Not specified"

        prompt = self.ALIGNED_TASK_PROMPT.format(
            story_name=story.name,
            story_description=story.description or "No description",
            acceptance_criteria=ac_text
        )

        # Generate tasks
        try:
            response = self.llm_client.generate(prompt)

            # Parse and add tasks
            if hasattr(story, 'parse_tasks_content'):
                story.parse_tasks_content(response)

                # Check if tasks were added
                tasks = story.get_children_by_type('Task')
                if tasks:
                    logger.info(f"Generated {len(tasks)} tasks for story {story_id}")
                    return True

            return False
        except Exception as e:
            logger.error(f"Failed to regenerate tasks for {story_id}: {e}")
            return False

    def _regenerate_aligned_tasks(self, roadmap: Roadmap, story_id: str) -> bool:
        """Regenerate tasks for a story with misaligned tasks.

        Args:
            roadmap: The roadmap containing the story
            story_id: ID of the story

        Returns:
            True if successful, False otherwise
        """
        story = self._find_item(roadmap, story_id)
        if not story:
            logger.warning(f"Story {story_id} not found")
            return False

        # Clear existing tasks
        story.children = [c for c in story.children if c.item_type != 'Task']

        # Use same logic as regenerate_story_tasks
        return self._regenerate_story_tasks(roadmap, story_id)

    def _regenerate_epic_stories(self, roadmap: Roadmap, epic_id: str) -> bool:
        """Generate stories for an empty epic.

        Args:
            roadmap: The roadmap containing the epic
            epic_id: ID of the epic

        Returns:
            True if successful, False otherwise
        """
        epic = self._find_item(roadmap, epic_id)
        if not epic:
            logger.warning(f"Epic {epic_id} not found")
            return False

        # Build prompt
        prompt = self.EPIC_STORIES_PROMPT.format(
            epic_name=epic.name,
            epic_description=epic.description or "No description",
            next_story_prefix=epic_id
        )

        try:
            response = self.llm_client.generate(prompt)

            # Parse stories from response
            stories_created = self._parse_and_add_stories(epic, response)

            if stories_created > 0:
                logger.info(f"Generated {stories_created} stories for epic {epic_id}")
                return True

            return False
        except Exception as e:
            logger.error(f"Failed to regenerate stories for {epic_id}: {e}")
            return False

    def _parse_and_add_stories(self, epic: Item, response: str) -> int:
        """Parse story blocks from response and add to epic.

        Args:
            epic: The epic to add stories to
            response: LLM response containing story blocks

        Returns:
            Number of stories created
        """
        import re
        from arcane.items.story import Story

        story_pattern = r'###STORY_START###\s*(\S+)(.*?)###STORY_END###'
        matches = re.findall(story_pattern, response, re.DOTALL)

        stories_created = 0

        for story_id, story_content in matches:
            story_id = story_id.strip()

            # Extract title
            title_match = re.search(r'STORY_TITLE:\s*(.+?)(?:\n|$)', story_content)
            title = title_match.group(1).strip() if title_match else f"Story {story_id}"

            # Extract description
            desc_match = re.search(r'STORY_DESCRIPTION:\s*(.+?)(?=\n[A-Z_]+:|$)', story_content, re.DOTALL)
            description = desc_match.group(1).strip() if desc_match else ""

            # Extract acceptance criteria
            ac_match = re.search(r'ACCEPTANCE_CRITERIA:\s*(.+?)(?=\n[A-Z_]+:|$)', story_content, re.DOTALL)
            acceptance_criteria = []
            if ac_match:
                ac_text = ac_match.group(1)
                for line in ac_text.split('\n'):
                    line = line.strip()
                    if line.startswith('-'):
                        acceptance_criteria.append(line[1:].strip())

            try:
                story = Story(
                    name=title,
                    number=story_id,
                    parent=epic,
                    description=description
                )
                story.acceptance_criteria = acceptance_criteria
                epic.add_child(story)
                stories_created += 1
            except ValueError as e:
                logger.warning(f"Invalid story ID {story_id}: {e}")
                continue

        return stories_created

    def get_fix_summary(self, results: Dict[str, Any]) -> str:
        """Format fix results as a summary string.

        Args:
            results: Results from fix_issues()

        Returns:
            Formatted summary string
        """
        lines = [
            "Auto-Fix Summary",
            "=" * 30,
            f"Fixed: {results['fixed']}",
            f"Failed: {results['failed']}",
            f"Skipped: {results['skipped']}",
        ]

        if results['details']:
            lines.append("\nDetails:")
            for detail in results['details']:
                status = "OK" if detail['success'] else "FAILED"
                lines.append(f"  [{status}] {detail['item_id']}: {detail['message']}")

        return "\n".join(lines)
