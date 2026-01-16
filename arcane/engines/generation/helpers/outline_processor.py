"""Outline processing helper for roadmap generation."""

from typing import Dict, Any, Callable, Optional
from rich.console import Console
from rich.prompt import Confirm

from arcane.protocols.display_protocols import ConsoleDisplayProtocol
from arcane.protocols.llm_protocols import LLMClientProtocol
from arcane.prompts import RoadmapPromptBuilder
from arcane.utils.logging_config import get_logger

logger = get_logger(__name__)


class OutlineProcessor:
    """Handles outline generation, validation, and display."""

    def __init__(self, console: ConsoleDisplayProtocol):
        self.console = console
        self.prompt_builder = RoadmapPromptBuilder()

    def generate_and_confirm_outline(
        self,
        llm_client: LLMClientProtocol,
        idea: str,
        preferences: Dict[str, Any],
        save_callback: Optional[Callable[[str, str], str]] = None,
        save_prompt_callback: Optional[Callable[[str, str], str]] = None
    ) -> Optional[str]:
        """Generate and get user confirmation for the outline."""
        self.console.print("\n[bold]📋 Generating roadmap outline...[/bold]")

        # Generate outline using the prompt builder
        outline_prompt = self.prompt_builder.build_outline_prompt(
            idea_content=idea,
            preferences=preferences
        )

        outline = llm_client.generate(outline_prompt)

        # Save prompt if callback provided
        if save_prompt_callback:
            project_name = self.extract_project_name(outline) if outline else "roadmap"
            prompt_file = save_prompt_callback(outline_prompt, project_name)
            self.console.print(f"[dim]💾 Outline prompt saved to: {prompt_file}[/dim]")

        # Show outline summary
        lines = outline.split('\n')
        milestone_count = len([l for l in lines if l.strip().startswith('## Milestone')])
        epic_count = len([l for l in lines if l.strip().startswith('### Epic')])
        story_count = len([l for l in lines if l.strip().startswith('#### Story')])
        task_count = len([l for l in lines if l.strip().startswith('##### Task')])

        self.console.print(f"\n[green]✅ Generated outline with:[/green]")
        self.console.print(f"  📊 {milestone_count} milestones")
        self.console.print(f"  📁 {epic_count} epics")
        self.console.print(f"  📄 {story_count} stories")
        self.console.print(f"  ✅ {task_count} tasks")

        # Show the complete outline structure
        self.console.print("\n[bold cyan]📝 Complete Outline Structure:[/bold cyan]")
        self.display_outline_tree(outline)

        # Save outline if callback provided
        if save_callback:
            project_name = self.extract_project_name(outline)
            outline_file = save_callback(outline, project_name)
            self.console.print(f"[dim]💾 Outline saved to: {outline_file}[/dim]")

        # Get user confirmation
        if not Confirm.ask("\n[cyan]Are you satisfied with this outline structure?[/cyan]", default=True):
            if Confirm.ask("[yellow]Would you like to regenerate the outline?[/yellow]"):
                return self.generate_and_confirm_outline(llm_client, idea, preferences, save_callback, save_prompt_callback)
            else:
                return None

        return outline

    def display_outline_tree(self, outline: str) -> None:
        """Display the outline in a tree structure."""
        lines = outline.split('\n')

        # Skip metadata section
        start_idx = 0
        for i, line in enumerate(lines):
            if line.strip() == "===END_METADATA===":
                start_idx = i + 1
                break

        # Display the hierarchical structure
        for line in lines[start_idx:]:
            if not line.strip() or line.strip().startswith('==='):
                continue

            # Apply indentation and colors based on level
            if line.strip().startswith('## Milestone'):
                self.console.print(f"[bold cyan]{line.strip()}[/bold cyan]")
            elif line.strip().startswith('### Epic'):
                self.console.print(f"[green]  {line.strip()[4:]}[/green]")
            elif line.strip().startswith('#### Story'):
                self.console.print(f"[yellow]    {line.strip()[5:]}[/yellow]")
            elif line.strip().startswith('##### Task'):
                self.console.print(f"[dim]      {line.strip()[6:]}[/dim]")
            elif line.strip().startswith('#'):
                self.console.print(f"[bold]{line.strip()}[/bold]")

    def extract_project_name(self, content: str) -> str:
        """Extract project name from content."""
        lines = content.split('\n')
        for line in lines:
            if line.strip().startswith('PROJECT_NAME:'):
                return line.split(':', 1)[1].strip()
            elif line.strip().startswith('# ') and not line.strip().startswith('## '):
                return line.strip('# ').strip()
        return "roadmap"