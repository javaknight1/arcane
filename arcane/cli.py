"""CLI commands for Arcane.

Provides the main command-line interface using Typer:
- new: Create a new roadmap from scratch
- resume: Resume an incomplete roadmap
- export: Export roadmap to a PM tool
- view: View a generated roadmap
- config: Manage configuration
"""

import asyncio
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.tree import Tree

from arcane.clients import create_client
from arcane.config import Settings
from arcane.generators import RoadmapOrchestrator
from arcane.items import Roadmap
from arcane.questions import QuestionConductor
from arcane.storage import StorageManager

app = typer.Typer(
    name="arcane",
    help="🔮 AI-powered roadmap generator",
    no_args_is_help=True,
)
console = Console()


async def _new(
    name: str | None,
    provider: str,
    output: str,
    interactive: bool,
) -> None:
    """Internal async implementation of the new command."""
    settings = Settings()

    # Validate API key
    if not settings.anthropic_api_key:
        console.print(
            "[red]Error:[/red] No API key found. "
            "Set ARCANE_ANTHROPIC_API_KEY environment variable or add to .env file."
        )
        raise typer.Exit(1)

    # Run discovery questions
    conductor = QuestionConductor(console)
    if name:
        conductor.answers["project_name"] = name

    context = await conductor.run()

    # Create client and storage
    client = create_client(
        provider,
        api_key=settings.anthropic_api_key,
        model=settings.model,
    )
    storage = StorageManager(Path(output))

    # Validate connection
    console.print("\n[dim]Validating API connection...[/dim]")
    if not await client.validate_connection():
        console.print("[red]Error:[/red] Could not connect to AI provider.")
        raise typer.Exit(1)
    console.print("[green]✓[/green] Connected to", client.provider_name)

    # Generate roadmap
    orchestrator = RoadmapOrchestrator(
        client=client,
        console=console,
        storage=storage,
        interactive=interactive,
    )

    roadmap = await orchestrator.generate(context)

    # Print output location
    project_slug = storage._slugify(roadmap.project_name)
    output_path = Path(output) / project_slug
    console.print(f"\n[bold]📁 Saved to:[/bold] {output_path.absolute()}")


async def _resume(path: str) -> None:
    """Internal async implementation of the resume command."""
    settings = Settings()
    path_obj = Path(path)

    # Load existing roadmap
    storage = StorageManager(path_obj.parent if path_obj.is_file() else path_obj)

    try:
        roadmap = await storage.load_roadmap(path_obj)
    except FileNotFoundError:
        console.print(f"[red]Error:[/red] Roadmap not found at {path}")
        raise typer.Exit(1)

    # Check for resume point
    resume_point = storage.get_resume_point(roadmap)
    if not resume_point:
        console.print("[green]✓[/green] Roadmap is already complete!")
        return

    console.print(f"[yellow]Resume point:[/yellow] {resume_point}")
    console.print("[dim]Resume functionality coming soon...[/dim]")


async def _export(path: str, to: str, workspace: str | None) -> None:
    """Internal async implementation of the export command."""
    path_obj = Path(path)

    # Load roadmap
    storage = StorageManager(path_obj.parent if path_obj.is_file() else path_obj)

    try:
        roadmap = await storage.load_roadmap(path_obj)
    except FileNotFoundError:
        console.print(f"[red]Error:[/red] Roadmap not found at {path}")
        raise typer.Exit(1)

    # Select export target
    to_lower = to.lower()

    if to_lower == "csv":
        # CSV export will be implemented in Step 14
        console.print("[dim]CSV export coming soon (Step 14)...[/dim]")
    elif to_lower == "linear":
        console.print("[dim]Linear export coming soon (Step 15)...[/dim]")
    elif to_lower == "jira":
        console.print("[dim]Jira export coming soon (Step 15)...[/dim]")
    elif to_lower == "notion":
        console.print("[dim]Notion export coming soon (Step 15)...[/dim]")
    else:
        console.print(
            f"[red]Error:[/red] Unknown export target: {to}\n"
            "Available targets: csv, linear, jira, notion"
        )
        raise typer.Exit(1)


async def _view(path: str, format: str) -> None:
    """Internal async implementation of the view command."""
    path_obj = Path(path)

    # Load roadmap
    if path_obj.is_dir():
        roadmap_file = path_obj / "roadmap.json"
    else:
        roadmap_file = path_obj

    if not roadmap_file.exists():
        console.print(f"[red]Error:[/red] Roadmap not found at {roadmap_file}")
        raise typer.Exit(1)

    roadmap = Roadmap.model_validate_json(roadmap_file.read_text())

    if format == "json":
        console.print(roadmap.model_dump_json(indent=2))

    elif format == "summary":
        _print_summary(roadmap)

    else:  # tree (default)
        _print_tree(roadmap)


def _print_summary(roadmap: Roadmap) -> None:
    """Print a summary of the roadmap."""
    counts = roadmap.total_items

    console.print(
        Panel(
            f"[bold]{roadmap.project_name}[/bold]\n\n"
            f"Created: {roadmap.created_at.strftime('%Y-%m-%d %H:%M')}\n"
            f"Updated: {roadmap.updated_at.strftime('%Y-%m-%d %H:%M')}\n\n"
            f"[cyan]Milestones:[/cyan] {counts['milestones']}\n"
            f"[cyan]Epics:[/cyan] {counts['epics']}\n"
            f"[cyan]Stories:[/cyan] {counts['stories']}\n"
            f"[cyan]Tasks:[/cyan] {counts['tasks']}\n\n"
            f"[bold]Total Hours:[/bold] {roadmap.total_hours}",
            title="📊 Roadmap Summary",
            border_style="blue",
        )
    )


def _print_tree(roadmap: Roadmap) -> None:
    """Print the roadmap as a tree."""
    tree = Tree(f"🔮 [bold]{roadmap.project_name}[/bold]")

    for milestone in roadmap.milestones:
        ms_branch = tree.add(
            f"📋 [bold cyan]{milestone.name}[/bold cyan] "
            f"[dim]({milestone.estimated_hours}h)[/dim]"
        )

        for epic in milestone.epics:
            ep_branch = ms_branch.add(
                f"🏗  [bold]{epic.name}[/bold] "
                f"[dim]({epic.estimated_hours}h)[/dim]"
            )

            for story in epic.stories:
                st_branch = ep_branch.add(
                    f"📝 {story.name} "
                    f"[dim]({story.estimated_hours}h)[/dim]"
                )

                for task in story.tasks:
                    st_branch.add(
                        f"[dim]• {task.name} ({task.estimated_hours}h)[/dim]"
                    )

    console.print(tree)
    console.print(f"\n[bold]Total:[/bold] {roadmap.total_hours} hours")


@app.command()
def new(
    name: str = typer.Option(
        None,
        "--name",
        "-n",
        help="Project name (skip the first question)",
    ),
    provider: str = typer.Option(
        "anthropic",
        "--provider",
        "-p",
        help="AI provider to use",
    ),
    output: str = typer.Option(
        "./",
        "--output",
        "-o",
        help="Output directory for the roadmap",
    ),
    no_interactive: bool = typer.Option(
        False,
        "--no-interactive",
        help="Skip review prompts between generation phases",
    ),
) -> None:
    """Create a new roadmap from scratch.

    Runs an interactive discovery session to gather project information,
    then generates a complete roadmap with milestones, epics, stories, and tasks.
    """
    asyncio.run(_new(name, provider, output, not no_interactive))


@app.command()
def resume(
    path: str = typer.Argument(
        ...,
        help="Path to project directory or roadmap.json",
    ),
) -> None:
    """Resume generating an incomplete roadmap.

    Detects where generation stopped and continues from that point.
    """
    asyncio.run(_resume(path))


@app.command()
def export(
    path: str = typer.Argument(
        ...,
        help="Path to roadmap.json or project directory",
    ),
    to: str = typer.Option(
        ...,
        "--to",
        "-t",
        help="Export target: csv, linear, jira, notion",
    ),
    workspace: str = typer.Option(
        None,
        "--workspace",
        "-w",
        help="Target workspace or project (for Linear, Jira, Notion)",
    ),
) -> None:
    """Export a roadmap to a project management tool.

    Supports CSV (universal import), Linear, Jira, and Notion.
    """
    asyncio.run(_export(path, to, workspace))


@app.command()
def view(
    path: str = typer.Argument(
        ...,
        help="Path to roadmap.json or project directory",
    ),
    format: str = typer.Option(
        "tree",
        "--format",
        "-f",
        help="Display format: tree, summary, json",
    ),
) -> None:
    """View a generated roadmap.

    Displays the roadmap in the specified format.
    """
    asyncio.run(_view(path, format))


@app.command()
def config(
    show: bool = typer.Option(
        False,
        "--show",
        help="Show current configuration",
    ),
) -> None:
    """Manage arcane configuration.

    Shows current settings when --show is specified.
    """
    if show:
        settings = Settings()
        console.print(
            Panel(
                f"[bold]Model:[/bold] {settings.model}\n"
                f"[bold]API Key:[/bold] {'✓ set' if settings.anthropic_api_key else '✗ missing'}\n"
                f"[bold]Max Retries:[/bold] {settings.max_retries}\n"
                f"[bold]Interactive:[/bold] {settings.interactive}\n"
                f"[bold]Auto Save:[/bold] {settings.auto_save}\n"
                f"[bold]Output Dir:[/bold] {settings.output_dir}\n\n"
                "[dim]PM Integrations:[/dim]\n"
                f"  Linear: {'✓ set' if settings.linear_api_key else '✗ not set'}\n"
                f"  Jira: {'✓ set' if settings.jira_api_token else '✗ not set'}\n"
                f"  Notion: {'✓ set' if settings.notion_api_key else '✗ not set'}",
                title="⚙️  Arcane Configuration",
                border_style="blue",
            )
        )
    else:
        console.print("Use [bold]arcane config --show[/bold] to display current settings.")
        console.print("\nConfiguration is set via environment variables or .env file:")
        console.print("  ARCANE_ANTHROPIC_API_KEY  - Required for generation")
        console.print("  ARCANE_MODEL              - Model to use (default: claude-sonnet-4-20250514)")
        console.print("  ARCANE_MAX_RETRIES        - Retry count (default: 3)")
        console.print("  ARCANE_LINEAR_API_KEY     - For Linear export")
        console.print("  ARCANE_JIRA_DOMAIN        - For Jira export")
        console.print("  ARCANE_JIRA_EMAIL         - For Jira export")
        console.print("  ARCANE_JIRA_API_TOKEN     - For Jira export")
        console.print("  ARCANE_NOTION_API_KEY     - For Notion export")
