"""Tests for arcane.storage.manager module."""

from datetime import datetime, timezone
from pathlib import Path

import pytest
import yaml

from arcane.items import (
    Roadmap,
    Milestone,
    Epic,
    Story,
    Task,
    ProjectContext,
    Priority,
    Status,
)
from arcane.storage import StorageManager


@pytest.fixture
def sample_context():
    """Sample ProjectContext for testing."""
    return ProjectContext(
        project_name="Test Project",
        vision="A test project for storage tests",
        problem_statement="Testing storage is important",
        target_users=["developers", "testers"],
        timeline="3 months",
        team_size=2,
        developer_experience="senior",
        budget_constraints="moderate",
        tech_stack=["Python", "pytest"],
        infrastructure_preferences="AWS",
        existing_codebase=False,
        must_have_features=["save", "load"],
        nice_to_have_features=["resume"],
        out_of_scope=["cloud sync"],
        similar_products=["other tools"],
        notes="Test notes",
    )


@pytest.fixture
def sample_task():
    """Sample Task for testing."""
    return Task(
        id="task-001",
        name="Implement feature",
        description="Implement the core feature",
        priority=Priority.HIGH,
        status=Status.NOT_STARTED,
        estimated_hours=4,
        acceptance_criteria=["Tests pass", "Code reviewed"],
        implementation_notes="Follow existing patterns",
        claude_code_prompt="Create a new module...",
    )


@pytest.fixture
def sample_story(sample_task):
    """Sample Story with tasks for testing."""
    return Story(
        id="story-001",
        name="User can do something",
        description="As a user, I want to do something",
        priority=Priority.HIGH,
        acceptance_criteria=["Feature works"],
        tasks=[sample_task],
    )


@pytest.fixture
def sample_epic(sample_story):
    """Sample Epic with stories for testing."""
    return Epic(
        id="epic-001",
        name="Core Features",
        description="Core functionality",
        priority=Priority.CRITICAL,
        goal="Deliver core features",
        stories=[sample_story],
    )


@pytest.fixture
def sample_milestone(sample_epic):
    """Sample Milestone with epics for testing."""
    return Milestone(
        id="milestone-001",
        name="MVP",
        description="Minimum viable product",
        priority=Priority.CRITICAL,
        goal="Launch MVP",
        epics=[sample_epic],
    )


@pytest.fixture
def complete_roadmap(sample_context, sample_milestone):
    """Complete roadmap with full hierarchy for testing."""
    return Roadmap(
        id="roadmap-001",
        project_name="Test Project",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        context=sample_context,
        milestones=[sample_milestone],
    )


@pytest.fixture
def large_roadmap(sample_context):
    """Larger roadmap with 2 milestones for testing."""
    tasks = [
        Task(
            id=f"task-{i}",
            name=f"Task {i}",
            description=f"Task {i} description",
            priority=Priority.MEDIUM,
            estimated_hours=3,
            acceptance_criteria=["Done"],
            implementation_notes="Notes",
            claude_code_prompt="Prompt",
        )
        for i in range(1, 5)
    ]

    stories = [
        Story(
            id=f"story-{i}",
            name=f"Story {i}",
            description=f"Story {i} description",
            priority=Priority.HIGH,
            acceptance_criteria=["Completed"],
            tasks=tasks[i * 2 - 2 : i * 2] if i <= 2 else [],
        )
        for i in range(1, 3)
    ]

    epics = [
        Epic(
            id=f"epic-{i}",
            name=f"Epic {i}",
            description=f"Epic {i} description",
            priority=Priority.HIGH,
            goal=f"Epic {i} goal",
            stories=[stories[i - 1]] if i <= 2 else [],
        )
        for i in range(1, 3)
    ]

    milestones = [
        Milestone(
            id=f"milestone-{i}",
            name=f"Milestone {i}",
            description=f"Milestone {i} description",
            priority=Priority.CRITICAL,
            goal=f"Milestone {i} goal",
            epics=[epics[i - 1]] if i <= 2 else [],
        )
        for i in range(1, 3)
    ]

    return Roadmap(
        id="roadmap-large",
        project_name="Large Project",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        context=sample_context,
        milestones=milestones,
    )


class TestStorageManagerSaveLoad:
    """Tests for save and load operations."""

    @pytest.mark.asyncio
    async def test_save_and_load_roundtrip(self, tmp_path, complete_roadmap):
        """Roadmap can be saved and loaded back with all fields intact."""
        storage = StorageManager(tmp_path)

        saved_path = await storage.save_roadmap(complete_roadmap)

        assert saved_path.exists()
        assert saved_path.name == "roadmap.json"

        loaded = await storage.load_roadmap(saved_path)

        assert loaded.id == complete_roadmap.id
        assert loaded.project_name == complete_roadmap.project_name
        assert len(loaded.milestones) == 1
        assert len(loaded.milestones[0].epics) == 1
        assert len(loaded.milestones[0].epics[0].stories) == 1
        assert len(loaded.milestones[0].epics[0].stories[0].tasks) == 1

    @pytest.mark.asyncio
    async def test_load_from_directory(self, tmp_path, complete_roadmap):
        """load_roadmap works with directory path."""
        storage = StorageManager(tmp_path)
        await storage.save_roadmap(complete_roadmap)

        project_dir = tmp_path / "test-project"
        loaded = await storage.load_roadmap(project_dir)

        assert loaded.id == complete_roadmap.id

    @pytest.mark.asyncio
    async def test_context_yaml_saved(self, tmp_path, complete_roadmap):
        """context.yaml is saved alongside roadmap.json."""
        storage = StorageManager(tmp_path)
        await storage.save_roadmap(complete_roadmap)

        context_path = tmp_path / "test-project" / "context.yaml"
        assert context_path.exists()

        with open(context_path) as f:
            context_data = yaml.safe_load(f)

        assert context_data["project_name"] == "Test Project"
        assert context_data["vision"] == "A test project for storage tests"
        assert "developers" in context_data["target_users"]

    @pytest.mark.asyncio
    async def test_load_context(self, tmp_path, complete_roadmap):
        """load_context loads context.yaml as ProjectContext."""
        storage = StorageManager(tmp_path)
        await storage.save_roadmap(complete_roadmap)

        context_path = tmp_path / "test-project" / "context.yaml"
        loaded_context = await storage.load_context(context_path)

        assert loaded_context.project_name == "Test Project"
        assert loaded_context.team_size == 2
        assert "Python" in loaded_context.tech_stack

    @pytest.mark.asyncio
    async def test_save_creates_directory(self, tmp_path, complete_roadmap):
        """save_roadmap creates project directory if it doesn't exist."""
        storage = StorageManager(tmp_path)

        project_dir = tmp_path / "test-project"
        assert not project_dir.exists()

        await storage.save_roadmap(complete_roadmap)

        assert project_dir.exists()
        assert project_dir.is_dir()


class TestResumePoint:
    """Tests for get_resume_point detection."""

    @pytest.mark.asyncio
    async def test_resume_point_complete(self, complete_roadmap):
        """Complete roadmap returns None for resume point."""
        storage = StorageManager(Path("."))

        resume = storage.get_resume_point(complete_roadmap)

        assert resume is None

    @pytest.mark.asyncio
    async def test_resume_point_missing_tasks(self, sample_context):
        """Detects story with no tasks."""
        story_no_tasks = Story(
            id="story-incomplete",
            name="Incomplete Story",
            description="Missing tasks",
            priority=Priority.HIGH,
            acceptance_criteria=["TBD"],
            tasks=[],
        )

        epic = Epic(
            id="epic-001",
            name="Epic",
            description="Epic desc",
            priority=Priority.HIGH,
            goal="Goal",
            stories=[story_no_tasks],
        )

        milestone = Milestone(
            id="milestone-001",
            name="MVP",
            description="MVP desc",
            priority=Priority.CRITICAL,
            goal="Launch",
            epics=[epic],
        )

        roadmap = Roadmap(
            id="roadmap-001",
            project_name="Test",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            context=sample_context,
            milestones=[milestone],
        )

        storage = StorageManager(Path("."))
        resume = storage.get_resume_point(roadmap)

        assert resume is not None
        assert "Incomplete Story" in resume
        assert "no tasks" in resume

    @pytest.mark.asyncio
    async def test_resume_point_missing_stories(self, sample_context):
        """Detects epic with no stories."""
        epic_no_stories = Epic(
            id="epic-incomplete",
            name="Empty Epic",
            description="No stories",
            priority=Priority.HIGH,
            goal="Goal",
            stories=[],
        )

        milestone = Milestone(
            id="milestone-001",
            name="MVP",
            description="MVP desc",
            priority=Priority.CRITICAL,
            goal="Launch",
            epics=[epic_no_stories],
        )

        roadmap = Roadmap(
            id="roadmap-001",
            project_name="Test",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            context=sample_context,
            milestones=[milestone],
        )

        storage = StorageManager(Path("."))
        resume = storage.get_resume_point(roadmap)

        assert resume is not None
        assert "Empty Epic" in resume
        assert "no stories" in resume

    @pytest.mark.asyncio
    async def test_resume_point_missing_epics(self, sample_context):
        """Detects milestone with no epics."""
        milestone_no_epics = Milestone(
            id="milestone-empty",
            name="Empty Milestone",
            description="No epics",
            priority=Priority.CRITICAL,
            goal="Goal",
            epics=[],
        )

        roadmap = Roadmap(
            id="roadmap-001",
            project_name="Test",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            context=sample_context,
            milestones=[milestone_no_epics],
        )

        storage = StorageManager(Path("."))
        resume = storage.get_resume_point(roadmap)

        assert resume is not None
        assert "Empty Milestone" in resume
        assert "no epics" in resume


class TestSlugify:
    """Tests for _slugify static method."""

    def test_slugify_spaces(self):
        """Spaces are replaced with hyphens."""
        assert StorageManager._slugify("My Cool Project") == "my-cool-project"

    def test_slugify_underscores(self):
        """Underscores are replaced with hyphens."""
        assert StorageManager._slugify("hello_world") == "hello-world"

    def test_slugify_mixed(self):
        """Mixed spaces and underscores."""
        assert StorageManager._slugify("Hello_World Project") == "hello-world-project"

    def test_slugify_lowercase(self):
        """Result is lowercase."""
        assert StorageManager._slugify("UPPERCASE") == "uppercase"

    def test_slugify_already_slug(self):
        """Already slugified names are unchanged."""
        assert StorageManager._slugify("already-slugified") == "already-slugified"
