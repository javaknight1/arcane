"""Tests for arcane.generators.base module."""

import pytest
from pydantic import BaseModel
from rich.console import Console

from arcane.core.clients.base import BaseAIClient, AIClientError, UsageStats
from arcane.core.generators.base import BaseGenerator, GenerationError
from arcane.core.generators.skeletons import MilestoneSkeleton, MilestoneSkeletonList
from arcane.core.items.base import Priority
from arcane.core.items.context import ProjectContext
from arcane.core.templates.loader import TemplateLoader


class MockClient(BaseAIClient):
    """Mock AI client for testing that returns pre-built responses."""

    def __init__(
        self,
        response: BaseModel | None = None,
        fail_count: int = 0,
    ):
        """Initialize mock client.

        Args:
            response: The response to return on successful calls.
            fail_count: Number of times to fail before succeeding.
                       If -1, always fails.
        """
        self._response = response
        self._fail_count = fail_count
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

        if self._fail_count == -1 or self._call_count <= self._fail_count:
            raise AIClientError(f"Mock failure #{self._call_count}")

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


class MilestoneGeneratorStub(BaseGenerator):
    """Concrete generator stub for testing."""

    @property
    def item_type(self) -> str:
        return "milestone"

    def get_response_model(self) -> type[BaseModel]:
        return MilestoneSkeletonList


@pytest.fixture
def sample_project_context():
    """Sample ProjectContext for testing."""
    return ProjectContext(
        project_name="TestProject",
        vision="A test project for unit testing",
        problem_statement="Testing generators is important",
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
def sample_response():
    """Sample MilestoneSkeletonList response."""
    return MilestoneSkeletonList(
        milestones=[
            MilestoneSkeleton(
                name="MVP",
                goal="Launch minimum viable product",
                description="First release with core functionality",
                priority=Priority.HIGH,
                suggested_epic_areas=["Core Features", "Basic UI"],
            ),
        ]
    )


@pytest.fixture
def console():
    """Rich console for testing (quiet mode)."""
    return Console(quiet=True)


@pytest.fixture
def templates():
    """Real TemplateLoader instance."""
    return TemplateLoader()


class TestBaseGeneratorGenerate:
    """Tests for BaseGenerator.generate() method."""

    @pytest.mark.asyncio
    async def test_generate_returns_response(
        self,
        sample_project_context,
        sample_response,
        console,
        templates,
    ):
        """generate() calls client and returns response model."""
        client = MockClient(response=sample_response)
        generator = MilestoneGeneratorStub(client, console, templates)

        result = await generator.generate(sample_project_context)

        assert isinstance(result, MilestoneSkeletonList)
        assert len(result.milestones) == 1
        assert result.milestones[0].name == "MVP"

    @pytest.mark.asyncio
    async def test_generate_retry_on_failure(
        self,
        sample_project_context,
        sample_response,
        console,
        templates,
    ):
        """generate() retries on first failure and succeeds on second."""
        client = MockClient(response=sample_response, fail_count=1)
        generator = MilestoneGeneratorStub(client, console, templates)

        result = await generator.generate(sample_project_context)

        assert isinstance(result, MilestoneSkeletonList)
        assert client._call_count == 2

    @pytest.mark.asyncio
    async def test_generate_raises_after_max_retries(
        self,
        sample_project_context,
        console,
        templates,
    ):
        """generate() raises GenerationError after max_retries exhausted."""
        client = MockClient(response=None, fail_count=-1)  # Always fails
        generator = MilestoneGeneratorStub(client, console, templates, max_retries=3)

        with pytest.raises(GenerationError) as exc_info:
            await generator.generate(sample_project_context)

        assert "Failed to generate milestone after 3 attempts" in str(exc_info.value)
        assert client._call_count == 3

    @pytest.mark.asyncio
    async def test_generate_with_parent_context(
        self,
        sample_project_context,
        sample_response,
        console,
        templates,
    ):
        """generate() accepts parent_context parameter."""
        client = MockClient(response=sample_response)
        generator = MilestoneGeneratorStub(client, console, templates)

        parent = {"milestone": {"name": "Parent", "goal": "Parent goal"}}
        result = await generator.generate(
            sample_project_context,
            parent_context=parent,
        )

        assert isinstance(result, MilestoneSkeletonList)

    @pytest.mark.asyncio
    async def test_generate_with_sibling_context(
        self,
        sample_project_context,
        sample_response,
        console,
        templates,
    ):
        """generate() accepts sibling_context parameter."""
        client = MockClient(response=sample_response)
        generator = MilestoneGeneratorStub(client, console, templates)

        siblings = ["Sibling 1", "Sibling 2"]
        result = await generator.generate(
            sample_project_context,
            sibling_context=siblings,
        )

        assert isinstance(result, MilestoneSkeletonList)

    @pytest.mark.asyncio
    async def test_generate_with_additional_guidance(
        self,
        sample_project_context,
        sample_response,
        console,
        templates,
    ):
        """generate() accepts additional_guidance parameter."""
        client = MockClient(response=sample_response)
        generator = MilestoneGeneratorStub(client, console, templates)

        result = await generator.generate(
            sample_project_context,
            additional_guidance="Focus on security",
        )

        assert isinstance(result, MilestoneSkeletonList)


class TestBaseGeneratorProperties:
    """Tests for BaseGenerator properties and methods."""

    def test_item_type_is_abstract(self):
        """item_type must be implemented by subclasses."""
        # MilestoneGeneratorStub implements it
        client = MockClient()
        console = Console(quiet=True)
        templates = TemplateLoader()
        generator = MilestoneGeneratorStub(client, console, templates)

        assert generator.item_type == "milestone"

    def test_get_response_model_is_abstract(self):
        """get_response_model must be implemented by subclasses."""
        client = MockClient()
        console = Console(quiet=True)
        templates = TemplateLoader()
        generator = MilestoneGeneratorStub(client, console, templates)

        assert generator.get_response_model() == MilestoneSkeletonList

    def test_validate_returns_empty_list_by_default(
        self,
        sample_project_context,
        sample_response,
    ):
        """_validate() returns empty list by default."""
        client = MockClient()
        console = Console(quiet=True)
        templates = TemplateLoader()
        generator = MilestoneGeneratorStub(client, console, templates)

        errors = generator._validate(sample_response, sample_project_context, None)

        assert errors == []


class TestGenerationError:
    """Tests for GenerationError exception."""

    def test_generation_error_is_exception(self):
        """GenerationError is a proper Exception."""
        error = GenerationError("Test error")
        assert isinstance(error, Exception)
        assert str(error) == "Test error"

    def test_generation_error_can_be_raised(self):
        """GenerationError can be raised and caught."""
        with pytest.raises(GenerationError) as exc_info:
            raise GenerationError("Generation failed")

        assert "Generation failed" in str(exc_info.value)
