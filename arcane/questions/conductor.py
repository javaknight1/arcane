"""Question conductor for running the interactive discovery flow.

The QuestionConductor orchestrates the question/answer session,
collecting user input and building a ProjectContext.
Supports back-navigation and answer summary before finalizing.
"""

from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table

from .base import Question, QuestionType
from .registry import QuestionRegistry
from ..items.context import ProjectContext

# Sentinel object returned by _ask() when user wants to go back
_BACK = object()


class QuestionConductor:
    """Runs the interactive question flow and builds a ProjectContext.

    The conductor iterates through all questions from the registry,
    presenting them by category and collecting user responses.
    Pre-filled answers (from CLI flags) are skipped.
    Supports back-navigation with '<' and displays a summary for review.
    """

    def __init__(self, console: Console, interactive: bool = True):
        """Initialize the conductor.

        Args:
            console: Rich Console instance for terminal output.
            interactive: Whether to show prompts and review summary.
                When False and all questions are prefilled, no prompts are shown.
        """
        self.console = console
        self.interactive = interactive
        self.registry = QuestionRegistry()
        self.answers: dict[str, Any] = {}

    async def run(self) -> ProjectContext:
        """Run the full question flow and return a ProjectContext.

        Presents questions by category, collects answers, and builds
        the ProjectContext from the collected data. Users can type '<'
        to go back to the previous question.

        Returns:
            ProjectContext populated with user answers.
        """
        # Track which keys were pre-filled (e.g., CLI flags)
        prefilled = set(self.answers.keys())

        questions = self.registry.get_all_questions()
        all_keys = {q.key for _, q in questions}
        all_prefilled = prefilled >= all_keys

        # Skip welcome panel if all questions are already answered
        if not all_prefilled:
            self.console.print(
                Panel(
                    "[bold magenta]Arcane[/bold magenta] - Let's build your roadmap!\n"
                    "Answer a few questions so we can generate the best plan for your project.\n"
                    "[dim]Type < at any prompt to go back to the previous question.[/dim]",
                    border_style="magenta",
                )
            )

        last_category = None
        idx = 0

        while idx < len(questions):
            category, question = questions[idx]

            # Skip pre-filled answers
            if question.key in prefilled:
                idx += 1
                continue

            # Print category header when it changes
            if category != last_category:
                last_category = category
                self.console.print(f"\n[bold cyan]── {category} ──[/bold cyan]")

            answer = self._ask(question)

            if answer is _BACK:
                # Find the previous non-prefilled question
                prev = idx - 1
                while prev >= 0 and questions[prev][1].key in prefilled:
                    prev -= 1

                if prev < 0:
                    self.console.print("  [dim]Already at the first question.[/dim]")
                    continue

                # Remove the previous answer so it gets re-asked
                prev_key = questions[prev][1].key
                self.answers.pop(prev_key, None)

                # Reset category tracking so header reprints if needed
                last_category = None
                idx = prev
                continue

            if answer is not None:
                self.answers[question.key] = answer
            idx += 1

        # Show summary and allow edits before finalizing
        # Skip review if all questions were prefilled and non-interactive
        if not (all_prefilled and not self.interactive):
            await self._review_summary(questions, prefilled)

        return ProjectContext(**self.answers)

    async def _review_summary(
        self,
        questions: list[tuple[str, Question]],
        prefilled: set[str],
    ) -> None:
        """Display answer summary and allow edits before finalizing."""
        while True:
            self._display_summary(questions)

            choice = Prompt.ask(
                "\n  [bold]Confirm answers?[/bold] [dim]([green]c[/green] to confirm, or enter a number to edit)[/dim]",
                default="c",
                console=self.console,
            )

            if choice.strip().lower() == "c":
                return

            # Try to parse as a question number
            try:
                num = int(choice.strip())
            except ValueError:
                self.console.print("  [red]Enter 'c' to confirm or a question number to edit.[/red]")
                continue

            # Find the question by display number
            display_idx = 0
            target_question = None
            for _category, question in questions:
                display_idx += 1
                if display_idx == num:
                    target_question = question
                    break

            if target_question is None:
                self.console.print(f"  [red]Invalid number. Enter 1-{display_idx}.[/red]")
                continue

            # Re-ask the question
            self.console.print()
            answer = self._ask(target_question, allow_back=False)
            if answer is not None:
                self.answers[target_question.key] = answer

    def _display_summary(self, questions: list[tuple[str, Question]]) -> None:
        """Display a numbered summary table of all answers."""
        table = Table(title="Your Answers", show_header=True, border_style="cyan")
        table.add_column("#", style="dim", width=3, justify="right")
        table.add_column("Question", style="cyan", max_width=35)
        table.add_column("Answer", style="white", max_width=50)

        for i, (category, question) in enumerate(questions, 1):
            answer = self.answers.get(question.key, "")
            display = self._format_answer(answer)
            table.add_row(str(i), question.key.replace("_", " ").title(), display)

        self.console.print()
        self.console.print(table)

    @staticmethod
    def _format_answer(answer: Any) -> str:
        """Format an answer value for display in the summary table."""
        if isinstance(answer, list):
            return ", ".join(str(x) for x in answer) if answer else "[dim]-[/dim]"
        if isinstance(answer, bool):
            return "Yes" if answer else "No"
        if answer == "" or answer is None:
            return "[dim]-[/dim]"
        return str(answer)

    def _ask(self, question: Question, allow_back: bool = True) -> Any:
        """Ask a single question and return the transformed answer.

        Args:
            question: The Question instance to ask.
            allow_back: Whether to allow '<' for back-navigation.

        Returns:
            The transformed answer, _BACK sentinel, or None if skipped.
        """
        if question.help_text:
            self.console.print(f"  [dim]{question.help_text}[/dim]")

        suffix = "" if question.required else " (optional, press Enter to skip)"
        back_hint = " [dim](<)[/dim]" if allow_back else ""

        while True:
            match question.question_type:
                case QuestionType.TEXT | QuestionType.LIST:
                    raw = Prompt.ask(
                        f"  {question.prompt}{suffix}{back_hint}",
                        default=question.default or "",
                        console=self.console,
                    )
                    if allow_back and raw.strip() == "<":
                        return _BACK

                case QuestionType.INT:
                    raw = Prompt.ask(
                        f"  {question.prompt}{back_hint}",
                        default=question.default or "",
                        console=self.console,
                    )
                    if allow_back and raw.strip() == "<":
                        return _BACK
                    # Validate it's actually an integer
                    try:
                        int(raw.strip()) if raw.strip() else None
                    except ValueError:
                        self.console.print("  [red]Please enter a number.[/red]")
                        continue

                case QuestionType.CHOICE:
                    choices = list(question.options) if question.options else []
                    if allow_back:
                        choices.append("<")
                    raw = Prompt.ask(
                        f"  {question.prompt}",
                        choices=choices,
                        default=question.default,
                        console=self.console,
                    )
                    if allow_back and raw.strip() == "<":
                        return _BACK

                case QuestionType.CONFIRM:
                    if allow_back:
                        raw = Prompt.ask(
                            f"  {question.prompt} [dim](y/n/<)[/dim]",
                            choices=["y", "n", "<"],
                            default="y" if question.default == "y" else "n",
                            console=self.console,
                        )
                        if raw.strip() == "<":
                            return _BACK
                        return raw.strip().lower() in ("y", "yes")
                    else:
                        result = Confirm.ask(
                            f"  {question.prompt}",
                            default=question.default == "y",
                            console=self.console,
                        )
                        return result

                case _:
                    raw = Prompt.ask(
                        f"  {question.prompt}{back_hint}",
                        console=self.console,
                    )
                    if allow_back and raw.strip() == "<":
                        return _BACK

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
