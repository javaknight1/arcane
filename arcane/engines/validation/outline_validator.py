"""Pre-generation outline validation."""

import re
from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
from arcane.utils.logging_config import get_logger

logger = get_logger(__name__)


class OutlineSeverity(Enum):
    """Severity level for outline validation issues."""
    ERROR = "error"      # Must fix before generation
    WARNING = "warning"  # Should fix, but can proceed
    INFO = "info"        # Suggestion for improvement


@dataclass
class OutlineIssue:
    """An outline validation issue."""
    severity: OutlineSeverity
    issue_type: str
    message: str
    line_number: Optional[int] = None
    item_id: Optional[str] = None
    suggested_fix: Optional[str] = None


class OutlineValidator:
    """Validates outline structure before expensive content generation.

    Catches structural issues early using regex-based validation,
    before any LLM calls are made for content generation.
    """

    # Required components for project types
    PROJECT_REQUIREMENTS = {
        'web_app': {
            'required': ['authentication', 'database', 'api'],
            'recommended': ['testing', 'deployment', 'monitoring'],
        },
        'mobile_app': {
            'required': ['authentication', 'api', 'ui'],
            'recommended': ['offline', 'push_notifications', 'testing'],
        },
        'api': {
            'required': ['authentication', 'database', 'api_endpoints'],
            'recommended': ['documentation', 'rate_limiting', 'monitoring'],
        },
        'saas': {
            'required': ['authentication', 'database', 'billing', 'api'],
            'recommended': ['admin_dashboard', 'analytics', 'notifications'],
        },
        'cli_tool': {
            'required': ['core_functionality', 'configuration'],
            'recommended': ['documentation', 'testing', 'packaging'],
        },
    }

    # Keywords that indicate components
    COMPONENT_KEYWORDS = {
        'authentication': ['auth', 'login', 'signup', 'signin', 'password', 'oauth', 'jwt', 'session'],
        'database': ['database', 'db', 'schema', 'migration', 'model', 'postgresql', 'mysql', 'mongodb'],
        'api': ['api', 'endpoint', 'rest', 'graphql', 'route'],
        'api_endpoints': ['endpoint', 'route', 'controller', 'handler'],
        'testing': ['test', 'spec', 'unit test', 'integration test', 'e2e'],
        'deployment': ['deploy', 'ci/cd', 'docker', 'kubernetes', 'infrastructure'],
        'monitoring': ['monitor', 'logging', 'metrics', 'observability', 'alerting'],
        'billing': ['billing', 'payment', 'subscription', 'stripe', 'invoice'],
        'ui': ['ui', 'interface', 'screen', 'component', 'view'],
        'offline': ['offline', 'sync', 'cache', 'local storage'],
        'push_notifications': ['notification', 'push', 'fcm', 'apns'],
        'documentation': ['doc', 'readme', 'guide', 'api doc'],
        'rate_limiting': ['rate limit', 'throttle', 'quota'],
        'admin_dashboard': ['admin', 'dashboard', 'back office'],
        'analytics': ['analytics', 'metrics', 'tracking', 'reporting'],
        'notifications': ['notification', 'email', 'alert'],
        'core_functionality': ['core', 'main', 'primary'],
        'configuration': ['config', 'settings', 'environment'],
        'packaging': ['package', 'publish', 'distribute', 'npm', 'pypi'],
    }

    # Regex patterns for parsing outline items
    MILESTONE_PATTERN = re.compile(r'^##\s*Milestone\s+(\d+):\s*(.+)', re.IGNORECASE)
    EPIC_PATTERN = re.compile(r'^###\s*Epic\s+(\d+\.\d+):\s*(.+)', re.IGNORECASE)
    STORY_PATTERN = re.compile(r'^####\s*Story\s+(\d+\.\d+\.\d+):\s*(.+)', re.IGNORECASE)
    TASK_PATTERN = re.compile(r'^#####\s*Task\s+(\d+\.\d+\.\d+\.\d+):\s*(.+)', re.IGNORECASE)

    def __init__(self):
        self.issues: List[OutlineIssue] = []
        self._parsed_items: Dict[str, Dict] = {}
        self._item_lists: Dict[str, List[Dict]] = {
            'milestones': [],
            'epics': [],
            'stories': [],
            'tasks': [],
        }

    def validate(
        self,
        outline: str,
        project_type: Optional[str] = None
    ) -> List[OutlineIssue]:
        """Run all validations on the outline.

        Args:
            outline: Raw outline text to validate
            project_type: Optional project type for component checking

        Returns:
            List of validation issues found
        """
        self.issues = []
        self._parsed_items = {}
        self._item_lists = {
            'milestones': [],
            'epics': [],
            'stories': [],
            'tasks': [],
        }

        # Parse the outline first
        self._parse_outline(outline)

        # Run structure validations (free, regex-based)
        self._validate_numbering()
        self._validate_hierarchy()
        self._validate_completeness()

        # Run content validations
        self._check_scope_balance()
        if project_type:
            self._check_required_components(outline, project_type)

        # Sort by severity
        self.issues.sort(key=lambda x: (
            0 if x.severity == OutlineSeverity.ERROR else
            1 if x.severity == OutlineSeverity.WARNING else 2
        ))

        return self.issues

    def _parse_outline(self, outline: str) -> None:
        """Parse outline into structured data for validation."""
        lines = outline.split('\n')

        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue

            # Check for milestone
            match = self.MILESTONE_PATTERN.match(line)
            if match:
                item = {
                    'type': 'milestone',
                    'number': match.group(1),
                    'name': match.group(2),
                    'line': line_num,
                    'full_id': match.group(1),
                }
                self._parsed_items[f"M{match.group(1)}"] = item
                self._item_lists['milestones'].append(item)
                continue

            # Check for epic
            match = self.EPIC_PATTERN.match(line)
            if match:
                item = {
                    'type': 'epic',
                    'number': match.group(1),
                    'name': match.group(2),
                    'line': line_num,
                    'full_id': match.group(1),
                    'parent_milestone': match.group(1).split('.')[0],
                }
                self._parsed_items[f"E{match.group(1)}"] = item
                self._item_lists['epics'].append(item)
                continue

            # Check for story
            match = self.STORY_PATTERN.match(line)
            if match:
                parts = match.group(1).split('.')
                item = {
                    'type': 'story',
                    'number': match.group(1),
                    'name': match.group(2),
                    'line': line_num,
                    'full_id': match.group(1),
                    'parent_epic': f"{parts[0]}.{parts[1]}",
                }
                self._parsed_items[f"S{match.group(1)}"] = item
                self._item_lists['stories'].append(item)
                continue

            # Check for task
            match = self.TASK_PATTERN.match(line)
            if match:
                parts = match.group(1).split('.')
                item = {
                    'type': 'task',
                    'number': match.group(1),
                    'name': match.group(2),
                    'line': line_num,
                    'full_id': match.group(1),
                    'parent_story': f"{parts[0]}.{parts[1]}.{parts[2]}",
                }
                self._parsed_items[f"T{match.group(1)}"] = item
                self._item_lists['tasks'].append(item)

    def _validate_numbering(self) -> None:
        """Check for numbering gaps and duplicates."""
        # Use item lists to detect duplicates (dict keys would overwrite)
        milestones = self._item_lists['milestones']
        epics = self._item_lists['epics']
        stories = self._item_lists['stories']
        tasks = self._item_lists['tasks']

        # Check milestone sequence
        self._check_sequence(
            milestones,
            'milestone',
            lambda m: int(m['number'])
        )

        # Check epic sequences within each milestone
        for milestone in milestones:
            milestone_epics = [e for e in epics if e['parent_milestone'] == milestone['number']]
            if milestone_epics:
                self._check_epic_sequence(milestone_epics, milestone['number'])

        # Check story sequences within each epic
        for epic in epics:
            epic_stories = [s for s in stories if s['parent_epic'] == epic['full_id']]
            if epic_stories:
                self._check_story_sequence(epic_stories, epic['full_id'])

        # Check task sequences within each story
        for story in stories:
            story_tasks = [t for t in tasks if t['parent_story'] == story['full_id']]
            if story_tasks:
                self._check_task_sequence(story_tasks, story['full_id'])

    def _check_sequence(
        self,
        items: List[Dict],
        item_type: str,
        key_func
    ) -> None:
        """Check for gaps and duplicates in a number sequence."""
        if not items:
            return

        numbers = [key_func(item) for item in items]

        # Check for duplicates (before sorting/deduping)
        seen = set()
        for num in numbers:
            if num in seen:
                self.issues.append(OutlineIssue(
                    severity=OutlineSeverity.ERROR,
                    issue_type='duplicate_number',
                    message=f"Duplicate {item_type} number: {num}",
                    suggested_fix=f"Renumber {item_type}s to avoid duplicates"
                ))
            seen.add(num)

        # Check for gaps (using unique sorted numbers, should start at 1)
        unique_sorted = sorted(set(numbers))
        expected = 1
        for num in unique_sorted:
            if num != expected:
                self.issues.append(OutlineIssue(
                    severity=OutlineSeverity.WARNING,
                    issue_type='numbering_gap',
                    message=f"Gap in {item_type} numbering: expected {expected}, found {num}",
                    suggested_fix=f"Renumber {item_type}s sequentially starting from 1"
                ))
            expected = num + 1

    def _check_epic_sequence(self, epics: List[Dict], milestone_num: str) -> None:
        """Check epic numbering within a milestone."""
        numbers = []
        for epic in epics:
            parts = epic['full_id'].split('.')
            if len(parts) >= 2:
                numbers.append(int(parts[1]))

        # Check for duplicates first
        seen = set()
        for num in numbers:
            if num in seen:
                self.issues.append(OutlineIssue(
                    severity=OutlineSeverity.ERROR,
                    issue_type='duplicate_number',
                    message=f"Duplicate epic number in Milestone {milestone_num}: {milestone_num}.{num}",
                    suggested_fix="Renumber epics within the milestone"
                ))
            seen.add(num)

        # Check sequence (should start at 0) using unique sorted numbers
        unique_sorted = sorted(set(numbers))
        expected = 0
        for num in unique_sorted:
            if num != expected:
                self.issues.append(OutlineIssue(
                    severity=OutlineSeverity.WARNING,
                    issue_type='numbering_gap',
                    message=f"Gap in epic numbering for Milestone {milestone_num}: expected .{expected}, found .{num}",
                    suggested_fix="Renumber epics sequentially starting from .0"
                ))
            expected = num + 1

    def _check_story_sequence(self, stories: List[Dict], epic_id: str) -> None:
        """Check story numbering within an epic."""
        numbers = []
        for story in stories:
            parts = story['full_id'].split('.')
            if len(parts) >= 3:
                numbers.append(int(parts[2]))

        numbers.sort()

        # Check for duplicates
        seen = set()
        for num in numbers:
            if num in seen:
                self.issues.append(OutlineIssue(
                    severity=OutlineSeverity.ERROR,
                    issue_type='duplicate_number',
                    message=f"Duplicate story number in Epic {epic_id}: {epic_id}.{num}",
                    suggested_fix="Renumber stories within the epic"
                ))
            seen.add(num)

    def _check_task_sequence(self, tasks: List[Dict], story_id: str) -> None:
        """Check task numbering within a story."""
        numbers = []
        for task in tasks:
            parts = task['full_id'].split('.')
            if len(parts) >= 4:
                numbers.append(int(parts[3]))

        numbers.sort()

        # Check for duplicates
        seen = set()
        for num in numbers:
            if num in seen:
                self.issues.append(OutlineIssue(
                    severity=OutlineSeverity.ERROR,
                    issue_type='duplicate_number',
                    message=f"Duplicate task number in Story {story_id}: {story_id}.{num}",
                    suggested_fix="Renumber tasks within the story"
                ))
            seen.add(num)

    def _validate_hierarchy(self) -> None:
        """Check for orphan items without proper parents."""
        milestones = {v['number'] for v in self._parsed_items.values() if v['type'] == 'milestone'}
        epics = {v['full_id'] for v in self._parsed_items.values() if v['type'] == 'epic'}
        stories = {v['full_id'] for v in self._parsed_items.values() if v['type'] == 'story'}

        # Check orphan epics
        for item in self._parsed_items.values():
            if item['type'] == 'epic':
                if item['parent_milestone'] not in milestones:
                    self.issues.append(OutlineIssue(
                        severity=OutlineSeverity.ERROR,
                        issue_type='orphan_item',
                        message=f"Epic {item['full_id']} references non-existent Milestone {item['parent_milestone']}",
                        line_number=item['line'],
                        item_id=item['full_id'],
                        suggested_fix=f"Add Milestone {item['parent_milestone']} or renumber epic"
                    ))

        # Check orphan stories
        for item in self._parsed_items.values():
            if item['type'] == 'story':
                if item['parent_epic'] not in epics:
                    self.issues.append(OutlineIssue(
                        severity=OutlineSeverity.ERROR,
                        issue_type='orphan_item',
                        message=f"Story {item['full_id']} references non-existent Epic {item['parent_epic']}",
                        line_number=item['line'],
                        item_id=item['full_id'],
                        suggested_fix=f"Add Epic {item['parent_epic']} or renumber story"
                    ))

        # Check orphan tasks
        for item in self._parsed_items.values():
            if item['type'] == 'task':
                if item['parent_story'] not in stories:
                    self.issues.append(OutlineIssue(
                        severity=OutlineSeverity.ERROR,
                        issue_type='orphan_item',
                        message=f"Task {item['full_id']} references non-existent Story {item['parent_story']}",
                        line_number=item['line'],
                        item_id=item['full_id'],
                        suggested_fix=f"Add Story {item['parent_story']} or renumber task"
                    ))

    def _validate_completeness(self) -> None:
        """Check for empty containers."""
        milestones = [v for v in self._parsed_items.values() if v['type'] == 'milestone']
        epics = [v for v in self._parsed_items.values() if v['type'] == 'epic']
        stories = [v for v in self._parsed_items.values() if v['type'] == 'story']
        tasks = [v for v in self._parsed_items.values() if v['type'] == 'task']

        # Check if outline has any content
        if not milestones:
            self.issues.append(OutlineIssue(
                severity=OutlineSeverity.ERROR,
                issue_type='empty_outline',
                message="Outline has no milestones",
                suggested_fix="Add at least one milestone with the format: ## Milestone 1: Name"
            ))
            return

        # Check milestones have epics
        epic_parents = {e['parent_milestone'] for e in epics}
        for milestone in milestones:
            if milestone['number'] not in epic_parents:
                self.issues.append(OutlineIssue(
                    severity=OutlineSeverity.WARNING,
                    issue_type='empty_milestone',
                    message=f"Milestone {milestone['number']} has no epics",
                    line_number=milestone['line'],
                    item_id=milestone['number'],
                    suggested_fix="Add epics to this milestone"
                ))

        # Check epics have stories
        story_parents = {s['parent_epic'] for s in stories}
        for epic in epics:
            if epic['full_id'] not in story_parents:
                self.issues.append(OutlineIssue(
                    severity=OutlineSeverity.WARNING,
                    issue_type='empty_epic',
                    message=f"Epic {epic['full_id']} has no stories",
                    line_number=epic['line'],
                    item_id=epic['full_id'],
                    suggested_fix="Add stories to this epic"
                ))

        # Check stories have tasks (optional - INFO level)
        task_parents = {t['parent_story'] for t in tasks}
        for story in stories:
            if story['full_id'] not in task_parents:
                self.issues.append(OutlineIssue(
                    severity=OutlineSeverity.INFO,
                    issue_type='story_no_tasks',
                    message=f"Story {story['full_id']} has no predefined tasks (will be generated)",
                    line_number=story['line'],
                    item_id=story['full_id']
                ))

    def _check_scope_balance(self) -> None:
        """Check for imbalanced milestones."""
        milestones = [v for v in self._parsed_items.values() if v['type'] == 'milestone']
        epics = [v for v in self._parsed_items.values() if v['type'] == 'epic']
        stories = [v for v in self._parsed_items.values() if v['type'] == 'story']

        if len(milestones) < 2:
            return  # Need at least 2 milestones to compare

        # Count items per milestone
        items_per_milestone = defaultdict(int)
        for epic in epics:
            items_per_milestone[epic['parent_milestone']] += 1
        for story in stories:
            milestone = story['full_id'].split('.')[0]
            items_per_milestone[milestone] += 1

        counts = list(items_per_milestone.values())
        if not counts:
            return

        avg_count = sum(counts) / len(counts)
        max_count = max(counts)
        min_count = min(counts)

        # Flag significantly unbalanced milestones
        for milestone in milestones:
            count = items_per_milestone.get(milestone['number'], 0)

            # Too few items (less than 30% of average)
            if count < avg_count * 0.3 and count < 3:
                self.issues.append(OutlineIssue(
                    severity=OutlineSeverity.WARNING,
                    issue_type='unbalanced_milestone',
                    message=f"Milestone {milestone['number']} has only {count} items (avg: {avg_count:.1f})",
                    line_number=milestone['line'],
                    item_id=milestone['number'],
                    suggested_fix="Consider combining with another milestone or adding more content"
                ))

            # Too many items (more than 200% of average)
            elif count > avg_count * 2 and count > 10:
                self.issues.append(OutlineIssue(
                    severity=OutlineSeverity.WARNING,
                    issue_type='unbalanced_milestone',
                    message=f"Milestone {milestone['number']} has {count} items (avg: {avg_count:.1f})",
                    line_number=milestone['line'],
                    item_id=milestone['number'],
                    suggested_fix="Consider splitting into multiple milestones"
                ))

    def _check_required_components(
        self,
        outline: str,
        project_type: str
    ) -> None:
        """Check if outline contains required components for project type."""
        if project_type not in self.PROJECT_REQUIREMENTS:
            return

        outline_lower = outline.lower()
        requirements = self.PROJECT_REQUIREMENTS[project_type]

        # Check required components
        for component in requirements.get('required', []):
            if not self._component_present(outline_lower, component):
                self.issues.append(OutlineIssue(
                    severity=OutlineSeverity.WARNING,
                    issue_type='missing_component',
                    message=f"Missing required component for {project_type}: {component}",
                    suggested_fix=f"Consider adding {component} functionality to your roadmap"
                ))

        # Check recommended components
        for component in requirements.get('recommended', []):
            if not self._component_present(outline_lower, component):
                self.issues.append(OutlineIssue(
                    severity=OutlineSeverity.INFO,
                    issue_type='missing_recommended',
                    message=f"Recommended component for {project_type} not found: {component}",
                    suggested_fix=f"Consider adding {component} for a more complete solution"
                ))

    def _component_present(self, outline_lower: str, component: str) -> bool:
        """Check if a component is present in the outline."""
        keywords = self.COMPONENT_KEYWORDS.get(component, [component])
        return any(kw in outline_lower for kw in keywords)

    def has_errors(self) -> bool:
        """Check if any ERROR-level issues were found."""
        return any(issue.severity == OutlineSeverity.ERROR for issue in self.issues)

    def has_warnings(self) -> bool:
        """Check if any WARNING-level issues were found."""
        return any(issue.severity == OutlineSeverity.WARNING for issue in self.issues)

    def get_summary(self) -> Dict[str, int]:
        """Get summary of issue counts by severity."""
        summary = {'errors': 0, 'warnings': 0, 'info': 0}
        for issue in self.issues:
            if issue.severity == OutlineSeverity.ERROR:
                summary['errors'] += 1
            elif issue.severity == OutlineSeverity.WARNING:
                summary['warnings'] += 1
            else:
                summary['info'] += 1
        return summary

    def format_issues(self, show_info: bool = False) -> str:
        """Format issues for display.

        Args:
            show_info: Whether to include INFO-level issues

        Returns:
            Formatted string of issues
        """
        lines = []

        for issue in self.issues:
            if issue.severity == OutlineSeverity.INFO and not show_info:
                continue

            if issue.severity == OutlineSeverity.ERROR:
                prefix = "[red]ERROR[/red]"
            elif issue.severity == OutlineSeverity.WARNING:
                prefix = "[yellow]WARNING[/yellow]"
            else:
                prefix = "[dim]INFO[/dim]"

            line = f"{prefix}: {issue.message}"
            if issue.line_number:
                line += f" (line {issue.line_number})"
            if issue.suggested_fix:
                line += f"\n  → {issue.suggested_fix}"

            lines.append(line)

        return "\n".join(lines)
