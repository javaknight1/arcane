"""Cost estimation for roadmap generation.

Provides estimates for API calls, tokens, and costs before generation starts.
"""

from dataclasses import dataclass


@dataclass
class CostEstimate:
    """Estimated costs for roadmap generation."""

    api_calls: int
    input_tokens: int
    output_tokens: int
    total_tokens: int
    estimated_cost_usd: float

    # Breakdown by level
    milestone_calls: int
    epic_calls: int
    story_calls: int
    task_calls: int


# Average tokens per API call (based on typical prompts and responses)
TOKENS_PER_CALL = {
    "milestone": {"input": 800, "output": 1500},
    "epic": {"input": 1000, "output": 1200},
    "story": {"input": 1200, "output": 1000},
    "task": {"input": 1500, "output": 2500},
}

# Model pricing per million tokens (as of 2024)
MODEL_PRICING = {
    "claude-sonnet-4-20250514": {"input": 3.00, "output": 15.00},
    "claude-3-5-sonnet-20241022": {"input": 3.00, "output": 15.00},
    "claude-3-opus-20240229": {"input": 15.00, "output": 75.00},
    "claude-3-haiku-20240307": {"input": 0.25, "output": 1.25},
    # Default fallback
    "default": {"input": 3.00, "output": 15.00},
}

# Expected items per level (conservative estimates for typical projects)
DEFAULT_ESTIMATES = {
    "milestones": 3,
    "epics_per_milestone": 3,
    "stories_per_epic": 3,
    "tasks_per_story": 3,
}


def estimate_generation_cost(
    model: str = "claude-sonnet-4-20250514",
    milestones: int | None = None,
    epics_per_milestone: int | None = None,
    stories_per_epic: int | None = None,
    tasks_per_story: int | None = None,
) -> CostEstimate:
    """Estimate the cost of generating a roadmap.

    Args:
        model: The model name to use for pricing.
        milestones: Expected number of milestones (default: 3).
        epics_per_milestone: Expected epics per milestone (default: 3).
        stories_per_epic: Expected stories per epic (default: 3).
        tasks_per_story: Expected tasks per story (default: 3).

    Returns:
        CostEstimate with API calls, tokens, and cost breakdown.
    """
    # Use defaults if not specified
    ms = milestones or DEFAULT_ESTIMATES["milestones"]
    ep_per_ms = epics_per_milestone or DEFAULT_ESTIMATES["epics_per_milestone"]
    st_per_ep = stories_per_epic or DEFAULT_ESTIMATES["stories_per_epic"]
    tk_per_st = tasks_per_story or DEFAULT_ESTIMATES["tasks_per_story"]

    # Calculate total items at each level
    total_epics = ms * ep_per_ms
    total_stories = total_epics * st_per_ep
    total_tasks = total_stories * tk_per_st

    # API calls: 1 per milestone gen + 1 per epic gen + 1 per story gen + 1 per task gen
    # But milestones/epics/stories are generated in batches, tasks individually
    milestone_calls = 1  # One call generates all milestones
    epic_calls = ms  # One call per milestone to generate its epics
    story_calls = total_epics  # One call per epic to generate its stories
    task_calls = total_stories  # One call per story to generate its tasks

    total_calls = milestone_calls + epic_calls + story_calls + task_calls

    # Calculate tokens
    input_tokens = (
        milestone_calls * TOKENS_PER_CALL["milestone"]["input"]
        + epic_calls * TOKENS_PER_CALL["epic"]["input"]
        + story_calls * TOKENS_PER_CALL["story"]["input"]
        + task_calls * TOKENS_PER_CALL["task"]["input"]
    )

    output_tokens = (
        milestone_calls * TOKENS_PER_CALL["milestone"]["output"]
        + epic_calls * TOKENS_PER_CALL["epic"]["output"]
        + story_calls * TOKENS_PER_CALL["story"]["output"]
        + task_calls * TOKENS_PER_CALL["task"]["output"]
    )

    total_tokens = input_tokens + output_tokens

    # Get pricing for model
    pricing = MODEL_PRICING.get(model, MODEL_PRICING["default"])

    # Calculate cost (pricing is per million tokens)
    input_cost = (input_tokens / 1_000_000) * pricing["input"]
    output_cost = (output_tokens / 1_000_000) * pricing["output"]
    total_cost = input_cost + output_cost

    return CostEstimate(
        api_calls=total_calls,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=total_tokens,
        estimated_cost_usd=total_cost,
        milestone_calls=milestone_calls,
        epic_calls=epic_calls,
        story_calls=story_calls,
        task_calls=task_calls,
    )


def format_cost_estimate(estimate: CostEstimate) -> str:
    """Format a cost estimate for display.

    Args:
        estimate: The cost estimate to format.

    Returns:
        Formatted string for console display.
    """
    lines = [
        "📊 Estimated generation:",
        f"   ~{estimate.api_calls} API calls",
        f"   ~{estimate.total_tokens:,} tokens ({estimate.input_tokens:,} in / {estimate.output_tokens:,} out)",
        f"   ~${estimate.estimated_cost_usd:.2f} estimated cost",
    ]
    return "\n".join(lines)


def format_actual_usage(usage: "UsageStats", model: str = "claude-sonnet-4-20250514") -> str:
    """Format actual usage statistics for display with per-level breakdown.

    Args:
        usage: UsageStats object with cumulative and per-level tracking.
        model: The model used for pricing calculation.

    Returns:
        Formatted string for console display.
    """
    pricing = MODEL_PRICING.get(model, MODEL_PRICING["default"])
    total_cost = usage.calculate_cost(pricing["input"], pricing["output"])

    lines = [
        "📊 Actual usage:",
        f"   {usage.api_calls} API calls",
        f"   {usage.total_tokens:,} tokens ({usage.input_tokens:,} in / {usage.output_tokens:,} out)",
        f"   ${total_cost:.4f} total cost",
    ]

    # Per-level breakdown if available
    level_order = ["milestone", "epic", "story", "task"]
    levels_with_data = [lv for lv in level_order if lv in usage.calls_by_level]

    if levels_with_data:
        lines.append("")
        lines.append("   Level        Calls   Input Tok   Output Tok")
        lines.append("   ─────────────────────────────────────────────")
        for level in levels_with_data:
            calls = usage.calls_by_level[level]
            tokens = usage.tokens_by_level.get(level, {"input": 0, "output": 0})
            lines.append(
                f"   {level:<12} {calls:>5}   {tokens['input']:>9,}   {tokens['output']:>10,}"
            )

    return "\n".join(lines)
