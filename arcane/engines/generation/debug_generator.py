"""Debug mode generator with LLM reasoning capture."""

import re
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from arcane.utils.logging_config import get_logger

logger = get_logger(__name__)


class ConfidenceLevel(Enum):
    """Confidence level for generation reasoning."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


@dataclass
class GenerationReasoning:
    """Captures LLM reasoning for a generation."""
    item_id: str
    item_type: str
    reasoning: str
    assumptions: List[str]
    uncertainties: List[str]
    confidence_level: ConfidenceLevel
    timestamp: datetime = field(default_factory=datetime.now)
    prompt_tokens: Optional[int] = None
    response_tokens: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'item_id': self.item_id,
            'item_type': self.item_type,
            'reasoning': self.reasoning,
            'assumptions': self.assumptions,
            'uncertainties': self.uncertainties,
            'confidence_level': self.confidence_level.value,
            'timestamp': self.timestamp.isoformat(),
            'prompt_tokens': self.prompt_tokens,
            'response_tokens': self.response_tokens,
        }


@dataclass
class DebugSession:
    """A debug session containing multiple reasoning entries."""
    session_id: str
    started_at: datetime
    entries: List[GenerationReasoning] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_entry(self, entry: GenerationReasoning) -> None:
        """Add a reasoning entry to the session."""
        self.entries.append(entry)

    def get_low_confidence_items(self) -> List[GenerationReasoning]:
        """Get all items with low confidence."""
        return [e for e in self.entries if e.confidence_level == ConfidenceLevel.LOW]

    def get_items_with_uncertainties(self) -> List[GenerationReasoning]:
        """Get all items that have uncertainties."""
        return [e for e in self.entries if e.uncertainties]

    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics for the session."""
        confidence_counts = {level: 0 for level in ConfidenceLevel}
        total_assumptions = 0
        total_uncertainties = 0

        for entry in self.entries:
            confidence_counts[entry.confidence_level] += 1
            total_assumptions += len(entry.assumptions)
            total_uncertainties += len(entry.uncertainties)

        return {
            'total_items': len(self.entries),
            'confidence_distribution': {
                level.value: count for level, count in confidence_counts.items()
            },
            'total_assumptions': total_assumptions,
            'total_uncertainties': total_uncertainties,
            'low_confidence_count': confidence_counts[ConfidenceLevel.LOW],
            'items_with_uncertainties': len(self.get_items_with_uncertainties()),
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary."""
        return {
            'session_id': self.session_id,
            'started_at': self.started_at.isoformat(),
            'metadata': self.metadata,
            'entries': [e.to_dict() for e in self.entries],
            'summary': self.get_summary(),
        }


class DebugGenerator:
    """Generator wrapper that captures LLM reasoning in debug mode.

    When debug mode is enabled, appends a reasoning suffix to prompts
    that asks the LLM to explain its choices, assumptions, and confidence.
    The reasoning is parsed from responses and logged for later analysis.
    """

    DEBUG_SUFFIX = """

=== REASONING (Required in debug mode) ===
After generating the content above, explain your reasoning:

**Why This Structure:**
[Explain why you chose this particular structure, organization, or approach]

**Assumptions Made:**
[List each assumption you made about the project, requirements, or context]
- Assumption 1
- Assumption 2

**Uncertainties:**
[List any uncertainties or areas where you had to guess]
- Uncertainty 1
- Uncertainty 2

**Confidence Level:**
[Choose exactly one: HIGH | MEDIUM | LOW]
- HIGH: Very confident in this generation, clear requirements
- MEDIUM: Reasonably confident, some interpretation needed
- LOW: Significant uncertainty, made substantial assumptions

=== END REASONING ===
"""

    def __init__(
        self,
        llm_client,
        debug_enabled: bool = False,
        session_id: Optional[str] = None
    ):
        """Initialize the debug generator.

        Args:
            llm_client: The LLM client to use for generation
            debug_enabled: Whether to capture reasoning
            session_id: Optional session ID for grouping entries
        """
        self.llm_client = llm_client
        self.debug_enabled = debug_enabled
        self.reasoning_log: List[GenerationReasoning] = []

        # Create debug session if enabled
        if debug_enabled:
            self.session = DebugSession(
                session_id=session_id or datetime.now().strftime("%Y%m%d_%H%M%S"),
                started_at=datetime.now()
            )
        else:
            self.session = None

    def generate(
        self,
        prompt: str,
        item_id: str = "unknown",
        item_type: str = "unknown"
    ) -> str:
        """Generate content, capturing reasoning if debug mode is enabled.

        Args:
            prompt: The generation prompt
            item_id: ID of the item being generated
            item_type: Type of item (milestone, epic, story, task)

        Returns:
            The generated content (without reasoning section)
        """
        content, _ = self.generate_with_reasoning(prompt, item_id, item_type)
        return content

    def generate_with_reasoning(
        self,
        prompt: str,
        item_id: str = "unknown",
        item_type: str = "unknown"
    ) -> Tuple[str, Optional[GenerationReasoning]]:
        """Generate content and optionally capture reasoning.

        Args:
            prompt: The generation prompt
            item_id: ID of the item being generated
            item_type: Type of item (milestone, epic, story, task)

        Returns:
            Tuple of (content, reasoning) where reasoning is None if debug disabled
        """
        if self.debug_enabled:
            debug_prompt = prompt + self.DEBUG_SUFFIX
            response = self.llm_client.generate(debug_prompt)
            content, reasoning = self._parse_debug_response(response, item_id, item_type)

            if reasoning:
                self.reasoning_log.append(reasoning)
                if self.session:
                    self.session.add_entry(reasoning)

            return content, reasoning
        else:
            return self.llm_client.generate(prompt), None

    def _parse_debug_response(
        self,
        response: str,
        item_id: str,
        item_type: str
    ) -> Tuple[str, Optional[GenerationReasoning]]:
        """Parse debug response to extract content and reasoning.

        Args:
            response: The full LLM response including reasoning
            item_id: ID of the item
            item_type: Type of item

        Returns:
            Tuple of (content, reasoning)
        """
        # Find the reasoning section
        reasoning_pattern = r'=== REASONING.*?===(.*?)=== END REASONING ==='
        reasoning_match = re.search(reasoning_pattern, response, re.DOTALL)

        if not reasoning_match:
            # No reasoning found, return full response
            logger.warning(f"Debug mode: No reasoning section found for {item_id}")
            return response, None

        # Extract content (everything before reasoning)
        reasoning_start = response.find('=== REASONING')
        content = response[:reasoning_start].strip()

        # Parse reasoning section
        reasoning_text = reasoning_match.group(1).strip()
        reasoning = self._parse_reasoning_section(reasoning_text, item_id, item_type)

        return content, reasoning

    def _parse_reasoning_section(
        self,
        reasoning_text: str,
        item_id: str,
        item_type: str
    ) -> GenerationReasoning:
        """Parse the reasoning section into structured data.

        Args:
            reasoning_text: The raw reasoning text
            item_id: ID of the item
            item_type: Type of item

        Returns:
            GenerationReasoning object
        """
        # Extract "Why This Structure" section
        why_pattern = r'\*\*Why This Structure:\*\*\s*(.*?)(?=\*\*Assumptions|\*\*Uncertainties|\*\*Confidence|$)'
        why_match = re.search(why_pattern, reasoning_text, re.DOTALL | re.IGNORECASE)
        reasoning_str = why_match.group(1).strip() if why_match else ""

        # Extract assumptions
        assumptions = self._extract_list_items(reasoning_text, 'Assumptions Made')

        # Extract uncertainties
        uncertainties = self._extract_list_items(reasoning_text, 'Uncertainties')

        # Extract confidence level
        confidence = self._extract_confidence(reasoning_text)

        return GenerationReasoning(
            item_id=item_id,
            item_type=item_type,
            reasoning=reasoning_str,
            assumptions=assumptions,
            uncertainties=uncertainties,
            confidence_level=confidence,
        )

    def _extract_list_items(self, text: str, section_name: str) -> List[str]:
        """Extract bullet points from a named section.

        Args:
            text: The text to search
            section_name: Name of the section (e.g., "Assumptions Made")

        Returns:
            List of extracted items
        """
        # Find the section
        section_pattern = rf'\*\*{section_name}:\*\*\s*(.*?)(?=\*\*[A-Z]|$)'
        section_match = re.search(section_pattern, text, re.DOTALL | re.IGNORECASE)

        if not section_match:
            return []

        section_text = section_match.group(1)

        # Extract bullet points
        items = []
        for line in section_text.split('\n'):
            line = line.strip()
            # Match lines starting with - or *
            if line.startswith('-') or line.startswith('*'):
                item = re.sub(r'^[-*]\s*', '', line).strip()
                if item and len(item) > 2:  # Ignore very short items
                    items.append(item)

        return items

    def _extract_confidence(self, text: str) -> ConfidenceLevel:
        """Extract confidence level from text.

        Args:
            text: The text to search

        Returns:
            ConfidenceLevel enum value
        """
        # Look for explicit confidence level
        confidence_pattern = r'\*\*Confidence Level:\*\*\s*(.*?)(?:\n|$)'
        confidence_match = re.search(confidence_pattern, text, re.IGNORECASE)

        if confidence_match:
            confidence_text = confidence_match.group(1).upper()
            if 'HIGH' in confidence_text:
                return ConfidenceLevel.HIGH
            elif 'MEDIUM' in confidence_text:
                return ConfidenceLevel.MEDIUM
            elif 'LOW' in confidence_text:
                return ConfidenceLevel.LOW

        return ConfidenceLevel.UNKNOWN

    def get_reasoning_log(self) -> List[GenerationReasoning]:
        """Get all captured reasoning entries.

        Returns:
            List of GenerationReasoning objects
        """
        return self.reasoning_log.copy()

    def get_session(self) -> Optional[DebugSession]:
        """Get the current debug session.

        Returns:
            DebugSession if debug mode is enabled, None otherwise
        """
        return self.session

    def get_low_confidence_items(self) -> List[GenerationReasoning]:
        """Get all items generated with low confidence.

        Returns:
            List of low confidence GenerationReasoning entries
        """
        return [r for r in self.reasoning_log if r.confidence_level == ConfidenceLevel.LOW]

    def get_uncertain_items(self) -> List[GenerationReasoning]:
        """Get all items that had uncertainties.

        Returns:
            List of GenerationReasoning entries with uncertainties
        """
        return [r for r in self.reasoning_log if r.uncertainties]

    def format_reasoning_report(self) -> str:
        """Generate a formatted report of all captured reasoning.

        Returns:
            Formatted string report
        """
        if not self.reasoning_log:
            return "No reasoning captured. Enable debug mode to capture LLM reasoning."

        lines = ["# Generation Reasoning Report", ""]

        # Summary
        if self.session:
            summary = self.session.get_summary()
            lines.extend([
                "## Summary",
                f"- Total items generated: {summary['total_items']}",
                f"- High confidence: {summary['confidence_distribution']['high']}",
                f"- Medium confidence: {summary['confidence_distribution']['medium']}",
                f"- Low confidence: {summary['confidence_distribution']['low']}",
                f"- Items with uncertainties: {summary['items_with_uncertainties']}",
                f"- Total assumptions made: {summary['total_assumptions']}",
                "",
            ])

        # Low confidence items (if any)
        low_confidence = self.get_low_confidence_items()
        if low_confidence:
            lines.extend([
                "## Low Confidence Items (Needs Review)",
                "",
            ])
            for entry in low_confidence:
                lines.extend([
                    f"### {entry.item_type.title()} {entry.item_id}",
                    f"**Reasoning:** {entry.reasoning[:200]}..." if len(entry.reasoning) > 200 else f"**Reasoning:** {entry.reasoning}",
                    "",
                    "**Uncertainties:**",
                ])
                for u in entry.uncertainties:
                    lines.append(f"- {u}")
                lines.append("")

        # Detailed entries
        lines.extend([
            "## Detailed Reasoning Log",
            "",
        ])
        for entry in self.reasoning_log:
            confidence_emoji = {
                ConfidenceLevel.HIGH: "🟢",
                ConfidenceLevel.MEDIUM: "🟡",
                ConfidenceLevel.LOW: "🔴",
                ConfidenceLevel.UNKNOWN: "⚪",
            }
            lines.extend([
                f"### {entry.item_type.title()} {entry.item_id} {confidence_emoji[entry.confidence_level]}",
                f"**Confidence:** {entry.confidence_level.value.upper()}",
                "",
                f"**Why This Structure:**",
                entry.reasoning or "(No reasoning provided)",
                "",
            ])

            if entry.assumptions:
                lines.append("**Assumptions:**")
                for a in entry.assumptions:
                    lines.append(f"- {a}")
                lines.append("")

            if entry.uncertainties:
                lines.append("**Uncertainties:**")
                for u in entry.uncertainties:
                    lines.append(f"- {u}")
                lines.append("")

            lines.append("---")
            lines.append("")

        return "\n".join(lines)

    def clear_log(self) -> None:
        """Clear the reasoning log."""
        self.reasoning_log = []
        if self.session:
            self.session.entries = []

    def export_session(self) -> Dict[str, Any]:
        """Export the debug session as a dictionary.

        Returns:
            Dictionary containing all session data
        """
        if self.session:
            return self.session.to_dict()
        return {
            'debug_enabled': False,
            'entries': [e.to_dict() for e in self.reasoning_log],
        }

    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics for the generation session.

        Returns:
            Dictionary with summary statistics
        """
        if not self.reasoning_log:
            return {
                'total_items': 0,
                'by_confidence': {'high': 0, 'medium': 0, 'low': 0, 'unknown': 0},
                'by_type': {},
                'total_assumptions': 0,
                'total_uncertainties': 0,
                'items_with_uncertainties': 0,
            }

        # Count by confidence level
        by_confidence = {'high': 0, 'medium': 0, 'low': 0, 'unknown': 0}
        for entry in self.reasoning_log:
            by_confidence[entry.confidence_level.value] += 1

        # Count by item type
        by_type: Dict[str, int] = {}
        for entry in self.reasoning_log:
            by_type[entry.item_type] = by_type.get(entry.item_type, 0) + 1

        # Count assumptions and uncertainties
        total_assumptions = sum(len(e.assumptions) for e in self.reasoning_log)
        total_uncertainties = sum(len(e.uncertainties) for e in self.reasoning_log)
        items_with_uncertainties = len([e for e in self.reasoning_log if e.uncertainties])

        return {
            'total_items': len(self.reasoning_log),
            'by_confidence': by_confidence,
            'by_type': by_type,
            'total_assumptions': total_assumptions,
            'total_uncertainties': total_uncertainties,
            'items_with_uncertainties': items_with_uncertainties,
        }

    def get_debug_report(self) -> str:
        """Generate a console-friendly debug report from reasoning logs.

        Returns:
            Formatted string report for console display
        """
        if not self.reasoning_log:
            return "No reasoning captured. Enable debug mode with --debug flag."

        lines = [
            "",
            "🔍 Generation Debug Report",
            "=" * 50,
        ]

        # Summary stats
        stats = self.get_summary_stats()
        lines.extend([
            f"Total items generated: {stats['total_items']}",
            f"  High confidence:   {stats['by_confidence']['high']}",
            f"  Medium confidence: {stats['by_confidence']['medium']}",
            f"  Low confidence:    {stats['by_confidence']['low']}",
        ])

        # Items by type
        if stats['by_type']:
            lines.append("\nItems by type:")
            for item_type, count in sorted(stats['by_type'].items()):
                lines.append(f"  • {item_type.title()}: {count}")

        # Low confidence items warning
        low_confidence = self.get_low_confidence_items()
        if low_confidence:
            lines.extend([
                "",
                "⚠️  Low Confidence Items (Need Review):",
            ])
            for entry in low_confidence:
                lines.append(f"  • {entry.item_type.title()} {entry.item_id}")
                if entry.uncertainties:
                    uncertainties_preview = ', '.join(entry.uncertainties[:3])
                    if len(entry.uncertainties) > 3:
                        uncertainties_preview += f" (+{len(entry.uncertainties) - 3} more)"
                    lines.append(f"    Uncertainties: {uncertainties_preview}")

        # Common assumptions analysis
        from collections import Counter
        all_assumptions: List[str] = []
        for entry in self.reasoning_log:
            all_assumptions.extend(entry.assumptions)

        if all_assumptions:
            # Normalize assumptions for comparison
            normalized = [a.lower().strip() for a in all_assumptions]
            common = Counter(normalized).most_common(5)

            lines.extend([
                "",
                "📝 Common Assumptions (across items):",
            ])
            for assumption, count in common:
                if count > 1:  # Only show if assumption appears multiple times
                    # Find original casing
                    original = next(a for a in all_assumptions if a.lower().strip() == assumption)
                    lines.append(f"  • {original[:60]}{'...' if len(original) > 60 else ''} ({count} items)")

        # Uncertainty hotspots
        uncertain_items = self.get_uncertain_items()
        if uncertain_items:
            lines.extend([
                "",
                f"❓ Items with Uncertainties: {len(uncertain_items)} of {len(self.reasoning_log)}",
            ])

        lines.extend([
            "",
            "=" * 50,
            "Use --debug-report <file> to save detailed JSON log",
        ])

        return "\n".join(lines)

    def save_debug_log(self, filepath: str) -> None:
        """Save detailed reasoning log to a JSON file.

        Args:
            filepath: Path to save the JSON file
        """
        import json
        from pathlib import Path

        data = {
            'generated_at': datetime.now().isoformat(),
            'summary': self.get_summary_stats(),
            'session_id': self.session.session_id if self.session else None,
            'items': [entry.to_dict() for entry in self.reasoning_log],
            'low_confidence_items': [
                entry.to_dict() for entry in self.get_low_confidence_items()
            ],
            'items_with_uncertainties': [
                entry.to_dict() for entry in self.get_uncertain_items()
            ],
        }

        # Ensure parent directory exists
        output_path = Path(filepath)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)

        logger.info(f"Debug log saved to: {filepath}")

    def get_item_reasoning(self, item_id: str) -> Optional[GenerationReasoning]:
        """Get reasoning for a specific item by ID.

        Args:
            item_id: The item ID to look up

        Returns:
            GenerationReasoning for the item, or None if not found
        """
        for entry in self.reasoning_log:
            if entry.item_id == item_id:
                return entry
        return None

    def get_items_by_type(self, item_type: str) -> List[GenerationReasoning]:
        """Get all reasoning entries for a specific item type.

        Args:
            item_type: Type of item (milestone, epic, story, task)

        Returns:
            List of matching GenerationReasoning entries
        """
        return [e for e in self.reasoning_log if e.item_type.lower() == item_type.lower()]
