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
from .validation import PreferenceValidator, ValidationSeverity
from .config.config_manager import get_config


class ArcaneCLI:
    """Clean, modular CLI application for AI-powered roadmap generation."""

    def __init__(
        self,
        compression_level: Optional[str] = None,
        model_mode: Optional[str] = None,
        debug_mode: bool = False,
        debug_report: Optional[str] = None
    ):
        self.console = Console()
        self.logger = get_logger(__name__)
        self.config = get_config()

        # Get compression settings from config or override
        self.compression_level = compression_level or self.config.get(
            'generation.compression_level', 'moderate'
        )
        show_stats = self.config.get('generation.show_compression_stats', False)

        # Get model mode setting
        self.model_mode = model_mode or self.config.get(
            'generation.model_mode', 'tiered'
        )

        # Debug mode settings
        self.debug_mode = debug_mode
        self.debug_report_path = debug_report
        self.debug_generator = None

        self.question_builder = QuestionBuilder(self.console)
        self.prompt_builder = RoadmapPromptBuilder(
            compression_level=self.compression_level,
            show_compression_stats=show_stats
        )
        self.validator = PreferenceValidator()
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

    def validate_preferences(self, preferences: Dict[str, Any]) -> bool:
        """
        Validate preferences for consistency and feasibility.

        Args:
            preferences: Dictionary of all collected preferences

        Returns:
            True if validation passes, False if critical issues found
        """
        try:
            self.console.print("\n[cyan]🔍 Validating preference consistency...[/cyan]")

            # Run validation
            issues = self.validator.validate_preferences(preferences)

            if not issues:
                self.console.print("[green]✅ All preferences validated successfully[/green]")
                return True

            # Display validation results
            self._display_validation_results(issues)

            # Check if we should proceed
            should_proceed, reason = self.validator.should_proceed(issues)

            if should_proceed:
                self.console.print(f"[yellow]⚠️  {reason}[/yellow]")

                # Ask user if they want to continue with warnings
                if issues:
                    from rich.prompt import Confirm
                    continue_anyway = Confirm.ask(
                        "\n[yellow]Do you want to continue with these validation warnings?[/yellow]",
                        default=True
                    )

                    if not continue_anyway:
                        self.console.print("[yellow]Operation cancelled by user due to validation issues[/yellow]")
                        return False

                return True
            else:
                self.console.print(f"[red]❌ {reason}[/red]")
                self.console.print("[red]Please resolve critical issues before proceeding[/red]")
                return False

        except Exception as e:
            self.console.print(f"[yellow]⚠️  Validation error: {str(e)}[/yellow]")
            self.console.print("[yellow]Proceeding without validation...[/yellow]")
            return True

    def collect_all_preferences_and_settings(self, cli_flags: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Collect all user preferences and system settings using QuestionBuilder."""
        try:
            # Check if a profile was specified
            profile_name = cli_flags.get('profile')
            if profile_name:
                from .config.profiles import ProjectProfiles

                self.console.print(f"\n[cyan]📋 Using predefined profile: {profile_name}[/cyan]")
                profile_data = ProjectProfiles.PROFILES[profile_name]
                self.console.print(f"[dim]{profile_data['description']}[/dim]")

                # Get profile preferences and merge with any additional CLI flags
                preferences = profile_data['preferences'].copy()

                # Override with any explicitly provided CLI flags (excluding profile)
                cli_overrides = {k: v for k, v in cli_flags.items()
                               if k not in ['profile'] and v is not None}
                preferences.update(cli_overrides)

                # Add required system preferences
                preferences['llm_provider'] = cli_flags.get('provider', 'claude')
                if 'output_dir' in cli_flags:
                    preferences['output_directory'] = cli_flags['output_dir']
                if 'idea_file' in cli_flags:
                    preferences['idea_file'] = cli_flags['idea_file']

                self.console.print(f"[green]✅ Profile loaded with {len(preferences)} preferences[/green]")
                return preferences
            else:
                # Normal question collection flow
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

            # Step 1: Aggregate preferences and generate insights
            from .engines.analysis import PreferenceAggregator
            aggregator = PreferenceAggregator()

            self.console.print("\n[cyan]🔍 Analyzing preferences and generating insights...[/cyan]")
            enhanced_context = aggregator.generate_enhanced_context(preferences)
            insights = aggregator.aggregate_preferences(preferences)

            # Display insights summary
            self._display_insights_summary(insights)

            # Build enhanced prompt with aggregated context
            enhanced_prompt = self.prompt_builder.build_prompt(
                idea_content=idea_content,
                preferences=enhanced_context,  # Use enhanced context instead of raw preferences
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

    def run(self, provider=None, idea_file=None, output_dir=None, compression=None, model_mode=None, debug=None, debug_report=None, **cli_flags):
        """Main application entry point with clean, modular flow.

        Args:
            provider: LLM provider to use
            idea_file: Path to idea file
            output_dir: Output directory for exports
            compression: Compression level ('none', 'light', 'moderate', 'aggressive')
            model_mode: Model selection mode ('tiered', 'premium', 'economy', 'standard')
            debug: Enable debug mode to capture LLM reasoning
            debug_report: Path to save detailed debug report JSON
            **cli_flags: Additional CLI flags
        """
        try:
            # Initialize logging
            setup_logging(level="INFO", rich_console=True)
            self.logger.info("Arcane CLI started")

            # Update compression level if provided
            if compression:
                self.compression_level = compression
                self.prompt_builder = RoadmapPromptBuilder(
                    compression_level=compression,
                    show_compression_stats=self.config.get('generation.show_compression_stats', False)
                )
                self.logger.info("Compression level set to: %s", compression)

            # Update model mode if provided
            if model_mode:
                self.model_mode = model_mode
                self.logger.info("Model mode set to: %s", model_mode)

            # Update debug mode if provided
            if debug is not None:
                self.debug_mode = debug
            if debug_report:
                self.debug_report_path = debug_report
                self.debug_mode = True  # Enable debug mode if report path specified

            if self.debug_mode:
                self.logger.info("Debug mode enabled - LLM reasoning will be captured")
                self.console.print("[dim]🔍 Debug mode enabled - capturing LLM reasoning[/dim]")
                # Initialize debug generator (will be wired to generation process later)
                from .engines.generation.debug_generator import DebugGenerator
                self.debug_generator = DebugGenerator(
                    llm_client=None,  # Will be set when generation starts
                    debug_enabled=True
                )

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

            # Step 2.5: Validate preferences for consistency and feasibility
            validation_passed = self.validate_preferences(all_preferences)
            if not validation_passed:
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

            # Step 7: Display compression stats if enabled
            if self.config.get('generation.show_compression_stats', False):
                self._display_compression_stats()

            # Step 8: Display debug report if enabled
            if self.debug_mode and self.debug_generator:
                self.console.print(self.debug_generator.get_debug_report())
                if self.debug_report_path:
                    self.debug_generator.save_debug_log(self.debug_report_path)
                    self.console.print(f"\n[green]📝 Debug log saved to: {self.debug_report_path}[/green]")

        except KeyboardInterrupt:
            self.console.print("\n[yellow]⚠️  Operation cancelled by user[/yellow]")
            self._display_exit_message()
        except Exception as e:
            self.console.print(f"\n[red]❌ Unexpected error: {str(e)}[/red]")

    def _display_insights_summary(self, insights):
        """Display aggregated insights summary."""
        from rich.table import Table
        from rich.panel import Panel

        # Risk Assessment Panel
        risk_color = {
            'low': 'green',
            'medium': 'yellow',
            'high': 'orange1',
            'critical': 'red'
        }.get(insights.risk_assessment.level.value, 'white')

        risk_panel = f"[{risk_color}]Risk Level: {insights.risk_assessment.level.value.upper()}[/{risk_color}]\n"
        risk_panel += f"Score: {insights.risk_assessment.score:.0%}\n"
        if insights.risk_assessment.factors:
            risk_panel += "\nTop Risk Factors:\n"
            for factor in insights.risk_assessment.factors[:3]:
                risk_panel += f"  • {factor}\n"

        self.console.print(Panel(risk_panel, title="⚠️ Risk Assessment", border_style=risk_color))

        # Feasibility Analysis
        if not insights.feasibility.is_feasible:
            feasibility_panel = "[red]⚠️ PROJECT MAY NOT BE FEASIBLE[/red]\n"
            feasibility_panel += f"Confidence: {insights.feasibility.confidence:.0%}\n\n"
            feasibility_panel += "Key Concerns:\n"
            for concern in insights.feasibility.concerns[:3]:
                feasibility_panel += f"  • {concern}\n"
            self.console.print(Panel(feasibility_panel, title="📊 Feasibility Analysis", border_style="red"))

        # Resource Alignment Table
        table = Table(title="📈 Resource Alignment")
        table.add_column("Resource", style="cyan")
        table.add_column("Alignment", style="green")
        table.add_column("Status", style="yellow")

        def get_status(score):
            if score >= 0.8:
                return "✅ Excellent"
            elif score >= 0.6:
                return "⚠️ Adequate"
            else:
                return "❌ Insufficient"

        table.add_row("Budget", f"{insights.resource_alignment.budget_alignment:.0%}",
                     get_status(insights.resource_alignment.budget_alignment))
        table.add_row("Team", f"{insights.resource_alignment.team_alignment:.0%}",
                     get_status(insights.resource_alignment.team_alignment))
        table.add_row("Timeline", f"{insights.resource_alignment.timeline_alignment:.0%}",
                     get_status(insights.resource_alignment.timeline_alignment))

        self.console.print(table)

        # Key Recommendations
        if insights.priority_recommendations:
            rec_text = "\n".join(f"  {i+1}. {rec}" for i, rec in enumerate(insights.priority_recommendations[:3]))
            self.console.print(Panel(rec_text, title="🎯 Priority Recommendations", border_style="cyan"))

        # Warning Flags
        if insights.warning_flags:
            for warning in insights.warning_flags[:3]:
                self.console.print(f"[red]{warning}[/red]")

        # Adjusted Estimates
        self.console.print("\n[bold cyan]📊 Adjusted Estimates:[/bold cyan]")
        self.console.print(f"  • Realistic Timeline: {insights.estimated_actual_timeline}")
        self.console.print(f"  • Recommended Team: {insights.recommended_team_size}")
        self.console.print(f"  • Minimum Budget: {insights.minimum_budget_estimate}")

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

    def _display_compression_stats(self):
        """Display prompt compression statistics."""
        stats = self.prompt_builder.get_total_savings()

        if stats['prompt_count'] == 0:
            return

        from rich.panel import Panel

        stats_text = (
            f"[cyan]Compression Level:[/cyan] {self.compression_level}\n"
            f"[cyan]Prompts Compressed:[/cyan] {stats['prompt_count']}\n"
            f"[cyan]Original Tokens:[/cyan] {stats['total_original_tokens']:,}\n"
            f"[cyan]Compressed Tokens:[/cyan] {stats['total_compressed_tokens']:,}\n"
            f"[green]Tokens Saved:[/green] {stats['total_tokens_saved']:,}\n"
            f"[green]Average Compression:[/green] {stats['average_compression_ratio']:.1f}%"
        )

        self.console.print(Panel(stats_text, title="📊 Compression Statistics", border_style="cyan"))

    def _display_validation_results(self, issues):
        """Display validation results in a user-friendly format."""

        # Validation summary
        summary = self.validator.get_validation_summary(issues)

        self.console.print(f"\n[bold cyan]🔍 Validation Results[/bold cyan]")
        self.console.print(f"Found {summary['total_issues']} issues: " +
                          f"{summary['by_severity']['critical']} critical, " +
                          f"{summary['by_severity']['error']} errors, " +
                          f"{summary['by_severity']['warning']} warnings, " +
                          f"{summary['by_severity']['info']} info")

        # Display issues by severity
        severity_colors = {
            ValidationSeverity.CRITICAL: "red",
            ValidationSeverity.ERROR: "orange1",
            ValidationSeverity.WARNING: "yellow",
            ValidationSeverity.INFO: "cyan"
        }

        severity_icons = {
            ValidationSeverity.CRITICAL: "🚨",
            ValidationSeverity.ERROR: "❌",
            ValidationSeverity.WARNING: "⚠️",
            ValidationSeverity.INFO: "ℹ️"
        }

        # Group issues by severity
        by_severity = {}
        for issue in issues:
            if issue.severity not in by_severity:
                by_severity[issue.severity] = []
            by_severity[issue.severity].append(issue)

        # Display each severity group
        for severity in [ValidationSeverity.CRITICAL, ValidationSeverity.ERROR,
                        ValidationSeverity.WARNING, ValidationSeverity.INFO]:
            if severity not in by_severity:
                continue

            color = severity_colors[severity]
            icon = severity_icons[severity]
            severity_issues = by_severity[severity]

            self.console.print(f"\n[bold {color}]{icon} {severity.value.title()} Issues ({len(severity_issues)}):[/bold {color}]")

            for i, issue in enumerate(severity_issues, 1):
                self.console.print(f"[{color}]{i}. {issue.message}[/{color}]")

                if issue.affected_preferences:
                    self.console.print(f"   [dim]Affects: {', '.join(issue.affected_preferences)}[/dim]")

                if issue.recommendation:
                    self.console.print(f"   [green]💡 Recommendation: {issue.recommendation}[/green]")

                self.console.print()


def main(
    compression: Optional[str] = None,
    model_mode: Optional[str] = None,
    debug: bool = False,
    debug_report: Optional[str] = None
):
    """CLI entry point.

    Args:
        compression: Optional compression level override
        model_mode: Optional model mode override ('tiered', 'premium', 'economy', 'standard')
        debug: Enable debug mode to capture LLM reasoning
        debug_report: Path to save detailed debug report JSON
    """
    cli = ArcaneCLI(
        compression_level=compression,
        model_mode=model_mode,
        debug_mode=debug,
        debug_report=debug_report
    )
    cli.run(compression=compression, model_mode=model_mode, debug=debug, debug_report=debug_report)


if __name__ == "__main__":
    main()