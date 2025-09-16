#!/usr/bin/env python3
"""Roadmap Generator CLI - Automated roadmap generation and Notion import."""

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

from .generator import RoadmapGenerator
from .importer import NotionImporter
from .llm_client import LLMClient
from .parser import parse_roadmap


class RoadmapCLI:
    """Main CLI application for roadmap generation and import."""

    def __init__(self):
        self.console = Console()
        self.llm_client = None
        self.roadmap_generator = None

    def display_banner(self):
        """Display welcome banner."""
        banner = Panel.fit(
            "[bold blue]🗺️  Roadmap Generator[/bold blue]\n"
            "[dim]Automated roadmap generation and Notion import[/dim]",
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

    def generate_roadmap(self, llm_provider: str, idea_file: Optional[str], preferences: Dict[str, Any]) -> Optional[str]:
        """Generate roadmap using selected LLM."""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task("🤖 Generating roadmap with AI...", total=None)

            try:
                # Initialize LLM client
                self.llm_client = LLMClient(llm_provider)
                self.roadmap_generator = RoadmapGenerator(self.llm_client)

                # Read idea file if provided
                idea_content = ""
                if idea_file:
                    with open(idea_file, 'r', encoding='utf-8') as f:
                        idea_content = f.read()

                # Generate roadmap
                roadmap_content = self.roadmap_generator.generate(idea_content, preferences)

                # Save roadmap to file
                roadmap_file = "generated_roadmap.txt"
                with open(roadmap_file, 'w', encoding='utf-8') as f:
                    f.write(roadmap_content)

                progress.update(task, description="✅ Roadmap generated successfully")
                self.console.print(f"\n[green]✅ Roadmap saved to: {roadmap_file}[/green]")

                return roadmap_file

            except Exception as e:
                progress.update(task, description="❌ Failed to generate roadmap")
                self.console.print(f"\n[red]❌ Error generating roadmap: {str(e)}[/red]")
                return None

    def convert_to_csv(self, roadmap_file: str) -> Optional[str]:
        """Convert roadmap text to CSV format."""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task("📊 Converting roadmap to CSV...", total=None)

            try:
                csv_file = "generated_roadmap.csv"
                roadmap_items = parse_roadmap(roadmap_file, csv_file)

                progress.update(task, description="✅ CSV conversion completed")
                self.console.print(f"[green]✅ CSV saved to: {csv_file}[/green]")
                self.console.print(f"[dim]Generated {len(roadmap_items)} roadmap items[/dim]")

                return csv_file

            except Exception as e:
                progress.update(task, description="❌ Failed to convert to CSV")
                self.console.print(f"[red]❌ Error converting to CSV: {str(e)}[/red]")
                return None

    def import_to_notion(self, csv_file: str) -> bool:
        """Import CSV to Notion."""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task("📤 Importing to Notion...", total=None)

            try:
                notion_token = os.getenv("NOTION_TOKEN")
                parent_page_id = os.getenv("NOTION_PARENT_PAGE_ID")

                importer = NotionImporter(notion_token, parent_page_id)
                importer.run_import(csv_file)

                progress.update(task, description="✅ Successfully imported to Notion")
                self.console.print("[green]✅ Roadmap imported to Notion successfully![/green]")

                return True

            except Exception as e:
                progress.update(task, description="❌ Failed to import to Notion")
                self.console.print(f"[red]❌ Error importing to Notion: {str(e)}[/red]")
                return False

    def display_summary(self, roadmap_file: str, csv_file: str, notion_success: bool):
        """Display final summary."""
        table = Table(title="🎉 Generation Complete!")
        table.add_column("Step", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Output", style="blue")

        table.add_row("1. Roadmap Generation", "✅ Success", roadmap_file)
        table.add_row("2. CSV Conversion", "✅ Success", csv_file)
        table.add_row("3. Notion Import", "✅ Success" if notion_success else "❌ Failed", "Check Notion workspace")

        self.console.print(table)

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
            roadmap_file = self.generate_roadmap(llm_provider, idea_file, preferences)
            if not roadmap_file:
                return

            # Step 6: Convert to CSV
            csv_file = self.convert_to_csv(roadmap_file)
            if not csv_file:
                return

            # Step 7: Import to Notion
            notion_success = self.import_to_notion(csv_file)

            # Step 8: Display summary
            self.display_summary(roadmap_file, csv_file, notion_success)

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