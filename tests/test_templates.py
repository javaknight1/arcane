"""Tests for arcane.templates module."""

import pytest
from jinja2 import TemplateNotFound

from arcane.core.templates import TemplateLoader


class TestTemplateLoaderSystem:
    """Tests for system prompt template rendering."""

    def test_render_system_milestone(self):
        """render_system('milestone') returns non-empty string containing 'milestone'."""
        loader = TemplateLoader()
        result = loader.render_system("milestone")

        assert result
        assert "milestone" in result.lower()

    def test_render_system_all_types(self):
        """All 4 system template types render without error."""
        loader = TemplateLoader()
        types = ["milestone", "epic", "story", "task"]

        for item_type in types:
            result = loader.render_system(item_type)
            assert result, f"Template for {item_type} returned empty string"

    def test_render_system_invalid_type(self):
        """Rendering a nonexistent template type raises TemplateNotFound."""
        loader = TemplateLoader()

        with pytest.raises(TemplateNotFound):
            loader.render_system("nonexistent")


class TestTemplateLoaderUser:
    """Tests for user prompt template rendering."""

    @pytest.fixture
    def sample_project_context(self):
        """Sample project context matching ProjectContext fields."""
        return {
            "project_name": "TestApp",
            "vision": "A test application for unit testing",
            "problem_statement": "Testing is hard without good tools",
            "target_users": ["developers", "QA engineers"],
            "timeline": "3 months",
            "team_size": 2,
            "developer_experience": "senior",
            "budget_constraints": "moderate",
            "tech_stack": ["Python", "pytest"],
            "infrastructure_preferences": "AWS",
            "existing_codebase": False,
            "must_have_features": ["unit tests", "integration tests"],
            "nice_to_have_features": ["coverage reports"],
            "out_of_scope": ["performance testing"],
            "similar_products": ["pytest", "unittest"],
            "notes": "Focus on simplicity",
        }

    def test_render_user_generate(self, sample_project_context):
        """render_user('generate', ...) contains the project name."""
        loader = TemplateLoader()
        result = loader.render_user("generate", project_context=sample_project_context)

        assert "TestApp" in result

    def test_render_user_generate_contains_fields(self, sample_project_context):
        """render_user('generate', ...) contains key project fields."""
        loader = TemplateLoader()
        result = loader.render_user("generate", project_context=sample_project_context)

        assert "TestApp" in result
        assert "A test application" in result
        assert "developers" in result
        assert "Python" in result
        assert "AWS" in result

    def test_render_user_with_parent(self, sample_project_context):
        """render_user with parent_context includes parent info."""
        loader = TemplateLoader()
        parent = {"milestone": {"name": "MVP", "goal": "Launch minimum viable product"}}

        result = loader.render_user(
            "generate",
            project_context=sample_project_context,
            parent_context=parent,
        )

        assert "MVP" in result
        assert "Parent Context" in result

    def test_render_user_with_siblings(self, sample_project_context):
        """render_user with sibling_context includes sibling names."""
        loader = TemplateLoader()
        siblings = ["Auth System", "Database"]

        result = loader.render_user(
            "generate",
            project_context=sample_project_context,
            sibling_context=siblings,
        )

        assert "Auth System" in result
        assert "Database" in result
        assert "Already Generated" in result

    def test_render_user_with_guidance(self, sample_project_context):
        """render_user with additional_guidance includes the guidance."""
        loader = TemplateLoader()
        guidance = "Focus on security features first"

        result = loader.render_user(
            "generate",
            project_context=sample_project_context,
            additional_guidance=guidance,
        )

        assert "Focus on security features first" in result
        assert "Additional Guidance" in result

    def test_render_user_refine(self, sample_project_context):
        """render_user('refine', ...) with errors lists the errors."""
        loader = TemplateLoader()
        errors = ["Missing name field", "Invalid priority value"]

        result = loader.render_user(
            "refine",
            project_context=sample_project_context,
            errors=errors,
        )

        assert "Missing name field" in result
        assert "Invalid priority value" in result
        assert "validation errors" in result.lower()

    def test_render_user_optional_fields_hidden(self):
        """Optional fields are not rendered when empty/default."""
        loader = TemplateLoader()
        minimal_context = {
            "project_name": "MinimalApp",
            "vision": "A minimal app",
            "problem_statement": "Minimal problem",
            "target_users": ["users"],
            "timeline": "1 month",
            "team_size": 1,
            "developer_experience": "junior",
            "budget_constraints": "minimal",
            "tech_stack": [],
            "infrastructure_preferences": "No preference",
            "existing_codebase": False,
            "must_have_features": ["core feature"],
            "nice_to_have_features": [],
            "out_of_scope": [],
            "similar_products": [],
            "notes": "",
        }

        result = loader.render_user("generate", project_context=minimal_context)

        assert "MinimalApp" in result
        assert "Tech Stack:" not in result
        assert "Infrastructure:" not in result
        assert "Nice-to-Have:" not in result
        assert "Out of Scope:" not in result
        assert "Similar Products:" not in result
        assert "Additional Notes:" not in result
