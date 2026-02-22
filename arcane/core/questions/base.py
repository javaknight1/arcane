"""Base interface for discovery questions.

Every question must define key, prompt, and question_type.
Questions are used by the QuestionConductor to gather project context
before AI generation begins.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any


class QuestionType(str, Enum):
    """Types of input a question can collect."""

    TEXT = "text"  # Free-form text input
    INT = "int"  # Integer input
    CHOICE = "choice"  # Single selection from options
    MULTI = "multi"  # Multiple selections from options
    LIST = "list"  # Comma-separated list input
    CONFIRM = "confirm"  # Yes/no


class Question(ABC):
    """Base interface for all discovery questions.

    Every question must define:
    - key: unique identifier (maps to ProjectContext field name)
    - prompt: the question string shown to the user
    - question_type: what kind of input to collect

    And can optionally override:
    - required: whether the user must answer
    - options: list of valid answers (for CHOICE and MULTI types)
    - default: default value if user skips
    - help_text: additional guidance for the user

    Subclasses can also override:
    - validate(): validate the raw user input
    - transform(): convert raw input to the output type
    """

    @property
    @abstractmethod
    def key(self) -> str:
        """Unique identifier for this question (maps to ProjectContext field)."""
        pass

    @property
    @abstractmethod
    def prompt(self) -> str:
        """The question text shown to the user."""
        pass

    @property
    @abstractmethod
    def question_type(self) -> QuestionType:
        """The type of input to collect."""
        pass

    @property
    def required(self) -> bool:
        """Whether the user must answer this question."""
        return True

    @property
    def options(self) -> list[str] | None:
        """List of valid answers for CHOICE and MULTI types."""
        return None

    @property
    def default(self) -> str | None:
        """Default value if user skips the question."""
        return None

    @property
    def help_text(self) -> str | None:
        """Additional guidance displayed to the user."""
        return None

    def validate(self, raw_input: str) -> bool:
        """Validate the raw user input.

        Override for custom validation logic.

        Args:
            raw_input: The raw string input from the user.

        Returns:
            True if the input is valid, False otherwise.
        """
        if self.required and not raw_input.strip():
            return False
        return True

    def transform(self, raw_input: str) -> Any:
        """Transform raw string input into the desired output type.

        Args:
            raw_input: The raw string input from the user.

        Returns:
            The transformed value appropriate for the question type.
        """
        raw = raw_input.strip()

        match self.question_type:
            case QuestionType.TEXT:
                return raw
            case QuestionType.INT:
                return int(raw) if raw else self.default
            case QuestionType.CHOICE:
                return raw
            case QuestionType.MULTI:
                return [x.strip() for x in raw.split(",") if x.strip()]
            case QuestionType.LIST:
                return [x.strip() for x in raw.split(",") if x.strip()]
            case QuestionType.CONFIRM:
                return raw.lower() in ("y", "yes", "true", "1")
