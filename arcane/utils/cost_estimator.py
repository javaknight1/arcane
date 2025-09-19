"""Cost estimation utilities for LLM API calls."""

import re
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class CostEstimate:
    """Cost estimation result."""
    input_tokens: int
    output_tokens: int
    input_cost: float
    output_cost: float
    total_cost: float
    provider: str
    model: str


class LLMCostEstimator:
    """Estimates costs for LLM API calls based on token counts and provider pricing."""

    # Current pricing as of 2024 (prices per 1M tokens)
    PRICING = {
        'claude': {
            'model': 'claude-3-5-sonnet-20241022',
            'input_price_per_1m': 3.00,   # $3 per 1M input tokens
            'output_price_per_1m': 15.00,  # $15 per 1M output tokens
        },
        'openai': {
            'model': 'gpt-4-turbo',
            'input_price_per_1m': 10.00,   # $10 per 1M input tokens
            'output_price_per_1m': 30.00,  # $30 per 1M output tokens
        },
        'gemini': {
            'model': 'gemini-1.5-pro',
            'input_price_per_1m': 1.25,    # $1.25 per 1M input tokens
            'output_price_per_1m': 5.00,   # $5 per 1M output tokens
        }
    }

    def __init__(self):
        """Initialize cost estimator."""
        pass

    def estimate_tokens(self, text: str) -> int:
        """
        Rough token estimation for text.

        This is an approximation - actual tokenization varies by model.
        General rule: ~4 characters per token for English text.
        """
        if not text:
            return 0

        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())

        # Rough estimation: 4 characters per token
        char_count = len(text)
        estimated_tokens = max(1, char_count // 4)

        return estimated_tokens

    def estimate_cost(self, provider: str, input_text: str, estimated_output_tokens: int) -> CostEstimate:
        """
        Estimate cost for a single API call.

        Args:
            provider: LLM provider ('claude', 'openai', 'gemini')
            input_text: The input prompt text
            estimated_output_tokens: Expected number of output tokens

        Returns:
            CostEstimate object with detailed cost breakdown
        """
        if provider not in self.PRICING:
            raise ValueError(f"Unknown provider: {provider}")

        pricing = self.PRICING[provider]

        # Estimate input tokens
        input_tokens = self.estimate_tokens(input_text)

        # Calculate costs
        input_cost = (input_tokens / 1_000_000) * pricing['input_price_per_1m']
        output_cost = (estimated_output_tokens / 1_000_000) * pricing['output_price_per_1m']
        total_cost = input_cost + output_cost

        return CostEstimate(
            input_tokens=input_tokens,
            output_tokens=estimated_output_tokens,
            input_cost=input_cost,
            output_cost=output_cost,
            total_cost=total_cost,
            provider=provider,
            model=pricing['model']
        )


    def format_cost_estimate(self, estimate: CostEstimate) -> str:
        """Format a cost estimate for display."""
        return (
            f"💰 {estimate.provider.title()} ({estimate.model}):\n"
            f"   📥 Input: {estimate.input_tokens:,} tokens → ${estimate.input_cost:.3f}\n"
            f"   📤 Output: {estimate.output_tokens:,} tokens → ${estimate.output_cost:.3f}\n"
            f"   💳 Total: ${estimate.total_cost:.3f}"
        )


    def estimate_individual_item_costs(self, provider: str, item_counts: Dict[str, int],
                                     idea_content: str) -> Dict[str, Any]:
        """
        Estimate costs for individual item generation strategy.

        Args:
            provider: LLM provider
            item_counts: Dict with counts of milestones, epics, stories, tasks
            idea_content: Project idea text for context size

        Returns:
            Detailed cost breakdown by item type
        """
        base_context_tokens = self.estimate_tokens(idea_content)

        # Estimated token sizes per item type
        item_estimates = {
            'milestone': {
                'input_base': 800,     # Template + context
                'output_avg': 400,     # Just header content
                'description': 'Milestone header only'
            },
            'epic': {
                'input_base': 1200,    # Template + context + milestone context
                'output_avg': 800,     # Epic details
                'description': 'Epic details only'
            },
            'story': {
                'input_base': 1500,    # Template + context + epic context + task list
                'output_avg': 1200,    # Story + all its tasks
                'description': 'Story with all tasks'
            }
        }

        estimates = []
        total_cost = 0
        total_api_calls = 0

        for item_type, count in item_counts.items():
            if item_type == 'total' or count == 0:
                continue

            # Skip tasks as they're generated with stories
            if item_type == 'tasks':
                continue

            # Map plural to singular correctly
            item_key_map = {
                'milestones': 'milestone',
                'epics': 'epic',
                'stories': 'story',
                'tasks': 'task'
            }
            item_key = item_key_map.get(item_type, item_type.rstrip('s'))
            if item_key not in item_estimates:
                continue

            est = item_estimates[item_key]

            # Calculate per-item cost
            input_tokens = base_context_tokens + est['input_base']
            output_tokens = est['output_avg']

            cost_per_item = self.estimate_cost(provider, " " * (input_tokens * 4), output_tokens)
            item_total_cost = cost_per_item.total_cost * count

            estimates.append({
                'item_type': item_type,
                'count': count,
                'cost_per_item': cost_per_item.total_cost,
                'total_cost': item_total_cost,
                'description': est['description'],
                'tokens_per_item': {
                    'input': input_tokens,
                    'output': output_tokens
                }
            })

            total_cost += item_total_cost
            total_api_calls += count

        # Add task generation note (tasks are included in story generation)
        if item_counts.get('tasks', 0) > 0:
            estimates.append({
                'item_type': 'tasks',
                'count': item_counts['tasks'],
                'cost_per_item': 0,
                'total_cost': 0,
                'description': 'Generated with stories (no additional cost)',
                'tokens_per_item': {'input': 0, 'output': 0}
            })

        return {
            'strategy': 'individual_items',
            'provider': provider,
            'item_estimates': estimates,
            'total_cost': total_cost,
            'total_api_calls': total_api_calls
        }


    def format_individual_item_costs(self, cost_data: Dict[str, Any]) -> str:
        """Format individual item cost breakdown for display."""
        lines = []
        lines.append("📊 Individual Item Generation Cost Estimate")
        lines.append(f"🔧 Provider: {cost_data['provider'].title()}")
        lines.append(f"📞 API Calls: {cost_data['total_api_calls']} (stories include their tasks)")
        lines.append("")

        # Calculate total items for context
        total_items = sum(item['count'] for item in cost_data['item_estimates'])
        lines.append(f"📋 Total Items: {total_items} (milestones + epics + stories + tasks)")
        lines.append("")

        lines.append("Cost Breakdown by Generation:")
        for item in cost_data['item_estimates']:
            if item['cost_per_item'] > 0:
                lines.append(f"  • {item['count']} {item['item_type']}: "
                           f"${item['cost_per_item']:.4f} each → ${item['total_cost']:.3f} total")
                lines.append(f"    ({item['description']})")
            else:
                lines.append(f"  • {item['count']} {item['item_type']}: ${item['total_cost']:.3f}")
                lines.append(f"    ({item['description']})")

        lines.append("")
        lines.append(f"💰 Total Estimated Cost: ${cost_data['total_cost']:.3f}")
        lines.append("")
        lines.append("ℹ️  Note: Tasks are generated together with stories to maintain coherence")

        return "\n".join(lines)