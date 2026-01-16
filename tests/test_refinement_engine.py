"""Tests for incremental refinement engine."""

import pytest
from unittest.mock import MagicMock
from datetime import datetime

from arcane.engines.generation.refinement_engine import (
    RefinementEngine,
    RefinementRecord,
)


class MockItem:
    """Mock item for testing."""
    def __init__(self, id, name, item_type, description="", content=None):
        self.id = id
        self.name = name
        self.item_type = item_type
        self.description = description
        self.content = content
        self.children = []
        self.parent = None
        self.technical_requirements = ""
        self.benefits = ""
        self.updated_at = datetime.now()

    def get_path(self):
        if self.parent:
            return f"{self.parent.get_path()} > {self.name}"
        return self.name


class TestRefinementRecord:
    """Tests for RefinementRecord dataclass."""

    def test_creation(self):
        """Test creating a refinement record."""
        record = RefinementRecord(
            item_id="1.0.1",
            version=1,
            content_before="Original content",
            content_after="Refined content",
            user_feedback="Make it more detailed"
        )

        assert record.item_id == "1.0.1"
        assert record.version == 1
        assert record.content_before == "Original content"
        assert record.content_after == "Refined content"
        assert record.user_feedback == "Make it more detailed"
        assert record.timestamp is not None

    def test_to_dict(self):
        """Test serialization to dictionary."""
        record = RefinementRecord(
            item_id="1.0.1",
            version=2,
            content_before="Before",
            content_after="After",
            user_feedback="Feedback",
            metadata={'key': 'value'}
        )

        result = record.to_dict()

        assert result['item_id'] == "1.0.1"
        assert result['version'] == 2
        assert result['content_before'] == "Before"
        assert result['content_after'] == "After"
        assert result['user_feedback'] == "Feedback"
        assert result['metadata'] == {'key': 'value'}
        assert 'timestamp' in result

    def test_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            'item_id': "1.0.1",
            'version': 1,
            'content_before': "Before",
            'content_after': "After",
            'user_feedback': "Feedback",
            'timestamp': "2024-01-15T10:30:00",
            'metadata': {'test': True}
        }

        record = RefinementRecord.from_dict(data)

        assert record.item_id == "1.0.1"
        assert record.version == 1
        assert record.user_feedback == "Feedback"
        assert record.metadata == {'test': True}


class TestRefinementEngineInit:
    """Tests for RefinementEngine initialization."""

    def test_init(self):
        """Test initializing the refinement engine."""
        mock_client = MagicMock()
        engine = RefinementEngine(mock_client)

        assert engine.llm_client is mock_client
        assert engine.history == {}
        assert engine._item_cache == {}


class TestRefineItem:
    """Tests for refine_item method."""

    @pytest.fixture
    def mock_llm_client(self):
        """Create a mock LLM client."""
        client = MagicMock()
        client.generate.return_value = "Refined content based on feedback"
        return client

    def test_refine_item_with_content(self, mock_llm_client):
        """Test refining an item with existing content."""
        engine = RefinementEngine(mock_llm_client)

        item = MockItem("1.0.1", "User Login", "Story", content="Original content here")
        result = engine.refine_item(item, "Make it more detailed", "Project context")

        assert result == "Refined content based on feedback"
        assert mock_llm_client.generate.called
        assert item.id in engine.history
        assert len(engine.history[item.id]) == 1

    def test_refine_item_with_description_only(self, mock_llm_client):
        """Test refining an item that only has description."""
        engine = RefinementEngine(mock_llm_client)

        item = MockItem("1.0.1", "User Login", "Story", description="Login functionality")
        result = engine.refine_item(item, "Add more acceptance criteria")

        assert result == "Refined content based on feedback"
        assert item.id in engine.history

    def test_refine_item_no_content_raises(self, mock_llm_client):
        """Test that refining item with no content raises error."""
        engine = RefinementEngine(mock_llm_client)

        item = MockItem("1.0.1", "Empty Story", "Story")
        item.description = ""

        with pytest.raises(ValueError, match="has no content to refine"):
            engine.refine_item(item, "Some feedback")

    def test_refine_item_increments_version(self, mock_llm_client):
        """Test that multiple refinements increment version."""
        mock_llm_client.generate.side_effect = ["V1", "V2", "V3"]
        engine = RefinementEngine(mock_llm_client)

        item = MockItem("1.0.1", "Story", "Story", content="Original")

        engine.refine_item(item, "Feedback 1")
        engine.refine_item(item, "Feedback 2")
        engine.refine_item(item, "Feedback 3")

        assert len(engine.history[item.id]) == 3
        assert engine.history[item.id][0].version == 1
        assert engine.history[item.id][1].version == 2
        assert engine.history[item.id][2].version == 3

    def test_refine_item_applies_content(self, mock_llm_client):
        """Test that refined content is applied to item."""
        mock_llm_client.generate.return_value = "New refined content"
        engine = RefinementEngine(mock_llm_client)

        item = MockItem("1.0.1", "Story", "Story", content="Original")
        engine.refine_item(item, "Refine please")

        assert item.content == "New refined content"

    def test_refine_item_no_apply(self, mock_llm_client):
        """Test refining without applying changes."""
        mock_llm_client.generate.return_value = "New content"
        engine = RefinementEngine(mock_llm_client)

        item = MockItem("1.0.1", "Story", "Story", content="Original")
        result = engine.refine_item(item, "Feedback", apply_immediately=False)

        assert result == "New content"
        assert item.content == "Original"  # Not changed


class TestRefineSection:
    """Tests for refine_section method."""

    @pytest.fixture
    def mock_llm_client(self):
        """Create a mock LLM client."""
        client = MagicMock()
        client.generate.return_value = "Refined section content"
        return client

    def test_refine_section(self, mock_llm_client):
        """Test refining a specific section."""
        engine = RefinementEngine(mock_llm_client)

        item = MockItem("1.0.1", "Story", "Story", content="Full content here")
        result = engine.refine_section(
            item,
            "description",
            "Current description",
            "Make it clearer"
        )

        assert result == "Refined section content"
        assert mock_llm_client.generate.called

    def test_refine_section_records_metadata(self, mock_llm_client):
        """Test that section refinement records section name."""
        engine = RefinementEngine(mock_llm_client)

        item = MockItem("1.0.1", "Story", "Story", content="Content")
        engine.refine_section(item, "acceptance_criteria", "AC list", "Add more")

        record = engine.history[item.id][0]
        assert record.metadata['section_name'] == "acceptance_criteria"
        assert record.metadata['targeted_refinement'] is True


class TestRevertToVersion:
    """Tests for revert_to_version method."""

    @pytest.fixture
    def engine_with_history(self):
        """Create engine with pre-populated history."""
        mock_client = MagicMock()
        mock_client.generate.side_effect = ["V1 content", "V2 content", "V3 content"]
        engine = RefinementEngine(mock_client)

        item = MockItem("1.0.1", "Story", "Story", content="Original content")
        engine.refine_item(item, "Feedback 1")
        engine.refine_item(item, "Feedback 2")
        engine.refine_item(item, "Feedback 3")

        return engine, item

    def test_revert_to_original(self, engine_with_history):
        """Test reverting to original version (version 0)."""
        engine, item = engine_with_history

        content = engine.revert_to_version(item.id, 0)

        assert content == "Original content"
        assert item.content == "Original content"

    def test_revert_to_version_1(self, engine_with_history):
        """Test reverting to version 1."""
        engine, item = engine_with_history

        content = engine.revert_to_version(item.id, 1)

        assert content == "V1 content"
        assert item.content == "V1 content"

    def test_revert_to_version_2(self, engine_with_history):
        """Test reverting to version 2."""
        engine, item = engine_with_history

        content = engine.revert_to_version(item.id, 2)

        assert content == "V2 content"

    def test_revert_no_history_raises(self):
        """Test that reverting item without history raises error."""
        engine = RefinementEngine(MagicMock())

        with pytest.raises(ValueError, match="No refinement history"):
            engine.revert_to_version("nonexistent", 1)

    def test_revert_invalid_version_raises(self, engine_with_history):
        """Test that invalid version number raises error."""
        engine, item = engine_with_history

        with pytest.raises(ValueError, match="Invalid version"):
            engine.revert_to_version(item.id, 10)

        with pytest.raises(ValueError, match="Invalid version"):
            engine.revert_to_version(item.id, -1)


class TestGetVersion:
    """Tests for get_version method."""

    def test_get_version_returns_content(self):
        """Test getting specific version content."""
        mock_client = MagicMock()
        mock_client.generate.side_effect = ["V1", "V2"]
        engine = RefinementEngine(mock_client)

        item = MockItem("1.0.1", "Story", "Story", content="Original")
        engine.refine_item(item, "F1")
        engine.refine_item(item, "F2")

        assert engine.get_version(item.id, 0) == "Original"
        assert engine.get_version(item.id, 1) == "V1"
        assert engine.get_version(item.id, 2) == "V2"

    def test_get_version_no_history(self):
        """Test getting version when no history exists."""
        engine = RefinementEngine(MagicMock())

        assert engine.get_version("nonexistent", 0) is None

    def test_get_version_invalid(self):
        """Test getting invalid version returns None."""
        mock_client = MagicMock()
        mock_client.generate.return_value = "V1"
        engine = RefinementEngine(mock_client)

        item = MockItem("1.0.1", "Story", "Story", content="Original")
        engine.refine_item(item, "Feedback")

        assert engine.get_version(item.id, 10) is None


class TestCompareVersions:
    """Tests for compare_versions method."""

    def test_compare_versions(self):
        """Test comparing all versions."""
        mock_client = MagicMock()
        mock_client.generate.side_effect = ["Short", "Longer content here"]
        engine = RefinementEngine(mock_client)

        item = MockItem("1.0.1", "Story", "Story", content="Original content")
        engine.refine_item(item, "Make it shorter")
        engine.refine_item(item, "Make it longer")

        comparison = engine.compare_versions(item.id)

        assert comparison['item_id'] == "1.0.1"
        assert comparison['total_versions'] == 2
        assert len(comparison['versions']) == 2
        assert comparison['versions'][0]['version'] == 1
        assert comparison['versions'][1]['version'] == 2

    def test_compare_versions_no_history(self):
        """Test comparing when no history exists."""
        engine = RefinementEngine(MagicMock())

        assert engine.compare_versions("nonexistent") is None


class TestGetVersionDiff:
    """Tests for get_version_diff method."""

    def test_get_version_diff(self):
        """Test getting diff between versions."""
        mock_client = MagicMock()
        mock_client.generate.side_effect = ["Short", "Much longer content\nWith multiple lines"]
        engine = RefinementEngine(mock_client)

        item = MockItem("1.0.1", "Story", "Story", content="Original")
        engine.refine_item(item, "F1")
        engine.refine_item(item, "F2")

        diff = engine.get_version_diff(item.id, 1, 2)

        assert diff['item_id'] == item.id
        assert diff['version1'] == 1
        assert diff['version2'] == 2
        assert 'length_change' in diff
        assert 'line_change' in diff

    def test_get_version_diff_invalid_raises(self):
        """Test that invalid version numbers raise error."""
        engine = RefinementEngine(MagicMock())

        with pytest.raises(ValueError):
            engine.get_version_diff("item", 1, 2)


class TestHistoryManagement:
    """Tests for history management methods."""

    @pytest.fixture
    def engine_with_data(self):
        """Create engine with test data."""
        mock_client = MagicMock()
        mock_client.generate.side_effect = ["R1", "R2", "R3", "R4"]
        engine = RefinementEngine(mock_client)

        item1 = MockItem("1.0.1", "Story 1", "Story", content="Content 1")
        item2 = MockItem("1.0.2", "Story 2", "Story", content="Content 2")

        engine.refine_item(item1, "F1")
        engine.refine_item(item1, "F2")
        engine.refine_item(item2, "F3")
        engine.refine_item(item2, "F4")

        return engine

    def test_get_history(self, engine_with_data):
        """Test getting history for an item."""
        history = engine_with_data.get_history("1.0.1")

        assert len(history) == 2
        assert history[0].user_feedback == "F1"
        assert history[1].user_feedback == "F2"

    def test_get_history_returns_copy(self, engine_with_data):
        """Test that get_history returns a copy."""
        history = engine_with_data.get_history("1.0.1")
        history.clear()

        # Original should be unchanged
        assert len(engine_with_data.history["1.0.1"]) == 2

    def test_get_feedback_summary(self, engine_with_data):
        """Test getting feedback summary."""
        feedback = engine_with_data.get_feedback_summary("1.0.1")

        assert feedback == ["F1", "F2"]

    def test_get_current_version(self, engine_with_data):
        """Test getting current version number."""
        assert engine_with_data.get_current_version("1.0.1") == 2
        assert engine_with_data.get_current_version("1.0.2") == 2
        assert engine_with_data.get_current_version("nonexistent") == 0

    def test_clear_history_single(self, engine_with_data):
        """Test clearing history for single item."""
        cleared = engine_with_data.clear_history("1.0.1")

        assert cleared == 1
        assert "1.0.1" not in engine_with_data.history
        assert "1.0.2" in engine_with_data.history

    def test_clear_history_all(self, engine_with_data):
        """Test clearing all history."""
        cleared = engine_with_data.clear_history()

        assert cleared == 2
        assert engine_with_data.history == {}

    def test_get_summary(self, engine_with_data):
        """Test getting summary statistics."""
        summary = engine_with_data.get_summary()

        assert summary['total_refinements'] == 4
        assert summary['items_refined'] == 2
        assert summary['average_refinements_per_item'] == 2.0
        assert summary['most_refined_count'] == 2


class TestExportImport:
    """Tests for export and import functionality."""

    @pytest.fixture
    def engine_with_data(self):
        """Create engine with test data."""
        mock_client = MagicMock()
        mock_client.generate.return_value = "Refined"
        engine = RefinementEngine(mock_client)

        item = MockItem("1.0.1", "Story", "Story", content="Original")
        engine.refine_item(item, "Feedback")

        return engine

    def test_export_history(self, engine_with_data, tmp_path):
        """Test exporting history to file."""
        import json

        filepath = tmp_path / "history.json"
        engine_with_data.export_history(str(filepath))

        assert filepath.exists()

        with open(filepath) as f:
            data = json.load(f)

        assert 'exported_at' in data
        assert '1.0.1' in data['items']
        assert len(data['items']['1.0.1']) == 1

    def test_export_creates_directories(self, engine_with_data, tmp_path):
        """Test that export creates parent directories."""
        filepath = tmp_path / "nested" / "deep" / "history.json"
        engine_with_data.export_history(str(filepath))

        assert filepath.exists()

    def test_import_history(self, tmp_path):
        """Test importing history from file."""
        import json

        # Create test file
        data = {
            'exported_at': '2024-01-15T10:00:00',
            'items': {
                '1.0.1': [{
                    'item_id': '1.0.1',
                    'version': 1,
                    'content_before': 'Before',
                    'content_after': 'After',
                    'user_feedback': 'Feedback',
                    'timestamp': '2024-01-15T10:30:00',
                    'metadata': {}
                }]
            }
        }

        filepath = tmp_path / "history.json"
        with open(filepath, 'w') as f:
            json.dump(data, f)

        # Import
        engine = RefinementEngine(MagicMock())
        count = engine.import_history(str(filepath))

        assert count == 1
        assert '1.0.1' in engine.history
        assert engine.history['1.0.1'][0].user_feedback == 'Feedback'


class TestHelperMethods:
    """Tests for helper methods."""

    def test_serialize_item_content(self):
        """Test serializing item content."""
        engine = RefinementEngine(MagicMock())

        item = MockItem("1.0.1", "User Login", "Story")
        item.description = "Allow users to login"
        item.technical_requirements = "Use OAuth2"
        item.benefits = "Improved security"

        content = engine._serialize_item_content(item)

        assert "# Story: User Login" in content
        assert "## Description" in content
        assert "Allow users to login" in content
        assert "## Technical Requirements" in content
        assert "## Benefits" in content

    def test_serialize_item_with_acceptance_criteria(self):
        """Test serializing item with acceptance criteria."""
        engine = RefinementEngine(MagicMock())

        item = MockItem("1.0.1", "Story", "Story")
        item.description = "Description"
        item.acceptance_criteria = ["AC1", "AC2", "AC3"]

        content = engine._serialize_item_content(item)

        assert "## Acceptance Criteria" in content
        assert "AC1:" in content
        assert "AC2:" in content

    def test_build_default_context(self):
        """Test building default context."""
        engine = RefinementEngine(MagicMock())

        parent = MockItem("1.0", "Epic", "Epic")
        item = MockItem("1.0.1", "Story", "Story")
        item.parent = parent
        child = MockItem("1.0.1.1", "Task", "Task")
        item.children = [child]

        context = engine._build_default_context(item)

        assert "Item path:" in context
        assert "Parent:" in context
        assert "Children:" in context


class TestIntegration:
    """Integration tests for refinement engine."""

    def test_full_refinement_workflow(self):
        """Test complete refinement workflow."""
        mock_client = MagicMock()
        mock_client.generate.side_effect = [
            "First refinement",
            "Second refinement",
            "Third refinement"
        ]
        engine = RefinementEngine(mock_client)

        # Create item
        item = MockItem("1.0.1", "User Authentication", "Story")
        item.content = "Original: Basic auth story"

        # First refinement
        v1 = engine.refine_item(item, "Add more detail about OAuth")
        assert v1 == "First refinement"
        assert engine.get_current_version(item.id) == 1

        # Second refinement
        v2 = engine.refine_item(item, "Include error handling scenarios")
        assert v2 == "Second refinement"
        assert engine.get_current_version(item.id) == 2

        # Third refinement
        v3 = engine.refine_item(item, "Add acceptance criteria")
        assert v3 == "Third refinement"
        assert engine.get_current_version(item.id) == 3

        # Check history
        history = engine.get_history(item.id)
        assert len(history) == 3

        # Revert to version 1
        engine.revert_to_version(item.id, 1)
        assert item.content == "First refinement"

        # Get comparison
        comparison = engine.compare_versions(item.id)
        assert comparison['total_versions'] == 3

        # Get summary
        summary = engine.get_summary()
        assert summary['total_refinements'] == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
