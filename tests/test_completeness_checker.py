"""Tests for the completeness checker."""

import pytest
from arcane.engines.validation import (
    CompletenessChecker,
    CompletenessIssue,
    CompletenessSeverity,
    CoverageMapping,
    TaskSuggestion,
)
from arcane.items.milestone import Milestone
from arcane.items.epic import Epic
from arcane.items.story import Story
from arcane.items.task import Task


class TestCompletenessCheckerBasics:
    """Basic tests for CompletenessChecker."""

    @pytest.fixture
    def checker(self):
        """Create a fresh checker."""
        return CompletenessChecker()

    @pytest.fixture
    def complete_roadmap(self):
        """Create a complete roadmap with proper coverage."""
        milestone = Milestone(name="MVP", number="1")

        epic = Epic(name="Core Features", number="1.0", parent=milestone)
        milestone.add_child(epic)

        story = Story(name="User Login", number="1.0.1", parent=epic)
        story.acceptance_criteria = [
            "User can enter email and password",
            "Invalid credentials show error message",
            "Successful login redirects to dashboard"
        ]
        epic.add_child(story)

        task1 = Task(name="Create login form", number="1.0.1.1", parent=story)
        task1.description = "Build login form with email and password fields"
        task1.satisfies_criteria = "AC1: User can enter email and password"
        story.add_child(task1)

        task2 = Task(name="Add validation", number="1.0.1.2", parent=story)
        task2.description = "Add form validation and error messages for invalid credentials"
        task2.satisfies_criteria = "AC2: Invalid credentials show error"
        story.add_child(task2)

        task3 = Task(name="Add redirect logic", number="1.0.1.3", parent=story)
        task3.description = "Redirect user to dashboard after successful login"
        task3.satisfies_criteria = "AC3: Successful login redirects"
        story.add_child(task3)

        return [milestone]

    def test_checker_initialization(self, checker):
        """Test that checker initializes correctly."""
        assert checker.issues == []

    def test_check_complete_roadmap(self, checker, complete_roadmap):
        """Test checking a complete roadmap."""
        issues = checker.check_all(complete_roadmap)

        # Should have no errors or warnings for a complete roadmap
        errors = [i for i in issues if i.severity == CompletenessSeverity.ERROR]
        warnings = [i for i in issues if i.severity == CompletenessSeverity.WARNING]
        assert len(errors) == 0
        assert len(warnings) == 0

    def test_get_summary(self, checker, complete_roadmap):
        """Test summary generation."""
        checker.check_all(complete_roadmap)
        summary = checker.get_summary()

        assert 'total_issues' in summary
        assert 'errors' in summary
        assert 'warnings' in summary
        assert 'info' in summary


class TestEmptyItemChecks:
    """Tests for empty item detection."""

    @pytest.fixture
    def checker(self):
        return CompletenessChecker()

    def test_empty_milestone_flagged(self, checker):
        """Test that empty milestone is flagged."""
        milestone = Milestone(name="Empty", number="1")

        issues = checker.check_all([milestone])

        empty_issues = [i for i in issues if i.issue_type == 'empty_milestone']
        assert len(empty_issues) == 1
        assert empty_issues[0].severity == CompletenessSeverity.ERROR

    def test_empty_epic_flagged(self, checker):
        """Test that empty epic is flagged."""
        milestone = Milestone(name="MVP", number="1")
        epic = Epic(name="Empty Epic", number="1.0", parent=milestone)
        milestone.add_child(epic)

        issues = checker.check_all([milestone])

        empty_issues = [i for i in issues if i.issue_type == 'empty_epic']
        assert len(empty_issues) == 1
        assert empty_issues[0].severity == CompletenessSeverity.ERROR

    def test_empty_story_flagged(self, checker):
        """Test that empty story is flagged."""
        milestone = Milestone(name="MVP", number="1")
        epic = Epic(name="Core", number="1.0", parent=milestone)
        milestone.add_child(epic)
        story = Story(name="Empty Story", number="1.0.1", parent=epic)
        epic.add_child(story)

        issues = checker.check_all([milestone])

        empty_issues = [i for i in issues if i.issue_type == 'empty_story']
        assert len(empty_issues) == 1
        assert empty_issues[0].severity == CompletenessSeverity.ERROR


class TestStoryTaskAlignment:
    """Tests for story-task alignment checking."""

    @pytest.fixture
    def checker(self):
        return CompletenessChecker()

    def test_full_coverage(self, checker):
        """Test story with full AC coverage."""
        story = Story(name="Login", number="1.0.1")
        story.acceptance_criteria = [
            "User can enter credentials",
            "System validates input"
        ]

        task1 = Task(name="Form", number="1.0.1.1", parent=story)
        task1.satisfies_criteria = "AC1: User can enter credentials"
        story.add_child(task1)

        task2 = Task(name="Validation", number="1.0.1.2", parent=story)
        task2.satisfies_criteria = "AC2: System validates input"
        story.add_child(task2)

        issues = checker.check_story_task_alignment(story)

        # Should have no uncovered criteria
        uncovered = [i for i in issues if i.issue_type == 'uncovered_criterion']
        assert len(uncovered) == 0

    def test_partial_coverage(self, checker):
        """Test story with partial AC coverage."""
        story = Story(name="Login", number="1.0.1")
        story.acceptance_criteria = [
            "User can enter credentials",
            "System validates input",
            "Error messages are displayed"
        ]

        task1 = Task(name="Form", number="1.0.1.1", parent=story)
        task1.satisfies_criteria = "AC1: User can enter credentials"
        story.add_child(task1)

        # AC2 and AC3 not covered

        issues = checker.check_story_task_alignment(story)

        uncovered = [i for i in issues if i.issue_type == 'uncovered_criterion']
        assert len(uncovered) == 2

    def test_no_criteria_info(self, checker):
        """Test story with no acceptance criteria."""
        story = Story(name="Login", number="1.0.1")
        story.acceptance_criteria = []

        task = Task(name="Form", number="1.0.1.1", parent=story)
        story.add_child(task)

        issues = checker.check_story_task_alignment(story)

        no_criteria = [i for i in issues if i.issue_type == 'no_criteria']
        assert len(no_criteria) == 1
        assert no_criteria[0].severity == CompletenessSeverity.INFO

    def test_low_coverage_warning(self, checker):
        """Test warning for low coverage percentage."""
        story = Story(name="Login", number="1.0.1")
        story.acceptance_criteria = [
            "Criterion 1",
            "Criterion 2",
            "Criterion 3",
            "Criterion 4",
            "Criterion 5"
        ]

        # Only one task covering one criterion
        task = Task(name="Task", number="1.0.1.1", parent=story)
        task.satisfies_criteria = "AC1"
        story.add_child(task)

        issues = checker.check_story_task_alignment(story)

        low_coverage = [i for i in issues if i.issue_type == 'low_coverage']
        assert len(low_coverage) == 1
        assert low_coverage[0].coverage_percentage == 20.0


class TestCoverageMapping:
    """Tests for coverage mapping functionality."""

    @pytest.fixture
    def checker(self):
        return CompletenessChecker()

    def test_map_tasks_to_criteria_explicit(self, checker):
        """Test mapping with explicit satisfies_criteria field."""
        story = Story(name="Test", number="1.0.1")
        story.acceptance_criteria = [
            "Criterion A",
            "Criterion B",
            "Criterion C"
        ]

        task1 = Task(name="Task 1", number="1.0.1.1", parent=story)
        task1.satisfies_criteria = "AC1, AC2"
        story.add_child(task1)

        task2 = Task(name="Task 2", number="1.0.1.2", parent=story)
        task2.satisfies_criteria = "AC3"
        story.add_child(task2)

        mapping = checker.map_tasks_to_criteria(story)

        assert mapping.criteria_count == 3
        assert mapping.task_count == 2
        assert "1.0.1.1" in mapping.coverage[0]  # AC1
        assert "1.0.1.1" in mapping.coverage[1]  # AC2
        assert "1.0.1.2" in mapping.coverage[2]  # AC3
        assert mapping.coverage_percentage == 100.0

    def test_map_tasks_to_criteria_implicit(self, checker):
        """Test mapping with implicit keyword matching."""
        story = Story(name="Test", number="1.0.1")
        story.acceptance_criteria = [
            "User can login with email",
            "System sends notification email"
        ]

        task = Task(name="Create login form", number="1.0.1.1", parent=story)
        task.description = "Build the login form with email input field"
        story.add_child(task)

        mapping = checker.map_tasks_to_criteria(story)

        # Should match first criterion by keyword overlap
        assert "1.0.1.1" in mapping.coverage[0]

    def test_coverage_percentage_calculation(self, checker):
        """Test coverage percentage calculation."""
        story = Story(name="Test", number="1.0.1")
        story.acceptance_criteria = ["AC1", "AC2", "AC3", "AC4"]

        task1 = Task(name="Task 1", number="1.0.1.1", parent=story)
        task1.satisfies_criteria = "AC1"
        story.add_child(task1)

        task2 = Task(name="Task 2", number="1.0.1.2", parent=story)
        task2.satisfies_criteria = "AC2"
        story.add_child(task2)

        mapping = checker.map_tasks_to_criteria(story)

        assert mapping.coverage_percentage == 50.0
        assert len(mapping.uncovered_criteria) == 2


class TestFindUncoveredCriteria:
    """Tests for finding uncovered criteria."""

    @pytest.fixture
    def checker(self):
        return CompletenessChecker()

    def test_find_uncovered_criteria(self, checker):
        """Test finding uncovered acceptance criteria."""
        story = Story(name="Test", number="1.0.1")
        story.acceptance_criteria = [
            "First criterion",
            "Second criterion",
            "Third criterion"
        ]

        task = Task(name="Task", number="1.0.1.1", parent=story)
        task.satisfies_criteria = "AC2"  # Only covers second
        story.add_child(task)

        uncovered = checker.find_uncovered_criteria(story)

        assert len(uncovered) == 2
        assert (0, "First criterion") in uncovered
        assert (2, "Third criterion") in uncovered

    def test_no_uncovered_criteria(self, checker):
        """Test when all criteria are covered."""
        story = Story(name="Test", number="1.0.1")
        story.acceptance_criteria = ["Criterion"]

        task = Task(name="Task", number="1.0.1.1", parent=story)
        task.satisfies_criteria = "AC1"
        story.add_child(task)

        uncovered = checker.find_uncovered_criteria(story)

        assert len(uncovered) == 0


class TestSuggestMissingTasks:
    """Tests for task suggestion functionality."""

    @pytest.fixture
    def checker(self):
        return CompletenessChecker()

    def test_suggest_missing_tasks(self, checker):
        """Test generating task suggestions."""
        story = Story(name="Test", number="1.0.1")
        story.acceptance_criteria = [
            "User can create account",
            "System validates email format"
        ]

        task = Task(name="Task", number="1.0.1.1", parent=story)
        task.satisfies_criteria = "AC1"
        story.add_child(task)

        suggestions = checker.suggest_missing_tasks(story)

        assert len(suggestions) == 1
        assert suggestions[0].criterion_index == 2
        assert "validates" in suggestions[0].criterion_text.lower()
        assert suggestions[0].work_type in ['implementation', 'testing']

    def test_no_suggestions_when_complete(self, checker):
        """Test no suggestions when fully covered."""
        story = Story(name="Test", number="1.0.1")
        story.acceptance_criteria = ["Only criterion"]

        task = Task(name="Task", number="1.0.1.1", parent=story)
        task.satisfies_criteria = "AC1"
        story.add_child(task)

        suggestions = checker.suggest_missing_tasks(story)

        assert len(suggestions) == 0

    def test_suggestion_work_type_inference(self, checker):
        """Test work type inference in suggestions."""
        story = Story(name="Test", number="1.0.1")
        story.acceptance_criteria = [
            "System should test all inputs",
            "Create user interface",
            "Document the API"
        ]

        # No tasks - all uncovered
        suggestions = checker.suggest_missing_tasks(story)

        assert len(suggestions) == 3
        work_types = {s.work_type for s in suggestions}
        assert 'testing' in work_types or 'implementation' in work_types


class TestTaskScopeMatch:
    """Tests for task scope matching."""

    @pytest.fixture
    def checker(self):
        return CompletenessChecker()

    def test_task_with_description(self, checker):
        """Test task with proper description."""
        task = Task(name="Create login form", number="1.0.1.1")
        task.description = "Build a login form with email and password fields"

        issues = checker.check_task_scope_match(task)

        incomplete = [i for i in issues if i.issue_type == 'incomplete_task']
        assert len(incomplete) == 0

    def test_task_without_description(self, checker):
        """Test task without description is flagged."""
        task = Task(name="Create login form", number="1.0.1.1")
        task.description = None

        issues = checker.check_task_scope_match(task)

        incomplete = [i for i in issues if i.issue_type == 'incomplete_task']
        assert len(incomplete) == 1

    def test_task_with_claude_prompt(self, checker):
        """Test task with Claude prompt is not flagged."""
        task = Task(name="Create login form", number="1.0.1.1")
        task.description = None
        task.claude_code_prompt = "Build a React login form component"

        issues = checker.check_task_scope_match(task)

        incomplete = [i for i in issues if i.issue_type == 'incomplete_task']
        assert len(incomplete) == 0


class TestEpicStoryCoverage:
    """Tests for epic-story coverage checking."""

    @pytest.fixture
    def checker(self):
        return CompletenessChecker()

    def test_epic_goals_covered(self, checker):
        """Test epic with goals covered by stories."""
        epic = Epic(name="Authentication", number="1.0")
        epic.goals = ["Implement user login", "Add password reset"]

        story1 = Story(name="User Login", number="1.0.1", parent=epic)
        story1.description = "Implement secure user login functionality"
        epic.add_child(story1)

        story2 = Story(name="Password Reset", number="1.0.2", parent=epic)
        story2.description = "Add password reset flow"
        epic.add_child(story2)

        issues = checker.check_epic_story_coverage(epic)

        uncovered_goals = [i for i in issues if i.issue_type == 'uncovered_goal']
        assert len(uncovered_goals) == 0

    def test_epic_goals_uncovered(self, checker):
        """Test epic with uncovered goals."""
        epic = Epic(name="Authentication", number="1.0")
        epic.goals = ["Implement user login", "Add password reset", "Enable 2FA"]

        story = Story(name="User Login", number="1.0.1", parent=epic)
        story.description = "Implement secure user login"
        epic.add_child(story)

        issues = checker.check_epic_story_coverage(epic)

        uncovered_goals = [i for i in issues if i.issue_type == 'uncovered_goal']
        # Should flag uncovered goals (password reset, 2FA)
        assert len(uncovered_goals) >= 1


class TestReportFormatting:
    """Tests for report formatting."""

    @pytest.fixture
    def checker(self):
        return CompletenessChecker()

    def test_format_report_basic(self, checker):
        """Test basic report formatting."""
        milestone = Milestone(name="MVP", number="1")
        epic = Epic(name="Core", number="1.0", parent=milestone)
        milestone.add_child(epic)
        story = Story(name="Feature", number="1.0.1", parent=epic)
        epic.add_child(story)

        checker.check_all([milestone])
        report = checker.format_report()

        assert "Completeness Check Report" in report
        assert "Total issues:" in report

    def test_format_coverage_report(self, checker):
        """Test coverage report formatting."""
        story = Story(name="Login", number="1.0.1")
        story.acceptance_criteria = [
            "User can login",
            "Error messages shown"
        ]

        task = Task(name="Form", number="1.0.1.1", parent=story)
        task.satisfies_criteria = "AC1"
        story.add_child(task)

        report = checker.format_coverage_report(story)

        assert "Coverage Report" in report
        assert "AC1" in report
        assert "AC2" in report
        assert "COVERED" in report or "[+]" in report


class TestDataClasses:
    """Tests for data classes."""

    def test_completeness_issue_creation(self):
        """Test creating CompletenessIssue."""
        issue = CompletenessIssue(
            severity=CompletenessSeverity.WARNING,
            item_id="1.0.1",
            issue_type="uncovered_criterion",
            description="AC1 not covered",
            suggested_fix="Add task",
            coverage_percentage=50.0
        )

        assert issue.severity == CompletenessSeverity.WARNING
        assert issue.item_id == "1.0.1"
        assert issue.coverage_percentage == 50.0

    def test_coverage_mapping_creation(self):
        """Test creating CoverageMapping."""
        mapping = CoverageMapping(
            story_id="1.0.1",
            criteria_count=3,
            task_count=2,
            coverage={0: ["1.0.1.1"], 1: ["1.0.1.2"], 2: []},
            uncovered_criteria=[2],
            coverage_percentage=66.7
        )

        assert mapping.story_id == "1.0.1"
        assert len(mapping.uncovered_criteria) == 1

    def test_task_suggestion_creation(self):
        """Test creating TaskSuggestion."""
        suggestion = TaskSuggestion(
            criterion_index=1,
            criterion_text="User can login",
            suggested_title="Implement login",
            suggested_goal="Ensure user can login",
            work_type="implementation",
            complexity="moderate"
        )

        assert suggestion.criterion_index == 1
        assert suggestion.work_type == "implementation"


class TestComplexScenarios:
    """Tests for complex scenarios."""

    @pytest.fixture
    def checker(self):
        return CompletenessChecker()

    def test_multi_task_single_criterion(self, checker):
        """Test multiple tasks covering same criterion."""
        story = Story(name="Test", number="1.0.1")
        story.acceptance_criteria = ["User can login"]

        task1 = Task(name="Frontend", number="1.0.1.1", parent=story)
        task1.satisfies_criteria = "AC1"
        story.add_child(task1)

        task2 = Task(name="Backend", number="1.0.1.2", parent=story)
        task2.satisfies_criteria = "AC1"
        story.add_child(task2)

        mapping = checker.map_tasks_to_criteria(story)

        assert len(mapping.coverage[0]) == 2
        assert mapping.coverage_percentage == 100.0

    def test_single_task_multi_criteria(self, checker):
        """Test single task covering multiple criteria."""
        story = Story(name="Test", number="1.0.1")
        story.acceptance_criteria = [
            "User sees form",
            "User can submit",
            "User gets confirmation"
        ]

        task = Task(name="Full form flow", number="1.0.1.1", parent=story)
        task.satisfies_criteria = "AC1, AC2, AC3"
        story.add_child(task)

        mapping = checker.map_tasks_to_criteria(story)

        assert all(mapping.coverage[i] for i in range(3))
        assert mapping.coverage_percentage == 100.0

    def test_large_roadmap(self, checker):
        """Test with larger roadmap structure."""
        milestone = Milestone(name="MVP", number="1")

        for e in range(3):
            epic = Epic(name=f"Epic {e}", number=f"1.{e}", parent=milestone)
            milestone.add_child(epic)

            for s in range(2):
                story = Story(name=f"Story {e}.{s}", number=f"1.{e}.{s+1}", parent=epic)
                story.acceptance_criteria = [f"AC{i}" for i in range(3)]
                epic.add_child(story)

                for t in range(3):
                    task = Task(name=f"Task {t}", number=f"1.{e}.{s+1}.{t+1}", parent=story)
                    task.satisfies_criteria = f"AC{t+1}"
                    story.add_child(task)

        issues = checker.check_all([milestone])

        # Should complete without error
        summary = checker.get_summary()
        assert summary['total_issues'] >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
