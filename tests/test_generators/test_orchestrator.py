"""Tests for arcane.generators.orchestrator module."""

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from pydantic import BaseModel
from rich.console import Console

from arcane.core.clients.base import BaseAIClient, AIClientError, UsageStats
from arcane.core.generators import (
    GenerationError,
    RoadmapOrchestrator,
    MilestoneSkeletonList,
    MilestoneSkeleton,
    EpicSkeletonList,
    EpicSkeleton,
    StorySkeletonList,
    StorySkeleton,
    TaskList,
)
from arcane.core.items import (
    Roadmap,
    Milestone,
    Epic,
    Story,
    Task,
    Priority,
    Status,
    ProjectContext,
)
from arcane.core.storage import StorageManager
from arcane.core.utils import generate_id


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


class FailingClient(MockClient):
    """Mock client that fails when generating a specific model type."""

    def __init__(self, fail_on: type[BaseModel]):
        super().__init__()
        self.fail_on = fail_on

    async def generate(
        self, system_prompt, user_prompt, response_model,
        max_tokens=4096, temperature=0.7, level=None,
    ):
        if response_model == self.fail_on:
            raise AIClientError(f"Simulated failure for {response_model}")
        return await super().generate(
            system_prompt, user_prompt, response_model,
            max_tokens, temperature, level,
        )


def _make_task():
    """Create a minimal task for testing."""
    return Task(
        id=generate_id("task"),
        name="Test task",
        description="A test task",
        priority=Priority.MEDIUM,
        estimated_hours=2,
        acceptance_criteria=["Done"],
        implementation_notes="Do it",
        claude_code_prompt="Implement the thing",
    )


def _make_roadmap(context, *, num_complete_milestones=0,
                  milestone_with_no_epics=False,
                  epic_with_no_stories=False,
                  story_with_no_tasks=False):
    """Build a roadmap with specific incomplete states for testing resume."""
    roadmap = Roadmap(
        id=generate_id("roadmap"),
        project_name=context.project_name,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        context=context,
    )

    # Add fully complete milestones
    for i in range(num_complete_milestones):
        ms = Milestone(
            id=generate_id("milestone"),
            name=f"Complete Milestone {i + 1}",
            goal=f"Goal {i + 1}",
            description=f"Description {i + 1}",
            priority=Priority.HIGH,
        )
        epic = Epic(
            id=generate_id("epic"),
            name=f"Complete Epic {i + 1}",
            goal=f"Epic goal {i + 1}",
            description=f"Epic desc {i + 1}",
            priority=Priority.HIGH,
        )
        story = Story(
            id=generate_id("story"),
            name=f"Complete Story {i + 1}",
            description=f"Story desc {i + 1}",
            priority=Priority.HIGH,
            acceptance_criteria=["Done"],
        )
        story.tasks = [_make_task()]
        epic.stories = [story]
        ms.epics = [epic]
        roadmap.milestones.append(ms)

    # Add a milestone with no epics
    if milestone_with_no_epics:
        ms = Milestone(
            id=generate_id("milestone"),
            name="Incomplete Milestone",
            goal="Needs epics",
            description="This milestone has no epics yet",
            priority=Priority.MEDIUM,
        )
        roadmap.milestones.append(ms)

    # Add a milestone with an epic that has no stories
    if epic_with_no_stories:
        ms = Milestone(
            id=generate_id("milestone"),
            name="Milestone With Empty Epic",
            goal="Has epic shells",
            description="This milestone has epics but no stories",
            priority=Priority.MEDIUM,
        )
        epic = Epic(
            id=generate_id("epic"),
            name="Empty Epic",
            goal="Needs stories",
            description="This epic has no stories yet",
            priority=Priority.MEDIUM,
        )
        ms.epics = [epic]
        roadmap.milestones.append(ms)

    # Add a milestone with an epic/story that has no tasks
    if story_with_no_tasks:
        ms = Milestone(
            id=generate_id("milestone"),
            name="Milestone With Empty Story",
            goal="Has story shells",
            description="This milestone has stories but no tasks",
            priority=Priority.MEDIUM,
        )
        epic = Epic(
            id=generate_id("epic"),
            name="Epic With Empty Story",
            goal="Has stories",
            description="This epic has stories without tasks",
            priority=Priority.MEDIUM,
        )
        story = Story(
            id=generate_id("story"),
            name="Empty Story",
            description="This story has no tasks yet",
            priority=Priority.MEDIUM,
            acceptance_criteria=["Needs tasks"],
        )
        epic.stories = [story]
        ms.epics = [epic]
        roadmap.milestones.append(ms)

    return roadmap


class TestCalculateResumeTotal:
    """Tests for _calculate_resume_total static method."""

    def test_complete_roadmap_returns_zero(self, sample_context):
        """Complete roadmap needs zero generation steps."""
        roadmap = _make_roadmap(sample_context, num_complete_milestones=2)
        assert RoadmapOrchestrator._calculate_resume_total(roadmap) == 0

    def test_milestone_with_no_epics(self, sample_context):
        """Milestone with no epics needs 1 step (epic gen)."""
        roadmap = _make_roadmap(sample_context, milestone_with_no_epics=True)
        assert RoadmapOrchestrator._calculate_resume_total(roadmap) == 1

    def test_epic_with_no_stories(self, sample_context):
        """Epic with no stories needs 1 step (story gen)."""
        roadmap = _make_roadmap(sample_context, epic_with_no_stories=True)
        assert RoadmapOrchestrator._calculate_resume_total(roadmap) == 1

    def test_story_with_no_tasks(self, sample_context):
        """Story with no tasks needs 1 step (task gen)."""
        roadmap = _make_roadmap(sample_context, story_with_no_tasks=True)
        assert RoadmapOrchestrator._calculate_resume_total(roadmap) == 1

    def test_multiple_incomplete_items(self, sample_context):
        """Multiple incomplete items sum their steps."""
        roadmap = _make_roadmap(
            sample_context,
            milestone_with_no_epics=True,
            epic_with_no_stories=True,
            story_with_no_tasks=True,
        )
        assert RoadmapOrchestrator._calculate_resume_total(roadmap) == 3

    def test_complete_plus_incomplete(self, sample_context):
        """Complete milestones don't add to total."""
        roadmap = _make_roadmap(
            sample_context,
            num_complete_milestones=2,
            story_with_no_tasks=True,
        )
        assert RoadmapOrchestrator._calculate_resume_total(roadmap) == 1


class TestGenerateShellSaving:
    """Tests that generate() saves shells before expanding them."""

    @pytest.mark.asyncio
    async def test_milestone_shells_saved_on_epic_gen_failure(
        self, tmp_path, sample_context, console,
    ):
        """When epic gen fails, all milestone shells are still saved to disk."""
        client = FailingClient(fail_on=EpicSkeletonList)
        storage = StorageManager(tmp_path)
        orchestrator = RoadmapOrchestrator(
            client, console, storage, interactive=False,
        )

        with pytest.raises(GenerationError):
            await orchestrator.generate(sample_context)

        roadmap = await storage.load_roadmap(tmp_path / "testapp" / "roadmap.json")

        # All milestone shells should be saved
        assert len(roadmap.milestones) == 2
        assert roadmap.milestones[0].name == "MVP"
        assert roadmap.milestones[1].name == "v1.0"

        # But no epics (generation failed before any could be created)
        for ms in roadmap.milestones:
            assert len(ms.epics) == 0

    @pytest.mark.asyncio
    async def test_epic_shells_saved_on_story_gen_failure(
        self, tmp_path, sample_context, console,
    ):
        """When story gen fails, all epic shells for the milestone are saved."""
        client = FailingClient(fail_on=StorySkeletonList)
        storage = StorageManager(tmp_path)
        orchestrator = RoadmapOrchestrator(
            client, console, storage, interactive=False,
        )

        with pytest.raises(GenerationError):
            await orchestrator.generate(sample_context)

        roadmap = await storage.load_roadmap(tmp_path / "testapp" / "roadmap.json")

        # First milestone should have all epic shells
        assert len(roadmap.milestones[0].epics) == 2
        assert roadmap.milestones[0].epics[0].name == "Authentication"
        assert roadmap.milestones[0].epics[1].name == "Dashboard"

        # But no stories
        for epic in roadmap.milestones[0].epics:
            assert len(epic.stories) == 0

    @pytest.mark.asyncio
    async def test_story_shells_saved_on_task_gen_failure(
        self, tmp_path, sample_context, console,
    ):
        """When task gen fails, all story shells for the epic are saved."""
        client = FailingClient(fail_on=TaskList)
        storage = StorageManager(tmp_path)
        orchestrator = RoadmapOrchestrator(
            client, console, storage, interactive=False,
        )

        with pytest.raises(GenerationError):
            await orchestrator.generate(sample_context)

        roadmap = await storage.load_roadmap(tmp_path / "testapp" / "roadmap.json")

        # First epic of first milestone should have story shells
        epic = roadmap.milestones[0].epics[0]
        assert len(epic.stories) == 1
        assert epic.stories[0].name == "User Login"

        # But no tasks
        assert len(epic.stories[0].tasks) == 0

    @pytest.mark.asyncio
    async def test_resume_detects_milestone_shells_after_failure(
        self, tmp_path, sample_context, console,
    ):
        """After epic gen failure, get_resume_point finds the incomplete milestone."""
        client = FailingClient(fail_on=EpicSkeletonList)
        storage = StorageManager(tmp_path)
        orchestrator = RoadmapOrchestrator(
            client, console, storage, interactive=False,
        )

        with pytest.raises(GenerationError):
            await orchestrator.generate(sample_context)

        roadmap = await storage.load_roadmap(tmp_path / "testapp" / "roadmap.json")
        resume_point = storage.get_resume_point(roadmap)
        assert resume_point is not None
        assert "no epics" in resume_point

    @pytest.mark.asyncio
    async def test_resume_detects_epic_shells_after_failure(
        self, tmp_path, sample_context, console,
    ):
        """After story gen failure, get_resume_point finds the incomplete epic."""
        client = FailingClient(fail_on=StorySkeletonList)
        storage = StorageManager(tmp_path)
        orchestrator = RoadmapOrchestrator(
            client, console, storage, interactive=False,
        )

        with pytest.raises(GenerationError):
            await orchestrator.generate(sample_context)

        roadmap = await storage.load_roadmap(tmp_path / "testapp" / "roadmap.json")
        resume_point = storage.get_resume_point(roadmap)
        assert resume_point is not None
        assert "no stories" in resume_point

    @pytest.mark.asyncio
    async def test_resume_detects_story_shells_after_failure(
        self, tmp_path, sample_context, console,
    ):
        """After task gen failure, get_resume_point finds the incomplete story."""
        client = FailingClient(fail_on=TaskList)
        storage = StorageManager(tmp_path)
        orchestrator = RoadmapOrchestrator(
            client, console, storage, interactive=False,
        )

        with pytest.raises(GenerationError):
            await orchestrator.generate(sample_context)

        roadmap = await storage.load_roadmap(tmp_path / "testapp" / "roadmap.json")
        resume_point = storage.get_resume_point(roadmap)
        assert resume_point is not None
        assert "no tasks" in resume_point


class TestResumeFromIncompleteRoadmap:
    """Tests that resume() correctly fills in incomplete roadmaps."""

    @pytest.mark.asyncio
    async def test_resume_fills_missing_epics(
        self, tmp_path, sample_context, console, mock_client,
    ):
        """Resume generates epics for a milestone that has none."""
        roadmap = _make_roadmap(sample_context, milestone_with_no_epics=True)
        storage = StorageManager(tmp_path)
        orchestrator = RoadmapOrchestrator(
            mock_client, console, storage, interactive=False,
        )

        result = await orchestrator.resume(roadmap)

        # The incomplete milestone should now have epics
        incomplete_ms = result.milestones[0]
        assert len(incomplete_ms.epics) > 0

        # And those epics should have stories and tasks
        for epic in incomplete_ms.epics:
            assert len(epic.stories) > 0
            for story in epic.stories:
                assert len(story.tasks) > 0

    @pytest.mark.asyncio
    async def test_resume_fills_missing_stories(
        self, tmp_path, sample_context, console, mock_client,
    ):
        """Resume generates stories for an epic that has none."""
        roadmap = _make_roadmap(sample_context, epic_with_no_stories=True)
        storage = StorageManager(tmp_path)
        orchestrator = RoadmapOrchestrator(
            mock_client, console, storage, interactive=False,
        )

        result = await orchestrator.resume(roadmap)

        # The incomplete epic should now have stories
        incomplete_epic = result.milestones[0].epics[0]
        assert len(incomplete_epic.stories) > 0

        # And those stories should have tasks
        for story in incomplete_epic.stories:
            assert len(story.tasks) > 0

    @pytest.mark.asyncio
    async def test_resume_fills_missing_tasks(
        self, tmp_path, sample_context, console, mock_client,
    ):
        """Resume generates tasks for a story that has none."""
        roadmap = _make_roadmap(sample_context, story_with_no_tasks=True)
        storage = StorageManager(tmp_path)
        orchestrator = RoadmapOrchestrator(
            mock_client, console, storage, interactive=False,
        )

        result = await orchestrator.resume(roadmap)

        # The incomplete story should now have tasks
        incomplete_story = result.milestones[0].epics[0].stories[0]
        assert len(incomplete_story.tasks) > 0

    @pytest.mark.asyncio
    async def test_resume_skips_complete_milestones(
        self, tmp_path, sample_context, console, mock_client,
    ):
        """Resume skips already-complete milestones and only fills incomplete ones."""
        roadmap = _make_roadmap(
            sample_context,
            num_complete_milestones=1,
            milestone_with_no_epics=True,
        )
        storage = StorageManager(tmp_path)
        orchestrator = RoadmapOrchestrator(
            mock_client, console, storage, interactive=False,
        )

        # Record the complete milestone's state before resume
        complete_ms_id = roadmap.milestones[0].id
        complete_ms_epic_count = len(roadmap.milestones[0].epics)

        result = await orchestrator.resume(roadmap)

        # Complete milestone should be unchanged
        assert result.milestones[0].id == complete_ms_id
        assert len(result.milestones[0].epics) == complete_ms_epic_count

        # Incomplete milestone should now be filled
        assert len(result.milestones[1].epics) > 0

    @pytest.mark.asyncio
    async def test_resume_complete_roadmap_is_noop(
        self, tmp_path, sample_context, console, mock_client,
    ):
        """Resume on an already-complete roadmap makes no API calls."""
        roadmap = _make_roadmap(sample_context, num_complete_milestones=2)
        storage = StorageManager(tmp_path)
        orchestrator = RoadmapOrchestrator(
            mock_client, console, storage, interactive=False,
        )

        mock_client._call_count = 0
        await orchestrator.resume(roadmap)

        # No API calls should have been made
        assert mock_client._call_count == 0

    @pytest.mark.asyncio
    async def test_resume_saves_epic_shells_before_expanding(
        self, tmp_path, sample_context, console,
    ):
        """In resume, epic shells are saved before story gen starts.

        If story gen fails during resume, the epic shells should persist
        so the next resume can detect the epics with no stories.
        """
        # Client that succeeds on epics but fails on stories
        client = FailingClient(fail_on=StorySkeletonList)
        roadmap = _make_roadmap(sample_context, milestone_with_no_epics=True)
        storage = StorageManager(tmp_path)

        # Save initial state
        await storage.save_roadmap(roadmap)

        orchestrator = RoadmapOrchestrator(
            client, console, storage, interactive=False,
        )

        with pytest.raises(GenerationError):
            await orchestrator.resume(roadmap)

        # Load what was saved before the failure
        slug = storage._slugify(sample_context.project_name)
        saved = await storage.load_roadmap(tmp_path / slug / "roadmap.json")

        # Epic shells should have been saved
        incomplete_ms = saved.milestones[0]
        assert len(incomplete_ms.epics) > 0

        # But no stories (story gen failed)
        for epic in incomplete_ms.epics:
            assert len(epic.stories) == 0

        # get_resume_point should detect the incomplete epics
        resume_point = storage.get_resume_point(saved)
        assert resume_point is not None
        assert "no stories" in resume_point

    @pytest.mark.asyncio
    async def test_resume_saves_story_shells_before_expanding(
        self, tmp_path, sample_context, console,
    ):
        """In resume, story shells are saved before task gen starts.

        If task gen fails during resume, the story shells should persist
        so the next resume can detect the stories with no tasks.
        """
        # Client that succeeds on stories but fails on tasks
        client = FailingClient(fail_on=TaskList)
        roadmap = _make_roadmap(sample_context, epic_with_no_stories=True)
        storage = StorageManager(tmp_path)

        await storage.save_roadmap(roadmap)

        orchestrator = RoadmapOrchestrator(
            client, console, storage, interactive=False,
        )

        with pytest.raises(GenerationError):
            await orchestrator.resume(roadmap)

        slug = storage._slugify(sample_context.project_name)
        saved = await storage.load_roadmap(tmp_path / slug / "roadmap.json")

        # Story shells should have been saved
        incomplete_epic = saved.milestones[0].epics[0]
        assert len(incomplete_epic.stories) > 0

        # But no tasks (task gen failed)
        for story in incomplete_epic.stories:
            assert len(story.tasks) == 0

        # get_resume_point should detect the incomplete stories
        resume_point = storage.get_resume_point(saved)
        assert resume_point is not None
        assert "no tasks" in resume_point
