"""Question registry for organizing discovery questions by category.

The QuestionRegistry provides an ordered collection of all questions,
grouped by category for structured presentation to the user.
"""

from .base import Question
from .basic import (
    ProjectNameQuestion,
    VisionQuestion,
    ProblemStatementQuestion,
    TargetUsersQuestion,
)
from .constraints import (
    TimelineQuestion,
    TeamSizeQuestion,
    DeveloperExperienceQuestion,
    BudgetQuestion,
)
from .technical import (
    TechStackQuestion,
    InfrastructureQuestion,
    ExistingCodebaseQuestion,
)
from .requirements import (
    MustHaveQuestion,
    NiceToHaveQuestion,
    OutOfScopeQuestion,
    SimilarProductsQuestion,
    NotesQuestion,
)


class QuestionRegistry:
    """Ordered collection of all questions, grouped by category.

    Categories are presented in order during the interactive question flow.
    Each category contains question classes that are instantiated when needed.
    """

    CATEGORIES: dict[str, list[type[Question]]] = {
        "Basic Information": [
            ProjectNameQuestion,
            VisionQuestion,
            ProblemStatementQuestion,
            TargetUsersQuestion,
        ],
        "Constraints": [
            TimelineQuestion,
            TeamSizeQuestion,
            DeveloperExperienceQuestion,
            BudgetQuestion,
        ],
        "Technical": [
            TechStackQuestion,
            InfrastructureQuestion,
            ExistingCodebaseQuestion,
        ],
        "Requirements": [
            MustHaveQuestion,
            NiceToHaveQuestion,
            OutOfScopeQuestion,
            SimilarProductsQuestion,
            NotesQuestion,
        ],
    }

    def get_all_questions(self) -> list[tuple[str, Question]]:
        """Return all questions as (category_name, question_instance) pairs.

        Questions are returned in category order, with each question
        instantiated from its class.

        Returns:
            List of (category_name, question_instance) tuples in order.
        """
        result = []
        for category, question_classes in self.CATEGORIES.items():
            for cls in question_classes:
                result.append((category, cls()))
        return result

    def get_category(self, category: str) -> list[Question]:
        """Return instantiated questions for one category.

        Args:
            category: The category name to retrieve.

        Returns:
            List of instantiated Question objects for the category.

        Raises:
            KeyError: If the category doesn't exist.
        """
        if category not in self.CATEGORIES:
            raise KeyError(f"Unknown category: {category}")
        return [cls() for cls in self.CATEGORIES[category]]
