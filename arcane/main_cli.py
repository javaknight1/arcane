#!/usr/bin/env python3
"""Arcane CLI - AI-powered roadmap generation and project management integration."""

import os
import sys
import signal
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

import inquirer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, Confirm
from rich.table import Table

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
        self.cancelled = False

        # Set up signal handler for Ctrl+C
        signal.signal(signal.SIGINT, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle Ctrl+C signals gracefully."""
        self.cancelled = True
        self.console.print("\n[yellow]🛑 Operation cancelled by user[/yellow]")
        self._display_exit_message()
        sys.exit(0)

    def _display_exit_message(self):
        """Display a helpful exit message when the user cancels."""
        self.console.print("\n[dim]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/dim]")
        self.console.print("[yellow]👋 Thanks for using Arcane![/yellow]")
        self.console.print("[dim]Your AI-powered roadmap generation tool[/dim]")
        self.console.print("")
        self.console.print("[cyan]💡 Next time:[/cyan]")
        self.console.print("   • Run [bold]python -m arcane interactive[/bold] to try again")
        self.console.print("   • Press [bold]Ctrl+C[/bold] anytime to safely exit")
        self.console.print("   • Use [bold]'cancel'[/bold] or [bold]'skip'[/bold] options in prompts")
        self.console.print("")
        self.console.print("[green]Need help?[/green] Check the documentation or create an issue")
        self.console.print("[dim]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/dim]")

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

        # Get available providers based on API keys
        available_providers = self._get_available_providers()

        if available_providers:
            self.console.print(f"[green]✅ {len(available_providers)} provider(s) configured with API keys[/green]")
        else:
            self.console.print("[yellow]⚠️  No API keys configured. All providers will show authentication errors.[/yellow]")

        self.console.print("[dim]Press Ctrl+C at any time to cancel[/dim]")

        choices = []
        if os.getenv('ANTHROPIC_API_KEY'):
            choices.append(('Claude (Anthropic) ✅', 'claude'))
        else:
            choices.append(('Claude (Anthropic) ⚠️ [No API key]', 'claude'))

        if os.getenv('OPENAI_API_KEY'):
            choices.append(('ChatGPT (OpenAI) ✅', 'openai'))
        else:
            choices.append(('ChatGPT (OpenAI) ⚠️ [No API key]', 'openai'))

        if os.getenv('GOOGLE_API_KEY'):
            choices.append(('Gemini (Google) ✅', 'gemini'))
        else:
            choices.append(('Gemini (Google) ⚠️ [No API key]', 'gemini'))

        # Always show cancel option
        choices.append(('❌ Cancel and Exit', 'cancel'))

        questions = [inquirer.List('llm', message="Choose LLM provider", choices=choices, carousel=True)]

        try:
            answers = inquirer.prompt(questions)
            if not answers or answers.get('llm') == 'cancel':
                self.console.print("[yellow]⚠️  Operation cancelled[/yellow]")
                return None
            return answers.get('llm')
        except KeyboardInterrupt:
            self.console.print("\n[yellow]⚠️  Operation cancelled by user[/yellow]")
            return None

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

    def _get_available_providers(self) -> list:
        """Get list of available LLM providers based on API keys."""
        available = []
        if os.getenv('ANTHROPIC_API_KEY'):
            available.append('Claude (Anthropic)')
        if os.getenv('OPENAI_API_KEY'):
            available.append('ChatGPT (OpenAI)')
        if os.getenv('GOOGLE_API_KEY'):
            available.append('Gemini (Google)')
        return available

    def get_idea_file(self) -> Optional[str]:
        """Prompt user for idea description file."""
        self.console.print("\n[bold]Idea Description File[/bold]")
        self.console.print("[dim]Provide a text file describing your project idea[/dim]")
        self.console.print("[dim]Press Ctrl+C at any time to cancel[/dim]")

        try:
            while True:
                try:
                    file_path = Prompt.ask("📁 Enter path to your idea text file (or 'skip' to continue without file, 'cancel' to exit)")

                    if file_path.lower() == 'cancel':
                        self.console.print("[yellow]⚠️  Operation cancelled[/yellow]")
                        return 'CANCEL'

                    if file_path.lower() == 'skip' or not file_path:
                        if not file_path or Confirm.ask("No file provided. Continue without file?", default=True):
                            return None
                        continue

                    path = Path(file_path).expanduser()
                    if path.exists() and path.is_file():
                        self.console.print(f"[green]✅ Found file: {path}[/green]")
                        return str(path)
                    else:
                        self.console.print(f"[red]❌ File not found: {path}[/red]")
                        retry_choice = inquirer.prompt([
                            inquirer.List(
                                'action',
                                message="What would you like to do?",
                                choices=[
                                    ('Try again', 'retry'),
                                    ('Skip file and continue', 'skip'),
                                    ('❌ Cancel and exit', 'cancel')
                                ]
                            )
                        ])

                        if not retry_choice or retry_choice.get('action') == 'cancel':
                            self.console.print("[yellow]⚠️  Operation cancelled[/yellow]")
                            return 'CANCEL'
                        elif retry_choice.get('action') == 'skip':
                            return None
                        # If 'retry', continue the loop

                except KeyboardInterrupt:
                    self.console.print("\n[yellow]⚠️  Operation cancelled by user[/yellow]")
                    return 'CANCEL'

        except KeyboardInterrupt:
            self.console.print("\n[yellow]⚠️  Operation cancelled by user[/yellow]")
            return 'CANCEL'

    def get_roadmap_preferences(self, preset_timeline=None, preset_complexity=None,
                                      preset_team_size=None, preset_focus=None) -> Dict[str, Any]:
        """Get user preferences for roadmap generation."""
        self.console.print("\n[bold]Roadmap Preferences[/bold]")

        # Build answers dict with preset values
        answers = {}
        questions = []

        # Add timeline question only if not preset
        if preset_timeline:
            answers['timeline'] = preset_timeline
            self.console.print(f"[green]⚙️  Timeline: {preset_timeline} (provided via flag)[/green]")
        else:
            questions.append(inquirer.List(
                'timeline',
                message="Project timeline",
                choices=[
                    ('3 months (MVP focus)', '3-months'),
                    ('6 months (Balanced)', '6-months'),
                    ('12 months (Comprehensive)', '12-months'),
                    ('Custom timeline', 'custom'),
                    ('❌ Cancel', 'cancel')
                ]
            ))

        # Add complexity question only if not preset
        if preset_complexity:
            answers['complexity'] = preset_complexity
            self.console.print(f"[green]⚙️  Complexity: {preset_complexity} (provided via flag)[/green]")
        else:
            questions.append(inquirer.List(
                'complexity',
                message="Technical complexity",
                choices=[
                    ('Simple (Basic CRUD, minimal integrations)', 'simple'),
                    ('Moderate (APIs, some integrations)', 'moderate'),
                    ('Complex (Microservices, advanced features)', 'complex'),
                    ('❌ Cancel', 'cancel')
                ]
            ))

        # Add team size question only if not preset
        if preset_team_size:
            answers['team_size'] = preset_team_size
            self.console.print(f"[green]⚙️  Team Size: {preset_team_size} (provided via flag)[/green]")
        else:
            questions.append(inquirer.List(
                'team_size',
                message="Development team size",
                choices=[
                    ('Solo developer', '1'),
                    ('Small team (2-3)', '2-3'),
                    ('Medium team (4-8)', '4-8'),
                    ('Large team (8+)', '8+'),
                    ('❌ Cancel', 'cancel')
                ]
            ))

        # Add focus question only if not preset
        if preset_focus:
            answers['focus'] = preset_focus
            self.console.print(f"[green]⚙️  Focus: {preset_focus} (provided via flag)[/green]")
        else:
            questions.append(inquirer.List(
                'focus',
                message="Primary focus",
                choices=[
                    ('MVP / Startup launch', 'mvp'),
                    ('Feature development', 'feature'),
                    ('System migration', 'migration'),
                    ('Performance optimization', 'optimization'),
                    ('❌ Cancel', 'cancel')
                ]
            ))

        # Only prompt if there are questions to ask
        if questions:
            self.console.print("[dim]Press Ctrl+C at any time to cancel[/dim]")

            try:
                prompt_answers = inquirer.prompt(questions)

                if not prompt_answers:
                    self.console.print("[yellow]⚠️  Preferences selection cancelled[/yellow]")
                    return {}

                # Check for cancellation in any answer
                for key, value in prompt_answers.items():
                    if value == 'cancel':
                        self.console.print("[yellow]⚠️  Preferences selection cancelled[/yellow]")
                        return {'__cancelled__': True}

                # Merge prompt answers with preset answers
                answers.update(prompt_answers)

            except KeyboardInterrupt:
                self.console.print("\n[yellow]⚠️  Preferences selection cancelled[/yellow]")
                return {'__cancelled__': True}

        # Handle custom timeline
        if answers.get('timeline') == 'custom':
            try:
                custom_timeline = Prompt.ask("Enter custom timeline (e.g., '4 months', '18 months')")
                answers['timeline'] = custom_timeline
            except KeyboardInterrupt:
                self.console.print("\n[yellow]⚠️  Custom timeline cancelled[/yellow]")
                return {'__cancelled__': True}

        return answers

    def generate_roadmap_guided(self, llm_provider: str, idea_file: Optional[str], preferences: Dict[str, Any], output_directory: Optional[str] = None) -> Optional[Roadmap]:
        """Generate roadmap using guided approach with user confirmation."""
        try:
            # Import the NEW guided generator with individual item generation
            from .engines.generation.new_guided_generator import NewGuidedRoadmapGenerator

            # Initialize new guided generator
            generator = NewGuidedRoadmapGenerator(llm_provider, output_directory)

            # Read idea file if provided
            if idea_file:
                with open(idea_file, 'r', encoding='utf-8') as f:
                    idea_content = f.read()
            else:
                idea_content = "Generate a comprehensive web application roadmap"

            # Generate roadmap with user guidance
            roadmap = generator.generate_roadmap(idea_content, preferences)

            if roadmap:
                stats = roadmap.get_statistics()
                self.console.print(f"\n[green]✅ Roadmap generation completed![/green]")
                self.console.print(f"[dim]Generated {stats['total_items']} items across {stats['milestones']} milestones[/dim]")

            return roadmap

        except Exception as e:
            self.console.print(f"[red]❌ Error during guided generation: {str(e)}[/red]")
            return None

    def get_output_directory(self) -> Optional[str]:
        """Get user preference for output directory."""
        self.console.print("\n[bold]File Output Settings[/bold]")
        self.console.print("[dim]Save generated files (CSV, LLM outputs, etc.) to disk?[/dim]")
        self.console.print("[dim]Press Ctrl+C at any time to cancel[/dim]")

        try:
            # Ask if they want to export files at all
            export_files = Confirm.ask("📁 Export files to directory?", default=True)

            if not export_files:
                self.console.print("[yellow]⚠️  File export disabled. Files will not be saved.[/yellow]")
                return None

            # Ask for directory with "output" as default
            while True:
                output_dir = Prompt.ask(
                    "📂 Enter output directory path (or 'cancel' to skip)",
                    default="output"
                )

                if output_dir.lower() == 'cancel':
                    self.console.print("[yellow]⚠️  File export cancelled[/yellow]")
                    return 'CANCEL'

                output_path = Path(output_dir.strip()).expanduser().resolve()

                try:
                    # Try to create the directory if it doesn't exist
                    output_path.mkdir(parents=True, exist_ok=True)

                    # Test write permissions
                    test_file = output_path / ".test_write"
                    test_file.write_text("test")
                    test_file.unlink()

                    self.console.print(f"[green]✅ Output directory set: {output_path}[/green]")
                    return str(output_path)

                except PermissionError:
                    self.console.print(f"[red]❌ Permission denied: {output_path}[/red]")
                    retry_choice = inquirer.prompt([
                        inquirer.List(
                            'action',
                            message="What would you like to do?",
                            choices=[
                                ('Try a different directory', 'retry'),
                                ('Skip file export (continue without saving)', 'skip'),
                                ('❌ Cancel and exit', 'cancel')
                            ]
                        )
                    ])

                    if not retry_choice or retry_choice.get('action') == 'cancel':
                        return 'CANCEL'
                    elif retry_choice.get('action') == 'skip':
                        return None
                    # If 'retry', continue the loop

                except Exception as e:
                    self.console.print(f"[red]❌ Invalid directory: {e}[/red]")
                    retry_choice = inquirer.prompt([
                        inquirer.List(
                            'action',
                            message="What would you like to do?",
                            choices=[
                                ('Try a different directory', 'retry'),
                                ('Skip file export (continue without saving)', 'skip'),
                                ('❌ Cancel and exit', 'cancel')
                            ]
                        )
                    ])

                    if not retry_choice or retry_choice.get('action') == 'cancel':
                        return 'CANCEL'
                    elif retry_choice.get('action') == 'skip':
                        return None
                    # If 'retry', continue the loop

        except KeyboardInterrupt:
            self.console.print("\n[yellow]⚠️  Output directory selection cancelled[/yellow]")
            return 'CANCEL'


    def export_roadmap(self, roadmap: Roadmap, output_directory: str) -> Optional[Dict[str, str]]:
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

                # Export to CSV only with consistent naming
                if hasattr(roadmap, 'metadata') and roadmap.metadata:
                    filename_base = roadmap.metadata.get_safe_filename_base()
                else:
                    filename_base = "generated_roadmap"

                # Use consistent timestamp_projectname format for CSV
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                csv_filename = f"{timestamp}_{filename_base}.csv"
                output_path = Path(output_directory) / csv_filename

                exported_files = self.export_engine.export_multiple(
                    roadmap,
                    str(output_path.with_suffix('')),  # Remove .csv as export_multiple adds it
                    formats=['csv']
                )

                progress.update(task, description="✅ Export completed")

                # Display exported files
                self.console.print("\n[green]✅ Exported roadmap to:[/green]")
                for file_path in exported_files:
                    self.console.print(f"  📁 {file_path}")

                return {
                    'csv': str(output_path) + ".csv"
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
            "✅ Success" if export_files else "⚠️ Skipped",
            f"CSV file created" if export_files else "No output directory specified"
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

    def run(self, provider=None, idea_file=None, output_dir=None, timeline=None,
            complexity=None, team_size=None, focus=None, no_export=False, formats=None):
        """Main application entry point with optional pre-set parameters."""
        try:
            # Display banner
            self.display_banner()

            # Step 1: Select LLM (or use provided)
            if provider:
                llm_provider = provider
                self.console.print(f"[green]🤖 Using LLM provider: {provider.title()}[/green]")
            else:
                llm_provider = self.select_llm()
                if not llm_provider:
                    self.console.print("[red]❌ No LLM provider selected. Exiting.[/red]")
                    return

            # Step 2: Check environment variables
            if not self.check_environment_variables(llm_provider):
                return

            # Step 3: Get idea file (or use provided)
            if idea_file:
                from pathlib import Path
                idea_path = Path(idea_file).expanduser()
                if idea_path.exists() and idea_path.is_file():
                    self.console.print(f"[green]📁 Using idea file: {idea_path}[/green]")
                    idea_file_path = str(idea_path)
                else:
                    self.console.print(f"[red]❌ Provided idea file not found: {idea_path}[/red]")
                    return
            else:
                idea_file_path = self.get_idea_file()
                if idea_file_path == 'CANCEL':
                    self._display_exit_message()
                    return

            # Step 4: Get output directory (or use provided/skip)
            if no_export:
                output_directory = None
                self.console.print("[yellow]📁 File export disabled (--no-export flag)[/yellow]")
            elif output_dir:
                from pathlib import Path
                output_path = Path(output_dir).expanduser().resolve()
                try:
                    output_path.mkdir(parents=True, exist_ok=True)
                    self.console.print(f"[green]📁 Using output directory: {output_path}[/green]")
                    output_directory = str(output_path)
                except Exception as e:
                    self.console.print(f"[red]❌ Cannot create output directory {output_path}: {e}[/red]")
                    return
            else:
                output_directory = self.get_output_directory()
                if output_directory == 'CANCEL':
                    self._display_exit_message()
                    return

            # Step 5: Get roadmap preferences (or use provided)
            if timeline and complexity and team_size and focus:
                # All preferences provided via flags
                preferences = {
                    'timeline': timeline,
                    'complexity': complexity,
                    'team_size': team_size,
                    'focus': focus
                }
                self.console.print("[green]⚙️  Using provided roadmap preferences:[/green]")
                self.console.print(f"   • Timeline: {timeline}")
                self.console.print(f"   • Complexity: {complexity}")
                self.console.print(f"   • Team Size: {team_size}")
                self.console.print(f"   • Focus: {focus}")
            else:
                # Get missing preferences interactively
                if timeline or complexity or team_size or focus:
                    self.console.print("[cyan]💡 Some preferences provided via flags, prompting for remaining...[/cyan]")

                preferences = self.get_roadmap_preferences(
                    preset_timeline=timeline,
                    preset_complexity=complexity,
                    preset_team_size=team_size,
                    preset_focus=focus
                )
                if not preferences or preferences.get('__cancelled__'):
                    self._display_exit_message()
                    return

            # Step 6: Generate roadmap using guided generation
            roadmap = self.generate_roadmap_guided(llm_provider, idea_file_path, preferences, output_directory)
            if not roadmap:
                return

            # Step 7: Export to files
            export_files = None
            if output_directory:
                export_files = self.export_roadmap(roadmap, output_directory)
                if not export_files:
                    return

            # Step 8: Import to Notion
            notion_success = self.import_to_notion(roadmap)

            # Step 9: Display summary
            self.display_summary(roadmap, export_files, notion_success)

        except KeyboardInterrupt:
            self.console.print("\n[yellow]⚠️  Operation cancelled by user[/yellow]")
            self._display_exit_message()
        except Exception as e:
            self.console.print(f"\n[red]❌ Unexpected error: {str(e)}[/red]")


def main():
    """CLI entry point."""
    cli = ArcaneCLI()
    cli.run()


if __name__ == "__main__":
    main()