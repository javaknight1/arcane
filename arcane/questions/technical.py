"""Technical discovery questions for project planning.

These questions gather technical preferences:
- Tech stack
- Infrastructure preferences
- Existing codebase status
"""

from .base import Question, QuestionType


class TechStackQuestion(Question):
    """Question to gather technology preferences."""

    @property
    def key(self) -> str:
        return "tech_stack"

    @property
    def prompt(self) -> str:
        return "What technologies do you want to use?"

    @property
    def question_type(self) -> QuestionType:
        return QuestionType.LIST

    @property
    def required(self) -> bool:
        return False

    @property
    def help_text(self) -> str:
        return "Comma-separated (e.g.: React, Go, PostgreSQL) or leave blank for AI to suggest"


class InfrastructureQuestion(Question):
    """Question to gather infrastructure preferences."""

    @property
    def key(self) -> str:
        return "infrastructure_preferences"

    @property
    def prompt(self) -> str:
        return "Any infrastructure preferences?"

    @property
    def question_type(self) -> QuestionType:
        return QuestionType.CHOICE

    @property
    def required(self) -> bool:
        return False

    @property
    def options(self) -> list[str]:
        return ["AWS", "GCP", "Azure", "Serverless", "Self-hosted", "No preference"]


class ExistingCodebaseQuestion(Question):
    """Question to determine if adding to existing code."""

    @property
    def key(self) -> str:
        return "existing_codebase"

    @property
    def prompt(self) -> str:
        return "Are you adding to an existing codebase?"

    @property
    def question_type(self) -> QuestionType:
        return QuestionType.CONFIRM

    @property
    def default(self) -> str:
        return "n"
