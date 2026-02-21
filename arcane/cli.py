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
from typing import Any

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from rich.tree import Tree

from arcane.clients import create_client
from arcane.config import Settings
from arcane.generators import RoadmapOrchestrator
from arcane.items import Roadmap
from arcane.models import SUPPORTED_MODELS, DEFAULT_MODEL, ModelInfo, resolve_model
from arcane.project_management import CSVClient
from arcane.questions import QuestionConductor
from arcane.questions.base import QuestionType
from arcane.questions.registry import QuestionRegistry
from arcane.storage import StorageManager
from arcane.utils import estimate_generation_cost, format_cost_estimate

app = typer.Typer(
    name="arcane",
    help="🔮 AI-powered roadmap generator",
    no_args_is_help=True,
)
console = Console()


def _split_csv(value: str | None) -> list[str] | None:
    """Split a comma-separated string into a list, or return None if input is None."""
    if value is None:
        return None
    return [x.strip() for x in value.split(",") if x.strip()]


def _build_prefilled(
    *,
    project_name: str | None = None,
    vision: str | None = None,
    problem_statement: str | None = None,
    target_users: list[str] | None = None,
    timeline: str | None = None,
    team_size: int | None = None,
    developer_experience: str | None = None,
    budget_constraints: str | None = None,
    tech_stack: list[str] | None = None,
    infrastructure_preferences: str | None = None,
    existing_codebase: bool | None = None,
    must_have_features: list[str] | None = None,
    nice_to_have_features: list[str] | None = None,
    out_of_scope: list[str] | None = None,
    similar_products: list[str] | None = None,
    notes: str | None = None,
) -> dict[str, Any]:
    """Build a dict of prefilled answers from CLI flags, validating choice types.

    Only non-None values are included in the result. Choice-type questions
    are validated against the actual options defined in the QuestionRegistry.

    Raises:
        typer.BadParameter: If a choice value is invalid or team_size is out of range.
    """
    # Build a lookup of question key -> question instance for validation
    registry = QuestionRegistry()
    questions_by_key = {q.key: q for _, q in registry.get_all_questions()}

    raw: dict[str, Any] = {
        "project_name": project_name,
        "vision": vision,
        "problem_statement": problem_statement,
        "target_users": target_users,
        "timeline": timeline,
        "team_size": team_size,
        "developer_experience": developer_experience,
        "budget_constraints": budget_constraints,
        "tech_stack": tech_stack,
        "infrastructure_preferences": infrastructure_preferences,
        "existing_codebase": existing_codebase,
        "must_have_features": must_have_features,
        "nice_to_have_features": nice_to_have_features,
        "out_of_scope": out_of_scope,
        "similar_products": similar_products,
        "notes": notes,
    }

    result: dict[str, Any] = {}
    for key, value in raw.items():
        if value is None:
            continue

        question = questions_by_key.get(key)
        if question and question.question_type == QuestionType.CHOICE and question.options:
            if value not in question.options:
                raise typer.BadParameter(
                    f"Invalid value '{value}' for --{key.replace('_', '-')}. "
                    f"Valid options: {', '.join(question.options)}"
                )

        if key == "team_size" and isinstance(value, int):
            if not (1 <= value <= 100):
                raise typer.BadParameter(
                    f"Team size must be between 1 and 100, got {value}"
                )

        result[key] = value

    return result


def _resolve_model_or_exit(model: str) -> ModelInfo:
    """Resolve a model alias/ID or exit with a helpful error message."""
    try:
        return resolve_model(model)
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


def _prompt_model_selection() -> str:
    """Interactively prompt the user to select an AI model."""
    from rich.prompt import Prompt

    console.print("\n[bold cyan]── Model Selection ──[/bold cyan]")
    for alias, info in SUPPORTED_MODELS.items():
        marker = " (default)" if alias == DEFAULT_MODEL else ""
        console.print(f"  [bold]{alias:<8}[/bold] {info.description}{marker}")

    choice = Prompt.ask(
        "\n  Which AI model should we use?",
        choices=list(SUPPORTED_MODELS.keys()),
        default=DEFAULT_MODEL,
        console=console,
    )
    return choice


async def _new(
    prefilled: dict[str, Any],
    model: str,
    output: str,
    interactive: bool,
    idea: str | None,
) -> None:
    """Internal async implementation of the new command."""
    settings = Settings()

    # Resolve model (CLI flag overrides settings)
    model_info = _resolve_model_or_exit(model)

    # Validate API key
    if not settings.anthropic_api_key:
        console.print(
            "[red]Error:[/red] No API key found. "
            "Set ARCANE_ANTHROPIC_API_KEY environment variable or add to .env file."
        )
        raise typer.Exit(1)

    # Load idea file if provided
    idea_content = None
    if idea:
        idea_path = Path(idea)
        if not idea_path.exists():
            console.print(f"[red]Error:[/red] Idea file not found: {idea}")
            raise typer.Exit(1)
        idea_content = idea_path.read_text(encoding="utf-8").strip()
        console.print(f"[green]✓[/green] Loaded idea file: {idea_path.name}")

    # Run discovery questions
    conductor = QuestionConductor(console, interactive=interactive)
    conductor.answers.update(prefilled)

    context = await conductor.run()

    # Append idea file content to notes
    if idea_content:
        if context.notes:
            context.notes = context.notes + "\n\n" + idea_content
        else:
            context.notes = idea_content

    # Create client and storage
    client = create_client(
        model_info.provider,
        api_key=settings.anthropic_api_key,
        model=model_info.model_id,
    )
    storage = StorageManager(Path(output))

    # Validate connection
    console.print("\n[dim]Validating API connection...[/dim]")
    if not await client.validate_connection():
        console.print("[red]Error:[/red] Could not connect to AI provider.")
        raise typer.Exit(1)
    console.print("[green]✓[/green] Connected to", client.provider_name)

    # Show cost estimate and confirm (only in interactive mode)
    if interactive:
        estimate = estimate_generation_cost(model=model_info.model_id)
        console.print()
        console.print(format_cost_estimate(estimate))
        console.print()

        if not Confirm.ask("Proceed with generation?", default=True, console=console):
            console.print("[dim]Generation cancelled.[/dim]")
            raise typer.Exit(0)

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


async def _resume(path: str, model: str | None = None, interactive: bool = True) -> None:
    """Internal async implementation of the resume command."""
    settings = Settings()
    path_obj = Path(path)

    # Resolve model (CLI flag > settings > default)
    model_str = model or settings.model
    model_info = _resolve_model_or_exit(model_str)

    # Validate API key
    if not settings.anthropic_api_key:
        console.print(
            "[red]Error:[/red] No API key found. "
            "Set ARCANE_ANTHROPIC_API_KEY environment variable or add to .env file."
        )
        raise typer.Exit(1)

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

    console.print(f"\n[bold]{roadmap.project_name}[/bold]")
    console.print(f"[yellow]Resume point:[/yellow] {resume_point}")

    # Create client
    client = create_client(
        model_info.provider,
        api_key=settings.anthropic_api_key,
        model=model_info.model_id,
    )

    # Validate connection
    console.print("\n[dim]Validating API connection...[/dim]")
    if not await client.validate_connection():
        console.print("[red]Error:[/red] Could not connect to AI provider.")
        raise typer.Exit(1)
    console.print("[green]✓[/green] Connected to", client.provider_name)

    if interactive:
        if not Confirm.ask("\nResume generation?", default=True, console=console):
            console.print("[dim]Resume cancelled.[/dim]")
            raise typer.Exit(0)

    # Resume generation
    orchestrator = RoadmapOrchestrator(
        client=client,
        console=console,
        storage=storage,
        interactive=interactive,
    )

    roadmap = await orchestrator.resume(roadmap)

    # Print output location
    project_slug = storage._slugify(roadmap.project_name)
    output_dir = path_obj.parent if path_obj.is_file() else path_obj
    console.print(f"\n[bold]📁 Saved to:[/bold] {output_dir.absolute()}")


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
        # Determine output path - put CSV next to roadmap.json
        if path_obj.is_file():
            output_path = path_obj.parent / "roadmap.csv"
        else:
            output_path = path_obj / "roadmap.csv"

        console.print(f"[dim]Exporting to CSV...[/dim]")
        client = CSVClient()
        result = await client.export(roadmap, output_path=str(output_path))

        if result.success:
            console.print(f"[green]✓[/green] Exported {result.items_created} items to CSV")
            console.print(f"[bold]📁 Saved to:[/bold] {result.url}")
        else:
            console.print(f"[red]Error:[/red] Export failed")
            for error in result.errors:
                console.print(f"  {error}")
            raise typer.Exit(1)

    elif to_lower == "linear":
        console.print("[dim]Linear export coming soon...[/dim]")
    elif to_lower == "jira":
        console.print("[dim]Jira export coming soon...[/dim]")
    elif to_lower == "notion":
        settings = Settings()
        if not settings.notion_api_key:
            console.print(
                "[red]Error:[/red] No Notion API key found. "
                "Set ARCANE_NOTION_API_KEY environment variable or add to .env file."
            )
            raise typer.Exit(1)

        if not workspace:
            console.print(
                "[red]Error:[/red] Notion export requires --workspace/-w with the parent page ID.\n"
                "Find it in the Notion URL: https://notion.so/Your-Page-[page_id_here]"
            )
            raise typer.Exit(1)

        from arcane.project_management import NotionClient

        client = NotionClient(api_key=settings.notion_api_key)

        console.print("[dim]Validating Notion credentials...[/dim]")
        if not await client.validate_credentials():
            console.print("[red]Error:[/red] Could not connect to Notion API. Check your API key.")
            raise typer.Exit(1)
        console.print("[green]✓[/green] Connected to Notion")

        console.print("[dim]Exporting to Notion...[/dim]")
        result = await client.export(roadmap, parent_page_id=workspace)

        if result.success:
            console.print(f"[green]✓[/green] Exported {result.items_created} items to Notion")
            if result.items_by_type:
                for type_name, count in result.items_by_type.items():
                    console.print(f"  {type_name}: {count}")
            if result.url:
                console.print(f"[bold]🔗 View at:[/bold] {result.url}")
            if result.warnings:
                console.print(f"\n[yellow]⚠ {len(result.warnings)} warning(s):[/yellow]")
                for w in result.warnings:
                    console.print(f"  {w}")
        else:
            console.print("[red]Error:[/red] Export failed")
            for error in result.errors:
                console.print(f"  {error}")
            raise typer.Exit(1)
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
    vision: str = typer.Option(
        None,
        "--vision",
        help="Project vision (2-3 sentence description)",
    ),
    problem: str = typer.Option(
        None,
        "--problem",
        help="Problem statement (what problem does this solve?)",
    ),
    users: str = typer.Option(
        None,
        "--users",
        help="Target users (comma-separated)",
    ),
    timeline: str = typer.Option(
        None,
        "--timeline",
        "-t",
        help="Target timeline (e.g. '3 months')",
    ),
    team_size: int = typer.Option(
        None,
        "--team-size",
        help="Number of developers (1-100)",
    ),
    experience: str = typer.Option(
        None,
        "--experience",
        help="Team experience level (junior, mid-level, senior, mixed)",
    ),
    budget: str = typer.Option(
        None,
        "--budget",
        help="Budget constraints",
    ),
    tech: str = typer.Option(
        None,
        "--tech",
        help="Tech stack (comma-separated)",
    ),
    infra: str = typer.Option(
        None,
        "--infra",
        help="Infrastructure preference (AWS, GCP, Azure, etc.)",
    ),
    existing_codebase: bool = typer.Option(
        None,
        "--existing-codebase/--no-existing-codebase",
        help="Adding to an existing codebase?",
    ),
    must_have: str = typer.Option(
        None,
        "--must-have",
        help="Must-have features (comma-separated)",
    ),
    nice_to_have: str = typer.Option(
        None,
        "--nice-to-have",
        help="Nice-to-have features (comma-separated)",
    ),
    out_of_scope: str = typer.Option(
        None,
        "--out-of-scope",
        help="Out-of-scope items (comma-separated)",
    ),
    similar: str = typer.Option(
        None,
        "--similar",
        help="Similar products or competitors (comma-separated)",
    ),
    notes: str = typer.Option(
        None,
        "--notes",
        help="Additional context or notes",
    ),
    model: str = typer.Option(
        None,
        "--model",
        "-m",
        help="AI model to use (sonnet, opus, haiku)",
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
    idea: str = typer.Option(
        None,
        "--idea",
        "-i",
        help="Path to an idea file with additional project context",
    ),
) -> None:
    """Create a new roadmap from scratch.

    Runs an interactive discovery session to gather project information,
    then generates a complete roadmap with milestones, epics, stories, and tasks.

    Use --idea to provide an idea file with extra context. The file contents
    are appended to your notes and injected into every AI generation call.
    See examples/idea-file-guide.txt for how to write one.

    All discovery questions can be pre-filled via flags. When all 16 are
    provided with --no-interactive, arcane runs with zero prompts.
    """
    prefilled = _build_prefilled(
        project_name=name,
        vision=vision,
        problem_statement=problem,
        target_users=_split_csv(users),
        timeline=timeline,
        team_size=team_size,
        developer_experience=experience,
        budget_constraints=budget,
        tech_stack=_split_csv(tech),
        infrastructure_preferences=infra,
        existing_codebase=existing_codebase,
        must_have_features=_split_csv(must_have),
        nice_to_have_features=_split_csv(nice_to_have),
        out_of_scope=_split_csv(out_of_scope),
        similar_products=_split_csv(similar),
        notes=notes,
    )

    # Resolve model: CLI flag > interactive prompt > settings > default
    interactive = not no_interactive
    if model is None:
        settings = Settings()
        if settings.model != DEFAULT_MODEL:
            # User set ARCANE_MODEL env var, use that
            model = settings.model
        elif interactive:
            # Interactive mode with no explicit model: prompt the user
            model = _prompt_model_selection()
        else:
            model = DEFAULT_MODEL

    asyncio.run(_new(prefilled, model, output, interactive, idea))


@app.command()
def resume(
    path: str = typer.Argument(
        ...,
        help="Path to project directory or roadmap.json",
    ),
    model: str = typer.Option(
        None,
        "--model",
        "-m",
        help="AI model to use (sonnet, opus, haiku)",
    ),
    no_interactive: bool = typer.Option(
        False,
        "--no-interactive",
        help="Skip review prompts and auto-approve all generated items",
    ),
) -> None:
    """Resume generating an incomplete roadmap.

    Detects where generation stopped and continues from that point.
    """
    # Resolve model: CLI flag > settings > default
    if model is None:
        settings = Settings()
        model = settings.model

    asyncio.run(_resume(path, model, not no_interactive))


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
        try:
            model_info = resolve_model(settings.model)
            model_display = f"{model_info.alias} ({model_info.model_id})"
        except ValueError:
            model_display = f"{settings.model} (unrecognized)"
        console.print(
            Panel(
                f"[bold]Model:[/bold] {model_display}\n"
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
        console.print(f"  ARCANE_MODEL              - Model to use (default: {DEFAULT_MODEL})")
        console.print("  ARCANE_MAX_RETRIES        - Retry count (default: 3)")
        console.print("  ARCANE_LINEAR_API_KEY     - For Linear export")
        console.print("  ARCANE_JIRA_DOMAIN        - For Jira export")
        console.print("  ARCANE_JIRA_EMAIL         - For Jira export")
        console.print("  ARCANE_JIRA_API_TOKEN     - For Jira export")
        console.print("  ARCANE_NOTION_API_KEY     - For Notion export")
