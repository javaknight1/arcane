"""Validation engines for roadmap items."""

from .dependency_validator import (
    DependencyValidator,
    DependencyIssue,
    IssueSeverity,
)
from .completeness_checker import (
    CompletenessChecker,
    CompletenessIssue,
    CompletenessSeverity,
    CoverageMapping,
    TaskSuggestion,
)
from .outline_validator import (
    OutlineValidator,
    OutlineIssue,
    OutlineSeverity,
)
from .cross_reference_validator import (
    CrossReferenceValidator,
    CoherenceIssue,
    CoherenceSeverity,
    CoherenceAutoFixer,
)

__all__ = [
    # Dependency validation
    'DependencyValidator',
    'DependencyIssue',
    'IssueSeverity',
    # Completeness checking
    'CompletenessChecker',
    'CompletenessIssue',
    'CompletenessSeverity',
    'CoverageMapping',
    'TaskSuggestion',
    # Outline validation
    'OutlineValidator',
    'OutlineIssue',
    'OutlineSeverity',
    # Cross-reference validation
    'CrossReferenceValidator',
    'CoherenceIssue',
    'CoherenceSeverity',
    'CoherenceAutoFixer',
]
