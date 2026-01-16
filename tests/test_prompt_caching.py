"""Tests for Claude prompt caching functionality."""

import pytest
import sys
from unittest.mock import MagicMock, patch, PropertyMock
from typing import List

# Import items first (they don't need anthropic)
from arcane.items.milestone import Milestone
from arcane.items.epic import Epic
from arcane.items.story import Story
from arcane.items.task import Task
from arcane.items.base import ItemStatus


class MockUsage:
    """Mock usage object with cache stats."""
    def __init__(self, cache_creation=0, cache_read=0):
        self.cache_creation_input_tokens = cache_creation
        self.cache_read_input_tokens = cache_read
        self.input_tokens = 1000
        self.output_tokens = 500


class MockResponse:
    """Mock Claude API response."""
    def __init__(self, text: str, usage: MockUsage = None):
        self.content = [MagicMock(text=text)]
        self.usage = usage or MockUsage()


@pytest.fixture
def mock_anthropic_module():
    """Fixture to mock the anthropic module."""
    mock_module = MagicMock()
    with patch.dict(sys.modules, {'anthropic': mock_module}):
        yield mock_module


class TestClaudeClientCaching:
    """Tests for ClaudeLLMClient caching methods."""

    @patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'})
    def test_create_cacheable_context(self, mock_anthropic_module):
        """Test creating cacheable context."""
        from arcane.clients.claude import ClaudeLLMClient
        mock_anthropic_module.Anthropic.return_value = MagicMock()
        client = ClaudeLLMClient()

        context = client.create_cacheable_context("Test roadmap context")

        assert "ROADMAP CONTEXT (CACHED)" in context
        assert "Test roadmap context" in context
        assert "INSTRUCTIONS" in context
        assert "consistency" in context.lower()

    @patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'})
    def test_generate_with_cached_system_basic(self, mock_anthropic_module):
        """Test basic cached system generation."""
        from arcane.clients.claude import ClaudeLLMClient
        mock_api_client = MagicMock()
        mock_api_client.messages.create.return_value = MockResponse("Generated content")
        mock_anthropic_module.Anthropic.return_value = mock_api_client

        client = ClaudeLLMClient()

        result = client.generate_with_cached_system(
            system_prompt="System prompt",
            user_prompt="User prompt"
        )

        assert result == "Generated content"

        # Verify cache_control was passed
        call_args = mock_api_client.messages.create.call_args
        system_config = call_args.kwargs['system'][0]
        assert system_config['cache_control'] == {"type": "ephemeral"}

    @patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'})
    def test_generate_with_cached_system_cache_disabled(self, mock_anthropic_module):
        """Test cached system generation with caching disabled."""
        from arcane.clients.claude import ClaudeLLMClient
        mock_api_client = MagicMock()
        mock_api_client.messages.create.return_value = MockResponse("Content")
        mock_anthropic_module.Anthropic.return_value = mock_api_client

        client = ClaudeLLMClient()

        result = client.generate_with_cached_system(
            system_prompt="System prompt",
            user_prompt="User prompt",
            cache_system=False
        )

        # Verify no cache_control was passed
        call_args = mock_api_client.messages.create.call_args
        system_config = call_args.kwargs['system'][0]
        assert 'cache_control' not in system_config

    @patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'})
    def test_generate_with_cached_system_logs_cache_stats(self, mock_anthropic_module):
        """Test that cache stats are logged."""
        from arcane.clients.claude import ClaudeLLMClient
        mock_api_client = MagicMock()
        mock_api_client.messages.create.return_value = MockResponse(
            "Content",
            MockUsage(cache_creation=100, cache_read=50)
        )
        mock_anthropic_module.Anthropic.return_value = mock_api_client

        client = ClaudeLLMClient()

        # Should not raise
        result = client.generate_with_cached_system(
            system_prompt="System",
            user_prompt="User"
        )

        assert result == "Content"

    @patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'})
    def test_generate_batch_with_cached_system(self, mock_anthropic_module):
        """Test batch generation with cached system."""
        from arcane.clients.claude import ClaudeLLMClient
        mock_api_client = MagicMock()
        mock_api_client.messages.create.side_effect = [
            MockResponse("Response 1"),
            MockResponse("Response 2"),
            MockResponse("Response 3"),
        ]
        mock_anthropic_module.Anthropic.return_value = mock_api_client

        client = ClaudeLLMClient()

        results = client.generate_batch_with_cached_system(
            system_prompt="System",
            user_prompts=["Prompt 1", "Prompt 2", "Prompt 3"]
        )

        assert len(results) == 3
        assert results[0] == "Response 1"
        assert results[1] == "Response 2"
        assert results[2] == "Response 3"

    @patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'})
    def test_get_cache_pricing_info(self, mock_anthropic_module):
        """Test cache pricing info."""
        from arcane.clients.claude import ClaudeLLMClient
        mock_anthropic_module.Anthropic.return_value = MagicMock()
        client = ClaudeLLMClient()

        pricing = client.get_cache_pricing_info()

        assert 'cache_write_cost_per_token' in pricing
        assert 'cache_read_cost_per_token' in pricing
        assert 'base_input_cost_per_token' in pricing
        assert 'cache_ttl_minutes' in pricing
        assert pricing['cache_ttl_minutes'] == 5

    @patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'})
    def test_generate_with_cached_system_retry_on_error(self, mock_anthropic_module):
        """Test retry logic on recoverable errors."""
        from arcane.clients.claude import ClaudeLLMClient
        mock_api_client = MagicMock()
        mock_api_client.messages.create.side_effect = [
            Exception("overloaded error"),
            MockResponse("Success after retry")
        ]
        mock_anthropic_module.Anthropic.return_value = mock_api_client

        client = ClaudeLLMClient()

        with patch('time.sleep'):  # Skip actual sleep
            result = client.generate_with_cached_system(
                system_prompt="System",
                user_prompt="User"
            )

        assert result == "Success after retry"
        assert mock_api_client.messages.create.call_count == 2


class TestRecursiveGeneratorCaching:
    """Tests for RecursiveRoadmapGenerator caching."""

    @pytest.fixture(autouse=True)
    def setup_generator(self):
        """Import generator with mocked anthropic module."""
        from arcane.engines.generation.recursive_generator import RecursiveRoadmapGenerator
        self.RecursiveRoadmapGenerator = RecursiveRoadmapGenerator

    def _create_mock_client(self):
        """Create a mock LLM client."""
        client = MagicMock()
        client.provider = 'claude'
        client.generate.return_value = "Generated content"
        client.generate_with_cached_system.return_value = "Cached content"
        client.create_cacheable_context.return_value = "Cached system prompt"
        return client

    def _create_sample_milestones(self) -> List[Milestone]:
        """Create sample milestones for testing."""
        milestone = Milestone(name="Test Milestone", number="1")
        milestone.outline_description = "Test milestone description"

        epic = Epic(name="Test Epic", number="1.0", parent=milestone)
        epic.outline_description = "Test epic description"

        story = Story(name="Test Story", number="1.0.1", parent=epic)
        story.outline_description = "Test story description"

        task = Task(name="Test Task", number="1.0.1.1", parent=story)
        task.outline_description = "Test task description"

        return [milestone]

    def test_init_caching_enabled_by_default(self):
        """Test that caching is enabled by default."""
        client = self._create_mock_client()
        generator = self.RecursiveRoadmapGenerator(client)

        assert generator._use_prompt_caching is True
        assert generator._cached_system_prompt is None

    def test_set_prompt_caching(self):
        """Test enabling/disabling prompt caching."""
        client = self._create_mock_client()
        generator = self.RecursiveRoadmapGenerator(client)

        generator.set_prompt_caching(False)
        assert generator._use_prompt_caching is False

        generator.set_prompt_caching(True)
        assert generator._use_prompt_caching is True

    def test_get_cache_stats_initial(self):
        """Test initial cache stats."""
        client = self._create_mock_client()
        generator = self.RecursiveRoadmapGenerator(client)

        stats = generator.get_cache_stats()

        assert stats['cache_hits'] == 0
        assert stats['cache_misses'] == 0
        assert stats['requests_with_caching'] == 0

    def test_invalidate_cache(self):
        """Test cache invalidation."""
        client = self._create_mock_client()
        generator = self.RecursiveRoadmapGenerator(client)

        # Set a cached prompt
        generator._cached_system_prompt = "Some cached prompt"

        generator.invalidate_cache()

        assert generator._cached_system_prompt is None

    def test_build_full_roadmap_context(self):
        """Test building full roadmap context."""
        client = self._create_mock_client()
        generator = self.RecursiveRoadmapGenerator(client)
        milestones = self._create_sample_milestones()

        context = generator._build_full_roadmap_context(milestones)

        assert "ROADMAP STRUCTURE" in context
        assert "Milestone 1" in context
        assert "Epic 1.0" in context
        assert "Story 1.0.1" in context
        assert "Task 1.0.1.1" in context

    def test_build_item_user_prompt(self):
        """Test building item user prompt."""
        client = self._create_mock_client()
        generator = self.RecursiveRoadmapGenerator(client)
        milestones = self._create_sample_milestones()
        item = milestones[0]

        prompt = generator._build_item_user_prompt(
            item,
            project_context="Test project",
            parent_context="Test parent",
            additional_context="Additional info"
        )

        assert "Generate content for Milestone" in prompt
        assert "Test project" in prompt
        assert "Test parent" in prompt
        assert "Additional info" in prompt
        assert "Generation Status" in prompt

    def test_generate_with_caching_creates_cache(self):
        """Test that first call creates cache."""
        client = self._create_mock_client()
        generator = self.RecursiveRoadmapGenerator(client, model_mode='standard')
        # Ensure our mock is used (bypasses _get_client_for_item)
        generator._client_cache['default'] = client
        generator._client_cache['milestone'] = client

        milestones = self._create_sample_milestones()
        item = milestones[0]

        # First call should create cache
        result = generator._generate_with_caching(
            item,
            project_context="Test project",
            milestones=milestones
        )

        assert generator._cached_system_prompt is not None
        assert generator._cache_stats['cache_misses'] == 1
        assert generator._cache_stats['requests_with_caching'] == 1

    def test_generate_with_caching_reuses_cache(self):
        """Test that subsequent calls reuse cache."""
        client = self._create_mock_client()
        generator = self.RecursiveRoadmapGenerator(client, model_mode='standard')
        # Ensure our mock is used
        generator._client_cache['default'] = client
        generator._client_cache['milestone'] = client

        milestones = self._create_sample_milestones()
        item = milestones[0]

        # First call
        generator._generate_with_caching(item, "Project", milestones)

        # Second call should reuse cache
        generator._generate_with_caching(item, "Project", milestones)

        assert generator._cache_stats['cache_misses'] == 1
        assert generator._cache_stats['cache_hits'] == 1
        assert generator._cache_stats['requests_with_caching'] == 2

    def test_generate_with_caching_fallback_for_non_claude(self):
        """Test fallback for non-Claude clients."""
        client = MagicMock(spec=['generate', 'provider'])
        client.provider = 'openai'
        client.generate.return_value = "OpenAI response"
        # spec ensures generate_with_cached_system doesn't exist

        generator = self.RecursiveRoadmapGenerator(client, model_mode='standard')
        # Ensure our mock is used
        generator._client_cache['default'] = client
        generator._client_cache['milestone'] = client

        milestones = self._create_sample_milestones()
        item = milestones[0]
        # Mock the generate_prompt to avoid template formatting issues
        item.generate_prompt = MagicMock(return_value="Test prompt")

        # Should fall back to regular generation
        result = generator._generate_with_caching(
            item,
            project_context="Test",
            milestones=milestones
        )

        client.generate.assert_called_once()


class TestItemGenerationInstructions:
    """Tests for Item.get_generation_instructions method."""

    def test_basic_instructions(self):
        """Test basic generation instructions."""
        milestone = Milestone(name="Test Milestone", number="1")

        instructions = milestone.get_generation_instructions()

        assert "Generate detailed content" in instructions
        assert "Milestone" in instructions
        assert "Output requirements" in instructions

    def test_instructions_with_semantic_context(self):
        """Test instructions include semantic context."""
        milestone = Milestone(name="Test", number="1")
        milestone.outline_description = "Test description"
        milestone.outline_what = "Test what"
        milestone.outline_why = "Test why"

        instructions = milestone.get_generation_instructions()

        assert "Test description" in instructions
        assert "Test what" in instructions
        assert "Test why" in instructions

    def test_instructions_without_semantic_context(self):
        """Test instructions without semantic context."""
        milestone = Milestone(name="Test", number="1")

        instructions = milestone.get_generation_instructions()

        # Should still have basic instructions
        assert "Generate detailed content" in instructions


class TestCachingIntegration:
    """Integration tests for caching functionality."""

    @pytest.fixture(autouse=True)
    def setup_generator(self):
        """Import generator."""
        from arcane.engines.generation.recursive_generator import RecursiveRoadmapGenerator
        self.RecursiveRoadmapGenerator = RecursiveRoadmapGenerator

    def test_full_caching_workflow(self):
        """Test full caching workflow."""
        client = MagicMock()
        client.provider = 'claude'
        client.generate.return_value = "Generated"
        client.generate_with_cached_system.return_value = "Cached response"
        client.create_cacheable_context.return_value = "System prompt"

        generator = self.RecursiveRoadmapGenerator(client, model_mode='standard')

        # Create multiple milestones
        m1 = Milestone(name="First", number="1")
        m1.outline_description = "First milestone"
        m2 = Milestone(name="Second", number="2")
        m2.outline_description = "Second milestone"
        milestones = [m1, m2]

        # Generate for first item - cache miss
        generator._generate_with_caching(m1, "Project", milestones)
        assert generator._cache_stats['cache_misses'] == 1

        # Generate for second item - cache hit
        generator._generate_with_caching(m2, "Project", milestones)
        assert generator._cache_stats['cache_hits'] == 1

        # Invalidate and generate again - cache miss
        generator.invalidate_cache()
        generator._generate_with_caching(m1, "Project", milestones)
        assert generator._cache_stats['cache_misses'] == 2

    def test_caching_disabled_workflow(self):
        """Test workflow with caching disabled."""
        client = MagicMock()
        client.provider = 'claude'
        client.generate_with_cached_system.return_value = "Response"
        client.create_cacheable_context.return_value = "System prompt"

        generator = self.RecursiveRoadmapGenerator(client, model_mode='standard')
        generator.set_prompt_caching(False)

        milestone = Milestone(name="M1", number="1")
        milestones = [milestone]

        generator._generate_with_caching(milestone, "Project", milestones)

        # Should still call generate_with_cached_system but with cache_system=False
        call_args = client.generate_with_cached_system.call_args
        assert call_args.kwargs['cache_system'] is False
