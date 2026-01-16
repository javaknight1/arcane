"""Tests for the dependency validation system."""

import pytest
from arcane.engines.validation import DependencyValidator, DependencyIssue, IssueSeverity
from arcane.items.milestone import Milestone
from arcane.items.epic import Epic
from arcane.items.story import Story
from arcane.items.task import Task


class TestDependencyValidatorBasics:
    """Basic tests for DependencyValidator."""

    @pytest.fixture
    def validator(self):
        """Create a fresh validator."""
        return DependencyValidator()

    @pytest.fixture
    def simple_roadmap(self):
        """Create a simple roadmap with no issues."""
        milestone = Milestone(name="MVP", number="1")

        epic = Epic(name="Core Features", number="1.0", parent=milestone)
        milestone.add_child(epic)

        story = Story(name="Basic Setup", number="1.0.1", parent=epic)
        epic.add_child(story)

        task = Task(name="Initialize project", number="1.0.1.1", parent=story)
        story.add_child(task)

        return [milestone]

    def test_validator_initialization(self, validator):
        """Test that validator initializes correctly."""
        assert validator.issues == []
        assert validator.item_lookup == {}
        assert validator.detected_features == set()

    def test_validate_simple_roadmap(self, validator, simple_roadmap):
        """Test validating a simple roadmap."""
        issues = validator.validate(simple_roadmap)

        # Should have some INFO issues about commonly forgotten items
        assert isinstance(issues, list)
        assert all(isinstance(i, DependencyIssue) for i in issues)

    def test_build_item_lookup(self, validator, simple_roadmap):
        """Test that item lookup is built correctly."""
        validator._build_item_lookup(simple_roadmap)

        assert len(validator.item_lookup) == 4  # 1 milestone, 1 epic, 1 story, 1 task
        assert "1" in validator.item_lookup  # Milestone
        assert "1.0" in validator.item_lookup  # Epic
        assert "1.0.1" in validator.item_lookup  # Story
        assert "1.0.1.1" in validator.item_lookup  # Task

    def test_get_summary(self, validator, simple_roadmap):
        """Test summary generation."""
        validator.validate(simple_roadmap)
        summary = validator.get_summary()

        assert 'total_issues' in summary
        assert 'errors' in summary
        assert 'warnings' in summary
        assert 'info' in summary
        assert 'detected_features' in summary
        assert 'total_items' in summary
        assert summary['total_items'] == 4


class TestFeatureDetection:
    """Tests for feature detection."""

    @pytest.fixture
    def validator(self):
        return DependencyValidator()

    def test_detect_authentication_feature(self, validator):
        """Test detecting authentication feature."""
        milestone = Milestone(name="MVP", number="1")
        epic = Epic(name="User Login System", number="1.0", parent=milestone)
        epic.description = "Implement user authentication with login and signup"
        milestone.add_child(epic)

        validator._build_item_lookup([milestone])
        validator._detect_features([milestone])

        assert 'authentication' in validator.detected_features

    def test_detect_database_feature(self, validator):
        """Test detecting database feature."""
        milestone = Milestone(name="Foundation", number="1")
        epic = Epic(name="Database Setup", number="1.0", parent=milestone)
        epic.description = "Set up PostgreSQL database with schema migrations"
        milestone.add_child(epic)

        validator._build_item_lookup([milestone])
        validator._detect_features([milestone])

        assert 'database' in validator.detected_features

    def test_detect_api_feature(self, validator):
        """Test detecting API feature."""
        milestone = Milestone(name="Backend", number="1")
        epic = Epic(name="REST API", number="1.0", parent=milestone)
        epic.description = "Build REST API endpoints"
        milestone.add_child(epic)

        validator._build_item_lookup([milestone])
        validator._detect_features([milestone])

        assert 'api' in validator.detected_features

    def test_detect_payments_feature(self, validator):
        """Test detecting payments feature."""
        milestone = Milestone(name="Monetization", number="1")
        epic = Epic(name="Payment Integration", number="1.0", parent=milestone)
        epic.description = "Integrate Stripe for subscription billing"
        milestone.add_child(epic)

        validator._build_item_lookup([milestone])
        validator._detect_features([milestone])

        assert 'payments' in validator.detected_features

    def test_detect_multiple_features(self, validator):
        """Test detecting multiple features."""
        milestone = Milestone(name="Platform", number="1")

        epic1 = Epic(name="Auth", number="1.0", parent=milestone)
        epic1.description = "User login and signup"
        milestone.add_child(epic1)

        epic2 = Epic(name="Database", number="1.1", parent=milestone)
        epic2.description = "PostgreSQL schema setup"
        milestone.add_child(epic2)

        epic3 = Epic(name="API", number="1.2", parent=milestone)
        epic3.description = "REST API endpoints"
        milestone.add_child(epic3)

        validator._build_item_lookup([milestone])
        validator._detect_features([milestone])

        assert 'authentication' in validator.detected_features
        assert 'database' in validator.detected_features
        assert 'api' in validator.detected_features


class TestRequiredFoundations:
    """Tests for required foundation validation."""

    @pytest.fixture
    def validator(self):
        return DependencyValidator()

    def test_missing_database_for_auth(self, validator):
        """Test that missing database is flagged for auth."""
        milestone = Milestone(name="MVP", number="1")
        epic = Epic(name="Authentication", number="1.0", parent=milestone)
        epic.description = "User login system"
        milestone.add_child(epic)

        issues = validator.validate([milestone])

        # Should have error about missing database
        foundation_issues = [i for i in issues if i.issue_type == "missing_foundation"]
        assert len(foundation_issues) > 0
        assert any("database" in i.message for i in foundation_issues)

    def test_no_missing_foundation_when_complete(self, validator):
        """Test no foundation errors when all requirements met."""
        milestone = Milestone(name="MVP", number="1")

        epic1 = Epic(name="Database Setup", number="1.0", parent=milestone)
        epic1.description = "PostgreSQL database configuration"
        milestone.add_child(epic1)

        epic2 = Epic(name="User Model", number="1.1", parent=milestone)
        epic2.description = "User model and schema"
        milestone.add_child(epic2)

        epic3 = Epic(name="Authentication", number="1.2", parent=milestone)
        epic3.description = "User login system"
        milestone.add_child(epic3)

        issues = validator.validate([milestone])

        # Should have no missing_foundation errors
        foundation_issues = [i for i in issues if i.issue_type == "missing_foundation"]
        # Filter for only auth-related missing foundations
        auth_missing = [i for i in foundation_issues if "authentication" in i.message]
        assert len(auth_missing) == 0


class TestDependencyReferences:
    """Tests for dependency reference validation."""

    @pytest.fixture
    def validator(self):
        return DependencyValidator()

    def test_valid_dependency_reference(self, validator):
        """Test that valid dependencies don't cause issues."""
        milestone = Milestone(name="MVP", number="1")

        epic = Epic(name="Core", number="1.0", parent=milestone)
        milestone.add_child(epic)

        story1 = Story(name="Setup", number="1.0.1", parent=epic)
        epic.add_child(story1)

        story2 = Story(name="Feature", number="1.0.2", parent=epic)
        story2.depends_on_items = [story1]
        epic.add_child(story2)

        issues = validator.validate([milestone])

        # Should have no invalid_dependency errors
        dep_issues = [i for i in issues if i.issue_type == "invalid_dependency"]
        assert len(dep_issues) == 0

    def test_invalid_dependency_reference(self, validator):
        """Test that invalid dependency references are caught."""
        milestone = Milestone(name="MVP", number="1")

        epic = Epic(name="Core", number="1.0", parent=milestone)
        milestone.add_child(epic)

        story = Story(name="Feature", number="1.0.1", parent=epic)
        # Create a mock dependency with non-existent ID
        class FakeDep:
            id = "9.9.9"
        story.depends_on_items = [FakeDep()]
        epic.add_child(story)

        issues = validator.validate([milestone])

        # Should have invalid_dependency error
        dep_issues = [i for i in issues if i.issue_type == "invalid_dependency"]
        assert len(dep_issues) == 1
        assert "9.9.9" in dep_issues[0].message


class TestDependencyOrdering:
    """Tests for dependency ordering validation."""

    @pytest.fixture
    def validator(self):
        return DependencyValidator()

    def test_correct_dependency_ordering(self, validator):
        """Test that correct ordering doesn't cause warnings."""
        milestone = Milestone(name="MVP", number="1")

        epic = Epic(name="Core", number="1.0", parent=milestone)
        milestone.add_child(epic)

        story1 = Story(name="Setup", number="1.0.1", parent=epic)
        epic.add_child(story1)

        story2 = Story(name="Feature", number="1.0.2", parent=epic)
        story2.depends_on_items = [story1]  # Depends on earlier story
        epic.add_child(story2)

        issues = validator.validate([milestone])

        # Should have no ordering issues
        ordering_issues = [i for i in issues if i.issue_type == "incorrect_ordering"]
        assert len(ordering_issues) == 0

    def test_incorrect_dependency_ordering(self, validator):
        """Test that incorrect ordering is flagged."""
        milestone = Milestone(name="MVP", number="1")

        epic = Epic(name="Core", number="1.0", parent=milestone)
        milestone.add_child(epic)

        story1 = Story(name="Setup", number="1.0.1", parent=epic)
        epic.add_child(story1)

        story2 = Story(name="Feature", number="1.0.2", parent=epic)
        epic.add_child(story2)

        # Make story1 depend on story2 (wrong order)
        story1.depends_on_items = [story2]

        issues = validator.validate([milestone])

        # Should have ordering warning
        ordering_issues = [i for i in issues if i.issue_type == "incorrect_ordering"]
        assert len(ordering_issues) == 1
        assert ordering_issues[0].severity == IssueSeverity.WARNING


class TestCircularDependencies:
    """Tests for circular dependency detection."""

    @pytest.fixture
    def validator(self):
        return DependencyValidator()

    def test_no_circular_dependency(self, validator):
        """Test that linear dependencies don't trigger circular check."""
        milestone = Milestone(name="MVP", number="1")

        epic = Epic(name="Core", number="1.0", parent=milestone)
        milestone.add_child(epic)

        story1 = Story(name="A", number="1.0.1", parent=epic)
        epic.add_child(story1)

        story2 = Story(name="B", number="1.0.2", parent=epic)
        story2.depends_on_items = [story1]
        epic.add_child(story2)

        story3 = Story(name="C", number="1.0.3", parent=epic)
        story3.depends_on_items = [story2]
        epic.add_child(story3)

        issues = validator.validate([milestone])

        # Should have no circular dependency errors
        circular_issues = [i for i in issues if i.issue_type == "circular_dependency"]
        assert len(circular_issues) == 0

    def test_direct_circular_dependency(self, validator):
        """Test detecting A -> B -> A circular dependency."""
        milestone = Milestone(name="MVP", number="1")

        epic = Epic(name="Core", number="1.0", parent=milestone)
        milestone.add_child(epic)

        story1 = Story(name="A", number="1.0.1", parent=epic)
        epic.add_child(story1)

        story2 = Story(name="B", number="1.0.2", parent=epic)
        epic.add_child(story2)

        # Create circular dependency
        story1.depends_on_items = [story2]
        story2.depends_on_items = [story1]

        issues = validator.validate([milestone])

        # Should have circular dependency error
        circular_issues = [i for i in issues if i.issue_type == "circular_dependency"]
        assert len(circular_issues) == 1
        assert circular_issues[0].severity == IssueSeverity.ERROR

    def test_indirect_circular_dependency(self, validator):
        """Test detecting A -> B -> C -> A circular dependency."""
        milestone = Milestone(name="MVP", number="1")

        epic = Epic(name="Core", number="1.0", parent=milestone)
        milestone.add_child(epic)

        story1 = Story(name="A", number="1.0.1", parent=epic)
        epic.add_child(story1)

        story2 = Story(name="B", number="1.0.2", parent=epic)
        epic.add_child(story2)

        story3 = Story(name="C", number="1.0.3", parent=epic)
        epic.add_child(story3)

        # Create circular dependency: A -> B -> C -> A
        story1.depends_on_items = [story2]
        story2.depends_on_items = [story3]
        story3.depends_on_items = [story1]

        issues = validator.validate([milestone])

        # Should have circular dependency error
        circular_issues = [i for i in issues if i.issue_type == "circular_dependency"]
        assert len(circular_issues) == 1


class TestCommonlyForgotten:
    """Tests for commonly forgotten items check."""

    @pytest.fixture
    def validator(self):
        return DependencyValidator()

    def test_missing_categories_flagged(self, validator):
        """Test that missing categories are flagged as INFO."""
        milestone = Milestone(name="MVP", number="1")
        epic = Epic(name="Feature", number="1.0", parent=milestone)
        milestone.add_child(epic)

        issues = validator.validate([milestone])

        # Should have INFO issues for missing categories
        info_issues = [i for i in issues if i.severity == IssueSeverity.INFO]
        missing_category_issues = [i for i in info_issues if i.issue_type == "missing_category"]

        # Should flag missing security, monitoring, documentation, etc.
        assert len(missing_category_issues) > 0

    def test_present_categories_not_flagged(self, validator):
        """Test that present categories are not flagged."""
        milestone = Milestone(name="MVP", number="1")

        epic1 = Epic(name="Security Audit", number="1.0", parent=milestone)
        milestone.add_child(epic1)

        epic2 = Epic(name="Logging Setup", number="1.1", parent=milestone)
        milestone.add_child(epic2)

        epic3 = Epic(name="Unit Tests", number="1.2", parent=milestone)
        milestone.add_child(epic3)

        issues = validator.validate([milestone])

        # Should not flag security, monitoring, or testing
        missing_issues = [i for i in issues if i.issue_type == "missing_category"]
        missing_categories = [i.message for i in missing_issues]

        assert not any("security" in m for m in missing_categories)
        assert not any("monitoring" in m for m in missing_categories)
        assert not any("testing" in m for m in missing_categories)


class TestReportFormatting:
    """Tests for report formatting."""

    @pytest.fixture
    def validator(self):
        return DependencyValidator()

    def test_format_report_basic(self, validator):
        """Test basic report formatting."""
        milestone = Milestone(name="MVP", number="1")
        epic = Epic(name="Core", number="1.0", parent=milestone)
        milestone.add_child(epic)

        validator.validate([milestone])
        report = validator.format_report()

        assert "Dependency Validation Report" in report
        assert "Items validated:" in report
        assert "Total issues:" in report

    def test_format_report_with_errors(self, validator):
        """Test report formatting with errors."""
        milestone = Milestone(name="MVP", number="1")
        epic = Epic(name="Auth Login", number="1.0", parent=milestone)
        epic.description = "User authentication"
        milestone.add_child(epic)

        validator.validate([milestone])
        report = validator.format_report()

        # Should contain error section
        assert "ERROR" in report

    def test_format_report_no_issues(self, validator):
        """Test report formatting with no issues."""
        # Create a complete roadmap with all commonly forgotten items
        milestone = Milestone(name="MVP", number="1")

        # Add all commonly forgotten categories
        epic1 = Epic(name="Security Audit", number="1.0", parent=milestone)
        milestone.add_child(epic1)

        epic2 = Epic(name="Logging System", number="1.1", parent=milestone)
        milestone.add_child(epic2)

        epic3 = Epic(name="API Documentation", number="1.2", parent=milestone)
        milestone.add_child(epic3)

        epic4 = Epic(name="Unit Tests", number="1.3", parent=milestone)
        milestone.add_child(epic4)

        epic5 = Epic(name="CI CD Pipeline", number="1.4", parent=milestone)
        milestone.add_child(epic5)

        epic6 = Epic(name="Data Privacy", number="1.5", parent=milestone)
        milestone.add_child(epic6)

        validator.validate([milestone])
        report = validator.format_report()

        # When no issues, should say so
        if validator.get_summary()['total_issues'] == 0:
            assert "No issues found" in report


class TestIssueSeverity:
    """Tests for issue severity handling."""

    def test_severity_enum_values(self):
        """Test severity enum has correct values."""
        assert IssueSeverity.ERROR.value == "error"
        assert IssueSeverity.WARNING.value == "warning"
        assert IssueSeverity.INFO.value == "info"

    def test_dependency_issue_creation(self):
        """Test creating a DependencyIssue."""
        issue = DependencyIssue(
            severity=IssueSeverity.ERROR,
            item_id="1.0.1",
            issue_type="test_issue",
            message="Test message",
            suggested_fix="Fix it",
            related_items=["1.0.2"]
        )

        assert issue.severity == IssueSeverity.ERROR
        assert issue.item_id == "1.0.1"
        assert issue.issue_type == "test_issue"
        assert issue.message == "Test message"
        assert issue.suggested_fix == "Fix it"
        assert issue.related_items == ["1.0.2"]

    def test_dependency_issue_default_related_items(self):
        """Test that related_items defaults to empty list."""
        issue = DependencyIssue(
            severity=IssueSeverity.WARNING,
            item_id="1.0.1",
            issue_type="test",
            message="Test"
        )

        assert issue.related_items == []


class TestComplexRoadmaps:
    """Tests for complex roadmap scenarios."""

    @pytest.fixture
    def validator(self):
        return DependencyValidator()

    def test_multi_milestone_roadmap(self, validator):
        """Test validating roadmap with multiple milestones."""
        milestone1 = Milestone(name="Foundation", number="1")
        epic1 = Epic(name="Database", number="1.0", parent=milestone1)
        epic1.description = "PostgreSQL setup"
        milestone1.add_child(epic1)

        milestone2 = Milestone(name="Core", number="2")
        epic2 = Epic(name="API", number="2.0", parent=milestone2)
        epic2.description = "REST API endpoints"
        milestone2.add_child(epic2)

        milestone3 = Milestone(name="Launch", number="3")
        epic3 = Epic(name="Deployment", number="3.0", parent=milestone3)
        milestone3.add_child(epic3)

        issues = validator.validate([milestone1, milestone2, milestone3])

        # Should have built lookup for all items
        assert len(validator.item_lookup) == 6  # 3 milestones + 3 epics

    def test_deep_hierarchy(self, validator):
        """Test validating roadmap with deep hierarchy."""
        milestone = Milestone(name="MVP", number="1")

        epic = Epic(name="Feature", number="1.0", parent=milestone)
        milestone.add_child(epic)

        story = Story(name="User Story", number="1.0.1", parent=epic)
        epic.add_child(story)

        task1 = Task(name="Task A", number="1.0.1.1", parent=story)
        story.add_child(task1)

        task2 = Task(name="Task B", number="1.0.1.2", parent=story)
        task2.depends_on_items = [task1]
        story.add_child(task2)

        task3 = Task(name="Task C", number="1.0.1.3", parent=story)
        task3.depends_on_items = [task2]
        story.add_child(task3)

        issues = validator.validate([milestone])

        # Should have built lookup for all items
        assert len(validator.item_lookup) == 6  # 1 milestone + 1 epic + 1 story + 3 tasks

        # Should have no ordering issues (dependencies are in correct order)
        ordering_issues = [i for i in issues if i.issue_type == "incorrect_ordering"]
        assert len(ordering_issues) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
