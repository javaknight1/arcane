"""Tests for arcane.project_management.csv module."""

import csv
from datetime import datetime, timezone
from pathlib import Path

import pytest

from arcane.items import (
    Epic,
    Milestone,
    Priority,
    ProjectContext,
    Roadmap,
    Status,
    Story,
    Task,
)
from arcane.project_management import CSVClient, ExportResult


@pytest.fixture
def sample_context():
    """Sample ProjectContext for testing."""
    return ProjectContext(
        project_name="Test Project",
        vision="A test application",
        problem_statement="Testing is important",
        target_users=["developers"],
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
        similar_products=["other apps"],
        notes="Test notes",
    )


@pytest.fixture
def sample_roadmap(sample_context):
    """Sample Roadmap with full hierarchy for testing."""
    task1 = Task(
        id="task-001",
        name="Create login form",
        description="Build the login form component",
        priority=Priority.HIGH,
        status=Status.NOT_STARTED,
        estimated_hours=4,
        acceptance_criteria=["Form renders", "Validates input"],
        implementation_notes="Use React Hook Form",
        claude_code_prompt="Create a login form with email and password fields...",
    )
    task2 = Task(
        id="task-002",
        name="Add form validation",
        description="Validate form inputs",
        priority=Priority.MEDIUM,
        status=Status.NOT_STARTED,
        estimated_hours=2,
        prerequisites=["task-001"],
        acceptance_criteria=["Email validated", "Password validated"],
        implementation_notes="Use Zod for validation",
        claude_code_prompt="Add Zod validation to the login form...",
    )

    story = Story(
        id="story-001",
        name="User Login",
        description="Users can log in with email/password",
        priority=Priority.CRITICAL,
        status=Status.NOT_STARTED,
        acceptance_criteria=["Can enter credentials", "Error on invalid"],
        tasks=[task1, task2],
    )

    epic = Epic(
        id="epic-001",
        name="Authentication",
        goal="Secure user authentication",
        description="User login and registration",
        priority=Priority.CRITICAL,
        status=Status.NOT_STARTED,
        stories=[story],
    )

    milestone = Milestone(
        id="milestone-001",
        name="MVP",
        goal="Launch minimum viable product",
        description="First release with core features",
        priority=Priority.CRITICAL,
        status=Status.NOT_STARTED,
        epics=[epic],
    )

    return Roadmap(
        id="roadmap-001",
        project_name="Test Project",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        context=sample_context,
        milestones=[milestone],
    )


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
