#!/usr/bin/env python3
"""Smoke test script for Arcane.

This script tests the full generation pipeline with a real Anthropic API call.
Use this to validate that prompts produce quality output before committing changes.

Usage:
    python scripts/smoke_test.py

Requirements:
    - ARCANE_ANTHROPIC_API_KEY must be set in .env or environment
    - Run from the project root directory

Output:
    - Generates roadmap to smoke-test-output/
    - Prints summary statistics
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from arcane.core.clients.anthropic import AnthropicClient
from arcane.core.config import Settings
from arcane.core.generators import RoadmapOrchestrator
from arcane.core.items import ProjectContext
from arcane.core.models import resolve_model
from arcane.core.project_management import CSVClient
from arcane.core.storage import StorageManager


# Hardcoded test context - small but realistic project
TEST_CONTEXT = ProjectContext(
    project_name="Task Tracker API",
    vision="A simple REST API for tracking personal tasks with categories and due dates",
    problem_statement="People need a lightweight way to track tasks without complex project management overhead",
    target_users=["individual developers", "small teams"],
    timeline="1 month MVP",
    team_size=1,
    developer_experience="senior",
    budget_constraints="minimal (free tier everything)",
    tech_stack=["Python", "FastAPI", "SQLite"],
    infrastructure_preferences="Serverless",
    existing_codebase=False,
    must_have_features=["CRUD for tasks", "task categories", "due date filtering"],
    nice_to_have_features=["email reminders", "recurring tasks"],
    out_of_scope=["mobile app", "real-time sync", "team collaboration"],
    similar_products=["Todoist", "Things"],
    notes="Keep it simple - this is for personal use",
)


async def run_smoke_test(console: Console, output_dir: Path) -> bool:
    """Run the full generation pipeline and export to CSV.

    Returns:
        True if smoke test passed, False otherwise.
    """
    settings = Settings()

    # Validate API key
    if not settings.anthropic_api_key:
        console.print("[red]Error: ARCANE_ANTHROPIC_API_KEY not set[/red]")
        console.print("Set it in .env or as an environment variable")
        return False

    model_info = resolve_model(settings.model)

    console.print(Panel(
        "[bold magenta]Arcane Smoke Test[/bold magenta]\n"
        f"Model: {model_info.alias} ({model_info.model_id})\n"
        f"Output: {output_dir}",
        border_style="magenta",
    ))

    # Create clients
    client = AnthropicClient(
        api_key=settings.anthropic_api_key,
        model=model_info.model_id,
    )

    # Validate connection
    console.print("\n[dim]Validating API connection...[/dim]")
    if not await client.validate_connection():
        console.print("[red]Error: Could not connect to Anthropic API[/red]")
        return False
    console.print("[green]API connection valid[/green]")

    # Set up storage and orchestrator
    storage = StorageManager(output_dir)
    orchestrator = RoadmapOrchestrator(
        client=client,
        console=console,
        storage=storage,
        interactive=False,  # No pauses for smoke test
    )

    # Show test context
    console.print("\n[bold]Test Project:[/bold]")
    console.print(f"  Name: {TEST_CONTEXT.project_name}")
    console.print(f"  Vision: {TEST_CONTEXT.vision}")
    console.print(f"  Tech: {', '.join(TEST_CONTEXT.tech_stack)}")
    console.print(f"  Must-have: {', '.join(TEST_CONTEXT.must_have_features)}")

    # Run generation
    start_time = datetime.now()
    console.print("\n[bold]Starting generation...[/bold]\n")

    try:
        roadmap = await orchestrator.generate(TEST_CONTEXT)
    except Exception as e:
        console.print(f"\n[red]Generation failed: {e}[/red]")
        return False

    elapsed = datetime.now() - start_time

    # Export to CSV
    console.print("\n[dim]Exporting to CSV...[/dim]")
    csv_client = CSVClient()
    csv_path = output_dir / "task-tracker-api" / "roadmap.csv"
    export_result = await csv_client.export(roadmap, output_path=str(csv_path))

    # Print results
    console.print("\n")
    console.print(Panel("[bold green]Smoke Test Complete[/bold green]", border_style="green"))

    # Summary table
    table = Table(title="Generation Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="white")

    counts = roadmap.total_items
    table.add_row("Milestones", str(counts["milestones"]))
    table.add_row("Epics", str(counts["epics"]))
    table.add_row("Stories", str(counts["stories"]))
    table.add_row("Tasks", str(counts["tasks"]))
    table.add_row("Total Hours", str(roadmap.total_hours))
    table.add_row("Generation Time", f"{elapsed.total_seconds():.1f}s")
    table.add_row("CSV Rows", str(export_result.items_created))

    console.print(table)

    # File locations
    console.print("\n[bold]Output files:[/bold]")
    console.print(f"  Roadmap: {output_dir / 'task-tracker-api' / 'roadmap.json'}")
    console.print(f"  Context: {output_dir / 'task-tracker-api' / 'context.yaml'}")
    console.print(f"  CSV: {csv_path}")

    # Quality checks
    console.print("\n[bold]Quality Checks:[/bold]")

    all_passed = True

    # Check milestone count
    if 1 <= counts["milestones"] <= 4:
        console.print("  [green]✓[/green] Milestone count reasonable (1-4)")
    else:
        console.print(f"  [red]✗[/red] Milestone count unusual: {counts['milestones']}")
        all_passed = False

    # Check tasks have prompts
    tasks_with_prompts = 0
    total_tasks = 0
    for ms in roadmap.milestones:
        for ep in ms.epics:
            for st in ep.stories:
                for task in st.tasks:
                    total_tasks += 1
                    if task.claude_code_prompt and len(task.claude_code_prompt) > 20:
                        tasks_with_prompts += 1

    if total_tasks > 0 and tasks_with_prompts == total_tasks:
        console.print(f"  [green]✓[/green] All {total_tasks} tasks have Claude Code prompts")
    else:
        console.print(f"  [red]✗[/red] Only {tasks_with_prompts}/{total_tasks} tasks have prompts")
        all_passed = False

    # Check hour estimates are reasonable
    if 10 <= roadmap.total_hours <= 200:
        console.print(f"  [green]✓[/green] Total hours reasonable ({roadmap.total_hours}h)")
    else:
        console.print(f"  [yellow]![/yellow] Total hours may be off: {roadmap.total_hours}h")

    # Check no duplicate names at same level
    milestone_names = [m.name for m in roadmap.milestones]
    if len(milestone_names) == len(set(milestone_names)):
        console.print("  [green]✓[/green] No duplicate milestone names")
    else:
        console.print("  [red]✗[/red] Duplicate milestone names found")
        all_passed = False

    return all_passed


def main():
    """Entry point for smoke test."""
    console = Console()

    # Create output directory
    output_dir = Path("smoke-test-output")
    output_dir.mkdir(exist_ok=True)

    console.print(f"\n[dim]Output directory: {output_dir.absolute()}[/dim]\n")

    # Run async smoke test
    success = asyncio.run(run_smoke_test(console, output_dir))

    if success:
        console.print("\n[bold green]All checks passed![/bold green]\n")
        sys.exit(0)
    else:
        console.print("\n[bold red]Some checks failed - review output above[/bold red]\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
