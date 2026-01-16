"""Template loading system for Arcane CLI."""

from pathlib import Path
from typing import Dict, Optional
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class TemplateLoader:
    """Loads and manages template files for roadmap generation."""

    def __init__(self):
        self.template_dir = Path(__file__).parent
        self._cache: Dict[str, str] = {}

    def load_template(self, template_name: str) -> str:
        """Load a template by name.

        Args:
            template_name: Name of the template to load

        Returns:
            Template content as string

        Raises:
            FileNotFoundError: If template file doesn't exist
        """
        if template_name in self._cache:
            return self._cache[template_name]

        template_path = self._resolve_template_path(template_name)

        if not template_path.exists():
            available = self.get_available_templates()
            raise FileNotFoundError(
                f"Template '{template_name}' not found. Available templates: {', '.join(available)}"
            )

        try:
            content = template_path.read_text(encoding='utf-8')
            self._cache[template_name] = content
            logger.debug("Loaded template: %s", template_name)
            return content
        except Exception as e:
            logger.error("Failed to load template %s: %s", template_name, e)
            raise

    def _resolve_template_path(self, template_name: str) -> Path:
        """Resolve template name to file path."""
        # Map template names to file paths
        template_mapping = {
            # Generation templates
            'roadmap_generation': 'generation/roadmap.txt',
            'outline_generation': 'generation/outline.txt',
            'semantic_outline_generation': 'generation/semantic_outline.txt',

            # Individual item templates
            'milestone_header_generation': 'individual_items/milestone.txt',
            'epic_generation_individual': 'individual_items/epic.txt',
            'story_with_tasks_generation': 'individual_items/story.txt',
            'task_generation_individual': 'individual_items/task.txt',

            # Two-pass story generation templates
            'story_description_generation': 'individual_items/story_description.txt',
            'story_tasks_generation': 'individual_items/story_tasks.txt',

            # Batch generation templates
            'epic_tasks_batch_generation': 'individual_items/epic_tasks_batch.txt',

            # Legacy template names for backward compatibility
            'milestone_generation_initial': 'individual_items/milestone.txt',
            'milestone_generation_continuation': 'individual_items/milestone.txt',
            'epic_generation': 'individual_items/epic.txt',
        }

        if template_name in template_mapping:
            return self.template_dir / template_mapping[template_name]

        # Fallback: try to find template file directly
        for subdir in ['generation', 'individual_items']:
            potential_path = self.template_dir / subdir / f"{template_name}.txt"
            if potential_path.exists():
                return potential_path

        return self.template_dir / f"{template_name}.txt"

    def get_available_templates(self) -> list[str]:
        """Get list of available template names."""
        templates = []

        for pattern in ['generation/*.txt', 'individual_items/*.txt']:
            for template_file in self.template_dir.glob(pattern):
                template_name = template_file.stem
                templates.append(template_name)

        return sorted(templates)

    def clear_cache(self) -> None:
        """Clear the template cache."""
        self._cache.clear()
        logger.debug("Template cache cleared")


# Global template loader instance
_template_loader = TemplateLoader()


def get_template(template_name: str) -> str:
    """Get a template by name.

    Args:
        template_name: Name of the template to load

    Returns:
        Template content as string
    """
    return _template_loader.load_template(template_name)


def get_available_templates() -> list[str]:
    """Get list of available template names."""
    return _template_loader.get_available_templates()


# Backward compatibility: provide PROMPT_TEMPLATES dict-like interface
class PromptTemplatesProxy:
    """Proxy class to provide backward compatibility with PROMPT_TEMPLATES dict."""

    def __getitem__(self, key: str) -> str:
        return get_template(key)

    def __contains__(self, key: str) -> bool:
        try:
            get_template(key)
            return True
        except FileNotFoundError:
            return False

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        try:
            return get_template(key)
        except FileNotFoundError:
            return default

    def keys(self):
        return get_available_templates()


# Provide backward compatibility
PROMPT_TEMPLATES = PromptTemplatesProxy()


__all__ = ['get_template', 'get_available_templates', 'PROMPT_TEMPLATES', 'TemplateLoader']