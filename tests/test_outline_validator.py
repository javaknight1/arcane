"""Tests for pre-generation outline validation."""

import pytest

from arcane.engines.validation.outline_validator import (
    OutlineValidator,
    OutlineIssue,
    OutlineSeverity,
)


class TestOutlineValidatorInit:
    """Tests for OutlineValidator initialization."""

    def test_init(self):
        """Test validator initialization."""
        validator = OutlineValidator()
        assert validator.issues == []
        assert validator._parsed_items == {}


class TestOutlineParsing:
    """Tests for outline parsing."""

    @pytest.fixture
    def validator(self):
        return OutlineValidator()

    def test_parses_milestones(self, validator):
        """Test parsing milestone lines."""
        outline = """
## Milestone 1: Foundation
## Milestone 2: Features
"""
        validator._parse_outline(outline)

        assert 'M1' in validator._parsed_items
        assert 'M2' in validator._parsed_items
        assert validator._parsed_items['M1']['name'] == 'Foundation'
        assert validator._parsed_items['M2']['name'] == 'Features'

    def test_parses_epics(self, validator):
        """Test parsing epic lines."""
        outline = """
## Milestone 1: Foundation
### Epic 1.0: Setup
### Epic 1.1: Configuration
"""
        validator._parse_outline(outline)

        assert 'E1.0' in validator._parsed_items
        assert 'E1.1' in validator._parsed_items
        assert validator._parsed_items['E1.0']['parent_milestone'] == '1'

    def test_parses_stories(self, validator):
        """Test parsing story lines."""
        outline = """
## Milestone 1: Foundation
### Epic 1.0: Setup
#### Story 1.0.1: Initial Setup
#### Story 1.0.2: Configuration
"""
        validator._parse_outline(outline)

        assert 'S1.0.1' in validator._parsed_items
        assert 'S1.0.2' in validator._parsed_items
        assert validator._parsed_items['S1.0.1']['parent_epic'] == '1.0'

    def test_parses_tasks(self, validator):
        """Test parsing task lines."""
        outline = """
## Milestone 1: Foundation
### Epic 1.0: Setup
#### Story 1.0.1: Initial Setup
##### Task 1.0.1.1: Create project
##### Task 1.0.1.2: Add dependencies
"""
        validator._parse_outline(outline)

        assert 'T1.0.1.1' in validator._parsed_items
        assert 'T1.0.1.2' in validator._parsed_items
        assert validator._parsed_items['T1.0.1.1']['parent_story'] == '1.0.1'

    def test_tracks_line_numbers(self, validator):
        """Test that line numbers are tracked."""
        outline = """
## Milestone 1: Foundation
### Epic 1.0: Setup
"""
        validator._parse_outline(outline)

        # Line 2 is the milestone (line 1 is empty)
        assert validator._parsed_items['M1']['line'] == 2
        assert validator._parsed_items['E1.0']['line'] == 3


class TestNumberingValidation:
    """Tests for numbering validation."""

    @pytest.fixture
    def validator(self):
        return OutlineValidator()

    def test_valid_sequential_numbering(self, validator):
        """Test that sequential numbering passes."""
        outline = """
## Milestone 1: First
## Milestone 2: Second
## Milestone 3: Third
"""
        issues = validator.validate(outline)
        numbering_issues = [i for i in issues if i.issue_type == 'numbering_gap']
        assert len(numbering_issues) == 0

    def test_detects_milestone_gap(self, validator):
        """Test detection of gap in milestone numbering."""
        outline = """
## Milestone 1: First
## Milestone 3: Third
"""
        issues = validator.validate(outline)
        gap_issues = [i for i in issues if i.issue_type == 'numbering_gap']
        assert len(gap_issues) >= 1
        assert any('expected 2' in i.message for i in gap_issues)

    def test_detects_duplicate_milestone(self, validator):
        """Test detection of duplicate milestone number."""
        outline = """
## Milestone 1: First
## Milestone 1: Also First
"""
        issues = validator.validate(outline)
        dup_issues = [i for i in issues if i.issue_type == 'duplicate_number']
        assert len(dup_issues) >= 1
        assert dup_issues[0].severity == OutlineSeverity.ERROR

    def test_detects_duplicate_epic(self, validator):
        """Test detection of duplicate epic number."""
        outline = """
## Milestone 1: Foundation
### Epic 1.0: Setup
### Epic 1.0: Also Setup
"""
        issues = validator.validate(outline)
        dup_issues = [i for i in issues if i.issue_type == 'duplicate_number' and 'epic' in i.message.lower()]
        assert len(dup_issues) >= 1

    def test_detects_epic_gap(self, validator):
        """Test detection of gap in epic numbering."""
        outline = """
## Milestone 1: Foundation
### Epic 1.0: First
### Epic 1.2: Third
"""
        issues = validator.validate(outline)
        gap_issues = [i for i in issues if i.issue_type == 'numbering_gap' and 'epic' in i.message.lower()]
        assert len(gap_issues) >= 1


class TestHierarchyValidation:
    """Tests for hierarchy validation."""

    @pytest.fixture
    def validator(self):
        return OutlineValidator()

    def test_valid_hierarchy(self, validator):
        """Test that valid hierarchy passes."""
        outline = """
## Milestone 1: Foundation
### Epic 1.0: Setup
#### Story 1.0.1: Initial
"""
        issues = validator.validate(outline)
        orphan_issues = [i for i in issues if i.issue_type == 'orphan_item']
        assert len(orphan_issues) == 0

    def test_detects_orphan_epic(self, validator):
        """Test detection of epic without milestone parent."""
        outline = """
### Epic 2.0: Orphan Epic
"""
        issues = validator.validate(outline)
        orphan_issues = [i for i in issues if i.issue_type == 'orphan_item']
        assert len(orphan_issues) >= 1
        assert any('Epic 2.0' in i.message for i in orphan_issues)

    def test_detects_orphan_story(self, validator):
        """Test detection of story without epic parent."""
        outline = """
## Milestone 1: Foundation
#### Story 1.1.1: Orphan Story
"""
        issues = validator.validate(outline)
        orphan_issues = [i for i in issues if i.issue_type == 'orphan_item']
        assert any('Story 1.1.1' in i.message for i in orphan_issues)

    def test_detects_orphan_task(self, validator):
        """Test detection of task without story parent."""
        outline = """
## Milestone 1: Foundation
### Epic 1.0: Setup
##### Task 1.0.5.1: Orphan Task
"""
        issues = validator.validate(outline)
        orphan_issues = [i for i in issues if i.issue_type == 'orphan_item']
        assert any('Task 1.0.5.1' in i.message for i in orphan_issues)


class TestCompletenessValidation:
    """Tests for completeness validation."""

    @pytest.fixture
    def validator(self):
        return OutlineValidator()

    def test_detects_empty_outline(self, validator):
        """Test detection of empty outline."""
        outline = """
Some random text
No milestones here
"""
        issues = validator.validate(outline)
        empty_issues = [i for i in issues if i.issue_type == 'empty_outline']
        assert len(empty_issues) == 1
        assert empty_issues[0].severity == OutlineSeverity.ERROR

    def test_detects_empty_milestone(self, validator):
        """Test detection of milestone with no epics."""
        outline = """
## Milestone 1: Foundation
## Milestone 2: Empty
### Epic 1.0: Belongs to M1
"""
        issues = validator.validate(outline)
        empty_issues = [i for i in issues if i.issue_type == 'empty_milestone']
        assert any('Milestone 2' in i.message for i in empty_issues)

    def test_detects_empty_epic(self, validator):
        """Test detection of epic with no stories."""
        outline = """
## Milestone 1: Foundation
### Epic 1.0: Has Stories
### Epic 1.1: Empty
#### Story 1.0.1: In first epic
"""
        issues = validator.validate(outline)
        empty_issues = [i for i in issues if i.issue_type == 'empty_epic']
        assert any('Epic 1.1' in i.message for i in empty_issues)

    def test_story_no_tasks_is_info(self, validator):
        """Test that story without tasks is INFO level (tasks will be generated)."""
        outline = """
## Milestone 1: Foundation
### Epic 1.0: Setup
#### Story 1.0.1: No Tasks Yet
"""
        issues = validator.validate(outline)
        no_task_issues = [i for i in issues if i.issue_type == 'story_no_tasks']
        assert len(no_task_issues) >= 1
        assert no_task_issues[0].severity == OutlineSeverity.INFO


class TestScopeBalanceValidation:
    """Tests for scope balance validation."""

    @pytest.fixture
    def validator(self):
        return OutlineValidator()

    def test_balanced_milestones_pass(self, validator):
        """Test that balanced milestones don't trigger warnings."""
        outline = """
## Milestone 1: Foundation
### Epic 1.0: Setup
#### Story 1.0.1: Init
#### Story 1.0.2: Config

## Milestone 2: Features
### Epic 2.0: Core
#### Story 2.0.1: Feature A
#### Story 2.0.2: Feature B
"""
        issues = validator.validate(outline)
        balance_issues = [i for i in issues if i.issue_type == 'unbalanced_milestone']
        assert len(balance_issues) == 0

    def test_detects_very_small_milestone(self, validator):
        """Test detection of very small milestone compared to others."""
        outline = """
## Milestone 1: Big
### Epic 1.0: Lots of content
#### Story 1.0.1: S1
#### Story 1.0.2: S2
#### Story 1.0.3: S3
#### Story 1.0.4: S4
#### Story 1.0.5: S5
#### Story 1.0.6: S6
#### Story 1.0.7: S7
#### Story 1.0.8: S8
#### Story 1.0.9: S9
#### Story 1.0.10: S10

## Milestone 2: Tiny
### Epic 2.0: Small
"""
        issues = validator.validate(outline)
        balance_issues = [i for i in issues if i.issue_type == 'unbalanced_milestone']
        assert any('Milestone 2' in i.message for i in balance_issues)


class TestRequiredComponentsValidation:
    """Tests for required components validation."""

    @pytest.fixture
    def validator(self):
        return OutlineValidator()

    def test_detects_missing_required_for_web_app(self, validator):
        """Test detection of missing required components for web app."""
        outline = """
## Milestone 1: Foundation
### Epic 1.0: UI Components
#### Story 1.0.1: Build pages
"""
        issues = validator.validate(outline, project_type='web_app')
        missing_issues = [i for i in issues if i.issue_type == 'missing_component']

        # Should flag missing authentication, database, api
        assert any('authentication' in i.message for i in missing_issues)
        assert any('database' in i.message for i in missing_issues)
        assert any('api' in i.message for i in missing_issues)

    def test_detects_missing_required_for_saas(self, validator):
        """Test detection of missing billing for SaaS."""
        outline = """
## Milestone 1: Foundation
### Epic 1.0: Auth
#### Story 1.0.1: Login functionality
### Epic 1.1: Database
#### Story 1.1.1: Schema design
### Epic 1.2: API
#### Story 1.2.1: Endpoints
"""
        issues = validator.validate(outline, project_type='saas')
        missing_issues = [i for i in issues if i.issue_type == 'missing_component']

        # Should flag missing billing
        assert any('billing' in i.message for i in missing_issues)

    def test_no_missing_when_components_present(self, validator):
        """Test that no missing components when all present."""
        outline = """
## Milestone 1: Foundation
### Epic 1.0: Authentication System
#### Story 1.0.1: Login and signup
### Epic 1.1: Database Layer
#### Story 1.1.1: Schema and migrations
### Epic 1.2: API Endpoints
#### Story 1.2.1: REST routes
"""
        issues = validator.validate(outline, project_type='web_app')
        missing_required = [i for i in issues if i.issue_type == 'missing_component']
        assert len(missing_required) == 0

    def test_recommended_components_are_info(self, validator):
        """Test that missing recommended components are INFO level."""
        outline = """
## Milestone 1: Foundation
### Epic 1.0: Auth
#### Story 1.0.1: Login with OAuth
### Epic 1.1: Database
#### Story 1.1.1: PostgreSQL setup
### Epic 1.2: API
#### Story 1.2.1: REST endpoints
"""
        issues = validator.validate(outline, project_type='web_app')
        recommended_issues = [i for i in issues if i.issue_type == 'missing_recommended']

        # Should suggest testing, deployment, monitoring
        assert all(i.severity == OutlineSeverity.INFO for i in recommended_issues)


class TestValidateFull:
    """Integration tests for full validation."""

    @pytest.fixture
    def validator(self):
        return OutlineValidator()

    def test_valid_complete_outline(self, validator):
        """Test that a valid outline passes with no errors."""
        outline = """
# Project Roadmap

## Milestone 1: Foundation
### Epic 1.0: Project Setup
#### Story 1.0.1: Initialize Repository
##### Task 1.0.1.1: Create git repo
##### Task 1.0.1.2: Add initial files
#### Story 1.0.2: Configure Tools
##### Task 1.0.2.1: Setup linting
##### Task 1.0.2.2: Setup formatting

### Epic 1.1: Authentication
#### Story 1.1.1: User Login
##### Task 1.1.1.1: Create login form
##### Task 1.1.1.2: Implement auth API

## Milestone 2: Features
### Epic 2.0: Core Functionality
#### Story 2.0.1: Main Feature
##### Task 2.0.1.1: Implement feature
##### Task 2.0.1.2: Add tests
"""
        issues = validator.validate(outline)
        errors = [i for i in issues if i.severity == OutlineSeverity.ERROR]
        assert len(errors) == 0

    def test_multiple_issues_detected(self, validator):
        """Test that multiple issues are detected and sorted."""
        outline = """
## Milestone 1: Foundation
## Milestone 1: Duplicate

### Epic 2.0: Orphan Epic

## Milestone 3: Has Gap
"""
        issues = validator.validate(outline)

        # Should have errors (duplicate, orphan) and warnings (gap)
        errors = [i for i in issues if i.severity == OutlineSeverity.ERROR]
        warnings = [i for i in issues if i.severity == OutlineSeverity.WARNING]

        assert len(errors) >= 2  # Duplicate + orphan
        assert len(warnings) >= 1  # Gap

        # Errors should come first
        if issues:
            assert issues[0].severity == OutlineSeverity.ERROR


class TestHelperMethods:
    """Tests for helper methods."""

    @pytest.fixture
    def validator(self):
        return OutlineValidator()

    def test_has_errors(self, validator):
        """Test has_errors method."""
        validator.issues = [
            OutlineIssue(OutlineSeverity.WARNING, 'test', 'warning'),
            OutlineIssue(OutlineSeverity.INFO, 'test', 'info'),
        ]
        assert validator.has_errors() is False

        validator.issues.append(
            OutlineIssue(OutlineSeverity.ERROR, 'test', 'error')
        )
        assert validator.has_errors() is True

    def test_has_warnings(self, validator):
        """Test has_warnings method."""
        validator.issues = [
            OutlineIssue(OutlineSeverity.INFO, 'test', 'info'),
        ]
        assert validator.has_warnings() is False

        validator.issues.append(
            OutlineIssue(OutlineSeverity.WARNING, 'test', 'warning')
        )
        assert validator.has_warnings() is True

    def test_get_summary(self, validator):
        """Test get_summary method."""
        validator.issues = [
            OutlineIssue(OutlineSeverity.ERROR, 'test', 'e1'),
            OutlineIssue(OutlineSeverity.ERROR, 'test', 'e2'),
            OutlineIssue(OutlineSeverity.WARNING, 'test', 'w1'),
            OutlineIssue(OutlineSeverity.INFO, 'test', 'i1'),
            OutlineIssue(OutlineSeverity.INFO, 'test', 'i2'),
            OutlineIssue(OutlineSeverity.INFO, 'test', 'i3'),
        ]

        summary = validator.get_summary()
        assert summary['errors'] == 2
        assert summary['warnings'] == 1
        assert summary['info'] == 3

    def test_format_issues(self, validator):
        """Test format_issues method."""
        validator.issues = [
            OutlineIssue(
                OutlineSeverity.ERROR,
                'test_error',
                'This is an error',
                line_number=5,
                suggested_fix='Fix this error'
            ),
            OutlineIssue(
                OutlineSeverity.WARNING,
                'test_warning',
                'This is a warning',
            ),
            OutlineIssue(
                OutlineSeverity.INFO,
                'test_info',
                'This is info',
            ),
        ]

        # Without info
        formatted = validator.format_issues(show_info=False)
        assert 'ERROR' in formatted
        assert 'WARNING' in formatted
        assert 'info' not in formatted.lower() or 'This is info' not in formatted
        assert 'line 5' in formatted
        assert 'Fix this error' in formatted

        # With info
        formatted_with_info = validator.format_issues(show_info=True)
        assert 'INFO' in formatted_with_info
        assert 'This is info' in formatted_with_info


class TestComponentKeywords:
    """Tests for component keyword detection."""

    @pytest.fixture
    def validator(self):
        return OutlineValidator()

    def test_detects_auth_keywords(self, validator):
        """Test detection of authentication keywords."""
        outline = """
## Milestone 1: Foundation
### Epic 1.0: User Login System
#### Story 1.0.1: OAuth integration
"""
        assert validator._component_present(outline.lower(), 'authentication')

    def test_detects_database_keywords(self, validator):
        """Test detection of database keywords."""
        outline = """
## Milestone 1: Foundation
### Epic 1.0: PostgreSQL Setup
#### Story 1.0.1: Schema migration
"""
        assert validator._component_present(outline.lower(), 'database')

    def test_detects_api_keywords(self, validator):
        """Test detection of API keywords."""
        outline = """
## Milestone 1: Foundation
### Epic 1.0: REST API
#### Story 1.0.1: GraphQL endpoints
"""
        assert validator._component_present(outline.lower(), 'api')


class TestEdgeCases:
    """Tests for edge cases."""

    @pytest.fixture
    def validator(self):
        return OutlineValidator()

    def test_empty_string(self, validator):
        """Test validation of empty string."""
        issues = validator.validate("")
        assert any(i.issue_type == 'empty_outline' for i in issues)

    def test_whitespace_only(self, validator):
        """Test validation of whitespace-only outline."""
        issues = validator.validate("   \n\n   \n")
        assert any(i.issue_type == 'empty_outline' for i in issues)

    def test_case_insensitive_parsing(self, validator):
        """Test that parsing is case-insensitive."""
        outline = """
## MILESTONE 1: Foundation
### EPIC 1.0: Setup
#### STORY 1.0.1: Init
"""
        validator._parse_outline(outline)
        assert 'M1' in validator._parsed_items
        assert 'E1.0' in validator._parsed_items
        assert 'S1.0.1' in validator._parsed_items

    def test_unknown_project_type(self, validator):
        """Test that unknown project type doesn't cause errors."""
        outline = """
## Milestone 1: Foundation
### Epic 1.0: Setup
#### Story 1.0.1: Init
"""
        # Should not raise
        issues = validator.validate(outline, project_type='unknown_type')
        # Should have no missing component issues for unknown type
        component_issues = [i for i in issues if 'component' in i.issue_type]
        assert len(component_issues) == 0

    def test_single_milestone(self, validator):
        """Test outline with single milestone (no balance check)."""
        outline = """
## Milestone 1: Only One
### Epic 1.0: Setup
#### Story 1.0.1: Init
"""
        issues = validator.validate(outline)
        balance_issues = [i for i in issues if i.issue_type == 'unbalanced_milestone']
        assert len(balance_issues) == 0  # Can't compare with just one


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
