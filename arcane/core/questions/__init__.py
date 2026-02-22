"""Discovery questions for gathering project context.

This module provides the Question interface, registry, conductor, and
concrete question implementations used to gather information before
roadmap generation.
"""

from .base import Question, QuestionType
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
from .registry import QuestionRegistry
from .conductor import QuestionConductor

__all__ = [
    # Base
    "Question",
    "QuestionType",
    # Registry and Conductor
    "QuestionRegistry",
    "QuestionConductor",
    # Basic
    "ProjectNameQuestion",
    "VisionQuestion",
    "ProblemStatementQuestion",
    "TargetUsersQuestion",
    # Constraints
    "TimelineQuestion",
    "TeamSizeQuestion",
    "DeveloperExperienceQuestion",
    "BudgetQuestion",
    # Technical
    "TechStackQuestion",
    "InfrastructureQuestion",
    "ExistingCodebaseQuestion",
    # Requirements
    "MustHaveQuestion",
    "NiceToHaveQuestion",
    "OutOfScopeQuestion",
    "SimilarProductsQuestion",
    "NotesQuestion",
]
