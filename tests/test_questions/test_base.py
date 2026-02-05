"""Tests for arcane.questions.base module."""

import pytest

from arcane.questions.base import Question, QuestionType


class TestQuestionTypeEnum:
    """Tests for the QuestionType enum."""

    def test_question_type_values(self):
        """Verify all QuestionType enum values exist."""
        assert QuestionType.TEXT == "text"
        assert QuestionType.INT == "int"
        assert QuestionType.CHOICE == "choice"
        assert QuestionType.MULTI == "multi"
        assert QuestionType.LIST == "list"
        assert QuestionType.CONFIRM == "confirm"

    def test_question_type_is_string_enum(self):
        """Verify QuestionType values are strings."""
        assert isinstance(QuestionType.TEXT.value, str)
        assert QuestionType.INT.value == "int"


# Concrete test question implementations for testing the abstract base
class TextTestQuestion(Question):
    """Test question for TEXT type."""

    @property
    def key(self) -> str:
        return "test_text"

    @property
    def prompt(self) -> str:
        return "Enter some text"

    @property
    def question_type(self) -> QuestionType:
        return QuestionType.TEXT


class IntTestQuestion(Question):
    """Test question for INT type."""

    @property
    def key(self) -> str:
        return "test_int"

    @property
    def prompt(self) -> str:
        return "Enter a number"

    @property
    def question_type(self) -> QuestionType:
        return QuestionType.INT

    @property
    def default(self) -> str:
        return "0"


class ListTestQuestion(Question):
    """Test question for LIST type."""

    @property
    def key(self) -> str:
        return "test_list"

    @property
    def prompt(self) -> str:
        return "Enter items"

    @property
    def question_type(self) -> QuestionType:
        return QuestionType.LIST


class ConfirmTestQuestion(Question):
    """Test question for CONFIRM type."""

    @property
    def key(self) -> str:
        return "test_confirm"

    @property
    def prompt(self) -> str:
        return "Do you confirm?"

    @property
    def question_type(self) -> QuestionType:
        return QuestionType.CONFIRM


class ChoiceTestQuestion(Question):
    """Test question for CHOICE type."""

    @property
    def key(self) -> str:
        return "test_choice"

    @property
    def prompt(self) -> str:
        return "Choose an option"

    @property
    def question_type(self) -> QuestionType:
        return QuestionType.CHOICE

    @property
    def options(self) -> list[str]:
        return ["option1", "option2", "option3"]


class OptionalTextQuestion(Question):
    """Test question that is not required."""

    @property
    def key(self) -> str:
        return "test_optional"

    @property
    def prompt(self) -> str:
        return "Optional input"

    @property
    def question_type(self) -> QuestionType:
        return QuestionType.TEXT

    @property
    def required(self) -> bool:
        return False


class TestQuestionInterface:
    """Tests for the Question abstract base class."""

    def test_question_properties(self):
        """Verify question properties return expected values."""
        question = TextTestQuestion()

        assert question.key == "test_text"
        assert question.prompt == "Enter some text"
        assert question.question_type == QuestionType.TEXT

    def test_default_required_is_true(self):
        """Verify required defaults to True."""
        question = TextTestQuestion()
        assert question.required is True

    def test_default_options_is_none(self):
        """Verify options defaults to None."""
        question = TextTestQuestion()
        assert question.options is None

    def test_default_default_is_none(self):
        """Verify default defaults to None."""
        question = TextTestQuestion()
        assert question.default is None

    def test_default_help_text_is_none(self):
        """Verify help_text defaults to None."""
        question = TextTestQuestion()
        assert question.help_text is None

    def test_custom_options(self):
        """Verify custom options are returned."""
        question = ChoiceTestQuestion()
        assert question.options == ["option1", "option2", "option3"]


class TestQuestionValidate:
    """Tests for Question.validate() method."""

    def test_validate_rejects_empty_when_required(self):
        """Validate rejects empty string when required=True."""
        question = TextTestQuestion()
        assert question.required is True
        assert question.validate("") is False
        assert question.validate("   ") is False

    def test_validate_accepts_non_empty(self):
        """Validate accepts non-empty string."""
        question = TextTestQuestion()
        assert question.validate("some text") is True
        assert question.validate("  text with spaces  ") is True

    def test_validate_accepts_empty_when_not_required(self):
        """Validate accepts empty string when required=False."""
        question = OptionalTextQuestion()
        assert question.required is False
        assert question.validate("") is True
        assert question.validate("   ") is True


class TestQuestionTransform:
    """Tests for Question.transform() method."""

    def test_transform_text_returns_stripped_string(self):
        """Transform for TEXT returns stripped string."""
        question = TextTestQuestion()
        assert question.transform("  hello world  ") == "hello world"
        assert question.transform("no spaces") == "no spaces"

    def test_transform_int_returns_integer(self):
        """Transform for INT returns integer."""
        question = IntTestQuestion()
        assert question.transform("3") == 3
        assert question.transform("  42  ") == 42
        assert question.transform("0") == 0

    def test_transform_int_returns_default_when_empty(self):
        """Transform for INT returns default when input is empty."""
        question = IntTestQuestion()
        assert question.default == "0"
        assert question.transform("") == "0"
        assert question.transform("   ") == "0"

    def test_transform_list_splits_by_comma(self):
        """Transform for LIST splits by comma and strips."""
        question = ListTestQuestion()
        assert question.transform("a, b, c") == ["a", "b", "c"]
        assert question.transform("  item1 ,  item2 , item3  ") == ["item1", "item2", "item3"]

    def test_transform_list_filters_empties(self):
        """Transform for LIST filters empty items."""
        question = ListTestQuestion()
        assert question.transform("a, , b, , c") == ["a", "b", "c"]
        assert question.transform(",,,") == []

    def test_transform_confirm_true_values(self):
        """Transform for CONFIRM returns True for affirmative values."""
        question = ConfirmTestQuestion()
        assert question.transform("y") is True
        assert question.transform("Y") is True
        assert question.transform("yes") is True
        assert question.transform("YES") is True
        assert question.transform("true") is True
        assert question.transform("True") is True
        assert question.transform("1") is True

    def test_transform_confirm_false_values(self):
        """Transform for CONFIRM returns False for negative values."""
        question = ConfirmTestQuestion()
        assert question.transform("n") is False
        assert question.transform("no") is False
        assert question.transform("NO") is False
        assert question.transform("false") is False
        assert question.transform("0") is False
        assert question.transform("anything else") is False

    def test_transform_choice_returns_stripped_string(self):
        """Transform for CHOICE returns stripped string."""
        question = ChoiceTestQuestion()
        assert question.transform("option1") == "option1"
        assert question.transform("  option2  ") == "option2"
