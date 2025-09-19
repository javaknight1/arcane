"""New guided roadmap generator using individual item generation approach."""

from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Confirm

from arcane.llm_clients import LLMClientFactory
from arcane.prompts.idea_processor import IdeaProcessor
from arcane.engines.generation.metadata_extractor import MetadataExtractor
from arcane.engines.generation.recursive_generator import RecursiveRoadmapGenerator
from arcane.engines.parsing.outline_parser import OutlineParser
from arcane.items import Roadmap
from arcane.utils.cost_estimator import LLMCostEstimator
from arcane.prompts.prompt_builder import PromptBuilder


class NewGuidedRoadmapGenerator:
    """New guided roadmap generator using individual item generation."""

    def __init__(self, llm_provider: str = 'claude', output_directory: Optional[str] = None):
        self.llm_provider = llm_provider
        self.llm_client = LLMClientFactory.create(llm_provider)
        self.idea_processor = IdeaProcessor()
        self.metadata_extractor = MetadataExtractor()
        self.cost_estimator = LLMCostEstimator()
        self.prompt_builder = PromptBuilder()
        self.recursive_generator = RecursiveRoadmapGenerator(self.llm_client)
        self.outline_parser = OutlineParser()
        self.console = Console()

        # Set up output directory
        if output_directory:
            self.output_dir = Path(output_directory)
            self.output_dir.mkdir(parents=True, exist_ok=True)
            self.save_outputs = True
        else:
            self.output_dir = None
            self.save_outputs = False

    def generate_roadmap(self, idea: str, preferences: Dict[str, Any]) -> Optional[Roadmap]:
        """Generate roadmap using the new individual item approach."""

        # Step 1: Ask user for generation mode preference first
        interactive_mode = self._ask_generation_mode()

        # Step 2: Generate outline
        outline = self._generate_and_confirm_outline(idea, preferences)
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
        if not self._show_and_confirm_individual_costs(idea, item_counts):
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
        self._show_generation_summary(summary)

        # Step 8: Export to markdown and save outputs
        markdown_content = self.recursive_generator.export_to_markdown(milestones)

        if self.save_outputs:
            project_name = self._extract_project_name(outline)
            self._save_complete_roadmap(markdown_content, project_name)

            # Save progress for potential resume
            progress_file = self.output_dir / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{project_name}_progress.json"
            self.recursive_generator.save_progress(milestones, str(progress_file))

        return roadmap

    def _generate_and_confirm_outline(self, idea: str, preferences: Dict[str, Any]) -> Optional[str]:
        """Generate and get user confirmation for the outline."""
        # First show upfront cost estimation
        if not self._show_upfront_cost_estimation(idea, preferences):
            return None

        self.console.print("\n[bold]📋 Generating roadmap outline...[/bold]")

        # Process idea content
        processed_idea = self.idea_processor.process_idea(idea)
        features_formatted = self.idea_processor.format_features(processed_idea['key_features'])
        processed_idea['key_features_formatted'] = features_formatted
        structured_prompt = self.idea_processor.build_structured_prompt(processed_idea)

        # Generate outline
        outline_prompt = self.prompt_builder.build_custom_prompt(
            'outline_generation',
            idea_content=structured_prompt,
            timeline=preferences.get('timeline', '6-months'),
            complexity=preferences.get('complexity', 'moderate'),
            team_size=preferences.get('team_size', '1'),
            focus=preferences.get('focus', 'balanced')
        )

        outline = self.llm_client.generate(outline_prompt)

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
        self._display_outline_tree(outline)

        # Save outline if output directory is set
        if self.save_outputs:
            project_name = self._extract_project_name(outline)
            outline_file = self._save_outline(outline, project_name)
            self.console.print(f"[dim]💾 Outline saved to: {outline_file}[/dim]")

        # Get user confirmation
        if not Confirm.ask("\n[cyan]Are you satisfied with this outline structure?[/cyan]", default=True):
            if Confirm.ask("[yellow]Would you like to regenerate the outline?[/yellow]"):
                return self._generate_and_confirm_outline(idea, preferences)
            else:
                return None

        return outline

    def _show_and_confirm_individual_costs(self, idea: str, item_counts: Dict[str, int]) -> bool:
        """Show cost estimates for individual item generation and get confirmation."""
        self.console.print("\n[bold cyan]💰 Individual Item Generation Cost Estimate[/bold cyan]")

        # Get cost estimate
        cost_data = self.cost_estimator.estimate_individual_item_costs(
            self.llm_provider, item_counts, idea
        )

        # Show detailed breakdown
        cost_display = self.cost_estimator.format_individual_item_costs(cost_data)
        self.console.print(Panel(cost_display, title="Cost Breakdown", border_style="cyan"))

        # Ask for confirmation
        return Confirm.ask(f"\n[cyan]Proceed with generation for ~${cost_data['total_cost']:.3f}?[/cyan]", default=True)

    def _show_generation_summary(self, summary: Dict[str, Any]) -> None:
        """Show generation results summary."""
        self.console.print("\n[bold cyan]📈 First Milestone Generation Summary[/bold cyan]")

        table = Table(title="First Milestone Results")
        table.add_column("Item Type", style="cyan")
        table.add_column("Total", style="white")
        table.add_column("Generated", style="green")
        table.add_column("Failed", style="red")
        table.add_column("Skipped", style="yellow")

        # Calculate attempted items (only count items that were actually processed)
        attempted_items = summary['generated'] + summary['failed'] + summary['skipped']

        for item_type, counts in summary['by_type'].items():
            # Only show rows for item types that had attempts
            attempted_for_type = counts['generated'] + counts['failed'] + counts['skipped']
            if attempted_for_type > 0:
                table.add_row(
                    item_type,
                    str(counts['total']),
                    str(counts['generated']),
                    str(counts['failed']),
                    str(counts['skipped'])
                )

        self.console.print(table)

        # Overall status based on attempted items only
        if attempted_items > 0:
            success_rate = (summary['generated'] / attempted_items) * 100
            if success_rate >= 90:
                status_style = "green"
                status_icon = "✅"
            elif success_rate >= 70:
                status_style = "yellow"
                status_icon = "⚠️"
            else:
                status_style = "red"
                status_icon = "❌"

            self.console.print(f"\n[{status_style}]{status_icon} Generation Success Rate: {success_rate:.1f}% ({summary['generated']}/{attempted_items} items)[/{status_style}]")
        else:
            self.console.print("\n[yellow]⚠️ No items were processed[/yellow]")

        # Show note about any unprocessed milestones
        remaining_milestones = summary['by_type']['Milestone']['total'] - summary['by_type']['Milestone']['generated']
        if remaining_milestones > 0:
            self.console.print(f"\n[dim]📝 Note: {remaining_milestones} milestones were not successfully generated[/dim]")

    def _extract_project_name(self, content: str) -> str:
        """Extract project name from content."""
        lines = content.split('\n')
        for line in lines:
            if line.strip().startswith('PROJECT_NAME:'):
                return line.split(':', 1)[1].strip()
            elif line.strip().startswith('# ') and not line.strip().startswith('## '):
                return line.strip('# ').strip()
        return "roadmap"

    def _save_outline(self, outline: str, project_name: str) -> str:
        """Save outline to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{project_name}_outline.md"
        filepath = self.output_dir / filename

        with open(filepath, 'w') as f:
            f.write(outline)

        return str(filepath)

    def _save_complete_roadmap(self, content: str, project_name: str) -> str:
        """Save complete roadmap to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{project_name}_complete_roadmap.md"
        filepath = self.output_dir / filename

        with open(filepath, 'w') as f:
            f.write(content)

        self.console.print(f"[green]💾 Complete roadmap saved to: {filepath}[/green]")
        return str(filepath)

    def _show_upfront_cost_estimation(self, idea: str, preferences: Dict[str, Any]) -> bool:
        """Show upfront cost estimation before generating outline."""
        self.console.print("\n[bold cyan]💰 Cost Estimation Analysis[/bold cyan]")

        # Estimate item counts based on preferences
        estimated_counts = self._estimate_item_counts(preferences)

        # Calculate costs for outline generation
        outline_cost = self.cost_estimator.estimate_cost(
            self.llm_provider,
            idea + "Generate comprehensive outline",  # Approximate prompt size
            3000  # Estimated outline output tokens
        )

        # Calculate average costs for individual items
        milestone_avg_cost = self.cost_estimator.estimate_cost(
            self.llm_provider,
            idea[:500] + "milestone context",  # Approximate context
            400  # Average milestone output
        )

        epic_avg_cost = self.cost_estimator.estimate_cost(
            self.llm_provider,
            idea[:500] + "epic context",
            800  # Average epic output
        )

        story_avg_cost = self.cost_estimator.estimate_cost(
            self.llm_provider,
            idea[:500] + "story and tasks context",
            1200  # Story with all tasks
        )

        # Display detailed breakdown
        self.console.print("\n[yellow]📊 Estimated Cost Breakdown:[/yellow]")
        self.console.print(f"\n1️⃣  Outline Generation: ${outline_cost.total_cost:.3f}")
        self.console.print(f"   • Input: ~{outline_cost.input_tokens:,} tokens")
        self.console.print(f"   • Output: ~{outline_cost.output_tokens:,} tokens")

        self.console.print(f"\n2️⃣  Individual Item Generation (Estimates):")
        self.console.print(f"   • Milestones: {estimated_counts['milestones']} × ${milestone_avg_cost.total_cost:.3f} = ${estimated_counts['milestones'] * milestone_avg_cost.total_cost:.3f}")
        self.console.print(f"   • Epics: {estimated_counts['epics']} × ${epic_avg_cost.total_cost:.3f} = ${estimated_counts['epics'] * epic_avg_cost.total_cost:.3f}")
        self.console.print(f"   • Stories: {estimated_counts['stories']} × ${story_avg_cost.total_cost:.3f} = ${estimated_counts['stories'] * story_avg_cost.total_cost:.3f}")
        self.console.print(f"   • Tasks: {estimated_counts['tasks']} (included with stories, no extra cost)")

        total_estimated = (outline_cost.total_cost +
                         estimated_counts['milestones'] * milestone_avg_cost.total_cost +
                         estimated_counts['epics'] * epic_avg_cost.total_cost +
                         estimated_counts['stories'] * story_avg_cost.total_cost)

        self.console.print(f"\n[bold]💰 Total Estimated Cost: ${total_estimated:.3f}[/bold]")
        self.console.print("[dim]Note: Actual costs may vary based on outline complexity and content generation[/dim]")

        return Confirm.ask(f"\n[cyan]Proceed with outline generation (~${outline_cost.total_cost:.3f})?[/cyan]", default=True)

    def _estimate_item_counts(self, preferences: Dict[str, Any]) -> Dict[str, int]:
        """Estimate item counts based on preferences."""
        timeline = preferences.get('timeline', '6-months')
        complexity = preferences.get('complexity', 'moderate')

        # Base estimates
        milestones = 4
        epics_per_milestone = 2
        stories_per_epic = 2
        tasks_per_story = 4

        # Adjust based on timeline
        if '3-months' in timeline:
            milestones = 3
        elif '12-months' in timeline:
            milestones = 6

        # Adjust based on complexity
        if complexity == 'simple':
            epics_per_milestone = 1.5
            stories_per_epic = 2
            tasks_per_story = 3
        elif complexity == 'complex':
            epics_per_milestone = 3
            stories_per_epic = 3
            tasks_per_story = 5

        return {
            'milestones': milestones,
            'epics': int(milestones * epics_per_milestone),
            'stories': int(milestones * epics_per_milestone * stories_per_epic),
            'tasks': int(milestones * epics_per_milestone * stories_per_epic * tasks_per_story)
        }

    def _display_outline_tree(self, outline: str) -> None:
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

    def _ask_generation_mode(self) -> bool:
        """Ask user whether they want interactive confirmations or automatic generation."""
        from rich.prompt import Prompt

        self.console.print("\n[bold cyan]🤖 Generation Mode Selection[/bold cyan]")
        self.console.print("How would you like to generate the roadmap items?")
        self.console.print("")
        self.console.print("[green]automatic[/green] - Generate all items without stopping for confirmation")
        self.console.print("[cyan]interactive[/cyan] - Prompt for confirmation after each item (continue/quit/regenerate)")

        choice = Prompt.ask(
            "\n[cyan]Choose generation mode[/cyan]",
            choices=["automatic", "interactive"],
            default="automatic"
        )

        if choice == "interactive":
            self.console.print("[cyan]✅ Interactive mode: You'll be prompted after each item[/cyan]")
            return True
        else:
            self.console.print("[green]✅ Automatic mode: All items will be generated continuously[/green]")
            return False

