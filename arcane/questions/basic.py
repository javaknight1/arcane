"""Basic discovery questions for project information.

These questions gather fundamental project details:
- Project name
- Vision/description
- Problem statement
- Target users
"""

from .base import Question, QuestionType


class ProjectNameQuestion(Question):
    """Question to gather the project name."""

    @property
    def key(self) -> str:
        return "project_name"

    @property
    def prompt(self) -> str:
        return "What's the name of your project?"

    @property
    def question_type(self) -> QuestionType:
        return QuestionType.TEXT


class VisionQuestion(Question):
    """Question to gather the project vision/description."""

    @property
    def key(self) -> str:
        return "vision"

    @property
    def prompt(self) -> str:
        return "Describe your app in 2-3 sentences. What does it do?"

    @property
    def question_type(self) -> QuestionType:
        return QuestionType.TEXT

    @property
    def help_text(self) -> str:
        return "Be specific about what the app does, not just the category"


class ProblemStatementQuestion(Question):
    """Question to gather the problem statement."""

    @property
    def key(self) -> str:
        return "problem_statement"

    @property
    def prompt(self) -> str:
        return "What problem does this solve for users?"

    @property
    def question_type(self) -> QuestionType:
        return QuestionType.TEXT


class TargetUsersQuestion(Question):
    """Question to gather target user information."""

    @property
    def key(self) -> str:
        return "target_users"

    @property
    def prompt(self) -> str:
        return "Who are your target users?"

    @property
    def question_type(self) -> QuestionType:
        return QuestionType.LIST

    @property
    def help_text(self) -> str:
        return "Comma-separated, e.g.: field technicians, dispatchers, business owners"
