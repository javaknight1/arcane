"""Tests for cross-reference validation."""

import pytest
from unittest.mock import MagicMock

from arcane.engines.validation.cross_reference_validator import (
    CrossReferenceValidator,
    CoherenceIssue,
    CoherenceSeverity,
    CoherenceAutoFixer,
)


class MockItem:
    """Mock item for testing."""
    def __init__(self, id, name, item_type, description="", children=None):
        self.id = id
        self.name = name
        self.item_type = item_type
        self.description = description
        self.children = children or []
        self.depends_on_items = []
        self.dependency_ids = []

    def get_children_by_type(self, type_name):
        return [c for c in self.children if c.item_type == type_name]


class MockRoadmap:
    """Mock roadmap for testing."""
    def __init__(self, items=None):
        self._items = items or []
        self._stories = []
        self._epics = []
        self._tasks = []

    def get_all_items(self):
        return self._items

    def get_stories(self):
        return self._stories

    def get_epics(self):
        return self._epics

    def get_tasks(self):
        return self._tasks


class TestCoherenceIssue:
    """Tests for CoherenceIssue dataclass."""

    def test_creation(self):
        """Test creating a coherence issue."""
        issue = CoherenceIssue(
            severity=CoherenceSeverity.CRITICAL,
            item_id="1.0.1",
            issue_type="missing_tasks",
            description="Story has no tasks"
        )

        assert issue.severity == CoherenceSeverity.CRITICAL
        assert issue.item_id == "1.0.1"
        assert issue.issue_type == "missing_tasks"
        assert issue.description == "Story has no tasks"

    def test_to_dict(self):
        """Test serialization to dictionary."""
        issue = CoherenceIssue(
            severity=CoherenceSeverity.WARNING,
            item_id="1.0.1",
            issue_type="potential_duplicate",
            description="Similar item found",
            related_item_id="1.0.2",
            suggestion="Consolidate items"
        )

        result = issue.to_dict()

        assert result['severity'] == "warning"
        assert result['item_id'] == "1.0.1"
        assert result['related_item_id'] == "1.0.2"
        assert result['suggestion'] == "Consolidate items"


class TestTaskStoryAlignment:
    """Tests for task-story alignment validation."""

    def test_story_with_no_tasks_is_critical(self):
        """Test that stories without tasks are flagged as critical."""
        story = MockItem("1.0.1", "User Login Story", "Story", "Implement user login")

        roadmap = MockRoadmap()
        roadmap._stories = [story]
        roadmap._items = [story]

        validator = CrossReferenceValidator()
        issues = validator.validate_roadmap(roadmap)

        assert len(issues) >= 1
        critical_issues = [i for i in issues if i.severity == CoherenceSeverity.CRITICAL]
        assert any(i.issue_type == "missing_tasks" for i in critical_issues)

    def test_story_with_aligned_tasks_passes(self):
        """Test that stories with aligned tasks don't generate alignment warnings."""
        task1 = MockItem("1.0.1.1", "Create login form UI", "Task", "Build the login form component")
        task2 = MockItem("1.0.1.2", "Implement authentication logic", "Task", "Handle user authentication")
        story = MockItem(
            "1.0.1",
            "User Login Feature",
            "Story",
            "Allow users to login with authentication",
            children=[task1, task2]
        )

        roadmap = MockRoadmap()
        roadmap._stories = [story]
        roadmap._items = [story, task1, task2]

        validator = CrossReferenceValidator()
        issues = validator.validate_roadmap(roadmap)

        # Should not have task_story_mismatch
        alignment_issues = [i for i in issues if i.issue_type == "task_story_mismatch"]
        assert len(alignment_issues) == 0

    def test_story_with_misaligned_tasks_warned(self):
        """Test that stories with misaligned tasks generate warnings."""
        # Tasks don't relate to the story at all
        task1 = MockItem("1.0.1.1", "Setup database connection", "Task", "Configure PostgreSQL")
        task2 = MockItem("1.0.1.2", "Create migration scripts", "Task", "Database migrations")
        story = MockItem(
            "1.0.1",
            "User Payment Processing",
            "Story",
            "Allow users to process payments with Stripe",
            children=[task1, task2]
        )

        roadmap = MockRoadmap()
        roadmap._stories = [story]
        roadmap._items = [story, task1, task2]

        validator = CrossReferenceValidator()
        issues = validator.validate_roadmap(roadmap)

        alignment_issues = [i for i in issues if i.issue_type == "task_story_mismatch"]
        assert len(alignment_issues) == 1
        assert alignment_issues[0].item_id == "1.0.1"


class TestDuplicateDetection:
    """Tests for duplicate work item detection."""

    def test_detects_very_similar_items(self):
        """Test that very similar item names are flagged."""
        item1 = MockItem("1.0.1", "Implement user authentication", "Story")
        item2 = MockItem("1.0.2", "Implement user authentication system", "Story")

        roadmap = MockRoadmap()
        roadmap._items = [item1, item2]

        validator = CrossReferenceValidator()
        issues = validator.validate_roadmap(roadmap)

        duplicate_issues = [i for i in issues if i.issue_type == "potential_duplicate"]
        assert len(duplicate_issues) == 1
        assert duplicate_issues[0].related_item_id in ["1.0.1", "1.0.2"]

    def test_different_items_not_flagged(self):
        """Test that different items are not flagged as duplicates."""
        item1 = MockItem("1.0.1", "User Authentication", "Story")
        item2 = MockItem("1.0.2", "Payment Processing", "Story")

        roadmap = MockRoadmap()
        roadmap._items = [item1, item2]

        validator = CrossReferenceValidator()
        issues = validator.validate_roadmap(roadmap)

        duplicate_issues = [i for i in issues if i.issue_type == "potential_duplicate"]
        assert len(duplicate_issues) == 0

    def test_case_insensitive_comparison(self):
        """Test that duplicate detection is case insensitive."""
        item1 = MockItem("1.0.1", "User Login System", "Story")
        item2 = MockItem("1.0.2", "USER LOGIN SYSTEM", "Story")

        roadmap = MockRoadmap()
        roadmap._items = [item1, item2]

        validator = CrossReferenceValidator()
        issues = validator.validate_roadmap(roadmap)

        duplicate_issues = [i for i in issues if i.issue_type == "potential_duplicate"]
        assert len(duplicate_issues) == 1

    def test_skips_project_item(self):
        """Test that project-level items are skipped in duplicate detection."""
        project = MockItem("0", "My Project", "Project")
        item1 = MockItem("1", "My Project Milestone", "Milestone")

        roadmap = MockRoadmap()
        roadmap._items = [project, item1]

        validator = CrossReferenceValidator()
        issues = validator.validate_roadmap(roadmap)

        # Should not flag project vs milestone as duplicate
        duplicate_issues = [i for i in issues if i.issue_type == "potential_duplicate"]
        assert len(duplicate_issues) == 0


class TestDependencyValidation:
    """Tests for dependency existence validation."""

    def test_valid_dependencies_pass(self):
        """Test that valid dependency references pass."""
        item1 = MockItem("1.0.1", "Setup Database", "Story")
        item2 = MockItem("1.0.2", "User Authentication", "Story")
        item2.dependency_ids = ["1.0.1"]

        roadmap = MockRoadmap()
        roadmap._items = [item1, item2]

        validator = CrossReferenceValidator()
        issues = validator.validate_roadmap(roadmap)

        dependency_issues = [i for i in issues if i.issue_type == "invalid_dependency"]
        assert len(dependency_issues) == 0

    def test_invalid_dependency_id_flagged(self):
        """Test that invalid dependency IDs are flagged."""
        item1 = MockItem("1.0.1", "User Authentication", "Story")
        item1.dependency_ids = ["99.99.99"]  # Non-existent

        roadmap = MockRoadmap()
        roadmap._items = [item1]

        validator = CrossReferenceValidator()
        issues = validator.validate_roadmap(roadmap)

        dependency_issues = [i for i in issues if i.issue_type == "invalid_dependency"]
        assert len(dependency_issues) == 1
        assert dependency_issues[0].severity == CoherenceSeverity.CRITICAL
        assert "99.99.99" in dependency_issues[0].description

    def test_invalid_depends_on_items_flagged(self):
        """Test that invalid depends_on_items references are flagged."""
        fake_dep = MockItem("99.99.99", "Non-existent", "Story")
        item1 = MockItem("1.0.1", "User Authentication", "Story")
        item1.depends_on_items = [fake_dep]

        roadmap = MockRoadmap()
        roadmap._items = [item1]  # Note: fake_dep is not in roadmap

        validator = CrossReferenceValidator()
        issues = validator.validate_roadmap(roadmap)

        dependency_issues = [i for i in issues if i.issue_type == "invalid_dependency"]
        assert len(dependency_issues) == 1


class TestScopeConsistency:
    """Tests for scope consistency validation."""

    def test_empty_epic_is_critical(self):
        """Test that epics with no stories are flagged as critical."""
        epic = MockItem("1.0", "User Management Epic", "Epic", children=[])

        roadmap = MockRoadmap()
        roadmap._epics = [epic]
        roadmap._items = [epic]

        validator = CrossReferenceValidator()
        issues = validator.validate_roadmap(roadmap)

        empty_epic_issues = [i for i in issues if i.issue_type == "empty_epic"]
        assert len(empty_epic_issues) == 1
        assert empty_epic_issues[0].severity == CoherenceSeverity.CRITICAL

    def test_single_story_epic_is_info(self):
        """Test that epics with only one story generate info."""
        story = MockItem("1.0.1", "Login Story", "Story")
        epic = MockItem("1.0", "Auth Epic", "Epic", children=[story])

        roadmap = MockRoadmap()
        roadmap._epics = [epic]
        roadmap._stories = [story]
        roadmap._items = [epic, story]

        validator = CrossReferenceValidator()
        issues = validator.validate_roadmap(roadmap)

        single_story_issues = [i for i in issues if i.issue_type == "single_story_epic"]
        assert len(single_story_issues) == 1
        assert single_story_issues[0].severity == CoherenceSeverity.INFO

    def test_oversized_epic_warned(self):
        """Test that epics with too many stories are warned."""
        stories = [
            MockItem(f"1.0.{i}", f"Story {i}", "Story")
            for i in range(12)  # 12 stories > 10 threshold
        ]
        epic = MockItem("1.0", "Large Epic", "Epic", children=stories)

        roadmap = MockRoadmap()
        roadmap._epics = [epic]
        roadmap._stories = stories
        roadmap._items = [epic] + stories

        validator = CrossReferenceValidator()
        issues = validator.validate_roadmap(roadmap)

        oversized_issues = [i for i in issues if i.issue_type == "oversized_epic"]
        assert len(oversized_issues) == 1
        assert oversized_issues[0].severity == CoherenceSeverity.WARNING
        assert "12 stories" in oversized_issues[0].description

    def test_oversized_story_warned(self):
        """Test that stories with too many tasks are warned."""
        tasks = [
            MockItem(f"1.0.1.{i}", f"Task {i}", "Task")
            for i in range(10)  # 10 tasks > 8 threshold
        ]
        story = MockItem("1.0.1", "Large Story", "Story", children=tasks)

        roadmap = MockRoadmap()
        roadmap._stories = [story]
        roadmap._items = [story] + tasks

        validator = CrossReferenceValidator()
        issues = validator.validate_roadmap(roadmap)

        oversized_issues = [i for i in issues if i.issue_type == "oversized_story"]
        assert len(oversized_issues) == 1
        assert "10 tasks" in oversized_issues[0].description

    def test_normal_sized_story_passes(self):
        """Test that normally sized stories don't generate warnings."""
        tasks = [
            MockItem(f"1.0.1.{i}", f"Task {i}", "Task")
            for i in range(5)  # 5 tasks is reasonable
        ]
        story = MockItem("1.0.1", "Normal Story", "Story", children=tasks)

        roadmap = MockRoadmap()
        roadmap._stories = [story]
        roadmap._items = [story] + tasks

        validator = CrossReferenceValidator()
        issues = validator.validate_roadmap(roadmap)

        oversized_issues = [i for i in issues if i.issue_type == "oversized_story"]
        assert len(oversized_issues) == 0


class TestNamingPatterns:
    """Tests for naming pattern consistency."""

    def test_repetitive_naming_flagged(self):
        """Test that repetitive naming patterns are flagged."""
        stories = [
            MockItem("1.0.1", "Create user login form", "Story"),
            MockItem("1.0.2", "Create user registration form", "Story"),
            MockItem("1.0.3", "Create user profile page", "Story"),
            MockItem("1.0.4", "Create user settings page", "Story"),
            MockItem("1.0.5", "Create user dashboard", "Story"),
        ]

        roadmap = MockRoadmap()
        roadmap._stories = stories
        roadmap._items = stories

        validator = CrossReferenceValidator()
        issues = validator.validate_roadmap(roadmap)

        naming_issues = [i for i in issues if i.issue_type == "repetitive_naming"]
        assert len(naming_issues) >= 1


class TestKeywordExtraction:
    """Tests for keyword extraction helper."""

    def test_extract_keywords_filters_stopwords(self):
        """Test that stop words are filtered out."""
        validator = CrossReferenceValidator()

        text = "The user will create a new login form for the application"
        keywords = validator._extract_keywords(text)

        assert "the" not in keywords
        assert "will" not in keywords
        assert "for" not in keywords
        assert "login" in keywords
        assert "form" in keywords
        assert "application" in keywords

    def test_extract_keywords_lowercase(self):
        """Test that keywords are lowercased."""
        validator = CrossReferenceValidator()

        text = "User Authentication System"
        keywords = validator._extract_keywords(text)

        assert "user" in keywords
        assert "authentication" in keywords
        assert "system" in keywords
        assert "User" not in keywords

    def test_extract_keywords_min_length(self):
        """Test that very short words are filtered."""
        validator = CrossReferenceValidator()

        text = "A UI UX API for the web"
        keywords = validator._extract_keywords(text)

        assert "web" in keywords
        # Short words like "ui", "ux", "api" (less than 3 chars) should be filtered
        assert "ui" not in keywords


class TestValidatorHelpers:
    """Tests for validator helper methods."""

    def test_get_summary(self):
        """Test getting validation summary."""
        validator = CrossReferenceValidator()
        validator.issues = [
            CoherenceIssue(CoherenceSeverity.CRITICAL, "1", "missing_tasks", "Test"),
            CoherenceIssue(CoherenceSeverity.CRITICAL, "2", "missing_tasks", "Test"),
            CoherenceIssue(CoherenceSeverity.WARNING, "3", "potential_duplicate", "Test"),
            CoherenceIssue(CoherenceSeverity.INFO, "4", "single_story_epic", "Test"),
        ]
        validator._item_lookup = {"1": None, "2": None, "3": None, "4": None}

        summary = validator.get_summary()

        assert summary['total_issues'] == 4
        assert summary['by_severity']['critical'] == 2
        assert summary['by_severity']['warning'] == 1
        assert summary['by_severity']['info'] == 1
        assert summary['by_type']['missing_tasks'] == 2
        assert summary['items_validated'] == 4

    def test_get_critical_issues(self):
        """Test filtering critical issues."""
        validator = CrossReferenceValidator()
        validator.issues = [
            CoherenceIssue(CoherenceSeverity.CRITICAL, "1", "missing_tasks", "Test"),
            CoherenceIssue(CoherenceSeverity.WARNING, "2", "potential_duplicate", "Test"),
            CoherenceIssue(CoherenceSeverity.CRITICAL, "3", "invalid_dependency", "Test"),
        ]

        critical = validator.get_critical_issues()

        assert len(critical) == 2
        assert all(i.severity == CoherenceSeverity.CRITICAL for i in critical)

    def test_has_critical_issues(self):
        """Test checking for critical issues."""
        validator = CrossReferenceValidator()

        # No issues
        assert not validator.has_critical_issues()

        # Only warnings
        validator.issues = [
            CoherenceIssue(CoherenceSeverity.WARNING, "1", "test", "Test"),
        ]
        assert not validator.has_critical_issues()

        # Has critical
        validator.issues.append(
            CoherenceIssue(CoherenceSeverity.CRITICAL, "2", "test", "Test")
        )
        assert validator.has_critical_issues()

    def test_format_report_empty(self):
        """Test formatting report with no issues."""
        validator = CrossReferenceValidator()
        validator._item_lookup = {"1": None, "2": None}

        report = validator.format_report()

        assert "Cross-Reference Validation Report" in report
        assert "Items validated: 2" in report
        assert "Total issues: 0" in report
        assert "No coherence issues found!" in report

    def test_format_report_with_issues(self):
        """Test formatting report with issues."""
        validator = CrossReferenceValidator()
        validator._item_lookup = {"1": None}
        validator.issues = [
            CoherenceIssue(
                CoherenceSeverity.CRITICAL,
                "1.0.1",
                "missing_tasks",
                "Story has no tasks",
                suggestion="Add tasks"
            ),
            CoherenceIssue(
                CoherenceSeverity.WARNING,
                "1.0.2",
                "potential_duplicate",
                "Similar to another item"
            ),
        ]

        report = validator.format_report()

        assert "CRITICAL (1):" in report
        assert "WARNING (1):" in report
        assert "missing_tasks" in report
        assert "Story has no tasks" in report
        assert "Add tasks" in report


class TestIntegration:
    """Integration tests for cross-reference validation."""

    def test_full_validation_flow(self):
        """Test complete validation flow with realistic data."""
        # Create a mini roadmap structure
        task1 = MockItem("1.0.1.1", "Create login form", "Task", "Build the form UI")
        task2 = MockItem("1.0.1.2", "Add validation", "Task", "Form validation logic")
        story1 = MockItem(
            "1.0.1",
            "User Login",
            "Story",
            "Allow users to login to the system",
            children=[task1, task2]
        )

        task3 = MockItem("1.0.2.1", "Create signup form", "Task", "Registration form")
        story2 = MockItem(
            "1.0.2",
            "User Registration",
            "Story",
            "Allow new users to register",
            children=[task3]
        )

        epic = MockItem("1.0", "User Authentication", "Epic", children=[story1, story2])
        milestone = MockItem("1", "MVP Release", "Milestone", children=[epic])
        project = MockItem("0", "My App", "Project", children=[milestone])

        roadmap = MockRoadmap()
        roadmap._items = [project, milestone, epic, story1, story2, task1, task2, task3]
        roadmap._stories = [story1, story2]
        roadmap._epics = [epic]

        validator = CrossReferenceValidator()
        issues = validator.validate_roadmap(roadmap)

        # Should pass without critical issues
        critical = [i for i in issues if i.severity == CoherenceSeverity.CRITICAL]
        assert len(critical) == 0

    def test_validates_all_categories(self):
        """Test that all validation categories are run."""
        # Create roadmap with various issues
        story_no_tasks = MockItem("1.0.1", "Orphan Story", "Story")
        story_duplicate1 = MockItem("1.0.2", "Setup Database Connection", "Story")
        story_duplicate2 = MockItem("1.0.3", "Setup Database Connections", "Story")

        item_with_bad_dep = MockItem("1.0.4", "Item with bad dep", "Story")
        item_with_bad_dep.dependency_ids = ["99.99.99"]

        empty_epic = MockItem("1.0", "Empty Epic", "Epic", children=[])

        roadmap = MockRoadmap()
        roadmap._items = [
            story_no_tasks, story_duplicate1, story_duplicate2,
            item_with_bad_dep, empty_epic
        ]
        roadmap._stories = [story_no_tasks, story_duplicate1, story_duplicate2, item_with_bad_dep]
        roadmap._epics = [empty_epic]

        validator = CrossReferenceValidator()
        issues = validator.validate_roadmap(roadmap)

        issue_types = {i.issue_type for i in issues}

        # Should detect all issue types
        assert "missing_tasks" in issue_types
        assert "potential_duplicate" in issue_types
        assert "invalid_dependency" in issue_types
        assert "empty_epic" in issue_types


class TestAutoFixableField:
    """Tests for auto_fixable field on CoherenceIssue."""

    def test_auto_fixable_default_false(self):
        """Test that auto_fixable defaults to False."""
        issue = CoherenceIssue(
            severity=CoherenceSeverity.WARNING,
            item_id="1.0.1",
            issue_type="potential_duplicate",
            description="Similar item"
        )

        assert issue.auto_fixable is False

    def test_auto_fixable_set_true(self):
        """Test setting auto_fixable to True."""
        issue = CoherenceIssue(
            severity=CoherenceSeverity.CRITICAL,
            item_id="1.0.1",
            issue_type="missing_tasks",
            description="Story has no tasks",
            auto_fixable=True
        )

        assert issue.auto_fixable is True

    def test_auto_fixable_in_to_dict(self):
        """Test that auto_fixable is included in to_dict."""
        issue = CoherenceIssue(
            severity=CoherenceSeverity.CRITICAL,
            item_id="1.0.1",
            issue_type="missing_tasks",
            description="Test",
            auto_fixable=True
        )

        result = issue.to_dict()
        assert result['auto_fixable'] is True

    def test_missing_tasks_is_auto_fixable(self):
        """Test that missing_tasks issues are marked auto-fixable."""
        story = MockItem("1.0.1", "Story without tasks", "Story")

        roadmap = MockRoadmap()
        roadmap._stories = [story]
        roadmap._items = [story]

        validator = CrossReferenceValidator()
        issues = validator.validate_roadmap(roadmap)

        missing_tasks = [i for i in issues if i.issue_type == "missing_tasks"]
        assert len(missing_tasks) == 1
        assert missing_tasks[0].auto_fixable is True

    def test_task_story_mismatch_is_auto_fixable(self):
        """Test that task_story_mismatch issues are marked auto-fixable."""
        # Misaligned tasks
        task1 = MockItem("1.0.1.1", "Setup database", "Task", "Configure PostgreSQL")
        story = MockItem(
            "1.0.1",
            "Payment Processing",
            "Story",
            "Process payments with Stripe",
            children=[task1]
        )

        roadmap = MockRoadmap()
        roadmap._stories = [story]
        roadmap._items = [story, task1]

        validator = CrossReferenceValidator()
        issues = validator.validate_roadmap(roadmap)

        mismatch = [i for i in issues if i.issue_type == "task_story_mismatch"]
        assert len(mismatch) == 1
        assert mismatch[0].auto_fixable is True

    def test_empty_epic_is_auto_fixable(self):
        """Test that empty_epic issues are marked auto-fixable."""
        epic = MockItem("1.0", "Empty Epic", "Epic", children=[])

        roadmap = MockRoadmap()
        roadmap._epics = [epic]
        roadmap._items = [epic]

        validator = CrossReferenceValidator()
        issues = validator.validate_roadmap(roadmap)

        empty = [i for i in issues if i.issue_type == "empty_epic"]
        assert len(empty) == 1
        assert empty[0].auto_fixable is True

    def test_potential_duplicate_not_auto_fixable(self):
        """Test that potential_duplicate issues are NOT auto-fixable."""
        item1 = MockItem("1.0.1", "User Authentication", "Story")
        item2 = MockItem("1.0.2", "User Authentication System", "Story")

        roadmap = MockRoadmap()
        roadmap._items = [item1, item2]

        validator = CrossReferenceValidator()
        issues = validator.validate_roadmap(roadmap)

        duplicate = [i for i in issues if i.issue_type == "potential_duplicate"]
        assert len(duplicate) == 1
        assert duplicate[0].auto_fixable is False

    def test_get_auto_fixable_issues(self):
        """Test getting only auto-fixable issues."""
        validator = CrossReferenceValidator()
        validator.issues = [
            CoherenceIssue(CoherenceSeverity.CRITICAL, "1", "missing_tasks", "Test", auto_fixable=True),
            CoherenceIssue(CoherenceSeverity.WARNING, "2", "potential_duplicate", "Test", auto_fixable=False),
            CoherenceIssue(CoherenceSeverity.CRITICAL, "3", "empty_epic", "Test", auto_fixable=True),
        ]

        auto_fixable = validator.get_auto_fixable_issues()

        assert len(auto_fixable) == 2
        assert all(i.auto_fixable for i in auto_fixable)


class TestCoherenceAutoFixer:
    """Tests for CoherenceAutoFixer class."""

    @pytest.fixture
    def mock_llm_client(self):
        """Create a mock LLM client."""
        return MagicMock()

    def test_init(self, mock_llm_client):
        """Test initializing the auto-fixer."""
        from arcane.engines.validation.cross_reference_validator import CoherenceAutoFixer

        fixer = CoherenceAutoFixer(mock_llm_client)

        assert fixer.llm_client is mock_llm_client
        assert fixer.generator is None

    def test_fix_issues_skips_non_auto_fixable(self, mock_llm_client):
        """Test that non-auto-fixable issues are skipped."""
        from arcane.engines.validation.cross_reference_validator import CoherenceAutoFixer

        fixer = CoherenceAutoFixer(mock_llm_client)

        roadmap = MockRoadmap()
        roadmap._items = []

        issues = [
            CoherenceIssue(CoherenceSeverity.WARNING, "1", "potential_duplicate", "Test", auto_fixable=False),
            CoherenceIssue(CoherenceSeverity.INFO, "2", "single_story_epic", "Test", auto_fixable=False),
        ]

        results = fixer.fix_issues(roadmap, issues)

        assert results['fixed'] == 0
        assert results['skipped'] == 2

    def test_fix_issues_respects_max_fixes(self, mock_llm_client):
        """Test that max_fixes limit is respected."""
        from arcane.engines.validation.cross_reference_validator import CoherenceAutoFixer

        fixer = CoherenceAutoFixer(mock_llm_client)

        roadmap = MockRoadmap()
        roadmap._items = []

        # Create many auto-fixable issues
        issues = [
            CoherenceIssue(CoherenceSeverity.CRITICAL, f"1.0.{i}", "missing_tasks", "Test", auto_fixable=True)
            for i in range(10)
        ]

        results = fixer.fix_issues(roadmap, issues, max_fixes=3)

        # Should only attempt 3 fixes
        assert len(results['details']) == 3

    def test_fix_missing_tasks_generates_content(self, mock_llm_client):
        """Test that fixing missing_tasks calls LLM to generate tasks."""
        from arcane.engines.validation.cross_reference_validator import CoherenceAutoFixer

        # Mock LLM response with task format
        mock_llm_client.generate.return_value = """
###TASK_START### 1.0.1.1
TASK_TITLE: Create login form
TASK_GOAL: Build the login form UI
TASK_DURATION_HOURS: 2
###TASK_END###
"""

        fixer = CoherenceAutoFixer(mock_llm_client)

        # Create a mock story with parse_tasks_content method
        story = MockItem("1.0.1", "User Login", "Story", "Allow users to login")
        story.acceptance_criteria = ["User can enter credentials", "User can submit form"]
        story.parse_tasks_content = MagicMock()

        roadmap = MockRoadmap()
        roadmap._items = [story]

        issues = [
            CoherenceIssue(CoherenceSeverity.CRITICAL, "1.0.1", "missing_tasks", "Test", auto_fixable=True)
        ]

        fixer.fix_issues(roadmap, issues)

        # Should have called LLM generate
        assert mock_llm_client.generate.called
        # Should have called parse_tasks_content
        assert story.parse_tasks_content.called

    def test_get_fix_summary(self, mock_llm_client):
        """Test formatting fix results summary."""
        from arcane.engines.validation.cross_reference_validator import CoherenceAutoFixer

        fixer = CoherenceAutoFixer(mock_llm_client)

        results = {
            'fixed': 2,
            'failed': 1,
            'skipped': 3,
            'details': [
                {'item_id': '1.0.1', 'success': True, 'message': 'Tasks regenerated'},
                {'item_id': '1.0.2', 'success': True, 'message': 'Tasks realigned'},
                {'item_id': '1.0.3', 'success': False, 'message': 'Story not found'},
            ]
        }

        summary = fixer.get_fix_summary(results)

        assert "Auto-Fix Summary" in summary
        assert "Fixed: 2" in summary
        assert "Failed: 1" in summary
        assert "Skipped: 3" in summary
        assert "[OK] 1.0.1" in summary
        assert "[FAILED] 1.0.3" in summary


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
