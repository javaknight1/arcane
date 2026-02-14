"""Tests for arcane.cli helper functions."""

import pytest
import typer

from arcane.cli import _split_csv, _build_prefilled


class TestSplitCsv:
    """Tests for the _split_csv helper."""

    def test_split_csv_basic(self):
        """Split a basic comma-separated string."""
        assert _split_csv("a, b, c") == ["a", "b", "c"]

    def test_split_csv_none(self):
        """None input returns None."""
        assert _split_csv(None) is None

    def test_split_csv_empty_string(self):
        """Empty string returns empty list."""
        assert _split_csv("") == []

    def test_split_csv_single_item(self):
        """Single item without commas."""
        assert _split_csv("hello") == ["hello"]

    def test_split_csv_strips_whitespace(self):
        """Whitespace around items is stripped."""
        assert _split_csv("  foo ,  bar  , baz  ") == ["foo", "bar", "baz"]

    def test_split_csv_filters_empty_items(self):
        """Empty items from consecutive commas are filtered."""
        assert _split_csv("a,,b,,,c") == ["a", "b", "c"]


class TestBuildPrefilled:
    """Tests for the _build_prefilled helper."""

    def test_build_prefilled_skips_none(self):
        """None values are excluded from the result."""
        result = _build_prefilled(project_name="Test")
        assert result == {"project_name": "Test"}
        assert "vision" not in result
        assert "timeline" not in result

    def test_build_prefilled_valid_choices(self):
        """Valid choice values pass validation."""
        result = _build_prefilled(
            timeline="3 months",
            developer_experience="senior",
            budget_constraints="moderate",
            infrastructure_preferences="AWS",
        )
        assert result["timeline"] == "3 months"
        assert result["developer_experience"] == "senior"
        assert result["budget_constraints"] == "moderate"
        assert result["infrastructure_preferences"] == "AWS"

    def test_build_prefilled_invalid_timeline(self):
        """Invalid timeline value raises BadParameter."""
        with pytest.raises(typer.BadParameter, match="Invalid value.*timeline"):
            _build_prefilled(timeline="2 weeks")

    def test_build_prefilled_invalid_experience(self):
        """Invalid experience value raises BadParameter."""
        with pytest.raises(typer.BadParameter, match="Invalid value.*experience"):
            _build_prefilled(developer_experience="expert")

    def test_build_prefilled_invalid_budget(self):
        """Invalid budget value raises BadParameter."""
        with pytest.raises(typer.BadParameter, match="Invalid value.*budget"):
            _build_prefilled(budget_constraints="unlimited")

    def test_build_prefilled_invalid_infra(self):
        """Invalid infrastructure value raises BadParameter."""
        with pytest.raises(typer.BadParameter, match="Invalid value.*infra"):
            _build_prefilled(infrastructure_preferences="DigitalOcean")

    def test_build_prefilled_invalid_team_size_zero(self):
        """Team size of 0 raises BadParameter."""
        with pytest.raises(typer.BadParameter, match="Team size must be between"):
            _build_prefilled(team_size=0)

    def test_build_prefilled_invalid_team_size_too_large(self):
        """Team size over 100 raises BadParameter."""
        with pytest.raises(typer.BadParameter, match="Team size must be between"):
            _build_prefilled(team_size=101)

    def test_build_prefilled_valid_team_size_boundaries(self):
        """Team size at boundaries (1 and 100) passes."""
        result = _build_prefilled(team_size=1)
        assert result["team_size"] == 1

        result = _build_prefilled(team_size=100)
        assert result["team_size"] == 100

    def test_build_prefilled_all_fields(self):
        """All 16 fields provided results in all 16 in the output."""
        result = _build_prefilled(
            project_name="Test Project",
            vision="A test vision",
            problem_statement="A test problem",
            target_users=["devs", "managers"],
            timeline="3 months",
            team_size=3,
            developer_experience="senior",
            budget_constraints="moderate",
            tech_stack=["Python", "React"],
            infrastructure_preferences="AWS",
            existing_codebase=False,
            must_have_features=["auth", "api"],
            nice_to_have_features=["dark mode"],
            out_of_scope=["mobile app"],
            similar_products=["competitor"],
            notes="Some notes",
        )
        assert len(result) == 16
        assert result["project_name"] == "Test Project"
        assert result["vision"] == "A test vision"
        assert result["problem_statement"] == "A test problem"
        assert result["target_users"] == ["devs", "managers"]
        assert result["timeline"] == "3 months"
        assert result["team_size"] == 3
        assert result["developer_experience"] == "senior"
        assert result["budget_constraints"] == "moderate"
        assert result["tech_stack"] == ["Python", "React"]
        assert result["infrastructure_preferences"] == "AWS"
        assert result["existing_codebase"] is False
        assert result["must_have_features"] == ["auth", "api"]
        assert result["nice_to_have_features"] == ["dark mode"]
        assert result["out_of_scope"] == ["mobile app"]
        assert result["similar_products"] == ["competitor"]
        assert result["notes"] == "Some notes"

    def test_build_prefilled_boolean_true(self):
        """Boolean True value is preserved."""
        result = _build_prefilled(existing_codebase=True)
        assert result["existing_codebase"] is True

    def test_build_prefilled_empty_lists(self):
        """Empty lists are included (not treated as None)."""
        result = _build_prefilled(tech_stack=[])
        assert result["tech_stack"] == []
