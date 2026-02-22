"""Comprehensive tests for all question classes.

Tests every question class across all four files (basic, constraints,
technical, requirements) to verify:
- Keys match ProjectContext fields
- question_type is set correctly
- transform() works with realistic input
"""

import pytest

from arcane.core.items import ProjectContext
from arcane.core.questions import (
    QuestionType,
    # Basic
    ProjectNameQuestion,
    VisionQuestion,
    ProblemStatementQuestion,
    TargetUsersQuestion,
    # Constraints
    TimelineQuestion,
    TeamSizeQuestion,
    DeveloperExperienceQuestion,
    BudgetQuestion,
    # Technical
    TechStackQuestion,
    InfrastructureQuestion,
    ExistingCodebaseQuestion,
    # Requirements
    MustHaveQuestion,
    NiceToHaveQuestion,
    OutOfScopeQuestion,
    SimilarProductsQuestion,
    NotesQuestion,
)


# All question classes for parametrized testing
ALL_QUESTION_CLASSES = [
    # Basic
    ProjectNameQuestion,
    VisionQuestion,
    ProblemStatementQuestion,
    TargetUsersQuestion,
    # Constraints
    TimelineQuestion,
    TeamSizeQuestion,
    DeveloperExperienceQuestion,
    BudgetQuestion,
    # Technical
    TechStackQuestion,
    InfrastructureQuestion,
    ExistingCodebaseQuestion,
    # Requirements
    MustHaveQuestion,
    NiceToHaveQuestion,
    OutOfScopeQuestion,
    SimilarProductsQuestion,
    NotesQuestion,
]


class TestAllQuestionsMatchContext:
    """Verify all question keys are valid ProjectContext fields."""

    @pytest.mark.parametrize("question_class", ALL_QUESTION_CLASSES)
    def test_key_is_valid_context_field(self, question_class):
        """Every question key must be a valid ProjectContext field name."""
        question = question_class()
        context_fields = set(ProjectContext.model_fields.keys())

        assert question.key in context_fields, (
            f"{question_class.__name__}.key = '{question.key}' "
            f"is not a valid ProjectContext field"
        )

    @pytest.mark.parametrize("question_class", ALL_QUESTION_CLASSES)
    def test_question_type_is_set(self, question_class):
        """Every question must have a valid question_type."""
        question = question_class()
        assert isinstance(question.question_type, QuestionType), (
            f"{question_class.__name__}.question_type must be a QuestionType"
        )


class TestBasicQuestionsTransform:
    """Test transform for basic questions."""

    def test_project_name_transform(self):
        """ProjectNameQuestion transforms to stripped string."""
        q = ProjectNameQuestion()
        assert q.transform("  My Project  ") == "My Project"

    def test_vision_transform(self):
        """VisionQuestion transforms to stripped string."""
        q = VisionQuestion()
        assert q.transform("  Build amazing apps  ") == "Build amazing apps"

    def test_problem_statement_transform(self):
        """ProblemStatementQuestion transforms to stripped string."""
        q = ProblemStatementQuestion()
        assert q.transform("  Users need better tools  ") == "Users need better tools"

    def test_target_users_transform(self):
        """TargetUsersQuestion transforms to list of strings."""
        q = TargetUsersQuestion()
        result = q.transform("developers, designers, product managers")
        assert result == ["developers", "designers", "product managers"]


class TestConstraintQuestionsTransform:
    """Test transform for constraint questions."""

    def test_timeline_transform(self):
        """TimelineQuestion transforms to stripped string (CHOICE)."""
        q = TimelineQuestion()
        assert q.transform("3 months") == "3 months"
        assert q.options == ["1 month MVP", "3 months", "6 months", "1 year", "custom"]

    def test_team_size_transform(self):
        """TeamSizeQuestion transforms to integer."""
        q = TeamSizeQuestion()
        assert q.transform("5") == 5
        assert q.transform("  10  ") == 10

    def test_developer_experience_transform(self):
        """DeveloperExperienceQuestion transforms to stripped string."""
        q = DeveloperExperienceQuestion()
        assert q.transform("senior") == "senior"
        assert q.options == ["junior", "mid-level", "senior", "mixed"]

    def test_budget_transform(self):
        """BudgetQuestion transforms to stripped string."""
        q = BudgetQuestion()
        assert q.transform("moderate") == "moderate"
        assert "minimal" in q.options[0]


class TestTeamSizeValidation:
    """Specific tests for TeamSizeQuestion.validate()."""

    def test_validate_zero_returns_false(self):
        """TeamSizeQuestion.validate('0') returns False."""
        q = TeamSizeQuestion()
        assert q.validate("0") is False

    def test_validate_one_returns_true(self):
        """TeamSizeQuestion.validate('1') returns True."""
        q = TeamSizeQuestion()
        assert q.validate("1") is True

    def test_validate_fifty_returns_true(self):
        """TeamSizeQuestion.validate('50') returns True."""
        q = TeamSizeQuestion()
        assert q.validate("50") is True

    def test_validate_hundred_returns_true(self):
        """TeamSizeQuestion.validate('100') returns True (boundary)."""
        q = TeamSizeQuestion()
        assert q.validate("100") is True

    def test_validate_101_returns_false(self):
        """TeamSizeQuestion.validate('101') returns False."""
        q = TeamSizeQuestion()
        assert q.validate("101") is False

    def test_validate_abc_returns_false(self):
        """TeamSizeQuestion.validate('abc') returns False."""
        q = TeamSizeQuestion()
        assert q.validate("abc") is False

    def test_validate_negative_returns_false(self):
        """TeamSizeQuestion.validate('-1') returns False."""
        q = TeamSizeQuestion()
        assert q.validate("-1") is False

    def test_validate_empty_uses_default(self):
        """TeamSizeQuestion.validate('') uses default value."""
        q = TeamSizeQuestion()
        assert q.default == "1"
        assert q.validate("") is True  # default of 1 is valid


class TestTechnicalQuestionsTransform:
    """Test transform for technical questions."""

    def test_tech_stack_transform(self):
        """TechStackQuestion transforms to list of strings."""
        q = TechStackQuestion()
        result = q.transform("React, Python, PostgreSQL")
        assert result == ["React", "Python", "PostgreSQL"]
        assert q.required is False

    def test_tech_stack_transform_empty(self):
        """TechStackQuestion transforms empty to empty list."""
        q = TechStackQuestion()
        assert q.transform("") == []

    def test_infrastructure_transform(self):
        """InfrastructureQuestion transforms to stripped string."""
        q = InfrastructureQuestion()
        assert q.transform("AWS") == "AWS"
        assert "AWS" in q.options
        assert q.required is False

    def test_existing_codebase_transform_yes(self):
        """ExistingCodebaseQuestion transforms 'y' to True."""
        q = ExistingCodebaseQuestion()
        assert q.transform("y") is True
        assert q.transform("yes") is True

    def test_existing_codebase_transform_no(self):
        """ExistingCodebaseQuestion transforms 'n' to False."""
        q = ExistingCodebaseQuestion()
        assert q.transform("n") is False
        assert q.transform("no") is False
        assert q.default == "n"


class TestRequirementQuestionsTransform:
    """Test transform for requirement questions."""

    def test_must_have_transform(self):
        """MustHaveQuestion transforms to list of strings."""
        q = MustHaveQuestion()
        result = q.transform("user auth, job scheduling, mobile app")
        assert result == ["user auth", "job scheduling", "mobile app"]
        assert q.required is True

    def test_nice_to_have_transform(self):
        """NiceToHaveQuestion transforms to list of strings."""
        q = NiceToHaveQuestion()
        result = q.transform("dark mode, export to PDF")
        assert result == ["dark mode", "export to PDF"]
        assert q.required is False

    def test_out_of_scope_transform(self):
        """OutOfScopeQuestion transforms to list of strings."""
        q = OutOfScopeQuestion()
        result = q.transform("blockchain, AI chat")
        assert result == ["blockchain", "AI chat"]
        assert q.required is False
        assert "avoid" in q.help_text.lower()

    def test_similar_products_transform(self):
        """SimilarProductsQuestion transforms to list of strings."""
        q = SimilarProductsQuestion()
        result = q.transform("Notion, Trello, Asana")
        assert result == ["Notion", "Trello", "Asana"]
        assert q.required is False

    def test_notes_transform(self):
        """NotesQuestion transforms to stripped string."""
        q = NotesQuestion()
        result = q.transform("  Must comply with HIPAA  ")
        assert result == "Must comply with HIPAA"
        assert q.required is False


class TestQuestionCount:
    """Verify we have all expected questions."""

    def test_total_question_count(self):
        """We should have exactly 16 question classes."""
        assert len(ALL_QUESTION_CLASSES) == 16

    def test_all_context_fields_covered(self):
        """Every ProjectContext field should have a corresponding question."""
        context_fields = set(ProjectContext.model_fields.keys())
        question_keys = {q().key for q in ALL_QUESTION_CLASSES}

        assert question_keys == context_fields, (
            f"Missing questions for: {context_fields - question_keys}\n"
            f"Extra questions: {question_keys - context_fields}"
        )
