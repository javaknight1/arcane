"""Outline processing helper for roadmap generation."""

from typing import Dict, Any, Callable, Optional, Tuple, List
from rich.console import Console
from rich.prompt import Confirm, Prompt
from rich.tree import Tree

from arcane.protocols.display_protocols import ConsoleDisplayProtocol
from arcane.protocols.llm_protocols import LLMClientProtocol
from arcane.prompts import RoadmapPromptBuilder
from arcane.engines.parsing.semantic_outline_parser import SemanticOutlineParser
from arcane.engines.validation import DependencyValidator, IssueSeverity
from arcane.models.outline_item import SemanticOutline
from arcane.items.milestone import Milestone
from arcane.utils.logging_config import get_logger

logger = get_logger(__name__)


class OutlineProcessor:
    """Handles outline generation, validation, and display."""

    def __init__(self, console: ConsoleDisplayProtocol):
        self.console = console
        self.prompt_builder = RoadmapPromptBuilder()
        self.semantic_parser = SemanticOutlineParser()

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

    def generate_semantic_outline(
        self,
        llm_client: LLMClientProtocol,
        idea: str,
        preferences: Dict[str, Any],
        save_callback: Optional[Callable[[str, str], str]] = None,
        save_prompt_callback: Optional[Callable[[str, str], str]] = None
    ) -> Tuple[Optional[str], Optional[SemanticOutline]]:
        """Generate a semantic outline with descriptions and dependencies.

        Returns:
            Tuple of (raw_outline_text, parsed_semantic_outline)
        """
        self.console.print("\n[bold]📋 Generating semantic roadmap outline...[/bold]")

        # Generate outline using semantic prompt
        outline_prompt = self.prompt_builder.build_semantic_outline_prompt(
            idea_content=idea,
            preferences=preferences
        )

        outline_text = llm_client.generate(outline_prompt)

        # Save prompt if callback provided
        if save_prompt_callback:
            project_name = self.extract_project_name(outline_text) if outline_text else "roadmap"
            prompt_file = save_prompt_callback(outline_prompt, project_name)
            self.console.print(f"[dim]💾 Outline prompt saved to: {prompt_file}[/dim]")

        # Parse the outline into semantic structure
        semantic_outline = self.semantic_parser.parse(outline_text)

        # Show parsing warnings/errors if any
        if self.semantic_parser.has_errors():
            self.console.print("\n[red]⚠️ Outline parsing errors:[/red]")
            for error in self.semantic_parser.parse_errors:
                self.console.print(f"  [red]• {error}[/red]")

        if self.semantic_parser.has_warnings():
            self.console.print("\n[yellow]⚠️ Outline parsing warnings:[/yellow]")
            for warning in self.semantic_parser.parse_warnings:
                self.console.print(f"  [yellow]• {warning}[/yellow]")

        # Show outline statistics
        stats = semantic_outline.get_statistics()
        self.console.print(f"\n[green]✅ Generated semantic outline with:[/green]")
        self.console.print(f"  📊 {stats['milestones']} milestones")
        self.console.print(f"  📁 {stats['epics']} epics")
        self.console.print(f"  📄 {stats['stories']} stories")
        self.console.print(f"  ✅ {stats['tasks']} tasks")
        self.console.print(f"  🔗 {stats['items_with_dependencies']} items with dependencies")
        self.console.print(f"  📝 {stats['items_with_descriptions']} items with descriptions")

        # Show the semantic outline structure
        self.console.print("\n[bold cyan]📝 Semantic Outline Structure:[/bold cyan]")
        self.display_semantic_outline_tree(semantic_outline)

        # Save outline if callback provided
        if save_callback:
            project_name = semantic_outline.project_name or "roadmap"
            outline_file = save_callback(outline_text, project_name)
            self.console.print(f"[dim]💾 Outline saved to: {outline_file}[/dim]")

        # Get user confirmation
        if not Confirm.ask("\n[cyan]Are you satisfied with this outline structure?[/cyan]", default=True):
            if Confirm.ask("[yellow]Would you like to regenerate the outline?[/yellow]"):
                return self.generate_semantic_outline(
                    llm_client, idea, preferences, save_callback, save_prompt_callback
                )
            else:
                return None, None

        return outline_text, semantic_outline

    def display_semantic_outline_tree(self, semantic_outline: SemanticOutline) -> None:
        """Display the semantic outline with descriptions and dependencies."""
        for milestone in semantic_outline.milestones:
            # Display milestone
            self.console.print(f"\n[bold cyan]## Milestone {milestone.id}: {milestone.title}[/bold cyan]")
            if milestone.description.full_text:
                self.console.print(f"   [dim]{milestone.description.full_text}[/dim]")
            if milestone.dependencies:
                dep_ids = [d.item_id for d in milestone.dependencies]
                self.console.print(f"   [magenta]Dependencies: {', '.join(dep_ids)}[/magenta]")

            for epic in milestone.children:
                # Display epic
                self.console.print(f"  [green]### Epic {epic.id}: {epic.title}[/green]")
                if epic.description.full_text:
                    self.console.print(f"     [dim]{epic.description.full_text}[/dim]")
                if epic.dependencies:
                    dep_ids = [d.item_id for d in epic.dependencies]
                    self.console.print(f"     [magenta]Deps: {', '.join(dep_ids)}[/magenta]")

                for story in epic.children:
                    # Display story
                    self.console.print(f"    [yellow]#### Story {story.id}: {story.title}[/yellow]")
                    if story.description.full_text:
                        self.console.print(f"       [dim]{story.description.full_text}[/dim]")
                    if story.dependencies:
                        dep_ids = [d.item_id for d in story.dependencies]
                        self.console.print(f"       [magenta]Deps: {', '.join(dep_ids)}[/magenta]")

                    for task in story.children:
                        # Display task
                        self.console.print(f"      [white]##### Task {task.id}: {task.title}[/white]")
                        if task.description.full_text:
                            self.console.print(f"         [dim]{task.description.full_text}[/dim]")
                        if task.dependencies:
                            dep_ids = [d.item_id for d in task.dependencies]
                            self.console.print(f"         [magenta]Deps: {', '.join(dep_ids)}[/magenta]")

    def validate_outline_dependencies(self, milestones: List[Milestone]) -> bool:
        """Validate dependencies in the parsed outline.

        Args:
            milestones: List of milestone objects to validate

        Returns:
            True if validation passes (no critical errors), False otherwise
        """
        self.console.print("\n[cyan]🔍 Validating outline dependencies...[/cyan]")

        validator = DependencyValidator()
        issues = validator.validate(milestones)

        if not issues:
            self.console.print("[green]✅ Outline dependencies look good![/green]")
            return True

        # Categorize issues
        errors = [i for i in issues if i.severity == IssueSeverity.ERROR]
        warnings = [i for i in issues if i.severity == IssueSeverity.WARNING]
        info_items = [i for i in issues if i.severity == IssueSeverity.INFO]

        # Display summary
        self.console.print(f"\n[yellow]Validation found {len(issues)} potential issues:[/yellow]")

        if errors:
            self.console.print(f"\n[red]❌ Critical Issues ({len(errors)}):[/red]")
            for issue in errors:
                self.console.print(f"  [red]• {issue.message}[/red]")
                if issue.suggested_fix:
                    self.console.print(f"    [dim]→ {issue.suggested_fix}[/dim]")

        if warnings:
            self.console.print(f"\n[yellow]⚠️ Warnings ({len(warnings)}):[/yellow]")
            for issue in warnings[:5]:  # Show first 5
                self.console.print(f"  [yellow]• {issue.message}[/yellow]")
            if len(warnings) > 5:
                self.console.print(f"  [dim]... and {len(warnings) - 5} more[/dim]")

        if info_items:
            self.console.print(f"\n[cyan]ℹ️ Suggestions ({len(info_items)}):[/cyan]")
            for issue in info_items[:3]:  # Show first 3
                self.console.print(f"  [cyan]• {issue.message}[/cyan]")
                if issue.suggested_fix:
                    self.console.print(f"    [dim]→ {issue.suggested_fix}[/dim]")

        # Return True if no critical errors
        return len(errors) == 0

    def get_validation_summary(self, milestones: List[Milestone]) -> Dict[str, Any]:
        """Get a summary of validation results.

        Args:
            milestones: List of milestone objects to validate

        Returns:
            Dictionary with validation summary
        """
        validator = DependencyValidator()
        issues = validator.validate(milestones)

        return {
            'total_issues': len(issues),
            'errors': len([i for i in issues if i.severity == IssueSeverity.ERROR]),
            'warnings': len([i for i in issues if i.severity == IssueSeverity.WARNING]),
            'info': len([i for i in issues if i.severity == IssueSeverity.INFO]),
            'detected_features': list(validator.detected_features),
            'is_valid': all(i.severity != IssueSeverity.ERROR for i in issues)
        }