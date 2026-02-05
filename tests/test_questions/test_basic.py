"""Tests for arcane.questions.basic module."""

import pytest

from arcane.questions.base import QuestionType
from arcane.questions.basic import (
    ProjectNameQuestion,
    VisionQuestion,
    ProblemStatementQuestion,
    TargetUsersQuestion,
)


class TestProjectNameQuestion:
    """Tests for ProjectNameQuestion."""

    def test_key_matches_context_field(self):
        """Verify key matches ProjectContext field name."""
        question = ProjectNameQuestion()
        assert question.key == "project_name"

    def test_question_type_is_text(self):
        """Verify question_type is TEXT."""
        question = ProjectNameQuestion()
        assert question.question_type == QuestionType.TEXT

    def test_required_is_true(self):
        """Verify required is True."""
        question = ProjectNameQuestion()
        assert question.required is True

    def test_prompt_is_set(self):
        """Verify prompt is set."""
        question = ProjectNameQuestion()
        assert question.prompt == "What's the name of your project?"

    def test_transform_returns_stripped_string(self):
        """Test transform with sample input."""
        question = ProjectNameQuestion()
        assert question.transform("  My Project  ") == "My Project"


class TestVisionQuestion:
    """Tests for VisionQuestion."""

    def test_key_matches_context_field(self):
        """Verify key matches ProjectContext field name."""
        question = VisionQuestion()
        assert question.key == "vision"

    def test_question_type_is_text(self):
        """Verify question_type is TEXT."""
        question = VisionQuestion()
        assert question.question_type == QuestionType.TEXT

    def test_required_is_true(self):
        """Verify required is True."""
        question = VisionQuestion()
        assert question.required is True

    def test_help_text_is_set(self):
        """Verify help_text is set."""
        question = VisionQuestion()
        assert question.help_text == "Be specific about what the app does, not just the category"

    def test_transform_returns_stripped_string(self):
        """Test transform with sample input."""
        question = VisionQuestion()
        result = question.transform("  A mobile app for tracking workouts  ")
        assert result == "A mobile app for tracking workouts"


class TestProblemStatementQuestion:
    """Tests for ProblemStatementQuestion."""

    def test_key_matches_context_field(self):
        """Verify key matches ProjectContext field name."""
        question = ProblemStatementQuestion()
        assert question.key == "problem_statement"

    def test_question_type_is_text(self):
        """Verify question_type is TEXT."""
        question = ProblemStatementQuestion()
        assert question.question_type == QuestionType.TEXT

    def test_required_is_true(self):
        """Verify required is True."""
        question = ProblemStatementQuestion()
        assert question.required is True

    def test_prompt_is_set(self):
        """Verify prompt is set."""
        question = ProblemStatementQuestion()
        assert question.prompt == "What problem does this solve for users?"

    def test_transform_returns_stripped_string(self):
        """Test transform with sample input."""
        question = ProblemStatementQuestion()
        result = question.transform("Users struggle to keep track of their fitness goals")
        assert result == "Users struggle to keep track of their fitness goals"


class TestTargetUsersQuestion:
    """Tests for TargetUsersQuestion."""

    def test_key_matches_context_field(self):
        """Verify key matches ProjectContext field name."""
        question = TargetUsersQuestion()
        assert question.key == "target_users"

    def test_question_type_is_list(self):
        """Verify question_type is LIST."""
        question = TargetUsersQuestion()
        assert question.question_type == QuestionType.LIST

    def test_required_is_true(self):
        """Verify required is True."""
        question = TargetUsersQuestion()
        assert question.required is True

    def test_help_text_is_set(self):
        """Verify help_text is set."""
        question = TargetUsersQuestion()
        assert "Comma-separated" in question.help_text

    def test_transform_returns_list(self):
        """Test transform with sample input."""
        question = TargetUsersQuestion()
        result = question.transform("field technicians, dispatchers, business owners")
        assert result == ["field technicians", "dispatchers", "business owners"]

    def test_transform_handles_extra_spaces(self):
        """Test transform handles extra spaces correctly."""
        question = TargetUsersQuestion()
        result = question.transform("  developers ,  designers  ,  product managers  ")
        assert result == ["developers", "designers", "product managers"]


class TestAllBasicQuestionsMatchContext:
    """Verify all basic questions have keys matching ProjectContext fields."""

    def test_all_keys_are_valid_context_fields(self):
        """All question keys should be valid ProjectContext field names."""
        from arcane.items import ProjectContext

        questions = [
            ProjectNameQuestion(),
            VisionQuestion(),
            ProblemStatementQuestion(),
            TargetUsersQuestion(),
        ]

        context_fields = set(ProjectContext.model_fields.keys())

        for question in questions:
            assert question.key in context_fields, (
                f"Question key '{question.key}' is not a valid ProjectContext field"
            )
