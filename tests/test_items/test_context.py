"""Tests for arcane.items.context module."""

import pytest
from pydantic import ValidationError

from arcane.core.items import ProjectContext


class TestProjectContext:
    """Tests for the ProjectContext model."""

    def test_context_with_required_fields(self):
        """Test creating ProjectContext with only required fields."""
        context = ProjectContext(
            project_name="My App",
            vision="Build an amazing app",
            problem_statement="Users need a better solution",
            target_users=["developers", "designers"],
            timeline="6 months",
            team_size=3,
            developer_experience="senior",
            budget_constraints="moderate",
            must_have_features=["auth", "dashboard"],
        )

        assert context.project_name == "My App"
        assert context.vision == "Build an amazing app"
        assert context.target_users == ["developers", "designers"]
        assert context.team_size == 3
        assert context.must_have_features == ["auth", "dashboard"]

        # Verify defaults
        assert context.tech_stack == []
        assert context.infrastructure_preferences == "No preference"
        assert context.existing_codebase is False
        assert context.nice_to_have_features == []
        assert context.out_of_scope == []
        assert context.similar_products == []
        assert context.notes == ""

    def test_context_with_all_fields(self):
        """Test creating ProjectContext with all fields specified."""
        context = ProjectContext(
            project_name="Enterprise App",
            vision="Transform business operations",
            problem_statement="Manual processes are slow",
            target_users=["enterprise customers", "admins"],
            timeline="12 months",
            team_size=8,
            developer_experience="mixed",
            budget_constraints="flexible",
            tech_stack=["React", "Python", "PostgreSQL"],
            infrastructure_preferences="AWS",
            existing_codebase=True,
            must_have_features=["SSO", "audit logs", "reporting"],
            nice_to_have_features=["mobile app", "API"],
            out_of_scope=["blockchain", "AI chat"],
            similar_products=["Salesforce", "HubSpot"],
            notes="Must comply with SOC2",
        )

        assert context.tech_stack == ["React", "Python", "PostgreSQL"]
        assert context.infrastructure_preferences == "AWS"
        assert context.existing_codebase is True
        assert context.nice_to_have_features == ["mobile app", "API"]
        assert context.out_of_scope == ["blockchain", "AI chat"]
        assert context.similar_products == ["Salesforce", "HubSpot"]
        assert context.notes == "Must comply with SOC2"

    def test_context_defaults_applied(self):
        """Test that default values are correctly applied."""
        context = ProjectContext(
            project_name="Test",
            vision="Test vision",
            problem_statement="Test problem",
            target_users=["testers"],
            timeline="1 month",
            team_size=1,
            developer_experience="junior",
            budget_constraints="minimal",
            must_have_features=["basic feature"],
        )

        # All optional fields should have defaults
        assert context.tech_stack == []
        assert context.infrastructure_preferences == "No preference"
        assert context.existing_codebase is False
        assert context.nice_to_have_features == []
        assert context.out_of_scope == []
        assert context.similar_products == []
        assert context.notes == ""

    def test_context_missing_required_field(self):
        """Test that missing required fields raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            ProjectContext(
                project_name="Test",
                # Missing: vision, problem_statement, target_users, etc.
            )

        errors = exc_info.value.errors()
        missing_fields = {e["loc"][0] for e in errors}
        assert "vision" in missing_fields
        assert "problem_statement" in missing_fields
        assert "target_users" in missing_fields

    def test_context_serialization(self):
        """Test ProjectContext serialization round-trip."""
        original = ProjectContext(
            project_name="Serialization Test",
            vision="Test serialization",
            problem_statement="Need to verify JSON works",
            target_users=["qa team"],
            timeline="2 weeks",
            team_size=2,
            developer_experience="mid-level",
            budget_constraints="bootstrap",
            tech_stack=["TypeScript", "Node.js"],
            must_have_features=["tests pass"],
            notes="Testing notes",
        )

        # Serialize to JSON
        json_str = original.model_dump_json()

        # Deserialize from JSON
        restored = ProjectContext.model_validate_json(json_str)

        assert restored.project_name == original.project_name
        assert restored.tech_stack == original.tech_stack
        assert restored.notes == original.notes
        assert restored.infrastructure_preferences == "No preference"

    def test_context_field_names_match_question_keys(self):
        """Verify field names match expected Question.key values.

        This is critical because the QuestionConductor builds ProjectContext
        directly from answer dict using field names as keys.
        """
        # Get all field names from the model
        field_names = set(ProjectContext.model_fields.keys())

        # These are the expected question keys from CLAUDE.md
        expected_keys = {
            "project_name",
            "vision",
            "problem_statement",
            "target_users",
            "timeline",
            "team_size",
            "developer_experience",
            "budget_constraints",
            "tech_stack",
            "infrastructure_preferences",
            "existing_codebase",
            "must_have_features",
            "nice_to_have_features",
            "out_of_scope",
            "similar_products",
            "notes",
        }

        assert field_names == expected_keys
