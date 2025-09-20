"""Preference validation and consistency checking module."""

from .preference_validator import PreferenceValidator, ValidationIssue, ValidationSeverity

__all__ = ['PreferenceValidator', 'ValidationIssue', 'ValidationSeverity']