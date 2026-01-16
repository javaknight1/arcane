"""Tests for context summarizer."""

import pytest
from unittest.mock import MagicMock
from arcane.engines.generation.helpers.context_summarizer import (
    ContextSummarizer,
    ContentSummary,
    DependencyChain
)
from arcane.items.milestone import Milestone
from arcane.items.epic import Epic
from arcane.items.story import Story
from arcane.items.task import Task
from arcane.items.base import ItemStatus


class TestContextSummarizer:
    """Tests for the ContextSummarizer class."""

    @pytest.fixture
    def summarizer(self):
        return ContextSummarizer()

    @pytest.fixture
    def sample_milestone(self):
        milestone = Milestone(name="Foundation", number="1")
        milestone.content = """
## Milestone 1: Foundation

**Decision:** Using PostgreSQL for the database
**Technology:** React with TypeScript for frontend
**Deliverable:** Complete authentication system

This milestone establishes the core infrastructure.
We chose PostgreSQL for its reliability and JSON support.
The frontend will be built with React and TypeScript.
"""
        milestone.generation_status = ItemStatus.GENERATED
        return milestone

    @pytest.fixture
    def sample_epic(self):
        epic = Epic(name="Authentication", number="1.0")
        epic.content = """
## Epic 1.0: Authentication

**Decision:** Using JWT tokens for session management
**Technology:** Passport.js for authentication middleware
**Deliverable:** Login, logout, and registration endpoints

Built with OAuth2 support for social logins.
"""
        epic.generation_status = ItemStatus.GENERATED
        return epic

    def test_extract_summary_from_content(self, summarizer, sample_milestone):
        """Test that summarizer extracts key information."""
        summary = summarizer.get_summary(sample_milestone)

        assert summary is not None
        assert summary.item_id == "1"
        assert summary.item_type == "Milestone"
        assert len(summary.key_decisions) > 0
        assert len(summary.technical_choices) > 0

    def test_extract_decisions(self, summarizer, sample_milestone):
        """Test that decisions are correctly extracted."""
        summary = summarizer.get_summary(sample_milestone)

        # Should find "Using PostgreSQL for the database"
        assert any("PostgreSQL" in d for d in summary.key_decisions)

    def test_extract_technical_choices(self, summarizer, sample_milestone):
        """Test that technical choices are correctly extracted."""
        summary = summarizer.get_summary(sample_milestone)

        # Should find "React with TypeScript"
        assert any("React" in t or "TypeScript" in t for t in summary.technical_choices)

    def test_extract_deliverables(self, summarizer, sample_milestone):
        """Test that deliverables are correctly extracted."""
        summary = summarizer.get_summary(sample_milestone)

        # Should find "Complete authentication system"
        assert any("authentication" in d.lower() for d in summary.deliverables)

    def test_summary_text_is_concise(self, summarizer, sample_milestone):
        """Test that summary text respects length limits."""
        summary = summarizer.get_summary(sample_milestone)

        assert len(summary.summary_text) <= 250  # With some buffer

    def test_summary_text_contains_item_info(self, summarizer, sample_milestone):
        """Test that summary text contains item identification."""
        summary = summarizer.get_summary(sample_milestone)

        assert "Milestone 1" in summary.summary_text
        assert "Foundation" in summary.summary_text

    def test_caching_works(self, summarizer, sample_milestone):
        """Test that summaries are cached."""
        summary1 = summarizer.get_summary(sample_milestone)
        summary2 = summarizer.get_summary(sample_milestone)

        assert summary1 is summary2  # Same object from cache

        stats = summarizer.get_cache_stats()
        assert stats['summary_cache_size'] == 1

    def test_force_refresh_bypasses_cache(self, summarizer, sample_milestone):
        """Test that force_refresh regenerates summary."""
        summary1 = summarizer.get_summary(sample_milestone)
        summary2 = summarizer.get_summary(sample_milestone, force_refresh=True)

        # Different objects (regenerated)
        assert summary1 is not summary2
        # But same content
        assert summary1.item_id == summary2.item_id

    def test_clear_cache(self, summarizer, sample_milestone):
        """Test that cache clearing works."""
        summarizer.get_summary(sample_milestone)

        stats = summarizer.get_cache_stats()
        assert stats['summary_cache_size'] == 1

        summarizer.clear_cache()

        stats = summarizer.get_cache_stats()
        assert stats['summary_cache_size'] == 0

    def test_no_content_returns_none(self, summarizer):
        """Test that items without content return None."""
        milestone = Milestone(name="Empty", number="2")
        milestone.content = None
        milestone.description = None

        summary = summarizer.get_summary(milestone)
        assert summary is None

    def test_fallback_to_description(self, summarizer):
        """Test fallback to description when no patterns match."""
        milestone = Milestone(name="Simple", number="3")
        milestone.content = None
        milestone.description = "This is a simple milestone without structured content"

        summary = summarizer.get_summary(milestone)

        assert summary is not None
        assert len(summary.key_decisions) > 0


class TestParentChainContext:
    """Tests for parent chain context building."""

    @pytest.fixture
    def summarizer(self):
        return ContextSummarizer()

    @pytest.fixture
    def hierarchy(self):
        """Create a milestone -> epic -> story hierarchy."""
        milestone = Milestone(name="Foundation", number="1")
        milestone.content = "Foundation milestone with PostgreSQL decision"
        milestone.generation_status = ItemStatus.GENERATED

        epic = Epic(name="Auth", number="1.0", parent=milestone)
        epic.content = "Auth epic with JWT tokens"
        epic.generation_status = ItemStatus.GENERATED
        milestone.add_child(epic)

        story = Story(name="Login", number="1.0.1", parent=epic)
        story.content = None  # Not generated yet
        epic.add_child(story)

        return milestone, epic, story

    def test_parent_chain_context(self, summarizer, hierarchy):
        """Test parent chain context building."""
        milestone, epic, story = hierarchy

        context = summarizer.get_parent_chain_context(story)

        assert "Milestone 1" in context
        assert "Epic 1.0" in context

    def test_parent_chain_order(self, summarizer, hierarchy):
        """Test that parent chain is in top-down order."""
        milestone, epic, story = hierarchy

        context = summarizer.get_parent_chain_context(story)
        lines = context.split('\n')

        # Milestone should come before Epic
        milestone_idx = next(i for i, l in enumerate(lines) if "Milestone" in l)
        epic_idx = next(i for i, l in enumerate(lines) if "Epic" in l)

        assert milestone_idx < epic_idx

    def test_no_parent_returns_default(self, summarizer):
        """Test that items without parents return default message."""
        milestone = Milestone(name="Orphan", number="1")

        context = summarizer.get_parent_chain_context(milestone)

        assert context == "No parent context available"


class TestSiblingContext:
    """Tests for sibling context building."""

    @pytest.fixture
    def summarizer(self):
        return ContextSummarizer()

    @pytest.fixture
    def epic_with_stories(self):
        """Create an epic with multiple stories."""
        epic = Epic(name="Auth", number="1.0")

        story1 = Story(name="Login", number="1.0.1", parent=epic)
        story1.content = "Login story with OAuth support"
        story1.generation_status = ItemStatus.GENERATED
        epic.add_child(story1)

        story2 = Story(name="Register", number="1.0.2", parent=epic)
        story2.content = None
        story2.generation_status = ItemStatus.PENDING
        epic.add_child(story2)

        story3 = Story(name="Logout", number="1.0.3", parent=epic)
        story3.content = "Logout story with session cleanup"
        story3.generation_status = ItemStatus.GENERATED
        epic.add_child(story3)

        return epic, story1, story2, story3

    def test_sibling_context(self, summarizer, epic_with_stories):
        """Test sibling context building."""
        epic, story1, story2, story3 = epic_with_stories

        context = summarizer.get_sibling_context(story2)

        # Should include generated siblings
        assert "Story 1.0.1" in context
        assert "Story 1.0.3" in context
        assert "✅" in context  # Generated indicator

    def test_sibling_context_excludes_self(self, summarizer, epic_with_stories):
        """Test that sibling context excludes the current item."""
        epic, story1, story2, story3 = epic_with_stories

        context = summarizer.get_sibling_context(story1)

        # Should not include itself
        assert context.count("Story 1.0.1") == 0 or "Login" not in context

    def test_sibling_context_include_pending(self, summarizer, epic_with_stories):
        """Test including pending siblings."""
        epic, story1, story2, story3 = epic_with_stories

        context = summarizer.get_sibling_context(story1, include_pending=True)

        # Should include pending indicator
        assert "⏳" in context
        assert "pending" in context.lower()

    def test_no_siblings_returns_default(self, summarizer):
        """Test that items without siblings return default message."""
        epic = Epic(name="Solo", number="1.0")
        story = Story(name="Only", number="1.0.1", parent=epic)
        epic.add_child(story)

        context = summarizer.get_sibling_context(story)

        assert context == "No sibling context"

    def test_no_parent_returns_default(self, summarizer):
        """Test that orphan items return default message."""
        story = Story(name="Orphan", number="1.0.1")

        context = summarizer.get_sibling_context(story)

        assert context == "No siblings"


class TestDependencyChain:
    """Tests for dependency chain building."""

    @pytest.fixture
    def summarizer(self):
        return ContextSummarizer()

    @pytest.fixture
    def items_with_dependencies(self):
        """Create items with dependencies."""
        task1 = Task(name="Init Repo", number="1.0.1.1")
        task1.id = "1.0.1.1"
        task1.content = "Initialize git repository with proper structure"
        task1.generation_status = ItemStatus.GENERATED
        task1.depends_on_items = []

        task2 = Task(name="Setup CI", number="1.0.1.2")
        task2.id = "1.0.1.2"
        task2.content = "Setup CI pipeline with GitHub Actions"
        task2.generation_status = ItemStatus.GENERATED
        task2.depends_on_items = [task1]

        task3 = Task(name="Configure CD", number="1.0.1.3")
        task3.id = "1.0.1.3"
        task3.content = None
        task3.generation_status = ItemStatus.PENDING
        task3.depends_on_items = [task1, task2]

        return task1, task2, task3

    def test_dependency_chain(self, summarizer, items_with_dependencies):
        """Test dependency chain building."""
        task1, task2, task3 = items_with_dependencies

        chain = summarizer.get_dependency_chain(task3)

        assert chain.target_item_id == "1.0.1.3"
        assert len(chain.chain) == 2  # task1 and task2

    def test_dependency_chain_only_generated(self, summarizer, items_with_dependencies):
        """Test that chain only includes generated items."""
        task1, task2, task3 = items_with_dependencies

        # Make task2 pending
        task2.generation_status = ItemStatus.PENDING

        chain = summarizer.get_dependency_chain(task3)

        # Should only include task1
        assert len(chain.chain) == 1
        assert chain.chain[0].item_id == "1.0.1.1"

    def test_no_dependencies_empty_chain(self, summarizer, items_with_dependencies):
        """Test that items without dependencies have empty chain."""
        task1, task2, task3 = items_with_dependencies

        chain = summarizer.get_dependency_chain(task1)

        assert len(chain.chain) == 0
        assert chain.total_depth == 0

    def test_chain_caching(self, summarizer, items_with_dependencies):
        """Test that dependency chains are cached."""
        task1, task2, task3 = items_with_dependencies

        chain1 = summarizer.get_dependency_chain(task3)
        chain2 = summarizer.get_dependency_chain(task3)

        assert chain1 is chain2


class TestFullCascadingContext:
    """Tests for the full cascading context builder."""

    @pytest.fixture
    def summarizer(self):
        return ContextSummarizer()

    @pytest.fixture
    def complete_hierarchy(self):
        """Create a complete hierarchy with dependencies."""
        milestone = Milestone(name="Foundation", number="1")
        milestone.content = "Foundation with PostgreSQL"
        milestone.generation_status = ItemStatus.GENERATED

        epic = Epic(name="Setup", number="1.0", parent=milestone)
        epic.content = "Setup epic with Docker"
        epic.generation_status = ItemStatus.GENERATED
        milestone.add_child(epic)

        story1 = Story(name="Repo", number="1.0.1", parent=epic)
        story1.content = "Repository setup"
        story1.generation_status = ItemStatus.GENERATED
        epic.add_child(story1)

        story2 = Story(name="CI", number="1.0.2", parent=epic)
        story2.outline_description = "Setup continuous integration"
        story2.depends_on_items = [story1]
        epic.add_child(story2)

        return milestone, epic, story1, story2

    def test_full_context_includes_parent_hierarchy(self, summarizer, complete_hierarchy):
        """Test that full context includes parent hierarchy."""
        milestone, epic, story1, story2 = complete_hierarchy

        context = summarizer.get_full_cascading_context(story2)

        assert "PARENT HIERARCHY" in context
        assert "Milestone 1" in context

    def test_full_context_includes_dependencies(self, summarizer, complete_hierarchy):
        """Test that full context includes dependencies."""
        milestone, epic, story1, story2 = complete_hierarchy

        context = summarizer.get_full_cascading_context(story2)

        assert "DEPENDENCIES" in context
        assert "Story 1.0.1" in context

    def test_full_context_includes_siblings(self, summarizer, complete_hierarchy):
        """Test that full context includes siblings."""
        milestone, epic, story1, story2 = complete_hierarchy

        context = summarizer.get_full_cascading_context(story2)

        assert "SIBLING" in context

    def test_full_context_includes_semantic_context(self, summarizer, complete_hierarchy):
        """Test that full context includes item's semantic context."""
        milestone, epic, story1, story2 = complete_hierarchy

        context = summarizer.get_full_cascading_context(story2)

        assert "PURPOSE" in context
        assert "continuous integration" in context


class TestLLMSummarization:
    """Tests for LLM-based summarization."""

    def test_summarize_with_llm(self):
        """Test LLM-based summarization."""
        mock_llm = MagicMock()
        mock_llm.generate.return_value = """
DECISIONS: Use PostgreSQL, Implement JWT auth
TECH: React, TypeScript, Node.js
DELIVERS: Auth system, User dashboard
"""

        summarizer = ContextSummarizer(llm_client=mock_llm)

        milestone = Milestone(name="Foundation", number="1")
        milestone.content = "Complex milestone content that needs LLM summarization"

        summary = summarizer.summarize_with_llm(milestone)

        assert summary is not None
        assert "PostgreSQL" in summary.key_decisions[0]
        assert "React" in summary.technical_choices[0]
        mock_llm.generate.assert_called_once()

    def test_summarize_without_llm_falls_back(self):
        """Test that summarize_with_llm falls back to pattern matching without LLM."""
        summarizer = ContextSummarizer(llm_client=None)

        milestone = Milestone(name="Foundation", number="1")
        milestone.content = "**Decision:** Using PostgreSQL"

        summary = summarizer.summarize_with_llm(milestone)

        # Should use pattern matching
        assert summary is not None
        assert any("PostgreSQL" in d for d in summary.key_decisions)


class TestContentSummaryDataclass:
    """Tests for the ContentSummary dataclass."""

    def test_content_summary_creation(self):
        """Test creating a ContentSummary."""
        summary = ContentSummary(
            item_id="1",
            item_type="Milestone",
            title="Foundation",
            key_decisions=["Use PostgreSQL"],
            technical_choices=["React"],
            deliverables=["Auth system"],
            integration_points=["User API"],
            summary_text="Milestone 1: Foundation | Decisions: Use PostgreSQL"
        )

        assert summary.item_id == "1"
        assert len(summary.key_decisions) == 1
        assert summary.full_content_hash == ""  # Default value


class TestDependencyChainDataclass:
    """Tests for the DependencyChain dataclass."""

    def test_dependency_chain_creation(self):
        """Test creating a DependencyChain."""
        chain = DependencyChain(
            target_item_id="1.0.1",
            chain=[],
            total_depth=0
        )

        assert chain.target_item_id == "1.0.1"
        assert len(chain.chain) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
