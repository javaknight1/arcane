"""Integration tests for the semantic outline generation system.

These tests verify the complete flow from outline parsing through
item conversion to content generation with semantic context.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch

from arcane.models.outline_item import (
    SemanticOutline,
    SemanticOutlineItem,
    OutlineItemType,
    OutlineItemDescription,
    OutlineDependency,
)
from arcane.engines.parsing.semantic_outline_parser import SemanticOutlineParser
from arcane.engines.generation.semantic_converter import SemanticToItemConverter
from arcane.items.base import Item, ItemStatus


# Sample semantic outline for testing
SAMPLE_SEMANTIC_OUTLINE = """
===PROJECT_METADATA===
PROJECT_NAME: Test API Project
PROJECT_TYPE: web api
TECH_STACK: Python, FastAPI, PostgreSQL
ESTIMATED_DURATION: 2 months
TEAM_SIZE: 2
DESCRIPTION: A RESTful API for user management
===END_METADATA===

# Test API Project

## Milestone 1: Foundation
> Establishes project foundation. Required for all development.
> Dependencies: None

### Epic 1.0: Project Setup
> Sets up development environment. Enables consistent development.
> Dependencies: None

#### Story 1.0.1: Repository Configuration
> Configures version control and CI/CD. Ensures code quality and collaboration.
> Dependencies: None

##### Task 1.0.1.1: Initialize Repository
> Creates git repository with proper structure. Foundation for version control.
> Dependencies: None

##### Task 1.0.1.2: Setup CI Pipeline
> Configures GitHub Actions for testing. Ensures automated quality checks.
> Dependencies: 1.0.1.1

#### Story 1.0.2: Development Environment
> Sets up local development tools. Standardizes development experience.
> Dependencies: 1.0.1

##### Task 1.0.2.1: Configure Virtual Environment
> Creates Python virtual environment. Isolates project dependencies.
> Dependencies: 1.0.1.1

##### Task 1.0.2.2: Setup Pre-commit Hooks
> Configures code formatting and linting. Maintains code quality.
> Dependencies: 1.0.2.1

## Milestone 2: Core API
> Implements core API functionality. Delivers user value.
> Dependencies: 1

### Epic 2.0: User Management
> Implements user CRUD operations. Core feature of the API.
> Dependencies: 1.0

#### Story 2.0.1: User Model
> Creates user data model and database schema. Foundation for user features.
> Dependencies: 1.0.2

##### Task 2.0.1.1: Define SQLAlchemy Model
> Creates User model with all fields. Database representation of users.
> Dependencies: 1.0.2.2

##### Task 2.0.1.2: Create Database Migrations
> Sets up Alembic migrations. Enables schema version control.
> Dependencies: 2.0.1.1
"""


class TestSemanticOutlineParserIntegration:
    """Integration tests for the semantic outline parser."""

    def test_parse_complete_outline(self):
        """Test parsing a complete semantic outline."""
        parser = SemanticOutlineParser()
        outline = parser.parse(SAMPLE_SEMANTIC_OUTLINE)

        assert outline.project_name == "Test API Project"
        assert outline.project_type == "web api"
        assert "Python" in outline.tech_stack

    def test_parse_all_item_levels(self):
        """Test that all hierarchy levels are correctly parsed."""
        parser = SemanticOutlineParser()
        outline = parser.parse(SAMPLE_SEMANTIC_OUTLINE)

        milestones = outline.get_milestones()
        assert len(milestones) == 2

        epics = outline.get_epics()
        assert len(epics) == 2

        stories = outline.get_stories()
        assert len(stories) == 3

        tasks = outline.get_tasks()
        assert len(tasks) == 6

    def test_parse_descriptions(self):
        """Test that descriptions are correctly parsed."""
        parser = SemanticOutlineParser()
        outline = parser.parse(SAMPLE_SEMANTIC_OUTLINE)

        milestone = outline.get_item("1")
        assert "foundation" in milestone.description.full_text.lower()

        story = outline.get_item("1.0.1")
        assert "version control" in story.description.full_text.lower()

        task = outline.get_item("1.0.1.1")
        assert "git repository" in task.description.full_text.lower()

    def test_parse_dependencies(self):
        """Test that dependencies are correctly parsed."""
        parser = SemanticOutlineParser()
        outline = parser.parse(SAMPLE_SEMANTIC_OUTLINE)

        # Task with no dependencies
        task1 = outline.get_item("1.0.1.1")
        assert not task1.has_dependencies()

        # Task with single dependency
        task2 = outline.get_item("1.0.1.2")
        assert task2.has_dependencies()
        assert task2.depends_on("1.0.1.1")

        # Cross-milestone dependency
        milestone2 = outline.get_item("2")
        assert milestone2.depends_on("1")

    def test_get_execution_order(self):
        """Test topological ordering respects dependencies."""
        parser = SemanticOutlineParser()
        outline = parser.parse(SAMPLE_SEMANTIC_OUTLINE)
        order = outline.get_execution_order()

        pos = {item.id: i for i, item in enumerate(order)}

        # Dependencies must come before dependents
        assert pos["1.0.1.1"] < pos["1.0.1.2"]
        assert pos["1.0.2.1"] < pos["1.0.2.2"]
        assert pos["2.0.1.1"] < pos["2.0.1.2"]
        assert pos["1"] < pos["2"]


class TestSemanticToItemConverterIntegration:
    """Integration tests for the semantic-to-item converter."""

    def test_convert_outline_to_items(self):
        """Test converting semantic outline to Item objects."""
        parser = SemanticOutlineParser()
        outline = parser.parse(SAMPLE_SEMANTIC_OUTLINE)

        converter = SemanticToItemConverter()
        milestones = converter.convert_outline(outline)

        assert len(milestones) == 2
        assert milestones[0].name == "Milestone 1: Foundation"
        assert milestones[1].name == "Milestone 2: Core API"

    def test_semantic_fields_transferred(self):
        """Test that semantic fields are transferred to Item objects."""
        parser = SemanticOutlineParser()
        outline = parser.parse(SAMPLE_SEMANTIC_OUTLINE)

        converter = SemanticToItemConverter()
        milestones = converter.convert_outline(outline)

        # Check milestone has semantic context
        milestone = milestones[0]
        assert "foundation" in milestone.outline_description.lower()

        # Check nested items have semantic context
        epic = milestone.children[0]
        assert "development environment" in epic.outline_description.lower()

        story = epic.children[0]
        assert "version control" in story.outline_description.lower()

    def test_dependencies_linked(self):
        """Test that dependencies are linked to actual Item objects."""
        parser = SemanticOutlineParser()
        outline = parser.parse(SAMPLE_SEMANTIC_OUTLINE)

        converter = SemanticToItemConverter()
        milestones = converter.convert_outline(outline)

        # Find task 1.0.1.2 which depends on 1.0.1.1
        task = converter.get_item_by_id("1.0.1.2")
        assert task is not None
        assert len(task.dependency_ids) == 1
        assert "1.0.1.1" in task.dependency_ids
        assert len(task.depends_on_items) == 1
        assert task.depends_on_items[0].id == "1.0.1.1"

    def test_generation_order(self):
        """Test that generation order respects dependencies."""
        parser = SemanticOutlineParser()
        outline = parser.parse(SAMPLE_SEMANTIC_OUTLINE)

        converter = SemanticToItemConverter()
        milestones = converter.convert_outline(outline)

        order = converter.get_generation_order()
        pos = {item.id: i for i, item in enumerate(order)}

        # Dependencies must come before dependents
        assert pos["1.0.1.1"] < pos["1.0.1.2"]
        assert pos["1.0.2.1"] < pos["1.0.2.2"]

    def test_statistics(self):
        """Test that statistics are correctly calculated."""
        parser = SemanticOutlineParser()
        outline = parser.parse(SAMPLE_SEMANTIC_OUTLINE)

        converter = SemanticToItemConverter()
        converter.convert_outline(outline)

        stats = converter.get_statistics()
        assert stats['milestones'] == 2
        assert stats['epics'] == 2
        assert stats['stories'] == 3
        assert stats['tasks'] == 6
        assert stats['total'] == 13
        assert stats['items_with_semantic_context'] == 13
        assert stats['items_with_dependencies'] > 0


class TestItemSemanticContextIntegration:
    """Integration tests for Item semantic context methods."""

    def test_has_semantic_context(self):
        """Test has_semantic_context method."""
        parser = SemanticOutlineParser()
        outline = parser.parse(SAMPLE_SEMANTIC_OUTLINE)

        converter = SemanticToItemConverter()
        converter.convert_outline(outline)

        task = converter.get_item_by_id("1.0.1.1")
        assert task.has_semantic_context()

    def test_get_semantic_context(self):
        """Test get_semantic_context method."""
        parser = SemanticOutlineParser()
        outline = parser.parse(SAMPLE_SEMANTIC_OUTLINE)

        converter = SemanticToItemConverter()
        converter.convert_outline(outline)

        task = converter.get_item_by_id("1.0.1.1")
        context = task.get_semantic_context()

        assert "Purpose:" in context
        assert "git repository" in context.lower()

    def test_get_dependency_context(self):
        """Test get_dependency_context method."""
        parser = SemanticOutlineParser()
        outline = parser.parse(SAMPLE_SEMANTIC_OUTLINE)

        converter = SemanticToItemConverter()
        converter.convert_outline(outline)

        # Task with dependency
        task = converter.get_item_by_id("1.0.1.2")
        context = task.get_dependency_context()
        assert "Task 1.0.1.1" in context

        # Task without dependencies
        task_no_deps = converter.get_item_by_id("1.0.1.1")
        context_no_deps = task_no_deps.get_dependency_context()
        assert "no dependencies" in context_no_deps.lower()


class TestOutlineProcessorIntegration:
    """Integration tests for the outline processor."""

    @patch('arcane.engines.generation.helpers.outline_processor.Confirm')
    def test_generate_semantic_outline(self, mock_confirm):
        """Test generating a semantic outline."""
        from arcane.engines.generation.helpers.outline_processor import OutlineProcessor

        # Mock console
        mock_console = MagicMock()

        # Mock LLM client
        mock_llm = MagicMock()
        mock_llm.generate.return_value = SAMPLE_SEMANTIC_OUTLINE

        # Mock user confirmation
        mock_confirm.ask.return_value = True

        processor = OutlineProcessor(mock_console)

        outline_text, semantic_outline = processor.generate_semantic_outline(
            mock_llm,
            "Build a user management API",
            {"complexity": "medium"}
        )

        assert outline_text is not None
        assert semantic_outline is not None
        assert semantic_outline.project_name == "Test API Project"
        assert len(semantic_outline.get_milestones()) == 2


class TestEndToEndSemanticFlow:
    """End-to-end tests for the complete semantic outline flow."""

    def test_full_flow_parse_convert_context(self):
        """Test the complete flow from parsing to context generation."""
        # Step 1: Parse outline
        parser = SemanticOutlineParser()
        outline = parser.parse(SAMPLE_SEMANTIC_OUTLINE)

        # Verify parsing
        assert outline.project_name == "Test API Project"
        assert len(outline.get_tasks()) == 6

        # Step 2: Convert to Items
        converter = SemanticToItemConverter()
        milestones = converter.convert_outline(outline)

        # Verify conversion
        assert len(milestones) == 2
        stats = converter.get_statistics()
        assert stats['total'] == 13

        # Step 3: Verify semantic context is available for generation
        for item_id in ["1", "1.0", "1.0.1", "1.0.1.1"]:
            item = converter.get_item_by_id(item_id)
            assert item is not None
            assert item.has_semantic_context()
            context = item.get_semantic_context()
            assert len(context) > 0

        # Step 4: Verify dependency chain is correct
        generation_order = converter.get_generation_order()
        task_order = [item.id for item in generation_order if item.item_type == 'Task']

        # 1.0.1.1 must come before 1.0.1.2
        assert task_order.index("1.0.1.1") < task_order.index("1.0.1.2")

        # 2.0.1.1 must come before 2.0.1.2
        assert task_order.index("2.0.1.1") < task_order.index("2.0.1.2")

    def test_dependency_context_chain(self):
        """Test that dependency context flows correctly through the chain."""
        parser = SemanticOutlineParser()
        outline = parser.parse(SAMPLE_SEMANTIC_OUTLINE)

        converter = SemanticToItemConverter()
        converter.convert_outline(outline)

        # Get a task with dependencies
        task = converter.get_item_by_id("2.0.1.2")  # Create Database Migrations
        assert task is not None

        # Verify it depends on 2.0.1.1
        assert "2.0.1.1" in task.dependency_ids

        # Get dependency context
        dep_context = task.get_dependency_context()
        assert "Task 2.0.1.1" in dep_context
        assert "SQLAlchemy" in dep_context or "User model" in dep_context.lower()


class TestValidationIntegration:
    """Integration tests for validation across the system."""

    def test_parser_validation_flows_to_converter(self):
        """Test that parser validation issues are properly reported."""
        # Outline with missing descriptions
        outline_text = """
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
        outline = parser.parse(outline_text)

        # Parser should have warnings about missing descriptions
        assert parser.has_warnings()

        # But converter should still work
        converter = SemanticToItemConverter()
        milestones = converter.convert_outline(outline)
        assert len(milestones) == 1

    def test_circular_dependency_detection(self):
        """Test that circular dependencies are detected."""
        outline_text = """
## Milestone 1: First
> First milestone.
> Dependencies: 2

## Milestone 2: Second
> Second milestone.
> Dependencies: 1
"""
        parser = SemanticOutlineParser()
        outline = parser.parse(outline_text)

        # Should have circular dependency error
        assert parser.has_errors()
        assert any("circular" in e.lower() for e in parser.parse_errors)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
