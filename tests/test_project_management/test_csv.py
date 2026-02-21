"""Tests for arcane.project_management.csv module."""

import csv
from pathlib import Path

import pytest

from arcane.project_management import CSVClient, ExportResult


class TestCSVClient:
    """Tests for CSVClient."""

    def test_name_property(self):
        """CSVClient has correct name."""
        client = CSVClient()
        assert client.name == "CSV"

    @pytest.mark.asyncio
    async def test_validate_credentials_always_true(self):
        """CSV export requires no credentials."""
        client = CSVClient()
        assert await client.validate_credentials() is True

    @pytest.mark.asyncio
    async def test_export_creates_file(self, tmp_path, sample_roadmap):
        """Export creates CSV file at specified path."""
        client = CSVClient()
        output_path = tmp_path / "output.csv"

        result = await client.export(sample_roadmap, output_path=str(output_path))

        assert result.success is True
        assert result.target == "CSV"
        assert output_path.exists()

    @pytest.mark.asyncio
    async def test_export_default_path(self, tmp_path, sample_roadmap, monkeypatch):
        """Export uses default path based on project name."""
        client = CSVClient()
        # Change to tmp directory so default path is created there
        monkeypatch.chdir(tmp_path)

        result = await client.export(sample_roadmap)

        assert result.success is True
        expected_path = tmp_path / "test-project" / "roadmap.csv"
        assert expected_path.exists()

    @pytest.mark.asyncio
    async def test_export_row_count(self, tmp_path, sample_roadmap):
        """Export creates correct number of rows."""
        client = CSVClient()
        output_path = tmp_path / "output.csv"

        result = await client.export(sample_roadmap, output_path=str(output_path))

        # 1 milestone + 1 epic + 1 story + 2 tasks = 5 rows
        assert result.items_created == 5

        # Verify by reading the file
        with open(output_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert len(rows) == 5

    @pytest.mark.asyncio
    async def test_export_hierarchy_preserved(self, tmp_path, sample_roadmap):
        """Export preserves parent-child relationships via Parent_ID."""
        client = CSVClient()
        output_path = tmp_path / "output.csv"

        await client.export(sample_roadmap, output_path=str(output_path))

        with open(output_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = {row["ID"]: row for row in reader}

        # Milestone's parent is roadmap
        assert rows["milestone-001"]["Parent_ID"] == "roadmap-001"
        # Epic's parent is milestone
        assert rows["epic-001"]["Parent_ID"] == "milestone-001"
        # Story's parent is epic
        assert rows["story-001"]["Parent_ID"] == "epic-001"
        # Tasks' parent is story
        assert rows["task-001"]["Parent_ID"] == "story-001"
        assert rows["task-002"]["Parent_ID"] == "story-001"

    @pytest.mark.asyncio
    async def test_export_item_types_correct(self, tmp_path, sample_roadmap):
        """Export includes correct Type for each item."""
        client = CSVClient()
        output_path = tmp_path / "output.csv"

        await client.export(sample_roadmap, output_path=str(output_path))

        with open(output_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = {row["ID"]: row for row in reader}

        assert rows["milestone-001"]["Type"] == "Milestone"
        assert rows["epic-001"]["Type"] == "Epic"
        assert rows["story-001"]["Type"] == "Story"
        assert rows["task-001"]["Type"] == "Task"
        assert rows["task-002"]["Type"] == "Task"

    @pytest.mark.asyncio
    async def test_export_task_has_claude_code_prompt(self, tmp_path, sample_roadmap):
        """Tasks include Claude_Code_Prompt field."""
        client = CSVClient()
        output_path = tmp_path / "output.csv"

        await client.export(sample_roadmap, output_path=str(output_path))

        with open(output_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = {row["ID"]: row for row in reader}

        assert rows["task-001"]["Claude_Code_Prompt"] != ""
        assert "login form" in rows["task-001"]["Claude_Code_Prompt"].lower()

    @pytest.mark.asyncio
    async def test_export_prerequisites_preserved(self, tmp_path, sample_roadmap):
        """Export preserves prerequisite IDs."""
        client = CSVClient()
        output_path = tmp_path / "output.csv"

        await client.export(sample_roadmap, output_path=str(output_path))

        with open(output_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = {row["ID"]: row for row in reader}

        # task-002 has task-001 as prerequisite
        assert "task-001" in rows["task-002"]["Prerequisites"]

    @pytest.mark.asyncio
    async def test_export_acceptance_criteria_joined(self, tmp_path, sample_roadmap):
        """Export joins acceptance criteria with pipe separator."""
        client = CSVClient()
        output_path = tmp_path / "output.csv"

        await client.export(sample_roadmap, output_path=str(output_path))

        with open(output_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = {row["ID"]: row for row in reader}

        # Task criteria joined with |
        assert "|" in rows["task-001"]["Acceptance_Criteria"]
        assert "Form renders" in rows["task-001"]["Acceptance_Criteria"]

    @pytest.mark.asyncio
    async def test_export_estimated_hours(self, tmp_path, sample_roadmap):
        """Export includes estimated hours for all items."""
        client = CSVClient()
        output_path = tmp_path / "output.csv"

        await client.export(sample_roadmap, output_path=str(output_path))

        with open(output_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = {row["ID"]: row for row in reader}

        # Task hours are direct
        assert rows["task-001"]["Estimated_Hours"] == "4"
        assert rows["task-002"]["Estimated_Hours"] == "2"
        # Story hours are sum of tasks
        assert rows["story-001"]["Estimated_Hours"] == "6"
        # Epic hours are sum of stories
        assert rows["epic-001"]["Estimated_Hours"] == "6"
        # Milestone hours are sum of epics
        assert rows["milestone-001"]["Estimated_Hours"] == "6"

    @pytest.mark.asyncio
    async def test_export_result_includes_url(self, tmp_path, sample_roadmap):
        """ExportResult includes absolute path to file."""
        client = CSVClient()
        output_path = tmp_path / "output.csv"

        result = await client.export(sample_roadmap, output_path=str(output_path))

        assert result.url is not None
        assert str(output_path.absolute()) in result.url


    @pytest.mark.asyncio
    async def test_export_items_by_type(self, tmp_path, sample_roadmap):
        """Export returns items_by_type breakdown."""
        client = CSVClient()
        output_path = tmp_path / "output.csv"

        result = await client.export(sample_roadmap, output_path=str(output_path))

        assert result.items_by_type == {
            "milestones": 1,
            "epics": 1,
            "stories": 1,
            "tasks": 2,
        }

    @pytest.mark.asyncio
    async def test_export_id_mapping(self, tmp_path, sample_roadmap):
        """Export returns id_mapping for all items."""
        client = CSVClient()
        output_path = tmp_path / "output.csv"

        result = await client.export(sample_roadmap, output_path=str(output_path))

        # CSV uses identity mapping (arcane ID = CSV ID)
        assert "milestone-001" in result.id_mapping
        assert "epic-001" in result.id_mapping
        assert "story-001" in result.id_mapping
        assert "task-001" in result.id_mapping
        assert "task-002" in result.id_mapping
        assert result.id_mapping["task-001"] == "task-001"

    @pytest.mark.asyncio
    async def test_export_no_warnings(self, tmp_path, sample_roadmap):
        """CSV export produces no warnings."""
        client = CSVClient()
        output_path = tmp_path / "output.csv"

        result = await client.export(sample_roadmap, output_path=str(output_path))

        assert result.warnings == []

    @pytest.mark.asyncio
    async def test_export_creates_docs_markdown(self, tmp_path, sample_roadmap):
        """Export creates project-docs.md alongside the CSV."""
        client = CSVClient()
        output_path = tmp_path / "output.csv"

        await client.export(sample_roadmap, output_path=str(output_path))

        docs_path = tmp_path / "project-docs.md"
        assert docs_path.exists()

        content = docs_path.read_text(encoding="utf-8")
        assert "# Project Overview" in content
        assert "# Requirements" in content
        assert "# Technical Decisions" in content
        assert "# Team & Constraints" in content


    @pytest.mark.asyncio
    async def test_export_calls_progress_callback(self, tmp_path, sample_roadmap):
        """Export calls progress_callback for each item."""
        client = CSVClient()
        output_path = tmp_path / "output.csv"
        calls = []

        def callback(item_type: str, item_name: str):
            calls.append((item_type, item_name))

        await client.export(
            sample_roadmap, progress_callback=callback, output_path=str(output_path)
        )

        # 1 milestone + 1 epic + 1 story + 2 tasks = 5 calls
        assert len(calls) == 5
        assert calls[0] == ("Milestone", "MVP")
        assert calls[1] == ("Epic", "Authentication")
        assert calls[2] == ("Story", "User Login")
        assert calls[3][0] == "Task"
        assert calls[4][0] == "Task"

    @pytest.mark.asyncio
    async def test_export_works_without_callback(self, tmp_path, sample_roadmap):
        """Export works when progress_callback is None."""
        client = CSVClient()
        output_path = tmp_path / "output.csv"

        result = await client.export(
            sample_roadmap, progress_callback=None, output_path=str(output_path)
        )

        assert result.success is True
        assert result.items_created == 5


class TestExportResult:
    """Tests for ExportResult model."""

    def test_export_result_success(self):
        """ExportResult can represent success."""
        result = ExportResult(
            success=True,
            target="CSV",
            items_created=10,
            url="/path/to/file.csv",
        )
        assert result.success is True
        assert result.target == "CSV"
        assert result.items_created == 10
        assert result.errors == []
        assert result.items_by_type == {}
        assert result.id_mapping == {}
        assert result.warnings == []

    def test_export_result_failure(self):
        """ExportResult can represent failure with errors."""
        result = ExportResult(
            success=False,
            target="Linear",
            items_created=0,
            errors=["API key invalid", "Connection failed"],
        )
        assert result.success is False
        assert len(result.errors) == 2

    def test_export_result_with_warnings(self):
        """ExportResult can include non-fatal warnings."""
        result = ExportResult(
            success=True,
            target="Linear",
            items_created=10,
            warnings=["Could not set status for task-01HQ", "Label 'urgent' not found"],
        )
        assert result.success is True
        assert len(result.warnings) == 2

    def test_export_result_with_items_by_type(self):
        """ExportResult can include items_by_type breakdown."""
        result = ExportResult(
            success=True,
            target="Jira",
            items_created=15,
            items_by_type={"milestones": 2, "epics": 4, "stories": 5, "tasks": 4},
        )
        assert result.items_by_type["milestones"] == 2
        assert sum(result.items_by_type.values()) == 15

    def test_export_result_with_id_mapping(self):
        """ExportResult can include id_mapping."""
        result = ExportResult(
            success=True,
            target="Linear",
            items_created=2,
            id_mapping={"task-01HQ": "LIN-123", "task-02HQ": "LIN-124"},
        )
        assert result.id_mapping["task-01HQ"] == "LIN-123"
        assert len(result.id_mapping) == 2
