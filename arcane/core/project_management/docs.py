"""Documentation page builders for project management integrations.

Transforms ProjectContext data into structured documentation pages that
PM clients (Linear, Jira, Notion) can convert into their native formats.

No AI generation — purely data formatting from existing ProjectContext fields.
"""

from pydantic import BaseModel

from arcane.core.items import ProjectContext


class DocSection(BaseModel):
    """A single section within a documentation page."""

    title: str
    content_type: str  # "paragraph" | "bullet_list" | "checklist" | "callout"
    items: list[str]
    icon: str | None = None


class DocPage(BaseModel):
    """A complete documentation page with titled sections."""

    title: str
    sections: list[DocSection]


def build_project_overview(context: ProjectContext) -> DocPage:
    """Build a project overview page from context."""
    sections: list[DocSection] = [
        DocSection(
            title="Vision",
            content_type="callout",
            items=[context.vision],
            icon="🔮",
        ),
        DocSection(
            title="Problem Statement",
            content_type="paragraph",
            items=[context.problem_statement],
        ),
        DocSection(
            title="Target Users",
            content_type="bullet_list",
            items=context.target_users,
        ),
    ]

    if context.similar_products:
        sections.append(
            DocSection(
                title="Similar Products",
                content_type="bullet_list",
                items=context.similar_products,
            )
        )

    if context.notes:
        sections.append(
            DocSection(
                title="Notes",
                content_type="paragraph",
                items=[context.notes],
            )
        )

    return DocPage(title="Project Overview", sections=sections)


def build_requirements(context: ProjectContext) -> DocPage:
    """Build a requirements page from context."""
    sections: list[DocSection] = [
        DocSection(
            title="Must-Have Features",
            content_type="checklist",
            items=context.must_have_features,
        ),
    ]

    if context.nice_to_have_features:
        sections.append(
            DocSection(
                title="Nice-to-Have Features",
                content_type="checklist",
                items=context.nice_to_have_features,
            )
        )

    if context.out_of_scope:
        sections.append(
            DocSection(
                title="Out of Scope",
                content_type="callout",
                items=context.out_of_scope,
                icon="🚫",
            )
        )

    return DocPage(title="Requirements", sections=sections)


def build_technical_decisions(context: ProjectContext) -> DocPage:
    """Build a technical decisions page from context."""
    sections: list[DocSection] = []

    if context.tech_stack:
        sections.append(
            DocSection(
                title="Tech Stack",
                content_type="bullet_list",
                items=context.tech_stack,
            )
        )

    sections.append(
        DocSection(
            title="Infrastructure",
            content_type="paragraph",
            items=[context.infrastructure_preferences],
        )
    )

    sections.append(
        DocSection(
            title="Existing Codebase",
            content_type="paragraph",
            items=["Yes — integrating with existing code" if context.existing_codebase else "No — greenfield project"],
        )
    )

    return DocPage(title="Technical Decisions", sections=sections)


def build_team_constraints(context: ProjectContext) -> DocPage:
    """Build a team constraints page from context."""
    return DocPage(
        title="Team & Constraints",
        sections=[
            DocSection(
                title="Timeline",
                content_type="callout",
                items=[context.timeline],
                icon="📅",
            ),
            DocSection(
                title="Team",
                content_type="paragraph",
                items=[f"{context.team_size} developer(s), {context.developer_experience} level"],
            ),
            DocSection(
                title="Budget",
                content_type="paragraph",
                items=[context.budget_constraints],
            ),
        ],
    )


def build_all_pages(context: ProjectContext) -> list[DocPage]:
    """Build all documentation pages from context."""
    return [
        build_project_overview(context),
        build_requirements(context),
        build_technical_decisions(context),
        build_team_constraints(context),
    ]


def _render_section(section: DocSection) -> str:
    """Render a single DocSection to markdown."""
    lines = [f"## {section.title}", ""]

    if section.content_type == "paragraph":
        for item in section.items:
            lines.append(item)
            lines.append("")
    elif section.content_type == "bullet_list":
        for item in section.items:
            lines.append(f"- {item}")
        lines.append("")
    elif section.content_type == "checklist":
        for item in section.items:
            lines.append(f"- [ ] {item}")
        lines.append("")
    elif section.content_type == "callout":
        icon_prefix = f"{section.icon} " if section.icon else ""
        if len(section.items) == 1:
            lines.append(f"> {icon_prefix}**{section.title}:** {section.items[0]}")
        else:
            lines.append(f"> {icon_prefix}**{section.title}:**")
            for item in section.items:
                lines.append(f"> - {item}")
        lines.append("")

    return "\n".join(lines)


def render_markdown(pages: list[DocPage]) -> str:
    """Render a list of DocPages to a markdown string.

    Each page becomes a ``# Title`` heading with its sections rendered
    underneath.  Pages are separated by ``---`` horizontal rules.
    """
    parts: list[str] = []

    for i, page in enumerate(pages):
        if i > 0:
            parts.append("---\n")
        parts.append(f"# {page.title}\n")
        for section in page.sections:
            parts.append(_render_section(section))

    return "\n".join(parts).rstrip("\n") + "\n"
