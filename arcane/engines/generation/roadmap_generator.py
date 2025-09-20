"""New guided roadmap generator using individual item generation approach."""

from typing import Dict, Any, Optional
from rich.console import Console
from rich.prompt import Prompt

from arcane.clients import LLMClientFactory
from arcane.engines.generation.metadata_extractor import MetadataExtractor
from arcane.engines.generation.recursive_generator import RecursiveRoadmapGenerator
from arcane.engines.parsing.outline_parser import OutlineParser
from arcane.items import Roadmap
from arcane.protocols.llm_protocols import LLMClientProtocol
from arcane.protocols.display_protocols import ConsoleDisplayProtocol
from arcane.protocols.roadmap_protocols import RoadmapProtocol
from arcane.config import get_config
from .helpers import CostEstimationHelper, OutlineProcessor, GenerationSummaryReporter, FileManager


class RoadmapGenerator:
    """Primary roadmap generation engine that orchestrates the complete generation workflow.

    This engine handles the entire roadmap generation process from user preferences
    to fully detailed roadmap structures, including cost estimation, outline generation,
    and individual item content generation.
    """

    def __init__(self, llm_provider: str = 'claude', output_directory: Optional[str] = None):
        self.config = get_config()
        self.llm_provider = llm_provider or self.config.get('llm.default_provider', 'claude')
        self.llm_client: LLMClientProtocol = LLMClientFactory.create(self.llm_provider)
        self.metadata_extractor = MetadataExtractor()
        self.recursive_generator = RecursiveRoadmapGenerator(self.llm_client)
        self.outline_parser = OutlineParser()
        self.console: ConsoleDisplayProtocol = Console()

        # Initialize helper classes
        self.cost_helper = CostEstimationHelper(self.console)
        self.outline_processor = OutlineProcessor(self.console)
        self.summary_reporter = GenerationSummaryReporter(self.console)
        self.file_manager = FileManager(self.console, output_directory)

    def generate_roadmap(self, idea: str, preferences: Dict[str, Any]) -> Optional[RoadmapProtocol]:
        """Generate roadmap using the new individual item approach."""

        # Step 1: Ask user for generation mode preference first
        interactive_mode = self._ask_generation_mode() if self.config.get('generation.interactive_mode', True) else False

        # Step 2: Generate outline
        outline = self.outline_processor.generate_and_confirm_outline(
            self.llm_client, idea, preferences,
            self.file_manager.save_outline if self.file_manager.save_outputs else None
        )
        if not outline:
            return None

        # Step 3: Parse outline into item objects
        self.console.print("\n[cyan]📊 Parsing outline into item objects...[/cyan]")
        milestones = self.outline_parser.parse_outline(outline)

        # Validate structure
        issues = self.outline_parser.validate_structure(milestones)
        if issues:
            self.console.print("[red]❌ Structure validation issues:[/red]")
            for issue in issues:
                self.console.print(f"[red]  • {issue}[/red]")
            return None

        # Step 4: Show cost estimates for individual item generation
        item_counts = self.outline_parser.count_items(milestones)
        if not self.cost_helper.show_and_confirm_individual_costs(self.llm_provider, idea, item_counts):
            self.console.print("[yellow]⚠️ Generation cancelled - cost not approved[/yellow]")
            return None

        # Step 5: Create roadmap object with proper Project structure
        from arcane.items.project import Project
        metadata, _ = self.metadata_extractor.extract_metadata(outline)

        # Create project from metadata
        project = Project(
            name=metadata.project_name,
            description=metadata.description,
            project_type=metadata.project_type,
            tech_stack=metadata.tech_stack,
            estimated_duration=metadata.estimated_duration,
            team_size=metadata.team_size
        )

        # Add milestones to project
        for milestone in milestones:
            project.add_milestone(milestone)

        roadmap = Roadmap(project)

        # Step 6: Generate all content using object-oriented approach
        self.console.print(f"\n[bold green]🚀 Starting roadmap generation[/bold green]")
        roadmap.generate_all_content(self.llm_client, idea, interactive_mode, self.console)

        # Step 7: Show generation summary
        summary = self.recursive_generator.get_generation_summary(milestones)
        self.summary_reporter.show_generation_summary(summary)

        # Step 8: Export to markdown and save outputs
        markdown_content = self.recursive_generator.export_to_markdown(milestones)

        if self.file_manager.save_outputs:
            project_name = self.file_manager.extract_project_name(outline)
            self.file_manager.save_complete_roadmap(markdown_content, project_name)

            # Save progress for potential resume
            progress_file = self.file_manager.get_progress_filepath(project_name)
            self.recursive_generator.save_progress(milestones, progress_file)

        return roadmap

    def _ask_generation_mode(self) -> bool:
        """Ask user whether they want interactive confirmations or automatic generation."""
        choices = self.config.get('generation.mode_choices', ["automatic", "interactive"])
        default_mode = self.config.get('generation.default_mode', "automatic")

        self.console.print("\n[bold cyan]🤖 Generation Mode Selection[/bold cyan]")
        self.console.print("How would you like to generate the roadmap items?")
        self.console.print("")
        self.console.print("[green]automatic[/green] - Generate all items without stopping for confirmation")
        self.console.print("[cyan]interactive[/cyan] - Prompt for confirmation after each item (continue/quit/regenerate)")

        choice = Prompt.ask(
            "\n[cyan]Choose generation mode[/cyan]",
            choices=choices,
            default=default_mode
        )

        if choice == "interactive":
            self.console.print("[cyan]✅ Interactive mode: You'll be prompted after each item[/cyan]")
            return True
        else:
            self.console.print("[green]✅ Automatic mode: All items will be generated continuously[/green]")
            return False