"""Tests for semantic outline data structures."""

import pytest
from arcane.models.outline_item import (
    SemanticOutlineItem,
    OutlineDependency,
    OutlineItemDescription,
    SemanticOutline,
    OutlineItemType,
)
from arcane.engines.parsing.semantic_outline_parser import SemanticOutlineParser


class TestOutlineDependency:
    """Tests for OutlineDependency dataclass."""

    def test_create_dependency(self):
        """Test creating a dependency."""
        dep = OutlineDependency(
            item_id="1.0.1",
            item_type="Story"
        )
        assert dep.item_id == "1.0.1"
        assert dep.item_type == "Story"
        assert dep.dependency_type == OutlineItemType.STORY

    def test_dependency_string(self):
        """Test string representation of dependency."""
        dep = OutlineDependency("1.0.1.1", "Task")
        assert str(dep) == "1.0.1.1"

    def test_dependency_id_alias(self):
        """Test dependency_id alias."""
        dep = OutlineDependency("1.0.1", "Story")
        assert dep.dependency_id == "1.0.1"


class TestOutlineItemDescription:
    """Tests for OutlineItemDescription dataclass."""

    def test_create_description(self):
        """Test creating a description."""
        desc = OutlineItemDescription(
            full_text="Sets up database. Required for persistence.",
            what="Sets up database.",
            why="Required for persistence."
        )
        assert desc.full_text == "Sets up database. Required for persistence."
        assert desc.what == "Sets up database."
        assert desc.why == "Required for persistence."

    def test_description_bool(self):
        """Test description truthiness."""
        empty_desc = OutlineItemDescription()
        assert not empty_desc

        full_desc = OutlineItemDescription(full_text="Has content")
        assert full_desc


class TestSemanticOutlineItem:
    """Tests for SemanticOutlineItem dataclass."""

    def test_create_item(self):
        """Test creating an outline item."""
        desc = OutlineItemDescription(
            full_text="Implements login functionality. Required for user access."
        )
        item = SemanticOutlineItem(
            id="1.0.1",
            title="User Authentication",
            item_type=OutlineItemType.STORY,
            description=desc
        )
        assert item.id == "1.0.1"
        assert item.item_type == OutlineItemType.STORY
        assert item.title == "User Authentication"
        assert item.name == "User Authentication"  # Alias
        assert "login functionality" in item.description.full_text

    def test_parent_id_milestone(self):
        """Test parent ID for milestone (no parent)."""
        item = SemanticOutlineItem(id="1", title="Foundation", item_type=OutlineItemType.MILESTONE)
        assert item.parent_id is None

    def test_parent_id_epic(self):
        """Test parent ID for epic."""
        item = SemanticOutlineItem(id="1.0", title="Setup", item_type=OutlineItemType.EPIC)
        assert item.parent_id == "1"

    def test_parent_id_story(self):
        """Test parent ID for story."""
        item = SemanticOutlineItem(id="1.0.1", title="Config", item_type=OutlineItemType.STORY)
        assert item.parent_id == "1.0"

    def test_parent_id_task(self):
        """Test parent ID for task."""
        item = SemanticOutlineItem(id="1.0.1.1", title="Init", item_type=OutlineItemType.TASK)
        assert item.parent_id == "1.0.1"

    def test_number_alias(self):
        """Test number property alias for id."""
        item = SemanticOutlineItem(id="1.0.1", title="Test", item_type=OutlineItemType.STORY)
        assert item.number == "1.0.1"

    def test_dependency_ids(self):
        """Test getting dependency IDs."""
        item = SemanticOutlineItem(
            id="1.0.1.2",
            title="Setup Branch",
            item_type=OutlineItemType.TASK,
            dependencies=[
                OutlineDependency("1.0.1.1", "Task"),
                OutlineDependency("1.0.1", "Story")
            ]
        )
        assert item.dependency_ids == ["1.0.1.1", "1.0.1"]

    def test_has_dependencies(self):
        """Test checking for dependencies."""
        item_with_deps = SemanticOutlineItem(
            id="1.0.1.2",
            title="Test",
            item_type=OutlineItemType.TASK,
            dependencies=[OutlineDependency("1.0.1.1", "Task")]
        )
        item_without_deps = SemanticOutlineItem(
            id="1.0.1.1",
            title="Test",
            item_type=OutlineItemType.TASK
        )
        assert item_with_deps.has_dependencies() is True
        assert item_without_deps.has_dependencies() is False

    def test_depends_on(self):
        """Test checking specific dependency."""
        item = SemanticOutlineItem(
            id="1.0.1.3",
            title="Configure CI",
            item_type=OutlineItemType.TASK,
            dependencies=[
                OutlineDependency("1.0.1.1", "Task"),
                OutlineDependency("1.0.1.2", "Task")
            ]
        )
        assert item.depends_on("1.0.1.1") is True
        assert item.depends_on("1.0.1.2") is True
        assert item.depends_on("1.0.1.4") is False

    def test_add_child(self):
        """Test adding a child item."""
        parent = SemanticOutlineItem(id="1.0", title="Epic", item_type=OutlineItemType.EPIC)
        child = SemanticOutlineItem(id="1.0.1", title="Story", item_type=OutlineItemType.STORY)

        parent.add_child(child)

        assert len(parent.children) == 1
        assert child.parent == parent

    def test_to_dict(self):
        """Test dictionary representation."""
        item = SemanticOutlineItem(
            id="1.0.1",
            title="Repository Setup",
            item_type=OutlineItemType.STORY,
            description=OutlineItemDescription(full_text="Sets up the git repository."),
            dependencies=[OutlineDependency("1.0", "Epic")]
        )
        d = item.to_dict()
        assert d['id'] == "1.0.1"
        assert d['type'] == "Story"
        assert d['title'] == "Repository Setup"
        assert d['name'] == "Repository Setup"
        assert d['description'] == "Sets up the git repository."
        assert d['dependencies'] == ["1.0"]


class TestSemanticOutline:
    """Tests for SemanticOutline class."""

    SAMPLE_OUTLINE = """
===PROJECT_METADATA===
PROJECT_NAME: Test Project
PROJECT_TYPE: web app
TECH_STACK: Python, React
ESTIMATED_DURATION: 3 months
TEAM_SIZE: 3
DESCRIPTION: A sample test project
===END_METADATA===

# Test Project

## Milestone 1: Foundation
> Establishes project foundation. Required for all development.
> Dependencies: None

### Epic 1.0: Environment Setup
> Sets up development environment. Enables consistent development.
> Dependencies: None

#### Story 1.0.1: Repository Configuration
> Configures version control. Ensures code collaboration.
> Dependencies: None

##### Task 1.0.1.1: Initialize Repository
> Creates git repository. Foundation for version control.
> Dependencies: None

##### Task 1.0.1.2: Setup Branches
> Defines branching strategy. Enables parallel development.
> Dependencies: 1.0.1.1

##### Task 1.0.1.3: Configure CI/CD
> Sets up automated pipelines. Ensures code quality.
> Dependencies: 1.0.1.1, 1.0.1.2

#### Story 1.0.2: Development Tools
> Installs dev tools. Standardizes development.
> Dependencies: 1.0.1

##### Task 1.0.2.1: Setup Environment
> Configures local dev environment. Reproducible setup.
> Dependencies: 1.0.1.1

## Milestone 2: Core Development
> Builds core features. Delivers user value.
> Dependencies: 1

### Epic 2.0: Backend API
> Implements backend services. Provides data layer.
> Dependencies: 1.0
"""

    def test_parse_metadata(self):
        """Test parsing project metadata."""
        parser = SemanticOutlineParser()
        outline = parser.parse(self.SAMPLE_OUTLINE)
        assert outline.project_name == "Test Project"
        assert outline.project_type == "web app"
        assert outline.tech_stack == "Python, React"
        assert outline.project_description == "A sample test project"

    def test_parse_milestones(self):
        """Test parsing milestones."""
        parser = SemanticOutlineParser()
        outline = parser.parse(self.SAMPLE_OUTLINE)
        milestones = outline.get_milestones()
        assert len(milestones) == 2
        assert milestones[0].title == "Foundation"
        assert milestones[1].title == "Core Development"

    def test_parse_epics(self):
        """Test parsing epics."""
        parser = SemanticOutlineParser()
        outline = parser.parse(self.SAMPLE_OUTLINE)
        epics = outline.get_epics()
        assert len(epics) == 2
        assert epics[0].title == "Environment Setup"
        assert epics[1].title == "Backend API"

    def test_parse_stories(self):
        """Test parsing stories."""
        parser = SemanticOutlineParser()
        outline = parser.parse(self.SAMPLE_OUTLINE)
        stories = outline.get_stories()
        assert len(stories) == 2
        assert stories[0].title == "Repository Configuration"
        assert stories[1].title == "Development Tools"

    def test_parse_tasks(self):
        """Test parsing tasks."""
        parser = SemanticOutlineParser()
        outline = parser.parse(self.SAMPLE_OUTLINE)
        tasks = outline.get_tasks()
        assert len(tasks) == 4
        task_titles = [t.title for t in tasks]
        assert "Initialize Repository" in task_titles
        assert "Setup Branches" in task_titles
        assert "Configure CI/CD" in task_titles
        assert "Setup Environment" in task_titles

    def test_parse_descriptions(self):
        """Test parsing item descriptions."""
        parser = SemanticOutlineParser()
        outline = parser.parse(self.SAMPLE_OUTLINE)
        milestone = outline.get_item("1")
        assert "foundation" in milestone.description.full_text.lower()

        story = outline.get_item("1.0.1")
        assert "version control" in story.description.full_text.lower()

    def test_parse_dependencies_none(self):
        """Test parsing items with no dependencies."""
        parser = SemanticOutlineParser()
        outline = parser.parse(self.SAMPLE_OUTLINE)
        task = outline.get_item("1.0.1.1")
        assert task.has_dependencies() is False

    def test_parse_dependencies_single(self):
        """Test parsing items with single dependency."""
        parser = SemanticOutlineParser()
        outline = parser.parse(self.SAMPLE_OUTLINE)
        task = outline.get_item("1.0.1.2")
        assert task.has_dependencies() is True
        assert task.depends_on("1.0.1.1")

    def test_parse_dependencies_multiple(self):
        """Test parsing items with multiple dependencies."""
        parser = SemanticOutlineParser()
        outline = parser.parse(self.SAMPLE_OUTLINE)
        task = outline.get_item("1.0.1.3")
        assert len(task.dependencies) == 2
        assert task.depends_on("1.0.1.1")
        assert task.depends_on("1.0.1.2")

    def test_get_children(self):
        """Test getting children of an item."""
        parser = SemanticOutlineParser()
        outline = parser.parse(self.SAMPLE_OUTLINE)
        children = outline.get_children("1.0.1")
        assert len(children) == 3  # 3 tasks under story 1.0.1
        child_ids = [c.id for c in children]
        assert "1.0.1.1" in child_ids
        assert "1.0.1.2" in child_ids
        assert "1.0.1.3" in child_ids

    def test_get_dependents(self):
        """Test getting items that depend on a given item."""
        parser = SemanticOutlineParser()
        outline = parser.parse(self.SAMPLE_OUTLINE)
        dependents = outline.get_dependents("1.0.1.1")
        dependent_ids = [d.id for d in dependents]
        assert "1.0.1.2" in dependent_ids
        assert "1.0.1.3" in dependent_ids
        assert "1.0.2.1" in dependent_ids

    def test_get_execution_order(self):
        """Test topological sort for execution order."""
        parser = SemanticOutlineParser()
        outline = parser.parse(self.SAMPLE_OUTLINE)
        order = outline.get_execution_order()

        # Find positions
        pos = {item.id: i for i, item in enumerate(order)}

        # Verify dependencies come before dependents
        assert pos["1.0.1.1"] < pos["1.0.1.2"]
        assert pos["1.0.1.1"] < pos["1.0.1.3"]
        assert pos["1.0.1.2"] < pos["1.0.1.3"]

    def test_get_statistics(self):
        """Test getting outline statistics."""
        parser = SemanticOutlineParser()
        outline = parser.parse(self.SAMPLE_OUTLINE)
        stats = outline.get_statistics()
        assert stats['milestones'] == 2
        assert stats['epics'] == 2
        assert stats['stories'] == 2
        assert stats['tasks'] == 4
        assert stats['total_items'] == 10  # 2 + 2 + 2 + 4
        assert stats['items_with_dependencies'] > 0
        assert stats['items_with_descriptions'] == 10

    def test_contains(self):
        """Test membership check."""
        parser = SemanticOutlineParser()
        outline = parser.parse(self.SAMPLE_OUTLINE)
        assert "1.0.1" in outline
        assert "9.9.9" not in outline

    def test_len(self):
        """Test length."""
        parser = SemanticOutlineParser()
        outline = parser.parse(self.SAMPLE_OUTLINE)
        assert len(outline) == 10

    def test_iteration(self):
        """Test iterating over items."""
        parser = SemanticOutlineParser()
        outline = parser.parse(self.SAMPLE_OUTLINE)
        items = list(outline)
        assert len(items) == 10
        assert all(isinstance(item, SemanticOutlineItem) for item in items)

    def test_to_dict(self):
        """Test dictionary representation."""
        parser = SemanticOutlineParser()
        outline = parser.parse(self.SAMPLE_OUTLINE)
        d = outline.to_dict()
        assert d['project_name'] == "Test Project"
        assert len(d['items']) == 10
        assert 'statistics' in d


class TestSemanticOutlineValidation:
    """Tests for outline validation."""

    def test_warns_on_missing_description(self):
        """Test warning when item has no description."""
        text = """
## Milestone 1: Foundation
> Dependencies: None

### Epic 1.0: Setup
> Dependencies: None

#### Story 1.0.1: Story
> Dependencies: None

##### Task 1.0.1.1: Task
> Dependencies: None
"""
        parser = SemanticOutlineParser()
        outline = parser.parse(text)
        assert parser.has_warnings()
        warnings = parser.parse_warnings
        assert any("no description" in w.lower() for w in warnings)

    def test_warns_on_invalid_dependency(self):
        """Test warning when dependency references unknown item."""
        text = """
## Milestone 1: Foundation
> Foundation phase. Sets up project.
> Dependencies: 99.99.99

### Epic 1.0: Setup
> Sets up things.
> Dependencies: None

#### Story 1.0.1: Story
> A story.
> Dependencies: None

##### Task 1.0.1.1: Task
> A task.
> Dependencies: None
"""
        parser = SemanticOutlineParser()
        outline = parser.parse(text)
        assert parser.has_warnings()
        warnings = parser.parse_warnings
        assert any("unknown dependency" in w.lower() for w in warnings)

    def test_error_on_circular_dependency(self):
        """Test error when circular dependency detected."""
        text = """
## Milestone 1: Foundation
> Foundation phase.
> Dependencies: 2

## Milestone 2: Development
> Development phase.
> Dependencies: 1
"""
        parser = SemanticOutlineParser()
        outline = parser.parse(text)
        assert parser.has_errors()
        errors = parser.parse_errors
        assert any("circular" in e.lower() for e in errors)


class TestOutlineItemTypeInference:
    """Tests for item type inference from ID."""

    def test_infer_milestone_type(self):
        """Test inferring milestone type from single-part ID."""
        parser = SemanticOutlineParser()
        assert parser._infer_item_type("1") == "Milestone"
        assert parser._infer_item_type("2") == "Milestone"

    def test_infer_epic_type(self):
        """Test inferring epic type from two-part ID."""
        parser = SemanticOutlineParser()
        assert parser._infer_item_type("1.0") == "Epic"
        assert parser._infer_item_type("2.1") == "Epic"

    def test_infer_story_type(self):
        """Test inferring story type from three-part ID."""
        parser = SemanticOutlineParser()
        assert parser._infer_item_type("1.0.1") == "Story"
        assert parser._infer_item_type("2.1.3") == "Story"

    def test_infer_task_type(self):
        """Test inferring task type from four-part ID."""
        parser = SemanticOutlineParser()
        assert parser._infer_item_type("1.0.1.1") == "Task"
        assert parser._infer_item_type("2.1.3.4") == "Task"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
