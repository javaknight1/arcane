#!/usr/bin/env python3
"""Refactored Arcane CLI - Clean, modular architecture."""

import os
import sys
import signal
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from rich.console import Console
from rich.panel import Panel

# Import our new modular components
from .utils.logging_config import setup_logging, get_logger
from .questions.question_builder import QuestionBuilder
from .prompts.roadmap_prompt_builder import RoadmapPromptBuilder
from .engines.export import FileExporter
from .engines.importers import NotionImporter
from .items import Roadmap


class ArcaneCLI:
    """Clean, modular CLI application for AI-powered roadmap generation."""

    def __init__(self):
        self.console = Console()
        self.logger = get_logger(__name__)
        self.question_builder = QuestionBuilder(self.console)
        self.prompt_builder = RoadmapPromptBuilder()
        self.export_engine = None
        self.import_engine = None
        self.current_roadmap = None
        self.cancelled = False

        # Set up signal handler for Ctrl+C
        signal.signal(signal.SIGINT, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle Ctrl+C signals gracefully."""
        # Signal handler parameters are required by signal.signal but not used
        del signum, frame  # Explicitly indicate parameters are unused
        self.cancelled = True
        self.console.print("\n[yellow]🛑 Operation cancelled by user[/yellow]")
        self._display_exit_message()
        sys.exit(0)

    def _display_exit_message(self):
        """Display a helpful exit message when the user cancels."""
        self.console.print("\n[dim]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/dim]")
        self.console.print("[yellow]👋 Thanks for using Arcane![/yellow]")
        self.console.print("[dim]Your AI-powered roadmap generation tool[/dim]")

    def display_banner(self):
        """Display welcome banner."""
        banner = Panel.fit(
            "[bold blue]🔮  Arcane[/bold blue]\n"
            "[dim]AI-powered roadmap generation and project integration[/dim]",
            border_style="blue"
        )
        self.console.print(banner)
        self.console.print()

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

    def collect_all_preferences_and_settings(self, cli_flags: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Collect all user preferences and system settings using QuestionBuilder."""
        try:
            return self.question_builder.collect_all_preferences(cli_flags)
        except Exception as e:
            self.console.print(f"[red]❌ Error collecting preferences and settings: {str(e)}[/red]")
            return None

    def generate_roadmap(self, preferences: Dict[str, Any]) -> Optional[Roadmap]:
        """Generate roadmap using preferences that include all necessary settings."""
        try:
            # Extract settings from preferences
            llm_provider = preferences.get('llm_provider')
            idea_file_path = preferences.get('idea_file')
            output_directory = preferences.get('output_directory')

            # Read idea file content
            if idea_file_path:
                with open(idea_file_path, 'r', encoding='utf-8') as f:
                    idea_content = f.read()
            else:
                idea_content = "Generate a comprehensive web application roadmap based on the provided preferences."

            # Build enhanced prompt
            enhanced_prompt = self.prompt_builder.build_prompt(
                idea_content=idea_content,
                preferences=preferences,
                idea_file_path=idea_file_path
            )

            self.console.print(f"\n[green]✅ Generated enhanced prompt ({len(enhanced_prompt)} characters)[/green]")

            # Use the enhanced prompt with LLM client directly
            from .clients.factory import LLMClientFactory

            try:
                llm_client = LLMClientFactory.create(llm_provider)
                enhanced_result = llm_client.generate(enhanced_prompt)
                self.console.print(f"[green]✅ Enhanced LLM generation completed ({len(enhanced_result)} characters)[/green]")

                # Fall back to existing generator for roadmap parsing
                from .engines.generation.roadmap_generator import RoadmapGenerator
                generator = RoadmapGenerator(llm_provider, output_directory)

            except Exception as e:
                self.console.print(f"[yellow]⚠️  Enhanced LLM integration failed: {e}[/yellow]")
                self.console.print("[yellow]Falling back to existing generator...[/yellow]")

                # Fall back to existing generator
                from .engines.generation.roadmap_generator import RoadmapGenerator
                generator = RoadmapGenerator(llm_provider, output_directory)

            # Generate roadmap using all comprehensive question data
            roadmap = generator.generate_roadmap(idea_content, preferences)

            if roadmap:
                stats = roadmap.get_statistics()
                self.console.print(f"\n[green]✅ Roadmap generation completed![/green]")
                self.console.print(f"[dim]Generated {stats['total_items']} items across {stats['milestones']} milestones[/dim]")

            return roadmap

        except Exception as e:
            self.console.print(f"[red]❌ Error during generation: {str(e)}[/red]")
            return None


    def export_roadmap(self, roadmap: Roadmap, output_directory: Optional[str]) -> Optional[Dict[str, str]]:
        """Export roadmap to files."""
        if not output_directory:
            return None

        try:
            self.export_engine = FileExporter()

            if hasattr(roadmap, 'metadata') and roadmap.metadata:
                filename_base = roadmap.metadata.get_safe_filename_base()
            else:
                filename_base = "generated_roadmap"

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            csv_filename = f"{timestamp}_{filename_base}.csv"
            output_path = Path(output_directory) / csv_filename

            exported_files = self.export_engine.export_multiple(
                roadmap,
                str(output_path.with_suffix('')),
                formats=['csv']
            )

            self.console.print("\n[green]✅ Exported roadmap to:[/green]")
            for file_path in exported_files:
                self.console.print(f"  📁 {file_path}")

            return {'csv': str(output_path) + ".csv"}

        except Exception as e:
            self.console.print(f"[red]❌ Error exporting roadmap: {str(e)}[/red]")
            return None

    def import_to_notion(self, roadmap: Roadmap) -> bool:
        """Import roadmap to Notion."""
        try:
            self.import_engine = NotionImporter()
            self.import_engine.import_roadmap(roadmap)
            self.console.print("[green]✅ Roadmap imported to Notion successfully![/green]")
            return True
        except Exception as e:
            self.console.print(f"[red]❌ Error importing to Notion: {str(e)}[/red]")
            return False

    def run(self, provider=None, idea_file=None, output_dir=None, **cli_flags):
        """Main application entry point with clean, modular flow."""
        try:
            # Initialize logging
            setup_logging(level="INFO", rich_console=True)
            self.logger.info("Arcane CLI started")

            # Display banner
            self.display_banner()

            # Add CLI flags to the flags dict
            all_cli_flags = cli_flags.copy()
            if provider:
                all_cli_flags['provider'] = provider
            if idea_file:
                all_cli_flags['idea_file'] = idea_file
            if output_dir:
                all_cli_flags['output_dir'] = output_dir

            # Step 1: Collect ALL preferences and settings using QuestionBuilder
            all_preferences = self.collect_all_preferences_and_settings(all_cli_flags)
            if not all_preferences:
                self._display_exit_message()
                return

            # Step 2: Check environment variables for selected LLM provider
            llm_provider = all_preferences.get('llm_provider')
            if not llm_provider:
                self.console.print("[red]❌ No LLM provider selected. Exiting.[/red]")
                return

            if not self.check_environment_variables(llm_provider):
                return

            # Step 3: Generate roadmap
            roadmap = self.generate_roadmap(all_preferences)
            if not roadmap:
                return

            # Step 4: Export roadmap
            output_directory = all_preferences.get('output_directory')
            export_files = self.export_roadmap(roadmap, output_directory)

            # Step 5: Import to Notion
            notion_success = self.import_to_notion(roadmap)

            # Step 6: Display summary
            self._display_summary(roadmap, export_files, notion_success)

        except KeyboardInterrupt:
            self.console.print("\n[yellow]⚠️  Operation cancelled by user[/yellow]")
            self._display_exit_message()
        except Exception as e:
            self.console.print(f"\n[red]❌ Unexpected error: {str(e)}[/red]")

    def _display_summary(self, roadmap: Roadmap, export_files: Optional[Dict[str, str]], notion_success: bool):
        """Display final summary."""
        from rich.table import Table

        table = Table(title="🎉 Generation Complete!")
        table.add_column("Step", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Output", style="blue")

        stats = roadmap.get_statistics()
        table.add_row("1. Roadmap Generation", "✅ Success", f"{stats['total_items']} items generated")
        table.add_row("2. File Export", "✅ Success" if export_files else "⚠️ Skipped", "CSV file created" if export_files else "No output directory")
        table.add_row("3. Notion Import", "✅ Success" if notion_success else "❌ Failed", "Check Notion workspace" if notion_success else "See error above")

        self.console.print(table)


def main():
    """CLI entry point."""
    cli = ArcaneCLI()
    cli.run()


if __name__ == "__main__":
    main()