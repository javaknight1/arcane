"""Requirements discovery questions for project planning.

These questions gather feature requirements:
- Must-have features
- Nice-to-have features
- Out of scope items
- Similar products for reference
- Additional notes
"""

from .base import Question, QuestionType


class MustHaveQuestion(Question):
    """Question to gather must-have features."""

    @property
    def key(self) -> str:
        return "must_have_features"

    @property
    def prompt(self) -> str:
        return "What features are absolutely required for launch?"

    @property
    def question_type(self) -> QuestionType:
        return QuestionType.LIST

    @property
    def help_text(self) -> str:
        return "Comma-separated, e.g.: user auth, job scheduling, mobile app"


class NiceToHaveQuestion(Question):
    """Question to gather nice-to-have features."""

    @property
    def key(self) -> str:
        return "nice_to_have_features"

    @property
    def prompt(self) -> str:
        return "What features would be nice to have but aren't critical?"

    @property
    def question_type(self) -> QuestionType:
        return QuestionType.LIST

    @property
    def required(self) -> bool:
        return False


class OutOfScopeQuestion(Question):
    """Question to gather out-of-scope items."""

    @property
    def key(self) -> str:
        return "out_of_scope"

    @property
    def prompt(self) -> str:
        return "Anything explicitly out of scope?"

    @property
    def question_type(self) -> QuestionType:
        return QuestionType.LIST

    @property
    def required(self) -> bool:
        return False

    @property
    def help_text(self) -> str:
        return "Helps the AI avoid generating roadmap items for things you don't want"


class SimilarProductsQuestion(Question):
    """Question to gather similar product references."""

    @property
    def key(self) -> str:
        return "similar_products"

    @property
    def prompt(self) -> str:
        return "Any similar products or competitors to reference?"

    @property
    def question_type(self) -> QuestionType:
        return QuestionType.LIST

    @property
    def required(self) -> bool:
        return False


class NotesQuestion(Question):
    """Question to gather additional notes."""

    @property
    def key(self) -> str:
        return "notes"

    @property
    def prompt(self) -> str:
        return "Any additional context or notes?"

    @property
    def question_type(self) -> QuestionType:
        return QuestionType.TEXT

    @property
    def required(self) -> bool:
        return False
