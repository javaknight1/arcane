"""Tests for arcane.utils module."""

import pytest

from arcane.utils import generate_id


class TestGenerateId:
    """Tests for the generate_id function."""

    def test_generate_id_has_prefix(self):
        """Verify generate_id produces an ID starting with the given prefix."""
        result = generate_id("task")
        assert result.startswith("task-")

    def test_generate_id_unique(self):
        """Verify two calls to generate_id produce different IDs."""
        id1 = generate_id("task")
        id2 = generate_id("task")
        assert id1 != id2

    def test_generate_id_various_prefixes(self):
        """Test generate_id with various prefix types used in the project."""
        prefixes = ["milestone", "epic", "story", "task", "roadmap"]

        for prefix in prefixes:
            result = generate_id(prefix)
            assert result.startswith(f"{prefix}-"), f"ID should start with '{prefix}-'"
            # Verify ULID part exists (26 characters after prefix and hyphen)
            ulid_part = result[len(prefix) + 1 :]
            assert len(ulid_part) == 26, f"ULID part should be 26 characters, got {len(ulid_part)}"

    def test_generate_id_format(self):
        """Verify the ID format is prefix-ULID."""
        result = generate_id("epic")
        parts = result.split("-", 1)
        assert len(parts) == 2
        assert parts[0] == "epic"
        # ULID is 26 characters
        assert len(parts[1]) == 26
