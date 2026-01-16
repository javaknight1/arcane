"""Integration tests for cascading context in generation flow."""

import pytest
from unittest.mock import MagicMock, patch
from arcane.engines.generation.recursive_generator import RecursiveRoadmapGenerator
from arcane.engines.generation.helpers.context_summarizer import ContextSummarizer, ContentSummary
from arcane.prompts.context_injector import ContextInjector
from arcane.items.milestone import Milestone
from arcane.items.epic import Epic
from arcane.items.story import Story
from arcane.items.task import Task
from arcane.items.base import ItemStatus


class TestRecursiveGeneratorCascadingContext:
    """Tests for the RecursiveRoadmapGenerator with cascading context."""

    @pytest.fixture
    def mock_llm_client(self):
        """Create a mock LLM client."""
        client = MagicMock()
        client.provider = 'claude'
        client.generate.return_value = """
:::MILESTONE_DESCRIPTION:::
This is a test milestone description.

:::MILESTONE_GOAL:::
Complete the foundation phase.

:::KEY_DELIVERABLES:::
- Deliverable 1
- Deliverable 2

:::BENEFITS:::
- Benefit 1
- Benefit 2

:::PREREQUISITES:::
None

:::SUCCESS_CRITERIA:::
- Criterion 1
- Criterion 2

:::RISKS_IF_DELAYED:::
- Risk 1

:::TECHNICAL_REQUIREMENTS:::
- Using PostgreSQL database
- React frontend

:::WORK_TYPE:::
implementation

:::COMPLEXITY:::
complex

:::PRIORITY:::
Critical

:::DURATION_HOURS:::
160

:::TAGS:::
core-scope, backend, frontend
"""
        return client

    @pytest.fixture
    def generator(self, mock_llm_client):
        """Create a RecursiveRoadmapGenerator with mock LLM."""
        return RecursiveRoadmapGenerator(mock_llm_client)

    @pytest.fixture
    def sample_hierarchy(self):
        """Create a sample milestone hierarchy."""
        milestone = Milestone(name="Foundation", number="1")

        epic = Epic(name="Auth", number="1.0", parent=milestone)
        milestone.add_child(epic)

        story1 = Story(name="Login", number="1.0.1", parent=epic)
        epic.add_child(story1)

        story2 = Story(name="Register", number="1.0.2", parent=epic)
        epic.add_child(story2)

        return [milestone]

    def test_generator_has_context_summarizer(self, generator):
        """Test that generator initializes with context summarizer."""
        assert hasattr(generator, 'context_summarizer')
        assert isinstance(generator.context_summarizer, ContextSummarizer)

    def test_generator_has_generated_items_tracking(self, generator):
        """Test that generator has generated items tracking."""
        assert hasattr(generator, 'generated_items')
        assert isinstance(generator.generated_items, list)

    def test_build_generation_order(self, generator, sample_hierarchy):
        """Test building generation order."""
        order = generator._build_generation_order(sample_hierarchy)

        assert len(order) == 4  # 1 milestone + 1 epic + 2 stories
        assert order[0].item_type == 'Milestone'
        assert order[1].item_type == 'Epic'
        assert order[2].item_type == 'Story'
        assert order[3].item_type == 'Story'

    def test_get_status_icon(self, generator):
        """Test status icon retrieval."""
        milestone = Milestone(name="Test", number="1")

        milestone.generation_status = ItemStatus.GENERATED
        assert generator._get_status_icon(milestone) == "✅"

        milestone.generation_status = ItemStatus.PENDING
        assert generator._get_status_icon(milestone) == "⏳"

        milestone.generation_status = ItemStatus.FAILED
        assert generator._get_status_icon(milestone) == "❌"

    def test_get_item_title(self, generator):
        """Test extracting clean item title."""
        milestone = Milestone(name="Foundation", number="1")
        # Milestone name becomes "Milestone 1: Foundation"
        assert generator._get_item_title(milestone) == "Foundation"

        epic = Epic(name="Auth", number="1.0")
        assert generator._get_item_title(epic) == "Auth"

    def test_build_parent_context_with_summaries(self, generator):
        """Test building parent context with summaries."""
        milestone = Milestone(name="Foundation", number="1")
        milestone.content = "**Decision:** Using PostgreSQL"
        milestone.generation_status = ItemStatus.GENERATED

        epic = Epic(name="Auth", number="1.0", parent=milestone)
        milestone.add_child(epic)
        epic.content = "**Technology:** JWT tokens"
        epic.generation_status = ItemStatus.GENERATED

        story = Story(name="Login", number="1.0.1", parent=epic)
        epic.add_child(story)

        context = generator._build_parent_context_with_summaries(story)

        assert "Parent Hierarchy" in context
        assert "Milestone 1" in context
        assert "Epic 1.0" in context

    def test_combine_context_layers(self, generator):
        """Test combining context layers."""
        combined = generator._combine_context_layers(
            roadmap_context="=== ROADMAP ===\nMilestone 1",
            cascading_context="=== CASCADING ===\nDecisions here",
            semantic_context="=== SEMANTIC ===\nPurpose here"
        )

        assert "ROADMAP" in combined
        assert "CASCADING" in combined
        assert "SEMANTIC" in combined
        assert "CONSISTENCY REQUIREMENTS" in combined


class TestContextInjector:
    """Tests for the ContextInjector helper."""

    def test_inject_context_prepends_to_prompt(self):
        """Test that context is prepended to prompt."""
        base_prompt = "Generate content for item X"
        cascading = "Previous decisions: Use React"

        result = ContextInjector.inject_context(
            base_prompt,
            cascading_context=cascading
        )

        assert "CASCADING CONTEXT" in result
        assert "Previous decisions: Use React" in result
        assert result.index("CASCADING CONTEXT") < result.index("Generate content")

    def test_inject_context_replaces_existing(self):
        """Test that existing context section is replaced."""
        base_prompt = "=== CONTEXT ===\nOld context\n\nGenerate content"
        cascading = "New cascading context"

        result = ContextInjector.inject_context(
            base_prompt,
            cascading_context=cascading
        )

        assert "New cascading context" in result
        # Original marker should be replaced
        assert "Old context" not in result or "CASCADING CONTEXT" in result

    def test_inject_minimal_context(self):
        """Test minimal context injection."""
        base_prompt = "Generate content"
        cascading = "Key decision: Use PostgreSQL"

        result = ContextInjector.inject_minimal_context(
            base_prompt,
            cascading_context=cascading
        )

        assert "CONTEXT" in result
        assert "Key decision" in result
        assert "Generate content" in result

    def test_build_dependency_section_with_deps(self):
        """Test building dependency section with dependencies."""
        summaries = [
            ContentSummary(
                item_id="1.0.1",
                item_type="Story",
                title="Login",
                key_decisions=["Use JWT"],
                technical_choices=["Passport.js"],
                deliverables=["Auth endpoints"],
                integration_points=[],
                summary_text="Story 1.0.1: Login | Tech: Passport.js"
            )
        ]

        result = ContextInjector.build_dependency_section(summaries)

        assert "depends on" in result.lower()
        assert "Story 1.0.1" in result
        assert "Use JWT" in result

    def test_build_dependency_section_no_deps(self):
        """Test building dependency section with no dependencies."""
        result = ContextInjector.build_dependency_section([])

        assert "no dependencies" in result.lower()

    def test_build_sibling_section(self):
        """Test building sibling section."""
        summaries = [
            ContentSummary(
                item_id="1.0.1",
                item_type="Story",
                title="Login",
                key_decisions=[],
                technical_choices=[],
                deliverables=[],
                integration_points=[],
                summary_text="Story 1.0.1: Login"
            )
        ]

        result = ContextInjector.build_sibling_section(summaries)

        assert "Generated sibling" in result
        assert "✅" in result
        assert "Story 1.0.1" in result

    def test_build_sibling_section_with_pending(self):
        """Test building sibling section with pending items."""
        milestone = Milestone(name="Test", number="1")
        pending_siblings = [milestone]

        result = ContextInjector.build_sibling_section([], pending_siblings)

        assert "Pending sibling" in result
        assert "⏳" in result

    def test_build_tech_stack_reminder(self):
        """Test building tech stack reminder."""
        tech_choices = ["React", "PostgreSQL", "Node.js"]

        result = ContextInjector.build_tech_stack_reminder(tech_choices)

        assert "TECH STACK" in result
        assert "React" in result
        assert "PostgreSQL" in result

    def test_build_tech_stack_reminder_empty(self):
        """Test tech stack reminder with no choices."""
        result = ContextInjector.build_tech_stack_reminder([])
        assert result == ""

    def test_extract_all_tech_choices(self):
        """Test extracting tech choices from summaries."""
        summaries = [
            ContentSummary(
                item_id="1",
                item_type="Milestone",
                title="Foundation",
                key_decisions=[],
                technical_choices=["React", "PostgreSQL"],
                deliverables=[],
                integration_points=[],
                summary_text=""
            ),
            ContentSummary(
                item_id="2",
                item_type="Milestone",
                title="Core",
                key_decisions=[],
                technical_choices=["Node.js", "Redis"],
                deliverables=[],
                integration_points=[],
                summary_text=""
            )
        ]

        result = ContextInjector.extract_all_tech_choices(summaries)

        assert "React" in result
        assert "PostgreSQL" in result
        assert "Node.js" in result
        assert "Redis" in result


class TestCascadingContextFlow:
    """End-to-end tests for cascading context flow."""

    @pytest.fixture
    def mock_llm_client(self):
        """Create a mock LLM client that returns different content based on item."""
        client = MagicMock()
        client.provider = 'claude'

        def generate_response(prompt):
            if "Milestone" in prompt:
                return """
:::MILESTONE_DESCRIPTION:::
Foundation milestone using PostgreSQL and React.

:::MILESTONE_GOAL:::
Establish foundation.

:::KEY_DELIVERABLES:::
- Database setup
- Frontend scaffold

:::BENEFITS:::
- Solid foundation

:::PREREQUISITES:::
None

:::SUCCESS_CRITERIA:::
- All systems operational

:::RISKS_IF_DELAYED:::
- Project delays

:::TECHNICAL_REQUIREMENTS:::
**Technology:** PostgreSQL database
**Technology:** React with TypeScript

:::WORK_TYPE:::
implementation

:::COMPLEXITY:::
complex

:::PRIORITY:::
Critical

:::DURATION_HOURS:::
160

:::TAGS:::
core-scope
"""
            else:
                return """
:::EPIC_DESCRIPTION:::
Auth epic building on foundation.

:::EPIC_GOALS:::
- Implement auth

:::BENEFITS:::
- Secure system

:::TECHNICAL_REQUIREMENTS:::
Built with JWT tokens

:::PREREQUISITES:::
Milestone 1

:::SUCCESS_METRICS:::
- All auth tests pass

:::RISKS_AND_MITIGATIONS:::
- None

:::WORK_TYPE:::
implementation

:::COMPLEXITY:::
moderate

:::PRIORITY:::
High

:::DURATION_HOURS:::
80

:::TAGS:::
backend, security
"""

        client.generate.side_effect = generate_response
        return client

    def test_context_flows_through_hierarchy(self, mock_llm_client):
        """Test that context flows from milestone to epic."""
        generator = RecursiveRoadmapGenerator(mock_llm_client)

        # Create hierarchy
        milestone = Milestone(name="Foundation", number="1")
        epic = Epic(name="Auth", number="1.0", parent=milestone)
        milestone.add_child(epic)

        # Generate milestone first
        milestone.update_generation_status(ItemStatus.GENERATING)
        response = mock_llm_client.generate("Milestone prompt")
        milestone.parse_content(response)
        milestone.update_generation_status(ItemStatus.GENERATED)

        # Get summary of milestone
        summary = generator.context_summarizer.get_summary(milestone)

        assert summary is not None
        # Should extract PostgreSQL or React from technical requirements
        assert len(summary.technical_choices) > 0 or len(summary.key_decisions) > 0

    def test_sibling_context_built_correctly(self):
        """Test that sibling context is built correctly."""
        mock_llm = MagicMock()
        mock_llm.provider = 'claude'
        generator = RecursiveRoadmapGenerator(mock_llm)

        # Create epic with two stories
        epic = Epic(name="Auth", number="1.0")

        story1 = Story(name="Login", number="1.0.1", parent=epic)
        story1.content = "**Decision:** OAuth2 login"
        story1.generation_status = ItemStatus.GENERATED
        epic.add_child(story1)

        story2 = Story(name="Register", number="1.0.2", parent=epic)
        story2.generation_status = ItemStatus.PENDING
        epic.add_child(story2)

        # Get sibling context for story2
        context = generator.context_summarizer.get_sibling_context(story2)

        assert "Story 1.0.1" in context
        assert "✅" in context

    def test_full_cascading_context_includes_all_sections(self):
        """Test that full cascading context includes all relevant sections."""
        mock_llm = MagicMock()
        mock_llm.provider = 'claude'
        generator = RecursiveRoadmapGenerator(mock_llm)

        # Create hierarchy with content
        milestone = Milestone(name="Foundation", number="1")
        milestone.content = "**Decision:** Using PostgreSQL"
        milestone.generation_status = ItemStatus.GENERATED

        epic = Epic(name="Auth", number="1.0", parent=milestone)
        epic.content = "**Technology:** JWT tokens"
        epic.generation_status = ItemStatus.GENERATED
        milestone.add_child(epic)

        story = Story(name="Login", number="1.0.1", parent=epic)
        story.outline_description = "Implements user login"
        epic.add_child(story)

        # Get full cascading context
        context = generator.context_summarizer.get_full_cascading_context(story)

        assert "PARENT HIERARCHY" in context
        assert "PURPOSE" in context
        assert "login" in context.lower()


class TestTemplateContextPlaceholders:
    """Tests for template context placeholders."""

    def test_story_template_has_cascading_context_placeholder(self):
        """Test that story template has cascading context placeholder."""
        from arcane.templates import get_template

        template = get_template('story_with_tasks_generation')

        assert "{cascading_context}" in template
        assert "CASCADING CONTEXT" in template
        assert "CONSISTENCY REQUIREMENTS" in template

    def test_epic_template_has_cascading_context_placeholder(self):
        """Test that epic template has cascading context placeholder."""
        from arcane.templates import get_template

        template = get_template('epic_generation_individual')

        assert "{cascading_context}" in template
        assert "CASCADING CONTEXT" in template

    def test_milestone_template_has_cascading_context_placeholder(self):
        """Test that milestone template has cascading context placeholder."""
        from arcane.templates import get_template

        template = get_template('milestone_header_generation')

        assert "{cascading_context}" in template
        assert "CASCADING CONTEXT" in template


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
