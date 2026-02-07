"""Tests for arcane.generators.orchestrator module."""

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from pydantic import BaseModel
from rich.console import Console

from arcane.clients.base import BaseAIClient, UsageStats
from arcane.generators import (
    RoadmapOrchestrator,
    MilestoneSkeletonList,
    MilestoneSkeleton,
    EpicSkeletonList,
    EpicSkeleton,
    StorySkeletonList,
    StorySkeleton,
    TaskList,
)
from arcane.items import Task, Priority, ProjectContext
from arcane.storage import StorageManager
from arcane.utils import generate_id


class MockClient(BaseAIClient):
    """Mock AI client that returns different fixtures based on response_model type."""

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
        self._call_count += 1

        if response_model == MilestoneSkeletonList:
            return MilestoneSkeletonList(
                milestones=[
                    MilestoneSkeleton(
                        name="MVP",
                        goal="Launch minimum viable product",
                        description="First release with core features",
                        priority=Priority.CRITICAL,
                        suggested_epic_areas=["Auth", "Core"],
                    ),
                    MilestoneSkeleton(
                        name="v1.0",
                        goal="Full feature release",
                        description="Complete product with all features",
                        priority=Priority.HIGH,
                        suggested_epic_areas=["Advanced", "Polish"],
                    ),
                ]
            )

        elif response_model == EpicSkeletonList:
            return EpicSkeletonList(
                epics=[
                    EpicSkeleton(
                        name="Authentication",
                        goal="Secure user authentication",
                        description="User login and registration",
                        priority=Priority.CRITICAL,
                        suggested_story_areas=["Login", "Register"],
                    ),
                    EpicSkeleton(
                        name="Dashboard",
                        goal="User dashboard",
                        description="Main user interface",
                        priority=Priority.HIGH,
                        suggested_story_areas=["Widgets", "Layout"],
                    ),
                ]
            )

        elif response_model == StorySkeletonList:
            return StorySkeletonList(
                stories=[
                    StorySkeleton(
                        name="User Login",
                        description="Users can log in with email/password",
                        priority=Priority.CRITICAL,
                        acceptance_criteria=["Can enter credentials", "Error on invalid"],
                    ),
                ]
            )

        elif response_model == TaskList:
            return TaskList(
                tasks=[
                    Task(
                        id=generate_id("task"),
                        name="Create login form",
                        description="Build the login form component",
                        priority=Priority.HIGH,
                        estimated_hours=4,
                        acceptance_criteria=["Form renders", "Validates input"],
                        implementation_notes="Use React Hook Form",
                        claude_code_prompt="Create a login form...",
                    ),
                    Task(
                        id=generate_id("task"),
                        name="Add form validation",
                        description="Validate form inputs",
                        priority=Priority.MEDIUM,
                        estimated_hours=2,
                        acceptance_criteria=["Email validated", "Password validated"],
                        implementation_notes="Use Zod for validation",
                        claude_code_prompt="Add validation to the login form...",
                    ),
                ]
            )

        raise ValueError(f"Unknown response_model: {response_model}")

    async def validate_connection(self) -> bool:
        return True

    @property
    def provider_name(self) -> str:
        return "Mock Provider"

    @property
    def model_name(self) -> str:
        return "mock-model-1.0"

    @property
    def usage(self) -> UsageStats:
        return self._usage

    def reset_usage(self) -> None:
        self._usage.reset()


@pytest.fixture
def sample_context():
    """Sample ProjectContext for testing."""
    return ProjectContext(
        project_name="TestApp",
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
def console():
    """Quiet console for testing."""
    return Console(quiet=True)


@pytest.fixture
def mock_client():
    """Mock AI client."""
    return MockClient()


class TestRoadmapOrchestrator:
    """Tests for RoadmapOrchestrator."""

    @pytest.mark.asyncio
    async def test_full_generation(self, tmp_path, sample_context, console, mock_client):
        """Full generation produces correct hierarchy."""
        storage = StorageManager(tmp_path)
        orchestrator = RoadmapOrchestrator(
            mock_client, console, storage, interactive=False
        )

        roadmap = await orchestrator.generate(sample_context)

        # Verify structure
        assert roadmap is not None
        assert roadmap.project_name == "TestApp"

        # 2 milestones
        assert len(roadmap.milestones) == 2

        # Each milestone has 2 epics (4 total)
        total_epics = sum(len(m.epics) for m in roadmap.milestones)
        assert total_epics == 4

        # Each epic has 1 story (4 total)
        total_stories = sum(
            len(e.stories) for m in roadmap.milestones for e in m.epics
        )
        assert total_stories == 4

        # Each story has 2 tasks (8 total)
        total_tasks = sum(
            len(s.tasks)
            for m in roadmap.milestones
            for e in m.epics
            for s in e.stories
        )
        assert total_tasks == 8

        # Verify counts match computed property
        counts = roadmap.total_items
        assert counts["milestones"] == 2
        assert counts["epics"] == 4
        assert counts["stories"] == 4
        assert counts["tasks"] == 8

    @pytest.mark.asyncio
    async def test_total_hours_calculated(
        self, tmp_path, sample_context, console, mock_client
    ):
        """Total hours are calculated correctly."""
        storage = StorageManager(tmp_path)
        orchestrator = RoadmapOrchestrator(
            mock_client, console, storage, interactive=False
        )

        roadmap = await orchestrator.generate(sample_context)

        # Each story has 2 tasks (4 hours + 2 hours = 6 hours per story)
        # 4 stories × 6 hours = 24 hours total
        assert roadmap.total_hours == 24

    @pytest.mark.asyncio
    async def test_incremental_save(self, tmp_path, sample_context, console, mock_client):
        """Roadmap is saved after each story."""
        storage = StorageManager(tmp_path)

        # Track save calls
        save_count = 0
        original_save = storage.save_roadmap

        async def tracking_save(roadmap):
            nonlocal save_count
            save_count += 1
            return await original_save(roadmap)

        storage.save_roadmap = tracking_save

        orchestrator = RoadmapOrchestrator(
            mock_client, console, storage, interactive=False
        )

        await orchestrator.generate(sample_context)

        # Should save after each story (4 stories) plus final save
        # Actually saves once per story = 4, plus final = 5
        assert save_count >= 4

    @pytest.mark.asyncio
    async def test_roadmap_saved_to_disk(
        self, tmp_path, sample_context, console, mock_client
    ):
        """Roadmap is saved to disk."""
        storage = StorageManager(tmp_path)
        orchestrator = RoadmapOrchestrator(
            mock_client, console, storage, interactive=False
        )

        await orchestrator.generate(sample_context)

        # Check file exists
        project_dir = tmp_path / "testapp"
        assert project_dir.exists()
        assert (project_dir / "roadmap.json").exists()
        assert (project_dir / "context.yaml").exists()

    @pytest.mark.asyncio
    async def test_all_ids_unique(self, tmp_path, sample_context, console, mock_client):
        """All generated items have unique IDs."""
        storage = StorageManager(tmp_path)
        orchestrator = RoadmapOrchestrator(
            mock_client, console, storage, interactive=False
        )

        roadmap = await orchestrator.generate(sample_context)

        # Collect all IDs
        all_ids = [roadmap.id]
        for m in roadmap.milestones:
            all_ids.append(m.id)
            for e in m.epics:
                all_ids.append(e.id)
                for s in e.stories:
                    all_ids.append(s.id)
                    for t in s.tasks:
                        all_ids.append(t.id)

        # All IDs should be unique
        assert len(all_ids) == len(set(all_ids))

    @pytest.mark.asyncio
    async def test_milestones_have_correct_structure(
        self, tmp_path, sample_context, console, mock_client
    ):
        """Milestones have all expected fields."""
        storage = StorageManager(tmp_path)
        orchestrator = RoadmapOrchestrator(
            mock_client, console, storage, interactive=False
        )

        roadmap = await orchestrator.generate(sample_context)

        for milestone in roadmap.milestones:
            assert milestone.id.startswith("milestone-")
            assert milestone.name
            assert milestone.goal
            assert milestone.description
            assert milestone.priority is not None

    @pytest.mark.asyncio
    async def test_tasks_have_claude_code_prompt(
        self, tmp_path, sample_context, console, mock_client
    ):
        """All tasks have claude_code_prompt field."""
        storage = StorageManager(tmp_path)
        orchestrator = RoadmapOrchestrator(
            mock_client, console, storage, interactive=False
        )

        roadmap = await orchestrator.generate(sample_context)

        for m in roadmap.milestones:
            for e in m.epics:
                for s in e.stories:
                    for t in s.tasks:
                        assert t.claude_code_prompt
                        assert len(t.claude_code_prompt) > 0


class TestRoadmapOrchestratorInit:
    """Tests for RoadmapOrchestrator initialization."""

    def test_creates_all_generators(self, tmp_path, console, mock_client):
        """Orchestrator creates all 4 generators."""
        storage = StorageManager(tmp_path)
        orchestrator = RoadmapOrchestrator(mock_client, console, storage)

        assert orchestrator.milestone_gen is not None
        assert orchestrator.epic_gen is not None
        assert orchestrator.story_gen is not None
        assert orchestrator.task_gen is not None

    def test_stores_interactive_flag(self, tmp_path, console, mock_client):
        """Orchestrator stores interactive flag."""
        storage = StorageManager(tmp_path)

        orchestrator_interactive = RoadmapOrchestrator(
            mock_client, console, storage, interactive=True
        )
        assert orchestrator_interactive.interactive is True

        orchestrator_non_interactive = RoadmapOrchestrator(
            mock_client, console, storage, interactive=False
        )
        assert orchestrator_non_interactive.interactive is False
