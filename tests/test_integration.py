"""End-to-end integration tests for Arcane.

Tests the complete pipeline from context to generated roadmap to export,
using a mock AI client to simulate API responses.
"""

import csv
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path

import pytest
from pydantic import BaseModel
from rich.console import Console

from arcane.core.clients.base import BaseAIClient, UsageStats
from arcane.core.generators import (
    EpicSkeleton,
    EpicSkeletonList,
    MilestoneSkeleton,
    MilestoneSkeletonList,
    RoadmapOrchestrator,
    StorySkeleton,
    StorySkeletonList,
    TaskList,
)
from arcane.core.items import Priority, ProjectContext, Roadmap, Task
from arcane.core.project_management import CSVClient
from arcane.core.storage import StorageManager
from arcane.core.utils import generate_id


class MockAIClient(BaseAIClient):
    """Mock AI client that returns fixture data based on response_model type.

    This allows testing the full generation pipeline without making real API calls.
    Returns consistent fixture data that represents a realistic roadmap structure.
    """

    def __init__(self):
        self._call_count = 0
        self._usage = UsageStats()

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: type[BaseModel],
        max_tokens: int = 4096,
        temperature: float = 0.7,
        level: str | None = None,
    ) -> BaseModel:
        """Return fixture data based on the requested response_model type."""
        self._call_count += 1

        if response_model == MilestoneSkeletonList:
            return MilestoneSkeletonList(
                milestones=[
                    MilestoneSkeleton(
                        name="MVP",
                        goal="Launch minimum viable product",
                        description="Core features for initial launch",
                        priority=Priority.CRITICAL,
                        suggested_epic_areas=["Authentication", "Core Features"],
                    ),
                    MilestoneSkeleton(
                        name="v1.0",
                        goal="Full feature release",
                        description="Complete product with all planned features",
                        priority=Priority.HIGH,
                        suggested_epic_areas=["Advanced Features", "Polish"],
                    ),
                ]
            )

        elif response_model == EpicSkeletonList:
            return EpicSkeletonList(
                epics=[
                    EpicSkeleton(
                        name="User Authentication",
                        goal="Secure user login and registration",
                        description="Complete auth system with login, register, and password reset",
                        priority=Priority.CRITICAL,
                        suggested_story_areas=["Login", "Registration"],
                    ),
                    EpicSkeleton(
                        name="Dashboard",
                        goal="Main user interface",
                        description="User dashboard with widgets and navigation",
                        priority=Priority.HIGH,
                        suggested_story_areas=["Layout", "Widgets"],
                    ),
                ]
            )

        elif response_model == StorySkeletonList:
            return StorySkeletonList(
                stories=[
                    StorySkeleton(
                        name="User Login",
                        description="Users can log in with email and password",
                        priority=Priority.CRITICAL,
                        acceptance_criteria=[
                            "User can enter credentials",
                            "Invalid credentials show error",
                            "Successful login redirects to dashboard",
                        ],
                    ),
                ]
            )

        elif response_model == TaskList:
            return TaskList(
                tasks=[
                    Task(
                        id=generate_id("task"),
                        name="Create login form component",
                        description="Build React login form with email and password fields",
                        priority=Priority.HIGH,
                        estimated_hours=4,
                        acceptance_criteria=[
                            "Form renders with email field",
                            "Form renders with password field",
                            "Submit button is present",
                        ],
                        implementation_notes="Use React Hook Form for form state management",
                        claude_code_prompt=(
                            "Create a React login form component with:\n"
                            "- Email input with validation\n"
                            "- Password input with show/hide toggle\n"
                            "- Submit button with loading state\n"
                            "- Error message display area"
                        ),
                    ),
                    Task(
                        id=generate_id("task"),
                        name="Add form validation",
                        description="Implement client-side validation for login form",
                        priority=Priority.MEDIUM,
                        estimated_hours=2,
                        acceptance_criteria=[
                            "Email format is validated",
                            "Password minimum length enforced",
                            "Errors shown inline",
                        ],
                        implementation_notes="Use Zod for schema validation",
                        claude_code_prompt=(
                            "Add Zod validation to the login form:\n"
                            "- Email must be valid format\n"
                            "- Password must be at least 8 characters\n"
                            "- Show inline error messages"
                        ),
                    ),
                ]
            )

        raise ValueError(f"Unknown response_model: {response_model}")

    async def validate_connection(self) -> bool:
        """Always returns True for mock client."""
        return True

    @property
    def provider_name(self) -> str:
        """Return mock provider name."""
        return "Mock Provider"

    @property
    def model_name(self) -> str:
        """Return mock model name."""
        return "mock-model-1.0"

    @property
    def usage(self) -> UsageStats:
        return self._usage

    def reset_usage(self) -> None:
        self._usage.reset()


@pytest.fixture
def sample_context():
    """Sample ProjectContext for integration testing."""
    return ProjectContext(
        project_name="Integration Test App",
        vision="A comprehensive test application for integration testing",
        problem_statement="We need to verify end-to-end functionality",
        target_users=["developers", "QA engineers"],
        timeline="3 months",
        team_size=3,
        developer_experience="senior",
        budget_constraints="moderate",
        tech_stack=["Python", "React", "PostgreSQL"],
        infrastructure_preferences="AWS",
        existing_codebase=False,
        must_have_features=["authentication", "dashboard", "API"],
        nice_to_have_features=["dark mode", "notifications"],
        out_of_scope=["mobile app", "third-party integrations"],
        similar_products=["Notion", "Linear"],
        notes="This is a test context for integration testing",
    )


@pytest.fixture
def mock_client():
    """Create a mock AI client for testing."""
    return MockAIClient()


@pytest.fixture
def quiet_console():
    """Console that doesn't output (for quiet tests)."""
    return Console(quiet=True)


class TestFullPipeline:
    """Integration tests for the full generation pipeline."""

    @pytest.mark.asyncio
    async def test_full_pipeline_generates_roadmap(
        self, tmp_path, sample_context, mock_client, quiet_console
    ):
        """Full pipeline generates a complete roadmap."""
        storage = StorageManager(tmp_path)
        orchestrator = RoadmapOrchestrator(
            client=mock_client,
            console=quiet_console,
            storage=storage,
            interactive=False,
        )

        roadmap = await orchestrator.generate(sample_context)

        # Verify roadmap was created
        assert roadmap is not None
        assert roadmap.project_name == "Integration Test App"
        assert len(roadmap.milestones) > 0

    @pytest.mark.asyncio
    async def test_full_pipeline_counts_correct(
        self, tmp_path, sample_context, mock_client, quiet_console
    ):
        """Full pipeline generates expected item counts."""
        storage = StorageManager(tmp_path)
        orchestrator = RoadmapOrchestrator(
            client=mock_client,
            console=quiet_console,
            storage=storage,
            interactive=False,
        )

        roadmap = await orchestrator.generate(sample_context)
        counts = roadmap.total_items

        # Based on mock responses:
        # 2 milestones, each with 2 epics = 4 epics
        # Each epic has 1 story = 4 stories
        # Each story has 2 tasks = 8 tasks
        assert counts["milestones"] == 2
        assert counts["epics"] == 4
        assert counts["stories"] == 4
        assert counts["tasks"] == 8

    @pytest.mark.asyncio
    async def test_full_pipeline_all_ids_unique(
        self, tmp_path, sample_context, mock_client, quiet_console
    ):
        """All items in generated roadmap have unique IDs."""
        storage = StorageManager(tmp_path)
        orchestrator = RoadmapOrchestrator(
            client=mock_client,
            console=quiet_console,
            storage=storage,
            interactive=False,
        )

        roadmap = await orchestrator.generate(sample_context)

        # Collect all IDs
        all_ids = [roadmap.id]
        for milestone in roadmap.milestones:
            all_ids.append(milestone.id)
            for epic in milestone.epics:
                all_ids.append(epic.id)
                for story in epic.stories:
                    all_ids.append(story.id)
                    for task in story.tasks:
                        all_ids.append(task.id)

        # All IDs should be unique
        assert len(all_ids) == len(set(all_ids)), "Duplicate IDs found"

    @pytest.mark.asyncio
    async def test_full_pipeline_saves_to_disk(
        self, tmp_path, sample_context, mock_client, quiet_console
    ):
        """Full pipeline saves roadmap and context to disk."""
        storage = StorageManager(tmp_path)
        orchestrator = RoadmapOrchestrator(
            client=mock_client,
            console=quiet_console,
            storage=storage,
            interactive=False,
        )

        await orchestrator.generate(sample_context)

        # Check files exist
        project_dir = tmp_path / "integration-test-app"
        assert project_dir.exists()
        assert (project_dir / "roadmap.json").exists()
        assert (project_dir / "context.yaml").exists()

    @pytest.mark.asyncio
    async def test_full_pipeline_total_hours_calculated(
        self, tmp_path, sample_context, mock_client, quiet_console
    ):
        """Total hours are correctly calculated from task estimates."""
        storage = StorageManager(tmp_path)
        orchestrator = RoadmapOrchestrator(
            client=mock_client,
            console=quiet_console,
            storage=storage,
            interactive=False,
        )

        roadmap = await orchestrator.generate(sample_context)

        # Each story has 2 tasks: 4 hours + 2 hours = 6 hours per story
        # 4 stories * 6 hours = 24 hours total
        assert roadmap.total_hours == 24


class TestCSVExportFromGenerated:
    """Tests for exporting generated roadmaps to CSV."""

    @pytest.mark.asyncio
    async def test_csv_export_from_generated(
        self, tmp_path, sample_context, mock_client, quiet_console
    ):
        """CSV export works on generated roadmaps."""
        storage = StorageManager(tmp_path)
        orchestrator = RoadmapOrchestrator(
            client=mock_client,
            console=quiet_console,
            storage=storage,
            interactive=False,
        )

        roadmap = await orchestrator.generate(sample_context)

        # Export to CSV
        csv_client = CSVClient()
        csv_path = tmp_path / "export.csv"
        result = await csv_client.export(roadmap, output_path=str(csv_path))

        assert result.success is True
        assert csv_path.exists()

    @pytest.mark.asyncio
    async def test_csv_export_row_count_matches(
        self, tmp_path, sample_context, mock_client, quiet_console
    ):
        """CSV export contains all items from roadmap."""
        storage = StorageManager(tmp_path)
        orchestrator = RoadmapOrchestrator(
            client=mock_client,
            console=quiet_console,
            storage=storage,
            interactive=False,
        )

        roadmap = await orchestrator.generate(sample_context)
        counts = roadmap.total_items
        expected_rows = (
            counts["milestones"]
            + counts["epics"]
            + counts["stories"]
            + counts["tasks"]
        )

        # Export to CSV
        csv_client = CSVClient()
        csv_path = tmp_path / "export.csv"
        result = await csv_client.export(roadmap, output_path=str(csv_path))

        assert result.items_created == expected_rows

        # Verify by reading the file
        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert len(rows) == expected_rows

    @pytest.mark.asyncio
    async def test_csv_export_all_tasks_have_prompts(
        self, tmp_path, sample_context, mock_client, quiet_console
    ):
        """All tasks in CSV export have Claude Code prompts."""
        storage = StorageManager(tmp_path)
        orchestrator = RoadmapOrchestrator(
            client=mock_client,
            console=quiet_console,
            storage=storage,
            interactive=False,
        )

        roadmap = await orchestrator.generate(sample_context)

        # Export to CSV
        csv_client = CSVClient()
        csv_path = tmp_path / "export.csv"
        await csv_client.export(roadmap, output_path=str(csv_path))

        # Check all tasks have prompts
        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["Type"] == "Task":
                    assert row["Claude_Code_Prompt"], f"Task {row['ID']} has no prompt"


class TestViewTreeNoCrash:
    """Tests that view functionality doesn't crash on generated roadmaps."""

    @pytest.mark.asyncio
    async def test_view_tree_no_crash(
        self, tmp_path, sample_context, mock_client, quiet_console
    ):
        """View tree format doesn't crash on generated roadmap."""
        storage = StorageManager(tmp_path)
        orchestrator = RoadmapOrchestrator(
            client=mock_client,
            console=quiet_console,
            storage=storage,
            interactive=False,
        )

        roadmap = await orchestrator.generate(sample_context)

        # This should not raise any exceptions
        # We use a StringIO to capture the output
        output = StringIO()
        test_console = Console(file=output, force_terminal=True)

        # Import the tree printing function and run it
        from arcane.cli import _print_tree

        _print_tree.__globals__["console"] = test_console
        _print_tree(roadmap)

        # Verify some output was produced
        result = output.getvalue()
        assert len(result) > 0
        assert roadmap.project_name in result

    @pytest.mark.asyncio
    async def test_view_summary_no_crash(
        self, tmp_path, sample_context, mock_client, quiet_console
    ):
        """View summary format doesn't crash on generated roadmap."""
        storage = StorageManager(tmp_path)
        orchestrator = RoadmapOrchestrator(
            client=mock_client,
            console=quiet_console,
            storage=storage,
            interactive=False,
        )

        roadmap = await orchestrator.generate(sample_context)

        # This should not raise any exceptions
        output = StringIO()
        test_console = Console(file=output, force_terminal=True)

        from arcane.cli import _print_summary

        _print_summary.__globals__["console"] = test_console
        _print_summary(roadmap)

        # Verify some output was produced
        result = output.getvalue()
        assert len(result) > 0


class TestRoadmapSerialization:
    """Tests for roadmap serialization/deserialization."""

    @pytest.mark.asyncio
    async def test_roadmap_json_roundtrip(
        self, tmp_path, sample_context, mock_client, quiet_console
    ):
        """Roadmap can be serialized to JSON and loaded back."""
        storage = StorageManager(tmp_path)
        orchestrator = RoadmapOrchestrator(
            client=mock_client,
            console=quiet_console,
            storage=storage,
            interactive=False,
        )

        original = await orchestrator.generate(sample_context)

        # Save and load
        project_dir = tmp_path / "integration-test-app"
        roadmap_file = project_dir / "roadmap.json"

        loaded = Roadmap.model_validate_json(roadmap_file.read_text())

        # Verify loaded matches original
        assert loaded.id == original.id
        assert loaded.project_name == original.project_name
        assert len(loaded.milestones) == len(original.milestones)
        assert loaded.total_hours == original.total_hours
        assert loaded.total_items == original.total_items
