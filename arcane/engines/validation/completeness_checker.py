"""Completeness validation for roadmap items."""

import re
from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from arcane.items.milestone import Milestone
from arcane.items.epic import Epic
from arcane.items.story import Story
from arcane.items.task import Task
from arcane.items.base import Item
from arcane.utils.logging_config import get_logger

logger = get_logger(__name__)


class CompletenessSeverity(Enum):
    """Severity level for completeness issues."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class CompletenessIssue:
    """A completeness-related issue."""
    severity: CompletenessSeverity
    item_id: str
    issue_type: str
    description: str
    suggested_fix: Optional[str] = None
    related_items: List[str] = field(default_factory=list)
    coverage_percentage: Optional[float] = None


@dataclass
class CoverageMapping:
    """Maps tasks to acceptance criteria they cover."""
    story_id: str
    criteria_count: int
    task_count: int
    coverage: Dict[int, List[str]]  # criterion index -> list of task IDs
    uncovered_criteria: List[int]  # indices of uncovered criteria
    coverage_percentage: float


@dataclass
class TaskSuggestion:
    """A suggested task to improve coverage."""
    criterion_index: int
    criterion_text: str
    suggested_title: str
    suggested_goal: str
    work_type: str
    complexity: str


class CompletenessChecker:
    """Validates completeness of roadmap items."""

    # Keywords that suggest task types
    TASK_TYPE_KEYWORDS = {
        'implementation': ['create', 'build', 'implement', 'develop', 'add', 'integrate'],
        'testing': ['test', 'verify', 'validate', 'check', 'ensure', 'confirm'],
        'design': ['design', 'architect', 'plan', 'define', 'specify'],
        'documentation': ['document', 'write', 'describe', 'explain'],
        'configuration': ['configure', 'setup', 'set up', 'install', 'deploy'],
        'research': ['research', 'investigate', 'analyze', 'evaluate', 'assess'],
    }

    # Keywords that indicate complexity
    COMPLEXITY_KEYWORDS = {
        'simple': ['simple', 'basic', 'minor', 'small', 'quick', 'trivial'],
        'complex': ['complex', 'advanced', 'comprehensive', 'extensive', 'major', 'full'],
    }

    def __init__(self):
        self.issues: List[CompletenessIssue] = []

    def check_all(self, milestones: List[Milestone]) -> List[CompletenessIssue]:
        """Run all completeness checks on the roadmap.

        Args:
            milestones: List of milestone objects to validate

        Returns:
            List of completeness issues found
        """
        self.issues = []

        for milestone in milestones:
            self._check_milestone_completeness(milestone)

            for epic in milestone.get_children_by_type('Epic'):
                self._check_epic_completeness(epic)

                for story in epic.get_children_by_type('Story'):
                    self.issues.extend(self.check_story_task_alignment(story))

        return self.issues

    def _check_milestone_completeness(self, milestone: Milestone) -> None:
        """Check milestone has sufficient epics."""
        epics = milestone.get_children_by_type('Epic')

        if len(epics) == 0:
            self.issues.append(CompletenessIssue(
                severity=CompletenessSeverity.ERROR,
                item_id=milestone.id,
                issue_type='empty_milestone',
                description=f"Milestone '{milestone.name}' has no epics",
                suggested_fix="Add at least one epic to this milestone"
            ))

    def _check_epic_completeness(self, epic: Epic) -> None:
        """Check epic has sufficient stories."""
        stories = epic.get_children_by_type('Story')

        if len(stories) == 0:
            self.issues.append(CompletenessIssue(
                severity=CompletenessSeverity.ERROR,
                item_id=epic.id,
                issue_type='empty_epic',
                description=f"Epic '{epic.name}' has no stories",
                suggested_fix="Add at least one story to this epic"
            ))
        else:
            # Check epic-story coverage
            self.issues.extend(self.check_epic_story_coverage(epic))

    def check_story_task_alignment(self, story: Story) -> List[CompletenessIssue]:
        """Verify tasks cover all acceptance criteria.

        Args:
            story: Story to check

        Returns:
            List of completeness issues for this story
        """
        issues = []

        # Get acceptance criteria
        criteria = getattr(story, 'acceptance_criteria', [])
        if not criteria:
            # Try success_criteria as fallback
            criteria = getattr(story, 'success_criteria', [])

        tasks = story.get_children_by_type('Task')

        # Check for empty story
        if len(tasks) == 0:
            issues.append(CompletenessIssue(
                severity=CompletenessSeverity.ERROR,
                item_id=story.id,
                issue_type='empty_story',
                description=f"Story '{story.name}' has no tasks",
                suggested_fix="Add tasks to implement this story"
            ))
            return issues

        # Skip if no acceptance criteria defined
        if not criteria:
            issues.append(CompletenessIssue(
                severity=CompletenessSeverity.INFO,
                item_id=story.id,
                issue_type='no_criteria',
                description=f"Story '{story.name}' has no acceptance criteria defined",
                suggested_fix="Define acceptance criteria to validate task coverage"
            ))
            return issues

        # Build coverage map
        coverage = self._map_tasks_to_criteria(story)

        # Find uncovered criteria
        for i, criterion in enumerate(criteria):
            if i not in coverage.coverage or not coverage.coverage[i]:
                criterion_preview = criterion[:60] + "..." if len(criterion) > 60 else criterion
                issues.append(CompletenessIssue(
                    severity=CompletenessSeverity.WARNING,
                    item_id=story.id,
                    issue_type='uncovered_criterion',
                    description=f"AC{i+1} not covered by any task: {criterion_preview}",
                    suggested_fix="Add a task to address this acceptance criterion",
                    coverage_percentage=coverage.coverage_percentage
                ))

        # Check for low overall coverage
        if coverage.coverage_percentage < 50 and len(criteria) > 0:
            issues.append(CompletenessIssue(
                severity=CompletenessSeverity.WARNING,
                item_id=story.id,
                issue_type='low_coverage',
                description=f"Only {coverage.coverage_percentage:.0f}% of acceptance criteria covered",
                suggested_fix=f"Add tasks to cover {len(coverage.uncovered_criteria)} uncovered criteria",
                coverage_percentage=coverage.coverage_percentage
            ))

        return issues

    def check_epic_story_coverage(self, epic: Epic) -> List[CompletenessIssue]:
        """Verify stories cover epic goals.

        Args:
            epic: Epic to check

        Returns:
            List of completeness issues for this epic
        """
        issues = []

        # Get epic goals/deliverables
        goals = getattr(epic, 'goals', [])
        if not goals:
            # Try to extract from description
            goals = self._extract_goals_from_description(epic.description or "")

        stories = epic.get_children_by_type('Story')

        if not goals:
            return issues  # Can't check coverage without goals

        # Check each goal for story coverage
        for goal in goals:
            covered = False
            goal_lower = goal.lower()

            for story in stories:
                story_text = f"{story.name} {story.description or ''}".lower()
                # Check if story seems to address this goal
                if self._text_similarity(goal_lower, story_text) > 0.3:
                    covered = True
                    break

            if not covered:
                goal_preview = goal[:60] + "..." if len(goal) > 60 else goal
                issues.append(CompletenessIssue(
                    severity=CompletenessSeverity.INFO,
                    item_id=epic.id,
                    issue_type='uncovered_goal',
                    description=f"Epic goal may not be covered: {goal_preview}",
                    suggested_fix="Consider adding a story to address this goal"
                ))

        return issues

    def check_task_scope_match(self, task: Task) -> List[CompletenessIssue]:
        """Verify task matches its description/goal.

        Args:
            task: Task to check

        Returns:
            List of completeness issues for this task
        """
        issues = []

        # Check if task has sufficient description
        if not task.description and not getattr(task, 'claude_code_prompt', None):
            issues.append(CompletenessIssue(
                severity=CompletenessSeverity.WARNING,
                item_id=task.id,
                issue_type='incomplete_task',
                description=f"Task '{task.name}' has no description or implementation prompt",
                suggested_fix="Add a description or Claude Code prompt to this task"
            ))

        # Check if task title matches content
        task_title = task.name.lower()
        task_content = f"{task.description or ''} {getattr(task, 'claude_code_prompt', '') or ''}".lower()

        if task_content and len(task_content) > 20:
            # Extract key action words from title
            title_words = set(re.findall(r'\b\w+\b', task_title))
            content_words = set(re.findall(r'\b\w+\b', task_content))

            # Check for common words (excluding stop words)
            stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
                          'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
                          'would', 'could', 'should', 'may', 'might', 'must', 'shall',
                          'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from',
                          'as', 'into', 'through', 'during', 'before', 'after', 'above',
                          'below', 'between', 'under', 'again', 'further', 'then', 'once',
                          'task', 'and', 'or', 'but', 'if', 'this', 'that', 'these', 'those'}

            title_keywords = title_words - stop_words
            content_keywords = content_words - stop_words

            if title_keywords and content_keywords:
                overlap = len(title_keywords & content_keywords) / len(title_keywords)
                if overlap < 0.2:
                    issues.append(CompletenessIssue(
                        severity=CompletenessSeverity.INFO,
                        item_id=task.id,
                        issue_type='title_content_mismatch',
                        description=f"Task title may not match its content",
                        suggested_fix="Review task title to better reflect its implementation"
                    ))

        return issues

    def map_tasks_to_criteria(self, story: Story) -> CoverageMapping:
        """Create mapping of which tasks satisfy which criteria.

        Args:
            story: Story to analyze

        Returns:
            CoverageMapping with detailed coverage information
        """
        return self._map_tasks_to_criteria(story)

    def _map_tasks_to_criteria(self, story: Story) -> CoverageMapping:
        """Internal method to build coverage mapping."""
        criteria = getattr(story, 'acceptance_criteria', [])
        if not criteria:
            criteria = getattr(story, 'success_criteria', [])

        tasks = story.get_children_by_type('Task')

        coverage: Dict[int, List[str]] = {i: [] for i in range(len(criteria))}

        for task in tasks:
            # Check explicit satisfies_criteria field first
            satisfies = getattr(task, 'satisfies_criteria', '')
            if satisfies:
                # Parse AC references like "AC1, AC2" or "AC1: description"
                ac_matches = re.findall(r'AC(\d+)', satisfies, re.IGNORECASE)
                for ac_num in ac_matches:
                    idx = int(ac_num) - 1  # Convert to 0-indexed
                    if 0 <= idx < len(criteria):
                        coverage[idx].append(task.id)

            # Also check task content for criterion keywords
            task_text = self._get_task_text(task).lower()

            for i, criterion in enumerate(criteria):
                if task.id not in coverage[i]:  # Don't double-count
                    criterion_lower = criterion.lower()
                    if self._task_covers_criterion(task_text, criterion_lower):
                        coverage[i].append(task.id)

        # Calculate coverage percentage
        covered_count = sum(1 for tasks in coverage.values() if tasks)
        total_criteria = len(criteria) if criteria else 1
        coverage_pct = (covered_count / total_criteria) * 100 if total_criteria > 0 else 100

        uncovered = [i for i, tasks in coverage.items() if not tasks]

        return CoverageMapping(
            story_id=story.id,
            criteria_count=len(criteria),
            task_count=len(tasks),
            coverage=coverage,
            uncovered_criteria=uncovered,
            coverage_percentage=coverage_pct
        )

    def _get_task_text(self, task: Task) -> str:
        """Get all relevant text from a task."""
        parts = [
            task.name,
            task.description or '',
            getattr(task, 'claude_code_prompt', '') or '',
            getattr(task, 'technical_requirements', '') or ''
        ]
        return ' '.join(parts)

    def _task_covers_criterion(self, task_text: str, criterion: str) -> bool:
        """Check if task text indicates coverage of a criterion."""
        # Extract key words from criterion
        criterion_words = set(re.findall(r'\b\w{4,}\b', criterion))

        # Remove common words
        stop_words = {'should', 'must', 'will', 'when', 'then', 'that', 'this',
                      'with', 'have', 'from', 'user', 'system', 'able'}
        criterion_words -= stop_words

        if not criterion_words:
            return False

        # Check how many criterion words appear in task text
        matches = sum(1 for word in criterion_words if word in task_text)
        coverage_ratio = matches / len(criterion_words)

        return coverage_ratio >= 0.4  # At least 40% of keywords present

    def find_uncovered_criteria(self, story: Story) -> List[Tuple[int, str]]:
        """Find acceptance criteria without corresponding tasks.

        Args:
            story: Story to analyze

        Returns:
            List of (index, criterion_text) tuples for uncovered criteria
        """
        mapping = self._map_tasks_to_criteria(story)
        criteria = getattr(story, 'acceptance_criteria', [])
        if not criteria:
            criteria = getattr(story, 'success_criteria', [])

        uncovered = []
        for idx in mapping.uncovered_criteria:
            if 0 <= idx < len(criteria):
                uncovered.append((idx, criteria[idx]))

        return uncovered

    def suggest_missing_tasks(self, story: Story) -> List[TaskSuggestion]:
        """Generate suggestions for missing task coverage.

        Args:
            story: Story to analyze

        Returns:
            List of TaskSuggestion objects
        """
        uncovered = self.find_uncovered_criteria(story)
        suggestions = []

        for idx, criterion in uncovered:
            suggestion = self._create_task_suggestion(idx, criterion, story)
            suggestions.append(suggestion)

        return suggestions

    def _create_task_suggestion(self, idx: int, criterion: str, story: Story) -> TaskSuggestion:
        """Create a task suggestion for an uncovered criterion."""
        # Determine work type from criterion text
        work_type = self._infer_work_type(criterion)

        # Determine complexity
        complexity = self._infer_complexity(criterion)

        # Generate title
        title = self._generate_task_title(criterion)

        # Generate goal
        goal = self._generate_task_goal(criterion)

        return TaskSuggestion(
            criterion_index=idx + 1,  # 1-indexed for display
            criterion_text=criterion,
            suggested_title=title,
            suggested_goal=goal,
            work_type=work_type,
            complexity=complexity
        )

    def _infer_work_type(self, text: str) -> str:
        """Infer work type from text."""
        text_lower = text.lower()

        for work_type, keywords in self.TASK_TYPE_KEYWORDS.items():
            if any(kw in text_lower for kw in keywords):
                return work_type

        return 'implementation'  # Default

    def _infer_complexity(self, text: str) -> str:
        """Infer complexity from text."""
        text_lower = text.lower()

        for complexity, keywords in self.COMPLEXITY_KEYWORDS.items():
            if any(kw in text_lower for kw in keywords):
                return complexity

        return 'moderate'  # Default

    def _generate_task_title(self, criterion: str) -> str:
        """Generate a task title from criterion text."""
        # Extract action and subject from criterion
        criterion_clean = re.sub(r'^-?\s*\[[ x]?\]\s*', '', criterion)
        criterion_clean = re.sub(r'^AC\d+:\s*', '', criterion_clean, flags=re.IGNORECASE)

        # Try to extract a verb phrase
        words = criterion_clean.split()
        if len(words) > 6:
            # Truncate and add action prefix
            subject = ' '.join(words[:5])
            return f"Implement {subject}"
        elif len(words) > 0:
            return f"Implement: {criterion_clean}"
        else:
            return "Implement criterion"

    def _generate_task_goal(self, criterion: str) -> str:
        """Generate a task goal from criterion text."""
        criterion_clean = re.sub(r'^-?\s*\[[ x]?\]\s*', '', criterion)
        criterion_clean = re.sub(r'^AC\d+:\s*', '', criterion_clean, flags=re.IGNORECASE)

        return f"Ensure that {criterion_clean.lower()}"

    def _extract_goals_from_description(self, description: str) -> List[str]:
        """Extract goals from epic description."""
        goals = []

        # Look for bullet points
        bullet_pattern = r'^[-*•]\s*(.+)$'
        for line in description.split('\n'):
            match = re.match(bullet_pattern, line.strip())
            if match:
                goals.append(match.group(1))

        # Look for numbered items
        numbered_pattern = r'^\d+\.\s*(.+)$'
        for line in description.split('\n'):
            match = re.match(numbered_pattern, line.strip())
            if match:
                goals.append(match.group(1))

        return goals

    def _text_similarity(self, text1: str, text2: str) -> float:
        """Calculate simple word overlap similarity."""
        words1 = set(re.findall(r'\b\w{4,}\b', text1.lower()))
        words2 = set(re.findall(r'\b\w{4,}\b', text2.lower()))

        if not words1 or not words2:
            return 0.0

        intersection = len(words1 & words2)
        union = len(words1 | words2)

        return intersection / union if union > 0 else 0.0

    def get_summary(self) -> Dict[str, int]:
        """Get summary of completeness check results."""
        return {
            'total_issues': len(self.issues),
            'errors': len([i for i in self.issues if i.severity == CompletenessSeverity.ERROR]),
            'warnings': len([i for i in self.issues if i.severity == CompletenessSeverity.WARNING]),
            'info': len([i for i in self.issues if i.severity == CompletenessSeverity.INFO]),
        }

    def format_report(self) -> str:
        """Format completeness check results as a report."""
        lines = ["Completeness Check Report", "=" * 40]

        summary = self.get_summary()
        lines.append(f"\nTotal issues: {summary['total_issues']}")
        lines.append(f"  Errors: {summary['errors']}")
        lines.append(f"  Warnings: {summary['warnings']}")
        lines.append(f"  Info: {summary['info']}")

        if self.issues:
            lines.append("\n" + "-" * 40)

            for severity in [CompletenessSeverity.ERROR, CompletenessSeverity.WARNING, CompletenessSeverity.INFO]:
                severity_issues = [i for i in self.issues if i.severity == severity]
                if severity_issues:
                    icon = {"error": "ERROR", "warning": "WARNING", "info": "INFO"}[severity.value]
                    lines.append(f"\n{icon}S:")

                    for issue in severity_issues:
                        lines.append(f"  [{issue.item_id}] {issue.issue_type}")
                        lines.append(f"    {issue.description}")
                        if issue.coverage_percentage is not None:
                            lines.append(f"    Coverage: {issue.coverage_percentage:.0f}%")
                        if issue.suggested_fix:
                            lines.append(f"    -> Fix: {issue.suggested_fix}")
        else:
            lines.append("\nNo issues found!")

        return "\n".join(lines)

    def format_coverage_report(self, story: Story) -> str:
        """Format a detailed coverage report for a story."""
        mapping = self._map_tasks_to_criteria(story)
        criteria = getattr(story, 'acceptance_criteria', [])
        if not criteria:
            criteria = getattr(story, 'success_criteria', [])

        lines = [f"Coverage Report: {story.name}", "=" * 50]
        lines.append(f"\nCoverage: {mapping.coverage_percentage:.0f}%")
        lines.append(f"Criteria: {mapping.criteria_count}")
        lines.append(f"Tasks: {mapping.task_count}")

        lines.append("\nCriteria Coverage:")
        for i, criterion in enumerate(criteria):
            task_ids = mapping.coverage.get(i, [])
            status = "COVERED" if task_ids else "UNCOVERED"
            criterion_preview = criterion[:50] + "..." if len(criterion) > 50 else criterion

            if task_ids:
                lines.append(f"  [+] AC{i+1}: {criterion_preview}")
                lines.append(f"      Covered by: {', '.join(task_ids)}")
            else:
                lines.append(f"  [-] AC{i+1}: {criterion_preview}")
                lines.append(f"      NOT COVERED")

        if mapping.uncovered_criteria:
            lines.append(f"\nSuggested Tasks:")
            suggestions = self.suggest_missing_tasks(story)
            for suggestion in suggestions:
                lines.append(f"  - {suggestion.suggested_title}")
                lines.append(f"    Type: {suggestion.work_type}, Complexity: {suggestion.complexity}")

        return "\n".join(lines)
