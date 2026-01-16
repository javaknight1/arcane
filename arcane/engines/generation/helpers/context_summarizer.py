"""Context summarization for cascading context injection."""

import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from arcane.items.base import Item, ItemStatus
from arcane.protocols.llm_protocols import LLMClientProtocol
from arcane.utils.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class ContentSummary:
    """Summary of an item's generated content."""
    item_id: str
    item_type: str
    title: str
    key_decisions: List[str]
    technical_choices: List[str]
    deliverables: List[str]
    integration_points: List[str]
    summary_text: str
    full_content_hash: str = ""  # To detect if content changed


@dataclass
class DependencyChain:
    """Chain of dependencies for an item."""
    target_item_id: str
    chain: List[ContentSummary]
    total_depth: int


class ContextSummarizer:
    """Extracts and summarizes key decisions from generated content."""

    # Patterns for extracting key information
    DECISION_PATTERNS = [
        (r'\*\*(?:Decision|Choice|Selected|Using|Chose):\*\*\s*(.+?)(?:\n|$)', 'decision'),
        (r'(?:will use|using|chose|selected|decided on)\s+([A-Z][^\n.]+)', 'decision'),
        (r'\*\*(?:Technology|Tech Stack|Framework):\*\*\s*(.+?)(?:\n|$)', 'technical'),
        (r'(?:built with|implemented (?:using|with)|powered by)\s+([^\n.]+)', 'technical'),
        (r'\*\*(?:Deliverable|Output|Result):\*\*\s*(.+?)(?:\n|$)', 'deliverable'),
        (r'\*\*(?:Integrates? with|Connects? to|API):\*\*\s*(.+?)(?:\n|$)', 'integration'),
    ]

    # Max characters for different summary contexts
    MAX_SUMMARY_LENGTH = 200
    MAX_DECISION_LENGTH = 100
    MAX_CHAIN_ITEMS = 5

    def __init__(self, llm_client: Optional[LLMClientProtocol] = None):
        """Initialize summarizer with optional LLM for complex summarization."""
        self.llm_client = llm_client
        self._summary_cache: Dict[str, ContentSummary] = {}
        self._chain_cache: Dict[str, DependencyChain] = {}

    def get_summary(self, item: Item, force_refresh: bool = False) -> Optional[ContentSummary]:
        """Get or create summary for an item's content.

        Args:
            item: The item to summarize
            force_refresh: If True, regenerate even if cached

        Returns:
            ContentSummary or None if item has no content
        """
        # Check cache first
        cache_key = f"{item.id}:{hash(item.content or '')}"

        if not force_refresh and cache_key in self._summary_cache:
            return self._summary_cache[cache_key]

        # Skip if no content
        if not item.content and not item.description:
            return None

        # Extract summary
        summary = self._extract_summary(item)

        # Cache it
        self._summary_cache[cache_key] = summary

        return summary

    def _extract_summary(self, item: Item) -> ContentSummary:
        """Extract summary from item content using pattern matching."""
        content = item.content or item.description or ""

        key_decisions = []
        technical_choices = []
        deliverables = []
        integration_points = []

        # Apply extraction patterns
        for pattern, category in self.DECISION_PATTERNS:
            matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)

            for match in matches:
                clean_match = match.strip()[:self.MAX_DECISION_LENGTH]

                if category == 'decision':
                    key_decisions.append(clean_match)
                elif category == 'technical':
                    technical_choices.append(clean_match)
                elif category == 'deliverable':
                    deliverables.append(clean_match)
                elif category == 'integration':
                    integration_points.append(clean_match)

        # If pattern matching found nothing, extract from description
        if not any([key_decisions, technical_choices, deliverables]):
            # Fallback to first meaningful sentence
            if item.description:
                key_decisions.append(item.description[:self.MAX_DECISION_LENGTH])

        # Build summary text
        summary_text = self._build_summary_text(
            item, key_decisions, technical_choices, deliverables, integration_points
        )

        return ContentSummary(
            item_id=item.id,
            item_type=item.item_type,
            title=item.name,
            key_decisions=key_decisions[:3],  # Limit to top 3
            technical_choices=technical_choices[:3],
            deliverables=deliverables[:3],
            integration_points=integration_points[:3],
            summary_text=summary_text,
            full_content_hash=str(hash(content))
        )

    def _build_summary_text(
        self,
        item: Item,
        decisions: List[str],
        technical: List[str],
        deliverables: List[str],
        integrations: List[str]
    ) -> str:
        """Build a concise summary text for prompt injection."""
        parts = []

        # Title
        title = item.name.split(': ', 1)[-1] if ': ' in item.name else item.name
        parts.append(f"{item.item_type} {item.id}: {title}")

        # Key decisions
        if decisions:
            parts.append(f"Decisions: {'; '.join(decisions[:2])}")

        # Technical choices
        if technical:
            parts.append(f"Tech: {', '.join(technical[:2])}")

        # Deliverables
        if deliverables:
            parts.append(f"Delivers: {', '.join(deliverables[:2])}")

        # Integrations
        if integrations:
            parts.append(f"Integrates: {', '.join(integrations[:2])}")

        summary = " | ".join(parts)

        # Truncate if too long
        if len(summary) > self.MAX_SUMMARY_LENGTH:
            summary = summary[:self.MAX_SUMMARY_LENGTH - 3] + "..."

        return summary

    def get_dependency_chain(self, item: Item) -> DependencyChain:
        """Get summaries of all items this item depends on.

        Follows the dependency chain up to MAX_CHAIN_ITEMS depth.
        """
        cache_key = item.id

        if cache_key in self._chain_cache:
            return self._chain_cache[cache_key]

        chain = []
        visited = set()

        def collect_dependencies(current_item: Item, depth: int = 0):
            if depth >= self.MAX_CHAIN_ITEMS:
                return

            # Get direct dependencies
            deps = getattr(current_item, 'depends_on_items', [])

            for dep_item in deps:
                # Skip if already processed this dependency
                if dep_item.id in visited:
                    continue

                visited.add(dep_item.id)

                if dep_item.generation_status == ItemStatus.GENERATED:
                    summary = self.get_summary(dep_item)
                    if summary:
                        chain.append(summary)

                # Recurse into dependency's dependencies
                collect_dependencies(dep_item, depth + 1)

        collect_dependencies(item)

        result = DependencyChain(
            target_item_id=item.id,
            chain=chain,
            total_depth=len(chain)
        )

        self._chain_cache[cache_key] = result
        return result

    def get_parent_chain_context(self, item: Item) -> str:
        """Get context from parent chain (milestone -> epic -> story -> task)."""
        lines = []
        current = item.parent

        while current:
            summary = self.get_summary(current)
            if summary:
                lines.append(summary.summary_text)
            current = current.parent

        # Reverse so it's top-down (milestone first)
        lines.reverse()

        return "\n".join(lines) if lines else "No parent context available"

    def get_sibling_context(self, item: Item, include_pending: bool = False) -> str:
        """Get context from sibling items."""
        if not item.parent:
            return "No siblings"

        siblings = []
        for child in item.parent.children:
            if child.id == item.id:
                continue

            if child.generation_status == ItemStatus.GENERATED:
                summary = self.get_summary(child)
                if summary:
                    siblings.append(f"✅ {summary.summary_text}")
            elif include_pending:
                title = child.name.split(': ', 1)[-1] if ': ' in child.name else child.name
                siblings.append(f"⏳ {child.item_type} {child.id}: {title} (pending)")

        return "\n".join(siblings) if siblings else "No sibling context"

    def get_full_cascading_context(
        self,
        item: Item,
        include_roadmap_overview: bool = True,
        max_items: int = 10
    ) -> str:
        """Build complete cascading context for an item.

        This is the main method to call for prompt injection.
        """
        sections = []

        # Section 1: Parent chain
        parent_context = self.get_parent_chain_context(item)
        if parent_context and parent_context != "No parent context available":
            sections.append("=== PARENT HIERARCHY ===")
            sections.append(parent_context)

        # Section 2: Direct dependencies
        dep_chain = self.get_dependency_chain(item)
        if dep_chain.chain:
            sections.append("\n=== DEPENDENCIES (must be consistent with these) ===")
            for dep_summary in dep_chain.chain[:max_items]:
                sections.append(f"• {dep_summary.summary_text}")

        # Section 3: Sibling context
        sibling_context = self.get_sibling_context(item)
        if sibling_context and sibling_context != "No siblings":
            sections.append("\n=== SIBLING ITEMS ===")
            sections.append(sibling_context)

        # Section 4: Item's own semantic context
        if hasattr(item, 'outline_description') and item.outline_description:
            sections.append("\n=== THIS ITEM'S PURPOSE (from outline) ===")
            sections.append(item.outline_description)

        return "\n".join(sections) if sections else "No cascading context available"

    def summarize_with_llm(self, item: Item) -> Optional[ContentSummary]:
        """Use LLM to create a more intelligent summary.

        This is more expensive but produces better summaries for complex content.
        Only use for milestone/epic level items.
        """
        if not self.llm_client:
            return self.get_summary(item)

        if not item.content:
            return None

        prompt = f"""
Summarize the key decisions and outputs from this {item.item_type} content.
Be extremely concise - max 3 bullet points total.

Content:
{item.content[:2000]}

Return ONLY:
DECISIONS: [comma-separated key decisions]
TECH: [comma-separated technical choices]
DELIVERS: [comma-separated deliverables]
"""

        response = self.llm_client.generate(prompt)

        # Parse response
        decisions = []
        technical = []
        deliverables = []

        for line in response.split('\n'):
            if line.startswith('DECISIONS:'):
                decisions = [d.strip() for d in line.replace('DECISIONS:', '').split(',')]
            elif line.startswith('TECH:'):
                technical = [t.strip() for t in line.replace('TECH:', '').split(',')]
            elif line.startswith('DELIVERS:'):
                deliverables = [d.strip() for d in line.replace('DELIVERS:', '').split(',')]

        summary_text = self._build_summary_text(item, decisions, technical, deliverables, [])

        return ContentSummary(
            item_id=item.id,
            item_type=item.item_type,
            title=item.name,
            key_decisions=decisions,
            technical_choices=technical,
            deliverables=deliverables,
            integration_points=[],
            summary_text=summary_text,
            full_content_hash=str(hash(item.content))
        )

    def clear_cache(self) -> None:
        """Clear all cached summaries."""
        self._summary_cache.clear()
        self._chain_cache.clear()

    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        return {
            'summary_cache_size': len(self._summary_cache),
            'chain_cache_size': len(self._chain_cache)
        }
