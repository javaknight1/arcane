"""Question conductor for running the interactive discovery flow.

The QuestionConductor orchestrates the question/answer session,
collecting user input and building a ProjectContext.
"""

from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt, Confirm

from .base import Question, QuestionType
from .registry import QuestionRegistry
from ..items.context import ProjectContext


class QuestionConductor:
    """Runs the interactive question flow and builds a ProjectContext.

    The conductor iterates through all questions from the registry,
    presenting them by category and collecting user responses.
    Pre-filled answers (from CLI flags) are skipped.
    """

    def __init__(self, console: Console):
        """Initialize the conductor.

        Args:
            console: Rich Console instance for terminal output.
        """
        self.console = console
        self.registry = QuestionRegistry()
        self.answers: dict[str, Any] = {}

    async def run(self) -> ProjectContext:
        """Run the full question flow and return a ProjectContext.

        Presents questions by category, collects answers, and builds
        the ProjectContext from the collected data.

        Returns:
            ProjectContext populated with user answers.
        """
        self.console.print(
            Panel(
                "[bold magenta]Arcane[/bold magenta] - Let's build your roadmap!\n"
                "Answer a few questions so we can generate the best plan for your project.",
                border_style="magenta",
            )
        )

        current_category = None

        for category, question in self.registry.get_all_questions():
            # Print category header when category changes
            if category != current_category:
                current_category = category
                self.console.print(f"\n[bold cyan]── {category} ──[/bold cyan]")

            # Skip if already answered (e.g., --name flag pre-filled project_name)
            if question.key in self.answers:
                continue

            answer = self._ask(question)
            if answer is not None:
                self.answers[question.key] = answer

        return ProjectContext(**self.answers)

    def _ask(self, question: Question) -> Any:
        """Ask a single question and return the transformed answer.

        Args:
            question: The Question instance to ask.

        Returns:
            The transformed answer, or None if skipped.
        """
        # Print help text if present
        if question.help_text:
            self.console.print(f"  [dim]{question.help_text}[/dim]")

        suffix = "" if question.required else " (optional, press Enter to skip)"

        while True:
            match question.question_type:
                case QuestionType.TEXT | QuestionType.LIST:
                    raw = Prompt.ask(
                        f"  {question.prompt}{suffix}",
                        default=question.default or "",
                        console=self.console,
                    )
                case QuestionType.INT:
                    default_int = (
                        int(question.default) if question.default else None
                    )
                    raw = str(
                        IntPrompt.ask(
                            f"  {question.prompt}",
                            default=default_int,
                            console=self.console,
                        )
                    )
                case QuestionType.CHOICE:
                    raw = Prompt.ask(
                        f"  {question.prompt}",
                        choices=question.options,
                        default=question.default,
                        console=self.console,
                    )
                case QuestionType.CONFIRM:
                    result = Confirm.ask(
                        f"  {question.prompt}",
                        default=question.default == "y",
                        console=self.console,
                    )
                    return result
                case _:
                    raw = Prompt.ask(
                        f"  {question.prompt}",
                        console=self.console,
                    )

            # Handle empty input for optional questions
            if not raw.strip() and not question.required:
                if question.question_type in (QuestionType.LIST, QuestionType.MULTI):
                    return []
                return question.default if question.default else ""

            # Validate input
            if not question.validate(raw):
                self.console.print("  [red]Invalid input. Please try again.[/red]")
                continue

            return question.transform(raw)
