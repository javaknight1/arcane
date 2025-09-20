"""Prompt templates for LLM generation.

DEPRECATED: This file is being migrated to the new template system.
Use arcane.templates.get_template() instead.
"""

import warnings
from ..templates import PROMPT_TEMPLATES as _NEW_TEMPLATES

# Issue deprecation warning when imported
warnings.warn(
    "arcane.constants.templates is deprecated. Use arcane.templates.get_template() instead.",
    DeprecationWarning,
    stacklevel=2
)

# Provide backward compatibility through proxy
PROMPT_TEMPLATES = _NEW_TEMPLATES