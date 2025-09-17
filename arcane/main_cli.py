#!/usr/bin/env python3
"""Arcane CLI - AI-powered roadmap generation and project management integration."""

import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any

import inquirer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, Confirm
from rich.table import Table

from .engines.generation import RoadmapGenerationEngine
from .engines.export import FileExportEngine
from .engines.import_engine import NotionImportEngine
from .items import Roadmap


class ArcaneCLI:
    """Main CLI application for AI-powered roadmap generation."""

    def __init__(self):
        self.console = Console()
        self.generation_engine = None
        self.export_engine = None
        self.import_engine = None
        self.current_roadmap = None

    def display_banner(self):
        """Display welcome banner."""
        banner = Panel.fit(
            "[bold blue]🔮  Arcane[/bold blue]\n"
            "[dim]AI-powered roadmap generation and project integration[/dim]",
            border_style="blue"
        )
        self.console.print(banner)
        self.console.print()

    def select_llm(self) -> Optional[str]:
        """Prompt user to select LLM provider."""
        self.console.print("[bold]Select your preferred LLM provider:[/bold]")

        choices = [
            ('Claude (Anthropic)', 'claude'),
            ('ChatGPT (OpenAI)', 'openai'),
            ('Gemini (Google)', 'gemini'),
        ]

        questions = [inquirer.List('llm', message="Choose LLM provider", choices=choices, carousel=True)]
        answers = inquirer.prompt(questions)
        return answers.get('llm') if answers else None

    def check_environment_variables(self, llm_provider: str) -> bool:
        """Check if required environment variables are set."""
        env_requirements = {
            'claude': ['ANTHROPIC_API_KEY'],
            'openai': ['OPENAI_API_KEY'],
            'gemini': ['GOOGLE_API_KEY'],
            'notion': ['NOTION_TOKEN', 'NOTION_PARENT_PAGE_ID']
        }

        required_vars = env_requirements[llm_provider] + env_requirements['notion']
        missing_vars = [var for var in required_vars if not os.getenv(var)]

        if missing_vars:
            self.console.print("[bold red]❌ Missing required environment variables:[/bold red]")
            for var in missing_vars:
                self.console.print(f"  • {var}")
            self.console.print("\n[dim]Please set these in your .env file or environment[/dim]")
            return False

        self.console.print("[bold green]✅ All environment variables configured[/bold green]")
        return True

    def get_idea_file(self) -> Optional[str]:
        """Prompt user for idea description file."""
        self.console.print("\n[bold]Idea Description File[/bold]")
        self.console.print("[dim]Provide a text file describing your project idea[/dim]")

        while True:
            file_path = Prompt.ask("📁 Enter path to your idea text file")

            if not file_path:
                if not Confirm.ask("No file provided. Continue without file?"):
                    continue
                return None

            path = Path(file_path).expanduser()
            if path.exists() and path.is_file():
                self.console.print(f"[green]✅ Found file: {path}[/green]")
                return str(path)
            else:
                self.console.print(f"[red]❌ File not found: {path}[/red]")
                if not Confirm.ask("Try again?"):
                    return None

    def get_roadmap_preferences(self) -> Dict[str, Any]:
        """Get user preferences for roadmap generation."""
        self.console.print("\n[bold]Roadmap Preferences[/bold]")

        questions = [
            inquirer.List(
                'timeline',
                message="Project timeline",
                choices=[
                    ('3 months (MVP focus)', '3-months'),
                    ('6 months (Balanced)', '6-months'),
                    ('12 months (Comprehensive)', '12-months'),
                    ('Custom timeline', 'custom')
                ]
            ),
            inquirer.List(
                'complexity',
                message="Technical complexity",
                choices=[
                    ('Simple (Basic CRUD, minimal integrations)', 'simple'),
                    ('Moderate (APIs, some integrations)', 'moderate'),
                    ('Complex (Microservices, advanced features)', 'complex')
                ]
            ),
            inquirer.List(
                'team_size',
                message="Development team size",
                choices=[
                    ('Solo developer', '1'),
                    ('Small team (2-3)', '2-3'),
                    ('Medium team (4-8)', '4-8'),
                    ('Large team (8+)', '8+')
                ]
            ),
            inquirer.List(
                'focus',
                message="Primary focus",
                choices=[
                    ('MVP / Startup launch', 'mvp'),
                    ('Feature development', 'feature'),
                    ('System migration', 'migration'),
                    ('Performance optimization', 'optimization')
                ]
            )
        ]

        answers = inquirer.prompt(questions)

        # Handle custom timeline
        if answers and answers.get('timeline') == 'custom':
            custom_timeline = Prompt.ask("Enter custom timeline (e.g., '4 months', '18 months')")
            answers['timeline'] = custom_timeline

        return answers or {}

    def generate_roadmap(self, llm_provider: str, idea_file: Optional[str], preferences: Dict[str, Any]) -> Optional[Roadmap]:
        """Generate roadmap using selected LLM."""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task("🤖 Generating roadmap with AI...", total=None)

            try:
                # Initialize generation engine
                self.generation_engine = RoadmapGenerationEngine(llm_provider)

                # Read idea file if provided
                idea_content = ""
                if idea_file:
                    with open(idea_file, 'r', encoding='utf-8') as f:
                        idea_content = f.read()
                else:
                    idea_content = "Generate a comprehensive web application roadmap"

                # Generate roadmap
                self.current_roadmap = self.generation_engine.generate_roadmap(idea_content, preferences)

                progress.update(task, description="✅ Roadmap generated successfully")

                # Display statistics
                stats = self.current_roadmap.get_statistics()
                self.console.print(f"\n[green]✅ Roadmap generated successfully![/green]")
                self.console.print(f"[dim]Generated {stats['total_items']} items across {stats['milestones']} milestones[/dim]")

                return self.current_roadmap

            except Exception as e:
                progress.update(task, description="❌ Failed to generate roadmap")
                self.console.print(f"\n[red]❌ Error generating roadmap: {str(e)}[/red]")
                return None

    def export_roadmap(self, roadmap: Roadmap) -> Optional[Dict[str, str]]:
        """Export roadmap to multiple formats."""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task("📊 Exporting roadmap to files...", total=None)

            try:
                # Initialize export engine
                self.export_engine = FileExportEngine()

                # Export to all formats
                base_path = "generated_roadmap"
                exported_files = self.export_engine.export_multiple(
                    roadmap,
                    base_path,
                    formats=['csv', 'json', 'yaml']
                )

                progress.update(task, description="✅ Export completed")

                # Display exported files
                self.console.print("\n[green]✅ Exported roadmap to:[/green]")
                for file_path in exported_files:
                    self.console.print(f"  📁 {file_path}")

                return {
                    'csv': f"{base_path}.csv",
                    'json': f"{base_path}.json",
                    'yaml': f"{base_path}.yaml"
                }

            except Exception as e:
                progress.update(task, description="❌ Failed to export roadmap")
                self.console.print(f"[red]❌ Error exporting roadmap: {str(e)}[/red]")
                return None

    def import_to_notion(self, roadmap: Roadmap) -> bool:
        """Import roadmap to Notion."""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task("📤 Importing to Notion...", total=None)

            try:
                # Initialize import engine (uses env vars)
                self.import_engine = NotionImportEngine()

                # Import the roadmap
                result = self.import_engine.import_roadmap(roadmap)

                progress.update(task, description="✅ Successfully imported to Notion")
                self.console.print("[green]✅ Roadmap imported to Notion successfully![/green]")

                return True

            except Exception as e:
                progress.update(task, description="❌ Failed to import to Notion")
                self.console.print(f"[red]❌ Error importing to Notion: {str(e)}[/red]")
                return False

    def display_summary(self, roadmap: Roadmap, export_files: Dict[str, str], notion_success: bool):
        """Display final summary."""
        table = Table(title="🎉 Generation Complete!")
        table.add_column("Step", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Output", style="blue")

        stats = roadmap.get_statistics()
        table.add_row(
            "1. Roadmap Generation",
            "✅ Success",
            f"{stats['total_items']} items generated"
        )
        table.add_row(
            "2. File Export",
            "✅ Success",
            f"CSV, JSON, YAML files created"
        )
        table.add_row(
            "3. Notion Import",
            "✅ Success" if notion_success else "❌ Failed",
            "Check Notion workspace" if notion_success else "See error above"
        )

        self.console.print(table)

        if export_files:
            self.console.print("\n[bold]📁 Generated Files:[/bold]")
            for format_type, file_path in export_files.items():
                self.console.print(f"  • {format_type.upper()}: {file_path}")

    def run(self):
        """Main application entry point."""
        try:
            # Display banner
            self.display_banner()

            # Step 1: Select LLM
            llm_provider = self.select_llm()
            if not llm_provider:
                self.console.print("[red]❌ No LLM provider selected. Exiting.[/red]")
                return

            # Step 2: Check environment variables
            if not self.check_environment_variables(llm_provider):
                return

            # Step 3: Get idea file
            idea_file = self.get_idea_file()

            # Step 4: Get roadmap preferences
            preferences = self.get_roadmap_preferences()

            # Step 5: Generate roadmap
            roadmap = self.generate_roadmap(llm_provider, idea_file, preferences)
            if not roadmap:
                return

            # Step 6: Export to files
            export_files = self.export_roadmap(roadmap)
            if not export_files:
                return

            # Step 7: Import to Notion
            notion_success = self.import_to_notion(roadmap)

            # Step 8: Display summary
            self.display_summary(roadmap, export_files, notion_success)

        except KeyboardInterrupt:
            self.console.print("\n[yellow]⚠️  Operation cancelled by user[/yellow]")
        except Exception as e:
            self.console.print(f"\n[red]❌ Unexpected error: {str(e)}[/red]")


def main():
    """CLI entry point."""
    cli = RoadmapCLI()
    cli.run()


if __name__ == "__main__":
    main()