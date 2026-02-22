"""Template loader for Jinja2 prompt templates.

Loads and renders prompt templates for AI generation calls.
Templates are stored in the system/ and user/ subdirectories.
"""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader


class TemplateLoader:
    """Loads and renders Jinja2 prompt templates."""

    def __init__(self):
        template_dir = Path(__file__).parent
        self.env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def render_system(self, item_type: str) -> str:
        """Render a system prompt template (milestone, epic, story, task)."""
        template = self.env.get_template(f"system/{item_type}.j2")
        return template.render()

    def render_user(
        self,
        template_name: str,
        project_context: dict,
        parent_context: dict | None = None,
        sibling_context: list[str] | None = None,
        additional_guidance: str | None = None,
        errors: list[str] | None = None,
    ) -> str:
        """Render a user prompt template with context injection."""
        template = self.env.get_template(f"user/{template_name}.j2")
        return template.render(
            project=project_context,
            parent=parent_context,
            siblings=sibling_context,
            guidance=additional_guidance,
            errors=errors,
        )
