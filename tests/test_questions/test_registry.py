"""Tests for arcane.questions.registry module."""

import pytest

from arcane.items import ProjectContext
from arcane.questions import QuestionRegistry


class TestQuestionRegistry:
    """Tests for the QuestionRegistry class."""

    def test_all_categories_present(self):
        """Verify all 4 category names exist."""
        registry = QuestionRegistry()

        expected_categories = [
            "Basic Information",
            "Constraints",
            "Technical",
            "Requirements",
        ]

        for category in expected_categories:
            assert category in registry.CATEGORIES, (
                f"Category '{category}' not found in registry"
            )

    def test_get_all_questions_count(self):
        """Verify total is 16 questions (4+4+3+5)."""
        registry = QuestionRegistry()
        all_questions = registry.get_all_questions()

        assert len(all_questions) == 16, (
            f"Expected 16 questions, got {len(all_questions)}"
        )

    def test_category_counts(self):
        """Verify each category has the expected number of questions."""
        registry = QuestionRegistry()

        expected_counts = {
            "Basic Information": 4,
            "Constraints": 4,
            "Technical": 3,
            "Requirements": 5,
        }

        for category, expected_count in expected_counts.items():
            questions = registry.get_category(category)
            assert len(questions) == expected_count, (
                f"Category '{category}' has {len(questions)} questions, "
                f"expected {expected_count}"
            )

    def test_all_keys_map_to_context(self):
        """Every question's .key is a valid field on ProjectContext."""
        registry = QuestionRegistry()
        context_fields = set(ProjectContext.model_fields.keys())

        for category, question in registry.get_all_questions():
            assert question.key in context_fields, (
                f"Question key '{question.key}' from category '{category}' "
                f"is not a valid ProjectContext field"
            )

    def test_no_duplicate_keys(self):
        """All question keys are unique."""
        registry = QuestionRegistry()
        all_questions = registry.get_all_questions()

        keys = [q.key for _, q in all_questions]
        unique_keys = set(keys)

        assert len(keys) == len(unique_keys), (
            f"Duplicate keys found: {[k for k in keys if keys.count(k) > 1]}"
        )

    def test_category_order(self):
        """Basic Information comes first, Requirements comes last."""
        registry = QuestionRegistry()
        categories = list(registry.CATEGORIES.keys())

        assert categories[0] == "Basic Information", (
            f"First category should be 'Basic Information', got '{categories[0]}'"
        )
        assert categories[-1] == "Requirements", (
            f"Last category should be 'Requirements', got '{categories[-1]}'"
        )

    def test_get_all_questions_returns_tuples(self):
        """get_all_questions returns (category, question) tuples."""
        registry = QuestionRegistry()
        all_questions = registry.get_all_questions()

        for item in all_questions:
            assert isinstance(item, tuple), "Items should be tuples"
            assert len(item) == 2, "Tuples should have 2 elements"
            category, question = item
            assert isinstance(category, str), "First element should be category string"
            assert hasattr(question, "key"), "Second element should be a Question"

    def test_get_category_returns_questions(self):
        """get_category returns list of Question instances."""
        registry = QuestionRegistry()
        questions = registry.get_category("Basic Information")

        assert len(questions) == 4
        for q in questions:
            assert hasattr(q, "key")
            assert hasattr(q, "prompt")
            assert hasattr(q, "question_type")

    def test_get_category_raises_on_unknown(self):
        """get_category raises KeyError for unknown category."""
        registry = QuestionRegistry()

        with pytest.raises(KeyError) as exc_info:
            registry.get_category("Unknown Category")

        assert "Unknown category" in str(exc_info.value)

    def test_questions_are_instantiated(self):
        """Questions returned are instances, not classes."""
        registry = QuestionRegistry()
        all_questions = registry.get_all_questions()

        for category, question in all_questions:
            # Should be an instance, not a class
            assert not isinstance(question, type), (
                f"Question should be instance, got class: {question}"
            )
            # Should have instance method accessible
            assert callable(question.validate)
            assert callable(question.transform)

    def test_complete_coverage(self):
        """All ProjectContext fields have a corresponding question."""
        registry = QuestionRegistry()
        context_fields = set(ProjectContext.model_fields.keys())
        question_keys = {q.key for _, q in registry.get_all_questions()}

        assert question_keys == context_fields, (
            f"Missing questions for: {context_fields - question_keys}\n"
            f"Extra questions: {question_keys - context_fields}"
        )
