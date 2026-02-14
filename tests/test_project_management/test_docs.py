"""Tests for arcane.project_management.docs module."""

import pytest

from arcane.items import ProjectContext
from arcane.project_management.docs import (
    DocPage,
    DocSection,
    build_all_pages,
    build_project_overview,
    build_requirements,
    build_team_constraints,
    build_technical_decisions,
    render_markdown,
)


@pytest.fixture
def sample_context():
    """Sample ProjectContext with all fields populated."""
    return ProjectContext(
        project_name="Test Project",
        vision="A test application",
        problem_statement="Testing is important",
        target_users=["developers", "testers"],
        timeline="3 months",
        team_size=2,
        developer_experience="senior",
        budget_constraints="moderate",
        tech_stack=["Python", "React"],
        infrastructure_preferences="AWS",
        existing_codebase=False,
        must_have_features=["auth", "dashboard"],
        nice_to_have_features=["dark mode"],
        out_of_scope=["mobile app"],
        similar_products=["Jira", "Linear"],
        notes="Test notes",
    )


@pytest.fixture
def minimal_context():
    """ProjectContext with only required fields — optional lists empty."""
    return ProjectContext(
        project_name="Minimal Project",
        vision="A minimal app",
        problem_statement="Needs solving",
        target_users=["users"],
        timeline="1 month MVP",
        team_size=1,
        developer_experience="junior",
        budget_constraints="minimal (free tier everything)",
        must_have_features=["core feature"],
    )


class TestBuildProjectOverview:
    """Tests for build_project_overview."""

    def test_has_vision_section(self, sample_context):
        page = build_project_overview(sample_context)
        vision = next(s for s in page.sections if s.title == "Vision")
        assert vision.content_type == "callout"
        assert sample_context.vision in vision.items

    def test_has_problem_section(self, sample_context):
        page = build_project_overview(sample_context)
        problem = next(s for s in page.sections if s.title == "Problem Statement")
        assert problem.content_type == "paragraph"
        assert sample_context.problem_statement in problem.items

    def test_has_target_users_section(self, sample_context):
        page = build_project_overview(sample_context)
        users = next(s for s in page.sections if s.title == "Target Users")
        assert users.content_type == "bullet_list"
        assert users.items == ["developers", "testers"]

    def test_has_similar_products_when_present(self, sample_context):
        page = build_project_overview(sample_context)
        similar = next(s for s in page.sections if s.title == "Similar Products")
        assert similar.items == ["Jira", "Linear"]

    def test_has_notes_when_present(self, sample_context):
        page = build_project_overview(sample_context)
        notes = next(s for s in page.sections if s.title == "Notes")
        assert notes.items == ["Test notes"]

    def test_omits_similar_products_when_empty(self, minimal_context):
        page = build_project_overview(minimal_context)
        titles = [s.title for s in page.sections]
        assert "Similar Products" not in titles

    def test_omits_notes_when_empty(self, minimal_context):
        page = build_project_overview(minimal_context)
        titles = [s.title for s in page.sections]
        assert "Notes" not in titles

    def test_page_title(self, sample_context):
        page = build_project_overview(sample_context)
        assert page.title == "Project Overview"


class TestBuildRequirements:
    """Tests for build_requirements."""

    def test_has_must_have_checklist(self, sample_context):
        page = build_requirements(sample_context)
        must_have = next(s for s in page.sections if s.title == "Must-Have Features")
        assert must_have.content_type == "checklist"
        assert must_have.items == ["auth", "dashboard"]

    def test_has_nice_to_have_when_present(self, sample_context):
        page = build_requirements(sample_context)
        nice = next(s for s in page.sections if s.title == "Nice-to-Have Features")
        assert nice.content_type == "checklist"
        assert nice.items == ["dark mode"]

    def test_has_out_of_scope_callout(self, sample_context):
        page = build_requirements(sample_context)
        oos = next(s for s in page.sections if s.title == "Out of Scope")
        assert oos.content_type == "callout"
        assert oos.items == ["mobile app"]

    def test_omits_nice_to_have_when_empty(self, minimal_context):
        page = build_requirements(minimal_context)
        titles = [s.title for s in page.sections]
        assert "Nice-to-Have Features" not in titles

    def test_omits_out_of_scope_when_empty(self, minimal_context):
        page = build_requirements(minimal_context)
        titles = [s.title for s in page.sections]
        assert "Out of Scope" not in titles

    def test_page_title(self, sample_context):
        page = build_requirements(sample_context)
        assert page.title == "Requirements"


class TestBuildTechnicalDecisions:
    """Tests for build_technical_decisions."""

    def test_has_tech_stack_section(self, sample_context):
        page = build_technical_decisions(sample_context)
        tech = next(s for s in page.sections if s.title == "Tech Stack")
        assert tech.content_type == "bullet_list"
        assert tech.items == ["Python", "React"]

    def test_has_infrastructure_section(self, sample_context):
        page = build_technical_decisions(sample_context)
        infra = next(s for s in page.sections if s.title == "Infrastructure")
        assert infra.content_type == "paragraph"
        assert "AWS" in infra.items[0]

    def test_has_existing_codebase_section(self, sample_context):
        page = build_technical_decisions(sample_context)
        codebase = next(s for s in page.sections if s.title == "Existing Codebase")
        assert codebase.content_type == "paragraph"
        assert "greenfield" in codebase.items[0].lower()

    def test_existing_codebase_true(self, sample_context):
        sample_context.existing_codebase = True
        page = build_technical_decisions(sample_context)
        codebase = next(s for s in page.sections if s.title == "Existing Codebase")
        assert "existing" in codebase.items[0].lower()

    def test_omits_tech_stack_when_empty(self, minimal_context):
        page = build_technical_decisions(minimal_context)
        titles = [s.title for s in page.sections]
        assert "Tech Stack" not in titles

    def test_page_title(self, sample_context):
        page = build_technical_decisions(sample_context)
        assert page.title == "Technical Decisions"


class TestBuildTeamConstraints:
    """Tests for build_team_constraints."""

    def test_has_timeline_section(self, sample_context):
        page = build_team_constraints(sample_context)
        timeline = next(s for s in page.sections if s.title == "Timeline")
        assert timeline.content_type == "callout"
        assert "3 months" in timeline.items[0]

    def test_has_team_section(self, sample_context):
        page = build_team_constraints(sample_context)
        team = next(s for s in page.sections if s.title == "Team")
        assert team.content_type == "paragraph"
        assert "2 developer(s)" in team.items[0]
        assert "senior" in team.items[0]

    def test_has_budget_section(self, sample_context):
        page = build_team_constraints(sample_context)
        budget = next(s for s in page.sections if s.title == "Budget")
        assert budget.content_type == "paragraph"
        assert "moderate" in budget.items[0]

    def test_page_title(self, sample_context):
        page = build_team_constraints(sample_context)
        assert page.title == "Team & Constraints"


class TestBuildAllPages:
    """Tests for build_all_pages."""

    def test_returns_four_pages(self, sample_context):
        pages = build_all_pages(sample_context)
        assert len(pages) == 4

    def test_correct_page_titles(self, sample_context):
        pages = build_all_pages(sample_context)
        titles = [p.title for p in pages]
        assert titles == [
            "Project Overview",
            "Requirements",
            "Technical Decisions",
            "Team & Constraints",
        ]

    def test_all_pages_are_doc_pages(self, sample_context):
        pages = build_all_pages(sample_context)
        for page in pages:
            assert isinstance(page, DocPage)


class TestDocModels:
    """Tests for DocSection and DocPage models."""

    def test_doc_section_with_icon(self):
        section = DocSection(
            title="Test", content_type="callout", items=["item"], icon="🔮"
        )
        assert section.icon == "🔮"

    def test_doc_section_without_icon(self):
        section = DocSection(
            title="Test", content_type="paragraph", items=["item"]
        )
        assert section.icon is None

    def test_doc_page_empty_sections(self):
        page = DocPage(title="Empty", sections=[])
        assert page.sections == []


class TestRenderMarkdown:
    """Tests for render_markdown."""

    def test_render_markdown_paragraph(self):
        page = DocPage(
            title="Page",
            sections=[
                DocSection(title="Intro", content_type="paragraph", items=["Hello world"]),
            ],
        )
        md = render_markdown([page])
        assert "## Intro" in md
        assert "Hello world" in md
        # Should not have bullet markers
        assert "- Hello world" not in md

    def test_render_markdown_bullet_list(self):
        page = DocPage(
            title="Page",
            sections=[
                DocSection(title="Items", content_type="bullet_list", items=["one", "two"]),
            ],
        )
        md = render_markdown([page])
        assert "- one" in md
        assert "- two" in md
        # Should not have checkboxes
        assert "[ ]" not in md

    def test_render_markdown_checklist(self):
        page = DocPage(
            title="Page",
            sections=[
                DocSection(title="Tasks", content_type="checklist", items=["do this", "do that"]),
            ],
        )
        md = render_markdown([page])
        assert "- [ ] do this" in md
        assert "- [ ] do that" in md

    def test_render_markdown_callout(self):
        page = DocPage(
            title="Page",
            sections=[
                DocSection(
                    title="Warning",
                    content_type="callout",
                    items=["Be careful"],
                    icon="⚠️",
                ),
            ],
        )
        md = render_markdown([page])
        # Single-item callout
        assert '> ⚠️ **Warning:** Be careful' in md

    def test_render_markdown_callout_multi_item(self):
        page = DocPage(
            title="Page",
            sections=[
                DocSection(
                    title="Excluded",
                    content_type="callout",
                    items=["mobile app", "desktop app"],
                    icon="🚫",
                ),
            ],
        )
        md = render_markdown([page])
        assert "> 🚫 **Excluded:**" in md
        assert "> - mobile app" in md
        assert "> - desktop app" in md

    def test_render_markdown_callout_no_icon(self):
        page = DocPage(
            title="Page",
            sections=[
                DocSection(
                    title="Note",
                    content_type="callout",
                    items=["plain callout"],
                ),
            ],
        )
        md = render_markdown([page])
        assert "> **Note:** plain callout" in md

    def test_render_markdown_full(self, sample_context):
        pages = build_all_pages(sample_context)
        md = render_markdown(pages)

        # Page headings
        assert "# Project Overview" in md
        assert "# Requirements" in md
        assert "# Technical Decisions" in md
        assert "# Team & Constraints" in md

        # Page separators
        assert "---" in md

        # Spot-check content from different section types
        assert "A test application" in md  # vision callout
        assert "- [ ] auth" in md  # must-have checklist
        assert "- Python" in md  # tech stack bullet list

    def test_render_markdown_page_separator(self):
        page1 = DocPage(title="First", sections=[])
        page2 = DocPage(title="Second", sections=[])
        md = render_markdown([page1, page2])
        assert "# First" in md
        assert "---" in md
        assert "# Second" in md
