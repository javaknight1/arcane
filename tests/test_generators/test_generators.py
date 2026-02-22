"""Tests for individual generator implementations."""

import pytest
from pydantic import BaseModel
from rich.console import Console

from arcane.core.clients.base import BaseAIClient, AIClientError, UsageStats
from arcane.core.generators import (
    MilestoneGenerator,
    EpicGenerator,
    StoryGenerator,
    TaskGenerator,
    TaskList,
    MilestoneSkeletonList,
    MilestoneSkeleton,
    EpicSkeletonList,
    EpicSkeleton,
    StorySkeletonList,
    StorySkeleton,
)
from arcane.core.items import Task, Priority
from arcane.core.items.context import ProjectContext
from arcane.core.templates.loader import TemplateLoader


class MockClient(BaseAIClient):
    """Mock AI client that captures call arguments and returns pre-built responses."""

    def __init__(self, response: BaseModel | None = None):
        self._response = response
        self._last_system_prompt: str | None = None
        self._last_user_prompt: str | None = None
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
        self._last_system_prompt = system_prompt
        self._last_user_prompt = user_prompt
        self._call_count += 1
        return self._response

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
def sample_project_context():
    """Sample ProjectContext for testing."""
    return ProjectContext(
        project_name="TestProject",
        vision="A test project",
        problem_statement="Testing is important",
        target_users=["developers"],
        timeline="1 month",
        team_size=1,
        developer_experience="senior",
        budget_constraints="minimal",
        tech_stack=["Python"],
        infrastructure_preferences="No preference",
        existing_codebase=False,
        must_have_features=["core feature"],
        nice_to_have_features=[],
        out_of_scope=[],
        similar_products=[],
        notes="",
    )


@pytest.fixture
def console():
    """Rich console for testing (quiet mode)."""
    return Console(quiet=True)


@pytest.fixture
def templates():
    """Real TemplateLoader instance."""
    return TemplateLoader()


class TestMilestoneGenerator:
    """Tests for MilestoneGenerator."""

    def test_item_type(self, console, templates):
        """item_type returns 'milestone'."""
        client = MockClient()
        generator = MilestoneGenerator(client, console, templates)
        assert generator.item_type == "milestone"

    def test_get_response_model(self, console, templates):
        """get_response_model returns MilestoneSkeletonList."""
        client = MockClient()
        generator = MilestoneGenerator(client, console, templates)
        assert generator.get_response_model() == MilestoneSkeletonList

    @pytest.mark.asyncio
    async def test_generate_returns_milestone_list(
        self, sample_project_context, console, templates
    ):
        """generate() returns MilestoneSkeletonList."""
        response = MilestoneSkeletonList(
            milestones=[
                MilestoneSkeleton(
                    name="MVP",
                    goal="Launch MVP",
                    description="First release",
                    priority=Priority.HIGH,
                    suggested_epic_areas=["Core"],
                )
            ]
        )
        client = MockClient(response=response)
        generator = MilestoneGenerator(client, console, templates)

        result = await generator.generate(sample_project_context)

        assert isinstance(result, MilestoneSkeletonList)
        assert len(result.milestones) == 1

    @pytest.mark.asyncio
    async def test_uses_milestone_template(
        self, sample_project_context, console, templates
    ):
        """MilestoneGenerator uses milestone system template."""
        response = MilestoneSkeletonList(milestones=[])
        client = MockClient(response=response)
        generator = MilestoneGenerator(client, console, templates)

        await generator.generate(sample_project_context)

        # Check that the system prompt contains milestone-specific content
        assert client._last_system_prompt is not None
        assert "milestone" in client._last_system_prompt.lower()


class TestEpicGenerator:
    """Tests for EpicGenerator."""

    def test_item_type(self, console, templates):
        """item_type returns 'epic'."""
        client = MockClient()
        generator = EpicGenerator(client, console, templates)
        assert generator.item_type == "epic"

    def test_get_response_model(self, console, templates):
        """get_response_model returns EpicSkeletonList."""
        client = MockClient()
        generator = EpicGenerator(client, console, templates)
        assert generator.get_response_model() == EpicSkeletonList

    @pytest.mark.asyncio
    async def test_generate_returns_epic_list(
        self, sample_project_context, console, templates
    ):
        """generate() returns EpicSkeletonList."""
        response = EpicSkeletonList(
            epics=[
                EpicSkeleton(
                    name="Auth",
                    goal="User authentication",
                    description="Auth system",
                    priority=Priority.CRITICAL,
                    suggested_story_areas=["Login"],
                )
            ]
        )
        client = MockClient(response=response)
        generator = EpicGenerator(client, console, templates)

        result = await generator.generate(sample_project_context)

        assert isinstance(result, EpicSkeletonList)
        assert len(result.epics) == 1

    @pytest.mark.asyncio
    async def test_uses_epic_template(
        self, sample_project_context, console, templates
    ):
        """EpicGenerator uses epic system template."""
        response = EpicSkeletonList(epics=[])
        client = MockClient(response=response)
        generator = EpicGenerator(client, console, templates)

        await generator.generate(sample_project_context)

        assert client._last_system_prompt is not None
        assert "epic" in client._last_system_prompt.lower()


class TestStoryGenerator:
    """Tests for StoryGenerator."""

    def test_item_type(self, console, templates):
        """item_type returns 'story'."""
        client = MockClient()
        generator = StoryGenerator(client, console, templates)
        assert generator.item_type == "story"

    def test_get_response_model(self, console, templates):
        """get_response_model returns StorySkeletonList."""
        client = MockClient()
        generator = StoryGenerator(client, console, templates)
        assert generator.get_response_model() == StorySkeletonList

    @pytest.mark.asyncio
    async def test_generate_returns_story_list(
        self, sample_project_context, console, templates
    ):
        """generate() returns StorySkeletonList."""
        response = StorySkeletonList(
            stories=[
                StorySkeleton(
                    name="User Login",
                    description="Users can log in",
                    priority=Priority.CRITICAL,
                    acceptance_criteria=["Can login"],
                )
            ]
        )
        client = MockClient(response=response)
        generator = StoryGenerator(client, console, templates)

        result = await generator.generate(sample_project_context)

        assert isinstance(result, StorySkeletonList)
        assert len(result.stories) == 1

    @pytest.mark.asyncio
    async def test_uses_story_template(
        self, sample_project_context, console, templates
    ):
        """StoryGenerator uses story system template."""
        response = StorySkeletonList(stories=[])
        client = MockClient(response=response)
        generator = StoryGenerator(client, console, templates)

        await generator.generate(sample_project_context)

        assert client._last_system_prompt is not None
        assert "story" in client._last_system_prompt.lower()


class TestTaskGenerator:
    """Tests for TaskGenerator."""

    def test_item_type(self, console, templates):
        """item_type returns 'task'."""
        client = MockClient()
        generator = TaskGenerator(client, console, templates)
        assert generator.item_type == "task"

    def test_get_response_model(self, console, templates):
        """get_response_model returns TaskList (not a skeleton)."""
        client = MockClient()
        generator = TaskGenerator(client, console, templates)
        assert generator.get_response_model() == TaskList

    @pytest.mark.asyncio
    async def test_generate_returns_task_list(
        self, sample_project_context, console, templates
    ):
        """generate() returns TaskList with full Task objects."""
        response = TaskList(
            tasks=[
                Task(
                    id="task-001",
                    name="Implement login form",
                    description="Create the login form component",
                    priority=Priority.HIGH,
                    estimated_hours=4,
                    acceptance_criteria=["Form renders", "Validates input"],
                    implementation_notes="Use React Hook Form",
                    claude_code_prompt="Create a login form component...",
                )
            ]
        )
        client = MockClient(response=response)
        generator = TaskGenerator(client, console, templates)

        result = await generator.generate(sample_project_context)

        assert isinstance(result, TaskList)
        assert len(result.tasks) == 1
        assert isinstance(result.tasks[0], Task)
        assert result.tasks[0].estimated_hours == 4

    @pytest.mark.asyncio
    async def test_uses_task_template(
        self, sample_project_context, console, templates
    ):
        """TaskGenerator uses task system template."""
        response = TaskList(tasks=[])
        client = MockClient(response=response)
        generator = TaskGenerator(client, console, templates)

        await generator.generate(sample_project_context)

        assert client._last_system_prompt is not None
        assert "task" in client._last_system_prompt.lower()
        # Task template mentions claude_code_prompt
        assert "claude" in client._last_system_prompt.lower()


class TestTaskList:
    """Tests for TaskList model."""

    def test_task_list_creation(self):
        """TaskList can be created with Task objects."""
        task_list = TaskList(
            tasks=[
                Task(
                    id="task-001",
                    name="Test task",
                    description="A test task",
                    priority=Priority.MEDIUM,
                    estimated_hours=2,
                    acceptance_criteria=["Done"],
                    implementation_notes="Notes",
                    claude_code_prompt="Prompt",
                )
            ]
        )

        assert len(task_list.tasks) == 1
        assert task_list.tasks[0].name == "Test task"

    def test_task_list_empty(self):
        """TaskList can be empty."""
        task_list = TaskList(tasks=[])
        assert len(task_list.tasks) == 0

    def test_task_list_serialization(self):
        """TaskList can be serialized and deserialized."""
        original = TaskList(
            tasks=[
                Task(
                    id="task-001",
                    name="Test",
                    description="Desc",
                    priority=Priority.LOW,
                    estimated_hours=1,
                    acceptance_criteria=["AC"],
                    implementation_notes="Notes",
                    claude_code_prompt="Prompt",
                )
            ]
        )

        json_str = original.model_dump_json()
        restored = TaskList.model_validate_json(json_str)

        assert len(restored.tasks) == 1
        assert restored.tasks[0].name == "Test"
