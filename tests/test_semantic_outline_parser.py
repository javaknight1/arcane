"""Tests for semantic outline parser."""

import pytest
from arcane.engines.parsing.semantic_outline_parser import SemanticOutlineParser
from arcane.models.outline_item import OutlineItemType


SAMPLE_SEMANTIC_OUTLINE = '''
===PROJECT_METADATA===
PROJECT_NAME: Test Project
PROJECT_TYPE: web app
TECH_STACK: Python, FastAPI, React
ESTIMATED_DURATION: 3 months
TEAM_SIZE: 3
DESCRIPTION: A sample test project for unit testing
===END_METADATA===

# Test Project

## Milestone 1: Foundation
> Establishes core infrastructure. All features depend on this.
> Dependencies: None

### Epic 1.0: Database Setup
> Sets up PostgreSQL database with migrations. Required for data persistence.
> Dependencies: None

#### Story 1.0.1: Schema Design
> Design core database schema. Foundation for all data operations.
> Dependencies: None

##### Task 1.0.1.1: User Table
> Create users table with auth fields. Stores user credentials.
> Dependencies: None

##### Task 1.0.1.2: Session Table
> Create sessions table for JWT tokens. Enables token management.
> Dependencies: Task 1.0.1.1

### Epic 1.1: Authentication
> Complete auth system. Enables secure access.
> Dependencies: Epic 1.0

#### Story 1.1.1: Login Flow
> Implements login with email/password. Core user authentication.
> Dependencies: Story 1.0.1

##### Task 1.1.1.1: Login API
> Create POST /auth/login endpoint. Handles user authentication.
> Dependencies: Task 1.0.1.1, Task 1.0.1.2

## Milestone 2: Core Features
> Builds main application features. Delivers primary user value.
> Dependencies: 1

### Epic 2.0: User Management
> User CRUD operations. Enables user profile management.
> Dependencies: 1.1

#### Story 2.0.1: User Profile
> User profile page. Displays and edits user information.
> Dependencies: 1.1.1

##### Task 2.0.1.1: Profile API
> Create user profile endpoints. Serves profile data.
> Dependencies: 1.1.1.1
'''


class TestSemanticOutlineParser:
    """Tests for SemanticOutlineParser class."""

    def test_parse_basic_structure(self):
        """Test parsing of basic outline structure."""
        parser = SemanticOutlineParser()
        outline = parser.parse(SAMPLE_SEMANTIC_OUTLINE)

        # Check milestone count
        assert len(outline.milestones) == 2

        # Check epic count
        milestone = outline.milestones[0]
        assert len(milestone.children) == 2

        # Check story count in first epic
        epic = milestone.children[0]
        assert len(epic.children) == 1

        # Check task count
        story = epic.children[0]
        assert len(story.children) == 2

    def test_parse_metadata(self):
        """Test parsing of project metadata."""
        parser = SemanticOutlineParser()
        outline = parser.parse(SAMPLE_SEMANTIC_OUTLINE)

        assert outline.project_name == "Test Project"
        assert outline.project_type == "web app"
        assert outline.tech_stack == "Python, FastAPI, React"
        assert "sample test project" in outline.project_description.lower()

    def test_parse_item_titles(self):
        """Test that item titles are correctly parsed."""
        parser = SemanticOutlineParser()
        outline = parser.parse(SAMPLE_SEMANTIC_OUTLINE)

        milestone = outline.get_item_by_id("1")
        assert milestone is not None
        assert milestone.title == "Foundation"

        epic = outline.get_item_by_id("1.0")
        assert epic is not None
        assert epic.title == "Database Setup"

        story = outline.get_item_by_id("1.0.1")
        assert story is not None
        assert story.title == "Schema Design"

        task = outline.get_item_by_id("1.0.1.1")
        assert task is not None
        assert task.title == "User Table"

    def test_parse_item_types(self):
        """Test that item types are correctly assigned."""
        parser = SemanticOutlineParser()
        outline = parser.parse(SAMPLE_SEMANTIC_OUTLINE)

        assert outline.get_item_by_id("1").item_type == OutlineItemType.MILESTONE
        assert outline.get_item_by_id("1.0").item_type == OutlineItemType.EPIC
        assert outline.get_item_by_id("1.0.1").item_type == OutlineItemType.STORY
        assert outline.get_item_by_id("1.0.1.1").item_type == OutlineItemType.TASK

    def test_parse_descriptions(self):
        """Test parsing of item descriptions."""
        parser = SemanticOutlineParser()
        outline = parser.parse(SAMPLE_SEMANTIC_OUTLINE)

        milestone = outline.get_item_by_id("1")
        assert "core infrastructure" in milestone.description.full_text.lower()

        epic = outline.get_item_by_id("1.0")
        assert "postgresql" in epic.description.full_text.lower()

        story = outline.get_item_by_id("1.0.1")
        assert "database schema" in story.description.full_text.lower()

    def test_parse_description_what_why(self):
        """Test that descriptions are split into what/why."""
        parser = SemanticOutlineParser()
        outline = parser.parse(SAMPLE_SEMANTIC_OUTLINE)

        task = outline.get_item_by_id("1.0.1.1")
        assert task.description.what  # Should have 'what' part
        assert task.description.why  # Should have 'why' part

    def test_parse_dependencies_none(self):
        """Test parsing items with no dependencies."""
        parser = SemanticOutlineParser()
        outline = parser.parse(SAMPLE_SEMANTIC_OUTLINE)

        task = outline.get_item_by_id("1.0.1.1")
        assert len(task.dependencies) == 0
        assert not task.has_dependencies()

    def test_parse_dependencies_single(self):
        """Test parsing items with single dependency."""
        parser = SemanticOutlineParser()
        outline = parser.parse(SAMPLE_SEMANTIC_OUTLINE)

        task = outline.get_item_by_id("1.0.1.2")
        assert len(task.dependencies) == 1
        assert task.dependencies[0].item_id == "1.0.1.1"
        assert task.has_dependencies()

    def test_parse_dependencies_multiple(self):
        """Test parsing items with multiple dependencies."""
        parser = SemanticOutlineParser()
        outline = parser.parse(SAMPLE_SEMANTIC_OUTLINE)

        task = outline.get_item_by_id("1.1.1.1")
        assert len(task.dependencies) == 2
        dep_ids = [d.item_id for d in task.dependencies]
        assert "1.0.1.1" in dep_ids
        assert "1.0.1.2" in dep_ids

    def test_parse_dependencies_cross_epic(self):
        """Test parsing cross-epic dependencies."""
        parser = SemanticOutlineParser()
        outline = parser.parse(SAMPLE_SEMANTIC_OUTLINE)

        epic = outline.get_item_by_id("1.1")
        assert len(epic.dependencies) == 1
        assert epic.dependencies[0].item_id == "1.0"

    def test_parse_dependencies_cross_milestone(self):
        """Test parsing cross-milestone dependencies."""
        parser = SemanticOutlineParser()
        outline = parser.parse(SAMPLE_SEMANTIC_OUTLINE)

        milestone2 = outline.get_item_by_id("2")
        assert len(milestone2.dependencies) == 1
        assert milestone2.dependencies[0].item_id == "1"

    def test_validate_dependencies(self):
        """Test dependency validation."""
        parser = SemanticOutlineParser()
        outline = parser.parse(SAMPLE_SEMANTIC_OUTLINE)

        issues = outline.validate_dependencies()
        assert len(issues) == 0  # All dependencies should exist

    def test_validate_invalid_dependencies(self):
        """Test validation catches invalid dependencies."""
        invalid_outline = '''
## Milestone 1: Foundation
> Foundation phase.
> Dependencies: 99.99.99

### Epic 1.0: Setup
> Setup phase.
> Dependencies: None

#### Story 1.0.1: Init
> Initialize.
> Dependencies: None

##### Task 1.0.1.1: Task
> A task.
> Dependencies: None
'''
        parser = SemanticOutlineParser()
        outline = parser.parse(invalid_outline)

        issues = outline.validate_dependencies()
        assert len(issues) > 0
        assert any("99.99.99" in issue for issue in issues)

    def test_generation_order(self):
        """Test that generation order respects dependencies."""
        parser = SemanticOutlineParser()
        outline = parser.parse(SAMPLE_SEMANTIC_OUTLINE)

        order = outline.get_generation_order()

        # Find positions
        positions = {item.id: i for i, item in enumerate(order)}

        # Task 1.0.1.1 should come before 1.0.1.2
        assert positions.get("1.0.1.1", 999) < positions.get("1.0.1.2", 999)

        # Epic 1.0 should come before Epic 1.1
        assert positions.get("1.0", 999) < positions.get("1.1", 999)

        # Milestone 1 should come before Milestone 2
        assert positions.get("1", 999) < positions.get("2", 999)

    def test_statistics(self):
        """Test outline statistics."""
        parser = SemanticOutlineParser()
        outline = parser.parse(SAMPLE_SEMANTIC_OUTLINE)

        stats = outline.get_statistics()

        assert stats['milestones'] == 2
        assert stats['epics'] == 3  # 1.0, 1.1, 2.0
        assert stats['stories'] == 3  # 1.0.1, 1.1.1, 2.0.1
        assert stats['tasks'] == 4  # 1.0.1.1, 1.0.1.2, 1.1.1.1, 2.0.1.1
        assert stats['items_with_dependencies'] > 0

    def test_get_item_by_id(self):
        """Test getting items by ID."""
        parser = SemanticOutlineParser()
        outline = parser.parse(SAMPLE_SEMANTIC_OUTLINE)

        item = outline.get_item_by_id("1.0.1")
        assert item is not None
        assert item.title == "Schema Design"

        # Non-existent item
        assert outline.get_item_by_id("99.99.99") is None

    def test_get_items_by_type(self):
        """Test getting items by type."""
        parser = SemanticOutlineParser()
        outline = parser.parse(SAMPLE_SEMANTIC_OUTLINE)

        milestones = outline.get_milestones()
        assert len(milestones) == 2

        epics = outline.get_epics()
        assert len(epics) == 3

        stories = outline.get_stories()
        assert len(stories) == 3

        tasks = outline.get_tasks()
        assert len(tasks) == 4

    def test_parent_child_relationships(self):
        """Test parent-child relationships are set correctly."""
        parser = SemanticOutlineParser()
        outline = parser.parse(SAMPLE_SEMANTIC_OUTLINE)

        story = outline.get_item_by_id("1.0.1")
        assert story.parent is not None
        assert story.parent.id == "1.0"

        epic = outline.get_item_by_id("1.0")
        assert epic.parent is not None
        assert epic.parent.id == "1"

        milestone = outline.get_item_by_id("1")
        assert milestone.parent is None

    def test_children_list(self):
        """Test children lists are populated correctly."""
        parser = SemanticOutlineParser()
        outline = parser.parse(SAMPLE_SEMANTIC_OUTLINE)

        milestone = outline.get_item_by_id("1")
        assert len(milestone.children) == 2
        child_ids = [c.id for c in milestone.children]
        assert "1.0" in child_ids
        assert "1.1" in child_ids

    def test_get_dependents(self):
        """Test getting items that depend on a given item."""
        parser = SemanticOutlineParser()
        outline = parser.parse(SAMPLE_SEMANTIC_OUTLINE)

        dependents = outline.get_dependents("1.0.1.1")
        dependent_ids = [d.id for d in dependents]
        assert "1.0.1.2" in dependent_ids
        assert "1.1.1.1" in dependent_ids

    def test_line_numbers(self):
        """Test that line numbers are captured."""
        parser = SemanticOutlineParser()
        outline = parser.parse(SAMPLE_SEMANTIC_OUTLINE)

        milestone = outline.get_item_by_id("1")
        assert milestone.line_number > 0

        task = outline.get_item_by_id("1.0.1.1")
        assert task.line_number > 0
        assert task.line_number > milestone.line_number

    def test_to_dict(self):
        """Test dictionary conversion."""
        parser = SemanticOutlineParser()
        outline = parser.parse(SAMPLE_SEMANTIC_OUTLINE)

        d = outline.to_dict()
        assert d['project_name'] == "Test Project"
        assert len(d['items']) > 0
        assert 'statistics' in d


class TestSemanticOutlineParserErrors:
    """Tests for parser error handling."""

    def test_epic_without_milestone(self):
        """Test error when epic has no parent milestone."""
        outline_text = '''
### Epic 1.0: Orphan Epic
> An epic without a milestone.
> Dependencies: None

#### Story 1.0.1: Story
> A story.
> Dependencies: None

##### Task 1.0.1.1: Task
> A task.
> Dependencies: None
'''
        parser = SemanticOutlineParser()
        outline = parser.parse(outline_text)

        assert parser.has_errors()
        assert any("no parent milestone" in e.lower() for e in parser.parse_errors)

    def test_story_without_epic(self):
        """Test error when story has no parent epic."""
        outline_text = '''
## Milestone 1: Foundation
> Foundation.
> Dependencies: None

#### Story 1.0.1: Orphan Story
> A story without an epic.
> Dependencies: None

##### Task 1.0.1.1: Task
> A task.
> Dependencies: None
'''
        parser = SemanticOutlineParser()
        outline = parser.parse(outline_text)

        assert parser.has_errors()
        assert any("no parent epic" in e.lower() for e in parser.parse_errors)

    def test_task_without_story(self):
        """Test error when task has no parent story."""
        outline_text = '''
## Milestone 1: Foundation
> Foundation.
> Dependencies: None

### Epic 1.0: Setup
> Setup.
> Dependencies: None

##### Task 1.0.1.1: Orphan Task
> A task without a story.
> Dependencies: None
'''
        parser = SemanticOutlineParser()
        outline = parser.parse(outline_text)

        assert parser.has_errors()
        assert any("no parent story" in e.lower() for e in parser.parse_errors)

    def test_circular_dependency_detection(self):
        """Test detection of circular dependencies."""
        outline_text = '''
## Milestone 1: Foundation
> Foundation phase.
> Dependencies: 2

## Milestone 2: Development
> Development phase.
> Dependencies: 1
'''
        parser = SemanticOutlineParser()
        outline = parser.parse(outline_text)

        assert parser.has_errors()
        assert any("circular" in e.lower() for e in parser.parse_errors)

    def test_missing_description_warning(self):
        """Test warning for missing descriptions."""
        outline_text = '''
## Milestone 1: Foundation
> Dependencies: None

### Epic 1.0: Setup
> Dependencies: None

#### Story 1.0.1: Story
> Dependencies: None

##### Task 1.0.1.1: Task
> Dependencies: None
'''
        parser = SemanticOutlineParser()
        outline = parser.parse(outline_text)

        assert parser.has_warnings()
        assert any("no description" in w.lower() for w in parser.parse_warnings)

    def test_parse_report(self):
        """Test parse report generation."""
        parser = SemanticOutlineParser()
        outline = parser.parse(SAMPLE_SEMANTIC_OUTLINE)

        report = parser.get_parse_report()
        assert "Semantic Outline Parse Report" in report


class TestDependencyParsing:
    """Tests for dependency parsing edge cases."""

    def test_parse_dependency_with_type_prefix(self):
        """Test parsing dependencies with type prefix."""
        outline_text = '''
## Milestone 1: Foundation
> Foundation.
> Dependencies: None

### Epic 1.0: Setup
> Setup phase.
> Dependencies: None

#### Story 1.0.1: Story
> A story.
> Dependencies: None

##### Task 1.0.1.1: First Task
> First task.
> Dependencies: None

##### Task 1.0.1.2: Second Task
> Second task.
> Dependencies: Task 1.0.1.1
'''
        parser = SemanticOutlineParser()
        outline = parser.parse(outline_text)

        task = outline.get_item_by_id("1.0.1.2")
        assert len(task.dependencies) == 1
        assert task.dependencies[0].item_id == "1.0.1.1"

    def test_parse_dependency_without_type_prefix(self):
        """Test parsing raw ID dependencies."""
        outline_text = '''
## Milestone 1: Foundation
> Foundation.
> Dependencies: None

### Epic 1.0: Setup
> Setup phase.
> Dependencies: None

#### Story 1.0.1: Story
> A story.
> Dependencies: None

##### Task 1.0.1.1: First Task
> First task.
> Dependencies: None

##### Task 1.0.1.2: Second Task
> Second task.
> Dependencies: 1.0.1.1
'''
        parser = SemanticOutlineParser()
        outline = parser.parse(outline_text)

        task = outline.get_item_by_id("1.0.1.2")
        assert len(task.dependencies) == 1
        assert task.dependencies[0].item_id == "1.0.1.1"

    def test_parse_mixed_dependency_formats(self):
        """Test parsing mixed dependency formats."""
        outline_text = '''
## Milestone 1: Foundation
> Foundation.
> Dependencies: None

### Epic 1.0: Setup
> Setup phase.
> Dependencies: None

#### Story 1.0.1: Story
> A story.
> Dependencies: None

##### Task 1.0.1.1: First Task
> First task.
> Dependencies: None

##### Task 1.0.1.2: Second Task
> Second task.
> Dependencies: None

##### Task 1.0.1.3: Third Task
> Third task.
> Dependencies: Task 1.0.1.1, 1.0.1.2
'''
        parser = SemanticOutlineParser()
        outline = parser.parse(outline_text)

        task = outline.get_item_by_id("1.0.1.3")
        assert len(task.dependencies) == 2
        dep_ids = [d.item_id for d in task.dependencies]
        assert "1.0.1.1" in dep_ids
        assert "1.0.1.2" in dep_ids


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
