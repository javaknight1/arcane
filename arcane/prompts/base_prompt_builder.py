#!/usr/bin/env python3
"""Base prompt builder for all LLM prompts."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class BasePromptBuilder(ABC):
    """Abstract base class for all prompt builders."""

    def __init__(self):
        self.template = self._get_template()

    @abstractmethod
    def _get_template(self) -> str:
        """Get the prompt template for this builder."""
        pass

    @abstractmethod
    def build_prompt(self, **kwargs) -> str:
        """Build the complete prompt."""
        pass

    def _format_template(self, template: str, variables: Dict[str, Any]) -> str:
        """Format template with variables, handling missing values gracefully."""
        # Get all template variables
        template_vars = self.get_template_variables()

        # Add default values for missing variables
        for var in template_vars:
            if var not in variables:
                variables[var] = 'Not specified'

        try:
            return template.format(**variables)
        except KeyError as e:
            # Handle any remaining missing variables
            missing_var = str(e).strip("'")
            variables[missing_var] = 'Not specified'
            return template.format(**variables)

    def _prepare_variables(self, raw_variables: Dict[str, Any]) -> Dict[str, str]:
        """Prepare variables for template formatting."""
        formatted_vars = {}

        for key, value in raw_variables.items():
            if value is None:
                formatted_vars[key] = 'Not specified'
            elif isinstance(value, list):
                formatted_vars[key] = ', '.join(str(v) for v in value) if value else 'None'
            elif isinstance(value, bool):
                formatted_vars[key] = 'Yes' if value else 'No'
            else:
                formatted_vars[key] = str(value)

        return formatted_vars

    def validate_required_variables(self, variables: Dict[str, Any], required: list) -> None:
        """Validate that required variables are present."""
        missing = [var for var in required if var not in variables or variables[var] is None]
        if missing:
            raise ValueError(f"Missing required variables: {', '.join(missing)}")

    def get_template_variables(self) -> list:
        """Extract variable names from template."""
        import re
        pattern = r'\{([^}]+)\}'
        return re.findall(pattern, self.template)