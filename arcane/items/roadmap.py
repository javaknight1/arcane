"""Roadmap model - the top-level container.

The Roadmap is the complete output of Arcane, containing all milestones,
epics, stories, and tasks along with project context.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, computed_field

from .context import ProjectContext
from .milestone import Milestone


class StoredUsage(BaseModel):
    """Persisted token usage statistics across generation sessions.

    Stored in roadmap.json so usage accumulates across generate/resume runs.
    """

    api_calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    calls_by_level: dict[str, int] = {}
    tokens_by_level: dict[str, dict[str, int]] = {}

    @property
    def total_tokens(self) -> int:
        """Total tokens used (input + output)."""
        return self.input_tokens + self.output_tokens

    def calculate_cost(
        self, input_price_per_million: float, output_price_per_million: float
    ) -> float:
        """Calculate cost based on token pricing."""
        input_cost = (self.input_tokens / 1_000_000) * input_price_per_million
        output_cost = (self.output_tokens / 1_000_000) * output_price_per_million
        return input_cost + output_cost

    def merged_with(self, session_usage: object) -> StoredUsage:
        """Return a new StoredUsage combining this with session UsageStats.

        Args:
            session_usage: A UsageStats dataclass from the AI client.

        Returns:
            New StoredUsage with accumulated totals.
        """
        merged_calls = dict(self.calls_by_level)
        merged_tokens = {k: dict(v) for k, v in self.tokens_by_level.items()}

        for level, count in session_usage.calls_by_level.items():
            merged_calls[level] = merged_calls.get(level, 0) + count
        for level, tokens in session_usage.tokens_by_level.items():
            if level not in merged_tokens:
                merged_tokens[level] = {"input": 0, "output": 0}
            merged_tokens[level]["input"] += tokens["input"]
            merged_tokens[level]["output"] += tokens["output"]

        return StoredUsage(
            api_calls=self.api_calls + session_usage.api_calls,
            input_tokens=self.input_tokens + session_usage.input_tokens,
            output_tokens=self.output_tokens + session_usage.output_tokens,
            calls_by_level=merged_calls,
            tokens_by_level=merged_tokens,
        )


class Roadmap(BaseModel):
    """Top-level container. The complete output of Arcane.

    Contains the full project roadmap with all milestones and their
    nested epics, stories, and tasks.
    """

    id: str
    project_name: str
    created_at: datetime
    updated_at: datetime
    context: ProjectContext
    milestones: list[Milestone] = []
    usage: StoredUsage = StoredUsage()

    @computed_field
    @property
    def total_hours(self) -> int:
        """Total estimated hours from all milestones."""
        return sum(m.estimated_hours for m in self.milestones)

    @computed_field
    @property
    def total_items(self) -> dict[str, int]:
        """Count of all items by type."""
        milestones = len(self.milestones)
        epics = sum(len(m.epics) for m in self.milestones)
        stories = sum(len(e.stories) for m in self.milestones for e in m.epics)
        tasks = sum(
            len(s.tasks) for m in self.milestones for e in m.epics for s in e.stories
        )
        return {
            "milestones": milestones,
            "epics": epics,
            "stories": stories,
            "tasks": tasks,
        }
