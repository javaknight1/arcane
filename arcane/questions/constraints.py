"""Constraint discovery questions for project planning.

These questions gather project constraints:
- Timeline
- Team size
- Developer experience level
- Budget constraints
"""

from .base import Question, QuestionType


class TimelineQuestion(Question):
    """Question to gather the target timeline."""

    @property
    def key(self) -> str:
        return "timeline"

    @property
    def prompt(self) -> str:
        return "What's your target timeline?"

    @property
    def question_type(self) -> QuestionType:
        return QuestionType.CHOICE

    @property
    def options(self) -> list[str]:
        return ["1 month MVP", "3 months", "6 months", "1 year", "custom"]


class TeamSizeQuestion(Question):
    """Question to gather the team size."""

    @property
    def key(self) -> str:
        return "team_size"

    @property
    def prompt(self) -> str:
        return "How many developers will work on this?"

    @property
    def question_type(self) -> QuestionType:
        return QuestionType.INT

    @property
    def default(self) -> str:
        return "1"

    def validate(self, raw_input: str) -> bool:
        """Validate team size is between 1 and 100."""
        try:
            val = int(raw_input.strip()) if raw_input.strip() else int(self.default)
            return 1 <= val <= 100
        except ValueError:
            return False


class DeveloperExperienceQuestion(Question):
    """Question to gather the team's experience level."""

    @property
    def key(self) -> str:
        return "developer_experience"

    @property
    def prompt(self) -> str:
        return "What's the team's experience level?"

    @property
    def question_type(self) -> QuestionType:
        return QuestionType.CHOICE

    @property
    def options(self) -> list[str]:
        return ["junior", "mid-level", "senior", "mixed"]


class BudgetQuestion(Question):
    """Question to gather budget constraints."""

    @property
    def key(self) -> str:
        return "budget_constraints"

    @property
    def prompt(self) -> str:
        return "What's your budget situation?"

    @property
    def question_type(self) -> QuestionType:
        return QuestionType.CHOICE

    @property
    def options(self) -> list[str]:
        return ["minimal (free tier everything)", "moderate", "flexible"]
