"""Context injection utilities for prompt enhancement."""

from typing import Optional


class ContextInjector:
    """Injects cascading context into prompts for consistency."""

    CONTEXT_BLOCK_TEMPLATE = """
=== CASCADING CONTEXT (IMPORTANT - Be consistent with this) ===
{cascading_context}

=== PARENT HIERARCHY ===
{parent_context}

=== ROADMAP STATUS ===
{roadmap_overview}

=== CONSISTENCY REQUIREMENTS ===
Your generation MUST:
- Use technologies mentioned in earlier decisions
- Reference completed work appropriately
- Not duplicate functionality from sibling items
- Build logically on parent item's deliverables
"""

    MINIMAL_CONTEXT_TEMPLATE = """
=== CONTEXT ===
{cascading_context}

=== REQUIREMENTS ===
Be consistent with previous decisions. Build on completed work.
"""

    @classmethod
    def inject_context(
        cls,
        base_prompt: str,
        cascading_context: str,
        parent_context: str = "",
        roadmap_overview: str = ""
    ) -> str:
        """Inject context block into a prompt.

        Args:
            base_prompt: The original prompt template
            cascading_context: Context from previously generated items
            parent_context: Context from parent items in hierarchy
            roadmap_overview: Overview of roadmap generation status

        Returns:
            Enhanced prompt with context block
        """
        context_block = cls.CONTEXT_BLOCK_TEMPLATE.format(
            cascading_context=cascading_context or "No prior context",
            parent_context=parent_context or "No parent context",
            roadmap_overview=roadmap_overview or "No roadmap overview"
        )

        # Insert after the first section or at the beginning
        if "=== CONTEXT ===" in base_prompt:
            # Replace existing context section
            return base_prompt.replace("=== CONTEXT ===", context_block)
        elif "=== PROJECT CONTEXT ===" in base_prompt:
            # Insert before project context
            return base_prompt.replace(
                "=== PROJECT CONTEXT ===",
                context_block + "\n\n=== PROJECT CONTEXT ==="
            )
        else:
            # Prepend context block
            return context_block + "\n\n" + base_prompt

    @classmethod
    def inject_minimal_context(
        cls,
        base_prompt: str,
        cascading_context: str
    ) -> str:
        """Inject minimal context for simpler items.

        Args:
            base_prompt: The original prompt template
            cascading_context: Context from previously generated items

        Returns:
            Enhanced prompt with minimal context
        """
        context_block = cls.MINIMAL_CONTEXT_TEMPLATE.format(
            cascading_context=cascading_context or "No prior context"
        )

        return context_block + "\n\n" + base_prompt

    @classmethod
    def build_dependency_section(
        cls,
        dependency_summaries: list
    ) -> str:
        """Build a dependency context section.

        Args:
            dependency_summaries: List of ContentSummary objects from dependencies

        Returns:
            Formatted dependency section
        """
        if not dependency_summaries:
            return "No dependencies - this item can be implemented independently."

        lines = ["This item depends on the following completed items:"]

        for summary in dependency_summaries:
            lines.append(f"• {summary.summary_text}")

            if summary.key_decisions:
                lines.append(f"  Decisions: {'; '.join(summary.key_decisions[:2])}")

            if summary.technical_choices:
                lines.append(f"  Tech: {', '.join(summary.technical_choices[:2])}")

        lines.append("")
        lines.append("Ensure your generation is consistent with these dependencies.")

        return "\n".join(lines)

    @classmethod
    def build_sibling_section(
        cls,
        sibling_summaries: list,
        pending_siblings: Optional[list] = None
    ) -> str:
        """Build a sibling context section.

        Args:
            sibling_summaries: List of ContentSummary objects from generated siblings
            pending_siblings: List of pending sibling items (optional)

        Returns:
            Formatted sibling section
        """
        lines = []

        if sibling_summaries:
            lines.append("Generated sibling items:")
            for summary in sibling_summaries:
                lines.append(f"✅ {summary.summary_text}")

        if pending_siblings:
            lines.append("\nPending sibling items:")
            for item in pending_siblings:
                title = item.name.split(': ', 1)[-1] if ': ' in item.name else item.name
                lines.append(f"⏳ {item.item_type} {item.id}: {title}")

        if lines:
            lines.append("")
            lines.append("Avoid duplicating functionality from sibling items.")
            return "\n".join(lines)

        return "No sibling items."

    @classmethod
    def build_tech_stack_reminder(
        cls,
        tech_choices: list
    ) -> str:
        """Build a tech stack reminder section.

        Args:
            tech_choices: List of technology choices from earlier items

        Returns:
            Formatted tech stack reminder
        """
        if not tech_choices:
            return ""

        unique_tech = list(set(tech_choices))
        return f"""
=== TECH STACK (Use these technologies) ===
{', '.join(unique_tech[:10])}
"""

    @classmethod
    def extract_all_tech_choices(
        cls,
        summaries: list
    ) -> list:
        """Extract all technical choices from a list of summaries.

        Args:
            summaries: List of ContentSummary objects

        Returns:
            List of all technical choices
        """
        tech_choices = []
        for summary in summaries:
            tech_choices.extend(summary.technical_choices)
        return tech_choices
