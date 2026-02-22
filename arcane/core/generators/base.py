"""Base generator class with retry logic and validation.

All generators inherit from BaseGenerator which handles:
- Template rendering for system and user prompts
- AI client calls with structured output
- Retry logic with error feedback
- Custom validation hooks
"""

from abc import ABC, abstractmethod

from pydantic import BaseModel, ValidationError
from rich.console import Console

from arcane.core.clients.base import BaseAIClient, AIClientError
from arcane.core.items.context import ProjectContext
from arcane.core.templates.loader import TemplateLoader


class GenerationError(Exception):
    """Raised when generation fails after all retries."""

    pass


class BaseGenerator(ABC):
    """Base class for all generators.

    Handles: template rendering, AI calls, retry with feedback, validation.
    Subclasses only need to define item_type and response_model.
    """

    def __init__(
        self,
        client: BaseAIClient,
        console: Console,
        templates: TemplateLoader,
        max_retries: int = 3,
    ):
        self.client = client
        self.console = console
        self.templates = templates
        self.max_retries = max_retries

    @property
    @abstractmethod
    def item_type(self) -> str:
        """'milestone', 'epic', 'story', or 'task'"""
        pass

    @abstractmethod
    def get_response_model(self) -> type[BaseModel]:
        """The Pydantic model the AI response must conform to."""
        pass

    async def generate(
        self,
        project_context: ProjectContext,
        parent_context: dict | None = None,
        sibling_context: list[str] | None = None,
        additional_guidance: str | None = None,
    ) -> BaseModel:
        """Generate items with retry logic and validation."""

        system_prompt = self.templates.render_system(self.item_type)
        user_prompt = self.templates.render_user(
            "generate",
            project_context=project_context.model_dump(),
            parent_context=parent_context,
            sibling_context=sibling_context,
            additional_guidance=additional_guidance,
        )

        errors_so_far: list[str] = []

        for attempt in range(self.max_retries):
            try:
                if errors_so_far:
                    user_prompt = self.templates.render_user(
                        "refine",
                        project_context=project_context.model_dump(),
                        errors=errors_so_far,
                    )

                response = await self.client.generate(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    response_model=self.get_response_model(),
                    level=self.item_type,
                )

                extra_errors = self._validate(response, project_context, sibling_context)
                if extra_errors:
                    errors_so_far.extend(extra_errors)
                    continue

                return response

            except (AIClientError, ValidationError) as e:
                errors_so_far.append(str(e))
                if attempt < self.max_retries - 1:
                    self.console.print(
                        f"  [yellow]⚠ Attempt {attempt + 1} failed, retrying...[/yellow]"
                    )
                else:
                    raise GenerationError(
                        f"Failed to generate {self.item_type} after {self.max_retries} attempts.\n"
                        f"Errors: {errors_so_far}"
                    )

        # This should not be reached, but just in case
        raise GenerationError(
            f"Failed to generate {self.item_type} after {self.max_retries} attempts.\n"
            f"Errors: {errors_so_far}"
        )

    def _validate(
        self,
        response: BaseModel,
        context: ProjectContext,
        siblings: list[str] | None,
    ) -> list[str]:
        """Optional extra validation. Override in subclasses. Return error list."""
        return []
