"""Tests for refine CLI command."""

import pytest
import json
import tempfile
import argparse
from unittest.mock import MagicMock, patch
from pathlib import Path

from arcane.commands.refine import RefineCommand, MockRefinementItem, create_refine_command


class TestMockRefinementItem:
    """Tests for MockRefinementItem class."""

    def test_creation(self):
        """Test creating a mock item."""
        item = MockRefinementItem(
            item_id="1.0.1",
            name="Test Item",
            item_type="Story",
            content="Test content"
        )

        assert item.id == "1.0.1"
        assert item.name == "Test Item"
        assert item.item_type == "Story"
        assert item.content == "Test content"
        assert item.description == "Test content"

    def test_get_path(self):
        """Test get_path method."""
        item = MockRefinementItem(
            item_id="1.0.1",
            name="Test Item",
            item_type="Story",
            content="Content"
        )

        assert item.get_path() == "Test Item"

    def test_default_attributes(self):
        """Test default attribute values."""
        item = MockRefinementItem("1", "Name", "Type", "Content")

        assert item.children == []
        assert item.parent is None
        assert item.technical_requirements == ""
        assert item.benefits == ""


class TestRefineCommandInit:
    """Tests for RefineCommand initialization."""

    def test_init(self):
        """Test initializing the command."""
        cmd = RefineCommand()

        assert cmd.engine is None
        assert cmd.roadmap_data is None
        assert cmd.items_by_id == {}
        assert cmd.modified is False

    def test_create_refine_command(self):
        """Test factory function."""
        cmd = create_refine_command()

        assert isinstance(cmd, RefineCommand)


class TestRefineCommandLoadRoadmap:
    """Tests for roadmap loading."""

    def test_load_valid_roadmap(self):
        """Test loading a valid roadmap file."""
        cmd = RefineCommand()

        roadmap_data = {
            "milestones": [
                {
                    "id": "1",
                    "name": "Milestone 1",
                    "epics": [
                        {
                            "id": "1.0",
                            "name": "Epic 1",
                            "stories": [
                                {
                                    "id": "1.0.1",
                                    "name": "Story 1",
                                    "content": "Story content",
                                    "tasks": [
                                        {
                                            "id": "1.0.1.1",
                                            "name": "Task 1",
                                            "content": "Task content"
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(roadmap_data, f)
            filepath = f.name

        try:
            result = cmd._load_roadmap(filepath)

            assert result is True
            assert cmd.roadmap_data is not None
            assert len(cmd.items_by_id) == 4  # 1 milestone, 1 epic, 1 story, 1 task
            assert "1" in cmd.items_by_id
            assert "1.0" in cmd.items_by_id
            assert "1.0.1" in cmd.items_by_id
            assert "1.0.1.1" in cmd.items_by_id
        finally:
            Path(filepath).unlink()

    def test_load_nonexistent_file(self):
        """Test loading a nonexistent file."""
        cmd = RefineCommand()

        result = cmd._load_roadmap("/nonexistent/path.json")

        assert result is False

    def test_load_empty_roadmap(self):
        """Test loading an empty roadmap."""
        cmd = RefineCommand()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"milestones": []}, f)
            filepath = f.name

        try:
            result = cmd._load_roadmap(filepath)

            assert result is True
            assert cmd.items_by_id == {}
        finally:
            Path(filepath).unlink()


class TestRefineCommandSaveRoadmap:
    """Tests for roadmap saving."""

    def test_save_roadmap(self):
        """Test saving a roadmap file."""
        cmd = RefineCommand()
        cmd.roadmap_data = {"milestones": [], "name": "Test"}

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "output.json"
            cmd._save_roadmap(str(filepath))

            assert filepath.exists()
            with open(filepath) as f:
                saved_data = json.load(f)
            assert "last_modified" in saved_data
            assert saved_data["name"] == "Test"

    def test_save_creates_parent_dirs(self):
        """Test that save creates parent directories."""
        cmd = RefineCommand()
        cmd.roadmap_data = {"milestones": []}

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "nested" / "dir" / "output.json"
            cmd._save_roadmap(str(filepath))

            assert filepath.exists()


class TestRefineCommandItemLookup:
    """Tests for item lookup functionality."""

    def test_build_item_lookup(self):
        """Test building item lookup from nested structure."""
        cmd = RefineCommand()

        data = {
            "milestones": [
                {
                    "id": "M1",
                    "name": "Milestone",
                    "epics": [
                        {
                            "id": "E1",
                            "name": "Epic",
                            "stories": [
                                {
                                    "id": "S1",
                                    "name": "Story",
                                    "tasks": [
                                        {"id": "T1", "name": "Task"}
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ]
        }

        cmd._build_item_lookup(data)

        assert "M1" in cmd.items_by_id
        assert "E1" in cmd.items_by_id
        assert "S1" in cmd.items_by_id
        assert "T1" in cmd.items_by_id

    def test_build_lookup_multiple_milestones(self):
        """Test building lookup with multiple milestones."""
        cmd = RefineCommand()

        data = {
            "milestones": [
                {"id": "M1", "name": "M1", "epics": []},
                {"id": "M2", "name": "M2", "epics": []},
            ]
        }

        cmd._build_item_lookup(data)

        assert "M1" in cmd.items_by_id
        assert "M2" in cmd.items_by_id


class TestRefineCommandGetItemType:
    """Tests for item type detection."""

    def test_milestone_type(self):
        """Test detecting milestone type."""
        cmd = RefineCommand()

        assert cmd._get_item_type("1") == "Milestone"

    def test_epic_type(self):
        """Test detecting epic type."""
        cmd = RefineCommand()

        assert cmd._get_item_type("1.0") == "Epic"

    def test_story_type(self):
        """Test detecting story type."""
        cmd = RefineCommand()

        assert cmd._get_item_type("1.0.1") == "Story"

    def test_task_type(self):
        """Test detecting task type."""
        cmd = RefineCommand()

        assert cmd._get_item_type("1.0.1.1") == "Task"

    def test_unknown_type(self):
        """Test detecting unknown type."""
        cmd = RefineCommand()

        assert cmd._get_item_type("1.0.1.1.1") == "Item"


class TestRefineCommandVersionIndicator:
    """Tests for version indicator display."""

    def test_no_history(self):
        """Test version indicator with no history."""
        cmd = RefineCommand()
        cmd.engine = MagicMock()
        cmd.engine.history = {}

        result = cmd._get_version_indicator("1.0.1")

        assert result == ""

    def test_with_history(self):
        """Test version indicator with history."""
        cmd = RefineCommand()
        cmd.engine = MagicMock()
        cmd.engine.history = {"1.0.1": [MagicMock(), MagicMock()]}

        result = cmd._get_version_indicator("1.0.1")

        assert "(v2)" in result


class TestRefineCommandExecute:
    """Tests for command execution."""

    @patch('arcane.commands.refine.LLMClientFactory')
    def test_execute_file_not_found(self, mock_factory):
        """Test execute with nonexistent file."""
        cmd = RefineCommand()
        args = argparse.Namespace(
            roadmap_file="/nonexistent.json",
            item=None,
            interactive=False,
            feedback=None,
            revert=None,
            history=False,
            compare=False,
            provider='claude',
            output=None,
            history_file=None,
            dry_run=False
        )

        result = cmd.execute(args)

        assert result == 1

    @patch('arcane.commands.refine.LLMClientFactory')
    @patch('arcane.commands.refine.Confirm')
    def test_execute_with_history_flag(self, mock_confirm, mock_factory):
        """Test execute with history flag."""
        cmd = RefineCommand()
        mock_factory.create.return_value = MagicMock()

        roadmap_data = {"milestones": []}
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(roadmap_data, f)
            filepath = f.name

        try:
            args = argparse.Namespace(
                roadmap_file=filepath,
                item=None,
                interactive=False,
                feedback=None,
                revert=None,
                history=True,
                compare=False,
                provider='claude',
                output=None,
                history_file=None,
                dry_run=False
            )

            result = cmd.execute(args)

            assert result == 0
        finally:
            Path(filepath).unlink()

    @patch('arcane.commands.refine.LLMClientFactory')
    @patch('arcane.commands.refine.Confirm')
    def test_execute_dry_run(self, mock_confirm, mock_factory):
        """Test execute with dry run flag."""
        cmd = RefineCommand()
        mock_factory.create.return_value = MagicMock()

        roadmap_data = {"milestones": []}
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(roadmap_data, f)
            filepath = f.name

        try:
            args = argparse.Namespace(
                roadmap_file=filepath,
                item=None,
                interactive=False,
                feedback=None,
                revert=None,
                history=True,
                compare=False,
                provider='claude',
                output=None,
                history_file=None,
                dry_run=True
            )

            cmd.modified = True
            result = cmd.execute(args)

            assert result == 0
            # Confirm should not be called in dry run
            mock_confirm.ask.assert_not_called()
        finally:
            Path(filepath).unlink()


class TestRefineCommandViewItem:
    """Tests for viewing item details."""

    def test_view_nonexistent_item(self):
        """Test viewing a nonexistent item."""
        cmd = RefineCommand()
        cmd.items_by_id = {}

        # Should not raise
        cmd._view_item("nonexistent")

    def test_view_existing_item(self):
        """Test viewing an existing item."""
        cmd = RefineCommand()
        cmd.items_by_id = {
            "1.0.1": {
                "name": "Test Story",
                "content": "Test content",
                "status": "pending"
            }
        }

        # Should not raise
        cmd._view_item("1.0.1")


class TestRefineCommandRevertItem:
    """Tests for reverting items."""

    def test_revert_nonexistent_item(self):
        """Test reverting a nonexistent item."""
        cmd = RefineCommand()
        cmd.items_by_id = {}
        cmd.engine = MagicMock()

        # Should not raise
        cmd._revert_item("nonexistent", 0)

    def test_revert_existing_item(self):
        """Test reverting an existing item."""
        cmd = RefineCommand()
        cmd.items_by_id = {"1.0.1": {"content": "current"}}
        cmd.engine = MagicMock()
        cmd.engine.revert_to_version.return_value = "reverted content"

        cmd._revert_item("1.0.1", 0)

        assert cmd.items_by_id["1.0.1"]["content"] == "reverted content"
        assert cmd.modified is True

    def test_revert_with_invalid_version(self):
        """Test reverting with invalid version."""
        cmd = RefineCommand()
        cmd.items_by_id = {"1.0.1": {"content": "current"}}
        cmd.engine = MagicMock()
        cmd.engine.revert_to_version.side_effect = ValueError("Invalid version")

        # Should not raise
        cmd._revert_item("1.0.1", 99)


class TestRefineCommandCompareVersions:
    """Tests for comparing versions."""

    def test_compare_no_history(self):
        """Test comparing with no history."""
        cmd = RefineCommand()
        cmd.engine = MagicMock()
        cmd.engine.compare_versions.return_value = None

        # Should not raise
        cmd._compare_versions("1.0.1")

    def test_compare_with_history(self):
        """Test comparing with history."""
        cmd = RefineCommand()
        cmd.engine = MagicMock()
        cmd.engine.compare_versions.return_value = {
            'item_id': '1.0.1',
            'total_versions': 2,
            'versions': [
                {'version': 1, 'feedback': 'Feedback 1', 'timestamp': '2024-01-15T10:00:00', 'content_length_after': 100}
            ],
            'original_length': 50,
            'current_length': 100
        }

        # Should not raise
        cmd._compare_versions("1.0.1")


class TestRefineCommandShowHistory:
    """Tests for showing history."""

    def test_show_empty_history(self):
        """Test showing empty history."""
        cmd = RefineCommand()
        cmd.engine = MagicMock()
        cmd.engine.get_summary.return_value = {'total_refinements': 0}

        # Should not raise
        cmd._show_all_history()

    @patch('arcane.commands.refine.Confirm')
    def test_show_history_with_items(self, mock_confirm):
        """Test showing history with items."""
        mock_confirm.ask.return_value = False
        cmd = RefineCommand()
        cmd.engine = MagicMock()
        cmd.engine.get_summary.return_value = {
            'total_refinements': 5,
            'items_refined': 2,
            'average_refinements_per_item': 2.5,
            'most_refined_item': '1.0.1',
            'most_refined_count': 3
        }
        cmd.engine.history = {}

        # Should not raise
        cmd._show_all_history()


class TestRefineCommandShowSummary:
    """Tests for showing summary."""

    def test_show_summary(self):
        """Test showing summary."""
        cmd = RefineCommand()
        cmd.engine = MagicMock()
        cmd.engine.get_summary.return_value = {
            'total_refinements': 10,
            'items_refined': 5,
            'average_refinements_per_item': 2.0,
            'most_refined_item': '1.0.1',
            'most_refined_count': 4
        }

        # Should not raise
        cmd._show_summary()

    def test_show_summary_no_refinements(self):
        """Test showing summary with no refinements."""
        cmd = RefineCommand()
        cmd.engine = MagicMock()
        cmd.engine.get_summary.return_value = {
            'total_refinements': 0,
            'items_refined': 0,
            'average_refinements_per_item': 0,
            'most_refined_item': None,
            'most_refined_count': 0
        }

        # Should not raise
        cmd._show_summary()


class TestRefineCommandRefineSingleItem:
    """Tests for refining a single item."""

    def test_refine_nonexistent_item(self):
        """Test refining nonexistent item."""
        cmd = RefineCommand()
        cmd.items_by_id = {}

        # Should not raise
        cmd._refine_single_item("nonexistent", "feedback")

    def test_refine_item_no_content(self):
        """Test refining item with no content."""
        cmd = RefineCommand()
        cmd.items_by_id = {"1.0.1": {"name": "Test", "content": "", "description": ""}}

        # Should not raise
        cmd._refine_single_item("1.0.1", "feedback")

    def test_refine_item_with_content(self):
        """Test refining item with content."""
        cmd = RefineCommand()
        cmd.items_by_id = {"1.0.1": {"name": "Test", "content": "Original content"}}
        cmd.engine = MagicMock()
        cmd.engine.refine_item.return_value = "Refined content"

        cmd._refine_single_item("1.0.1", "feedback")

        assert cmd.items_by_id["1.0.1"]["content"] == "Refined content"
        assert cmd.modified is True


class TestRefineCommandHelp:
    """Tests for help display."""

    def test_show_help(self):
        """Test showing help."""
        cmd = RefineCommand()

        # Should not raise
        cmd._show_help()


class TestRefineCommandSetupParser:
    """Tests for argument parser setup."""

    def test_setup_parser(self):
        """Test setting up argument parser."""
        cmd = RefineCommand()
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()

        result = cmd.setup_parser(subparsers)

        assert result is not None

    def test_parser_arguments(self):
        """Test that parser has expected arguments."""
        cmd = RefineCommand()
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()

        refine_parser = cmd.setup_parser(subparsers)

        # Parse with minimum args to verify structure
        args = refine_parser.parse_args(['test.json'])
        assert args.roadmap_file == 'test.json'

    def test_parser_with_all_options(self):
        """Test parser with all options."""
        cmd = RefineCommand()
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()

        refine_parser = cmd.setup_parser(subparsers)

        args = refine_parser.parse_args([
            'test.json',
            '-i', '1.0.1',
            '--feedback', 'Test feedback',
            '--provider', 'openai',
            '--output', 'output.json',
            '--dry-run'
        ])

        assert args.roadmap_file == 'test.json'
        assert args.item == '1.0.1'
        assert args.feedback == 'Test feedback'
        assert args.provider == 'openai'
        assert args.output == 'output.json'
        assert args.dry_run is True
