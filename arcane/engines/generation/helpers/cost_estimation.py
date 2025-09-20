"""Cost estimation helper for roadmap generation."""

from typing import Dict, Any
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm

from arcane.protocols.display_protocols import ConsoleDisplayProtocol
from arcane.protocols.llm_protocols import CostEstimationProtocol
from arcane.utils.cost_estimator import LLMCostEstimator
from arcane.utils.logging_config import get_logger
from arcane.config import get_config

logger = get_logger(__name__)


class CostEstimationHelper:
    """Handles cost estimation and confirmation for roadmap generation."""

    def __init__(self, console: ConsoleDisplayProtocol):
        self.console = console
        self.cost_estimator: CostEstimationProtocol = LLMCostEstimator()
        self.config = get_config()

    def show_and_confirm_individual_costs(
        self,
        llm_provider: str,
        idea: str,
        item_counts: Dict[str, int]
    ) -> bool:
        """Show cost estimates for individual item generation and get confirmation."""
        self.console.print("\n[bold cyan]💰 Individual Item Generation Cost Estimate[/bold cyan]")

        # Get cost estimate
        cost_data = self.cost_estimator.estimate_individual_item_costs(
            llm_provider, item_counts, idea
        )

        # Show detailed breakdown
        cost_display = self.cost_estimator.format_individual_item_costs(cost_data)
        self.console.print(Panel(cost_display, title="Cost Breakdown", border_style="cyan"))

        # Ask for confirmation
        return Confirm.ask(
            f"\n[cyan]Proceed with generation for ~${cost_data['total_cost']:.3f}?[/cyan]",
            default=True
        )

    def show_upfront_cost_estimation(
        self,
        llm_provider: str,
        idea: str,
        preferences: Dict[str, Any]
    ) -> bool:
        """Show upfront cost estimation before generating outline."""
        self.console.print("\n[bold cyan]💰 Cost Estimation Analysis[/bold cyan]")

        # Estimate item counts based on preferences
        estimated_counts = self._estimate_item_counts(preferences)

        # Calculate costs for outline generation
        outline_tokens = self.config.get('generation.outline_output_tokens', 3000)
        outline_cost = self.cost_estimator.estimate_cost(
            llm_provider,
            idea + "Generate comprehensive outline",  # Approximate prompt size
            outline_tokens
        )

        # Calculate average costs for individual items
        milestone_tokens = self.config.get('generation.milestone_output_tokens', 400)
        epic_tokens = self.config.get('generation.epic_output_tokens', 800)
        story_tokens = self.config.get('generation.story_output_tokens', 1200)

        milestone_avg_cost = self.cost_estimator.estimate_cost(
            llm_provider,
            idea[:500] + "milestone context",  # Approximate context
            milestone_tokens
        )

        epic_avg_cost = self.cost_estimator.estimate_cost(
            llm_provider,
            idea[:500] + "epic context",
            epic_tokens
        )

        story_avg_cost = self.cost_estimator.estimate_cost(
            llm_provider,
            idea[:500] + "story and tasks context",
            story_tokens
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

        return Confirm.ask(
            f"\n[cyan]Proceed with outline generation (~${outline_cost.total_cost:.3f})?[/cyan]",
            default=True
        )

    def _estimate_item_counts(self, preferences: Dict[str, Any]) -> Dict[str, int]:
        """Estimate item counts based on preferences."""
        timeline = preferences.get('timeline', self.config.get('generation.default_timeline', '6-months'))
        complexity = preferences.get('complexity', self.config.get('generation.default_complexity', 'moderate'))

        # Get milestone counts from config
        milestone_counts = self.config.get('generation.milestones_per_timeline', {
            '3-months': 3, '6-months': 4, '12-months': 6
        })
        milestones = milestone_counts.get(timeline, 4)

        # Get complexity multipliers from config
        epic_multipliers = self.config.get('generation.epics_per_milestone', {
            'simple': 1.5, 'moderate': 2.0, 'complex': 3.0
        })
        story_multipliers = self.config.get('generation.stories_per_epic', {
            'simple': 2, 'moderate': 2, 'complex': 3
        })
        task_multipliers = self.config.get('generation.tasks_per_story', {
            'simple': 3, 'moderate': 4, 'complex': 5
        })

        epics_per_milestone = epic_multipliers.get(complexity, 2.0)
        stories_per_epic = story_multipliers.get(complexity, 2)
        tasks_per_story = task_multipliers.get(complexity, 4)

        return {
            'milestones': milestones,
            'epics': int(milestones * epics_per_milestone),
            'stories': int(milestones * epics_per_milestone * stories_per_epic),
            'tasks': int(milestones * epics_per_milestone * stories_per_epic * tasks_per_story)
        }