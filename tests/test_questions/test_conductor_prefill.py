"""Tests for QuestionConductor prefill and non-interactive mode."""

from unittest.mock import AsyncMock, patch

import pytest
from rich.console import Console

from arcane.items.context import ProjectContext
from arcane.questions.conductor import QuestionConductor


# Complete set of answers for all 16 questions
ALL_ANSWERS = {
    "project_name": "Test Project",
    "vision": "A test project vision",
    "problem_statement": "Solving a test problem",
    "target_users": ["developers", "testers"],
    "timeline": "3 months",
    "team_size": 2,
    "developer_experience": "senior",
    "budget_constraints": "moderate",
    "tech_stack": ["Python", "React"],
    "infrastructure_preferences": "AWS",
    "existing_codebase": False,
    "must_have_features": ["auth", "api"],
    "nice_to_have_features": ["dark mode"],
    "out_of_scope": ["mobile"],
    "similar_products": ["competitor"],
    "notes": "Some notes",
}


class TestAllPrefilledNonInteractive:
    """Tests for fully prefilled, non-interactive mode."""

    @pytest.mark.asyncio
    async def test_all_prefilled_non_interactive_returns_context(self):
        """Prefilling all 16 answers with interactive=False returns a valid ProjectContext."""
        console = Console(quiet=True)
        conductor = QuestionConductor(console, interactive=False)
        conductor.answers.update(ALL_ANSWERS)

        context = await conductor.run()

        assert isinstance(context, ProjectContext)
        assert context.project_name == "Test Project"
        assert context.vision == "A test project vision"
        assert context.problem_statement == "Solving a test problem"
        assert context.target_users == ["developers", "testers"]
        assert context.timeline == "3 months"
        assert context.team_size == 2
        assert context.developer_experience == "senior"
        assert context.budget_constraints == "moderate"
        assert context.tech_stack == ["Python", "React"]
        assert context.infrastructure_preferences == "AWS"
        assert context.existing_codebase is False
        assert context.must_have_features == ["auth", "api"]
        assert context.nice_to_have_features == ["dark mode"]
        assert context.out_of_scope == ["mobile"]
        assert context.similar_products == ["competitor"]
        assert context.notes == "Some notes"

    @pytest.mark.asyncio
    async def test_all_prefilled_non_interactive_skips_review(self):
        """When all prefilled and non-interactive, _review_summary is NOT called."""
        console = Console(quiet=True)
        conductor = QuestionConductor(console, interactive=False)
        conductor.answers.update(ALL_ANSWERS)

        with patch.object(conductor, "_review_summary", new_callable=AsyncMock) as mock_review:
            await conductor.run()
            mock_review.assert_not_called()

    @pytest.mark.asyncio
    async def test_all_prefilled_non_interactive_skips_welcome(self):
        """When all prefilled, the welcome panel is not printed."""
        console = Console(quiet=True)
        conductor = QuestionConductor(console, interactive=False)
        conductor.answers.update(ALL_ANSWERS)

        with patch.object(console, "print") as mock_print:
            await conductor.run()
            # No Panel should be printed (welcome banner)
            for call in mock_print.call_args_list:
                args = call[0]
                for arg in args:
                    assert "Let's build your roadmap" not in str(arg)


class TestAllPrefilledInteractive:
    """Tests for fully prefilled, interactive mode."""

    @pytest.mark.asyncio
    async def test_all_prefilled_interactive_shows_summary(self):
        """When all prefilled but interactive=True, _review_summary IS called."""
        console = Console(quiet=True)
        conductor = QuestionConductor(console, interactive=True)
        conductor.answers.update(ALL_ANSWERS)

        with patch.object(conductor, "_review_summary", new_callable=AsyncMock) as mock_review:
            await conductor.run()
            mock_review.assert_called_once()


class TestPartialPrefill:
    """Tests for partially prefilled answers."""

    @pytest.mark.asyncio
    async def test_partial_prefill_skips_prefilled_questions(self):
        """Prefilled answers are skipped, others are asked."""
        console = Console(quiet=True)
        conductor = QuestionConductor(console, interactive=False)
        # Only prefill project_name
        conductor.answers["project_name"] = "Partial Project"

        # Mock _ask to provide remaining answers
        remaining_answers = {
            "vision": "A vision",
            "problem_statement": "A problem",
            "target_users": ["devs"],
            "timeline": "3 months",
            "team_size": 1,
            "developer_experience": "senior",
            "budget_constraints": "moderate",
            "tech_stack": ["Python"],
            "infrastructure_preferences": "No preference",
            "existing_codebase": False,
            "must_have_features": ["feature1"],
            "nice_to_have_features": [],
            "out_of_scope": [],
            "similar_products": [],
            "notes": "",
        }

        call_count = 0

        def mock_ask(question, allow_back=True):
            nonlocal call_count
            call_count += 1
            return remaining_answers[question.key]

        with patch.object(conductor, "_ask", side_effect=mock_ask):
            with patch.object(conductor, "_review_summary", new_callable=AsyncMock):
                context = await conductor.run()

        assert context.project_name == "Partial Project"
        # 15 questions should have been asked (16 total minus 1 prefilled)
        assert call_count == 15
