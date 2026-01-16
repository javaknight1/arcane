"""Tests for extended thinking functionality."""

import pytest
import sys
from unittest.mock import MagicMock, patch
from typing import Dict, Any

# Import items first (they don't need anthropic)
from arcane.items.milestone import Milestone
from arcane.items.epic import Epic
from arcane.items.story import Story
from arcane.items.task import Task
from arcane.items.base import ItemStatus


class MockThinkingBlock:
    """Mock thinking block from Claude API."""
    def __init__(self, thinking: str):
        self.type = "thinking"
        self.thinking = thinking


class MockTextBlock:
    """Mock text block from Claude API."""
    def __init__(self, text: str):
        self.type = "text"
        self.text = text


class MockUsage:
    """Mock usage object."""
    def __init__(self, input_tokens=1000, output_tokens=500):
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens


class MockResponse:
    """Mock Claude API response with thinking."""
    def __init__(self, thinking: str = "", text: str = "", usage: MockUsage = None):
        self.content = []
        if thinking:
            self.content.append(MockThinkingBlock(thinking))
        if text:
            self.content.append(MockTextBlock(text))
        self.usage = usage or MockUsage()


@pytest.fixture
def mock_anthropic_module():
    """Fixture to mock the anthropic module."""
    mock_module = MagicMock()
    with patch.dict(sys.modules, {'anthropic': mock_module}):
        yield mock_module


class TestClaudeClientThinking:
    """Tests for ClaudeLLMClient extended thinking methods."""

    @patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'})
    def test_generate_with_thinking_basic(self, mock_anthropic_module):
        """Test basic thinking generation."""
        from arcane.clients.claude import ClaudeLLMClient
        mock_api_client = MagicMock()
        mock_api_client.messages.create.return_value = MockResponse(
            thinking="Let me think about this...",
            text="Here is my response"
        )
        mock_anthropic_module.Anthropic.return_value = mock_api_client

        client = ClaudeLLMClient()

        thinking, response = client.generate_with_thinking(
            prompt="Generate a milestone",
            thinking_budget=10000
        )

        assert thinking == "Let me think about this..."
        assert response == "Here is my response"

    @patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'})
    def test_generate_with_thinking_api_call(self, mock_anthropic_module):
        """Test that thinking API call has correct parameters."""
        from arcane.clients.claude import ClaudeLLMClient
        mock_api_client = MagicMock()
        mock_api_client.messages.create.return_value = MockResponse(
            thinking="Thinking...",
            text="Response"
        )
        mock_anthropic_module.Anthropic.return_value = mock_api_client

        client = ClaudeLLMClient()

        client.generate_with_thinking(
            prompt="Test prompt",
            thinking_budget=15000,
            max_tokens=20000
        )

        # Verify API call
        call_args = mock_api_client.messages.create.call_args
        assert call_args.kwargs['thinking'] == {
            "type": "enabled",
            "budget_tokens": 15000
        }
        assert call_args.kwargs['max_tokens'] == 20000

    @patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'})
    def test_generate_with_thinking_budget_clamping(self, mock_anthropic_module):
        """Test that thinking budget is clamped to valid range."""
        from arcane.clients.claude import ClaudeLLMClient
        mock_api_client = MagicMock()
        mock_api_client.messages.create.return_value = MockResponse(
            thinking="Thinking",
            text="Response"
        )
        mock_anthropic_module.Anthropic.return_value = mock_api_client

        client = ClaudeLLMClient()

        # Test minimum clamping
        client.generate_with_thinking(prompt="Test", thinking_budget=100)
        call_args = mock_api_client.messages.create.call_args
        assert call_args.kwargs['thinking']['budget_tokens'] == 1000  # Min is 1000

        # Test maximum clamping
        client.generate_with_thinking(prompt="Test", thinking_budget=200000)
        call_args = mock_api_client.messages.create.call_args
        assert call_args.kwargs['thinking']['budget_tokens'] == 100000  # Max is 100000

    @patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'})
    def test_generate_with_thinking_and_system(self, mock_anthropic_module):
        """Test thinking with system prompt."""
        from arcane.clients.claude import ClaudeLLMClient
        mock_api_client = MagicMock()
        mock_api_client.messages.create.return_value = MockResponse(
            thinking="Deep thinking...",
            text="Strategic response"
        )
        mock_anthropic_module.Anthropic.return_value = mock_api_client

        client = ClaudeLLMClient()

        thinking, response = client.generate_with_thinking_and_system(
            system_prompt="You are a roadmap generator",
            user_prompt="Generate a milestone",
            thinking_budget=10000,
            cache_system=True
        )

        assert thinking == "Deep thinking..."
        assert response == "Strategic response"

        # Verify system config with cache control
        call_args = mock_api_client.messages.create.call_args
        system_config = call_args.kwargs['system'][0]
        assert system_config['cache_control'] == {"type": "ephemeral"}

    @patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'})
    def test_generate_with_thinking_no_thinking_block(self, mock_anthropic_module):
        """Test handling response without thinking block."""
        from arcane.clients.claude import ClaudeLLMClient
        mock_api_client = MagicMock()
        mock_api_client.messages.create.return_value = MockResponse(
            thinking="",  # No thinking
            text="Just the response"
        )
        mock_anthropic_module.Anthropic.return_value = mock_api_client

        client = ClaudeLLMClient()

        thinking, response = client.generate_with_thinking(prompt="Test")

        assert thinking == ""
        assert response == "Just the response"

    @patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'})
    def test_generate_with_thinking_retry_on_error(self, mock_anthropic_module):
        """Test retry logic on recoverable errors."""
        from arcane.clients.claude import ClaudeLLMClient
        mock_api_client = MagicMock()
        mock_api_client.messages.create.side_effect = [
            Exception("overloaded error"),
            MockResponse(thinking="Thinking", text="Success after retry")
        ]
        mock_anthropic_module.Anthropic.return_value = mock_api_client

        client = ClaudeLLMClient()

        with patch('time.sleep'):
            thinking, response = client.generate_with_thinking(prompt="Test")

        assert response == "Success after retry"
        assert mock_api_client.messages.create.call_count == 2

    @patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'})
    def test_get_thinking_pricing_info(self, mock_anthropic_module):
        """Test thinking pricing info."""
        from arcane.clients.claude import ClaudeLLMClient
        mock_anthropic_module.Anthropic.return_value = MagicMock()
        client = ClaudeLLMClient()

        pricing = client.get_thinking_pricing_info()

        assert 'thinking_input_cost_per_token' in pricing
        assert 'min_thinking_budget' in pricing
        assert 'max_thinking_budget' in pricing
        assert 'recommended_budgets' in pricing
        assert pricing['min_thinking_budget'] == 1000
        assert pricing['max_thinking_budget'] == 100000


class TestRecursiveGeneratorThinking:
    """Tests for RecursiveRoadmapGenerator thinking integration."""

    @pytest.fixture(autouse=True)
    def setup_generator(self):
        """Import generator."""
        from arcane.engines.generation.recursive_generator import RecursiveRoadmapGenerator
        self.RecursiveRoadmapGenerator = RecursiveRoadmapGenerator

    def _create_mock_client(self):
        """Create a mock LLM client with thinking support."""
        client = MagicMock()
        client.provider = 'claude'
        client.generate.return_value = "Generated content"
        client.generate_with_thinking.return_value = ("Thinking content", "Response content")
        return client

    def test_thinking_enabled_by_default(self):
        """Test that thinking is enabled by default."""
        client = self._create_mock_client()
        generator = self.RecursiveRoadmapGenerator(client)

        assert generator._use_extended_thinking is True
        assert 'milestone' in generator._thinking_item_types
        assert 'outline' in generator._thinking_item_types

    def test_set_extended_thinking(self):
        """Test enabling/disabling extended thinking."""
        client = self._create_mock_client()
        generator = self.RecursiveRoadmapGenerator(client)

        generator.set_extended_thinking(False)
        assert generator._use_extended_thinking is False

        generator.set_extended_thinking(True)
        assert generator._use_extended_thinking is True

    def test_configure_thinking_items(self):
        """Test configuring thinking item types."""
        client = self._create_mock_client()
        generator = self.RecursiveRoadmapGenerator(client)

        generator.configure_thinking_items(
            item_types=['milestone', 'epic', 'story'],
            budgets={'story': 5000}
        )

        assert 'story' in generator._thinking_item_types
        assert generator._thinking_budgets['story'] == 5000

    def test_get_thinking_stats_initial(self):
        """Test initial thinking stats."""
        client = self._create_mock_client()
        generator = self.RecursiveRoadmapGenerator(client)

        stats = generator.get_thinking_stats()

        assert stats['items_with_thinking'] == 0
        assert stats['stored_thinking_count'] == 0

    def test_should_use_thinking_milestone(self):
        """Test that milestones should use thinking."""
        client = self._create_mock_client()
        generator = self.RecursiveRoadmapGenerator(client)

        milestone = Milestone(name="Test", number="1")

        assert generator._should_use_thinking(milestone) is True

    def test_should_use_thinking_task(self):
        """Test that tasks should not use thinking."""
        client = self._create_mock_client()
        generator = self.RecursiveRoadmapGenerator(client)

        task = Task(name="Test", number="1.0.1.1")

        assert generator._should_use_thinking(task) is False

    def test_should_use_thinking_complex_epic(self):
        """Test that complex epics can use thinking."""
        client = self._create_mock_client()
        generator = self.RecursiveRoadmapGenerator(client)

        epic = Epic(name="Test", number="1.0")
        epic.complexity = 'complex'

        assert generator._should_use_thinking(epic) is True

    def test_should_use_thinking_disabled(self):
        """Test that no items use thinking when disabled."""
        client = self._create_mock_client()
        generator = self.RecursiveRoadmapGenerator(client)
        generator.set_extended_thinking(False)

        milestone = Milestone(name="Test", number="1")

        assert generator._should_use_thinking(milestone) is False

    def test_get_thinking_budget(self):
        """Test getting thinking budget for different items."""
        client = self._create_mock_client()
        generator = self.RecursiveRoadmapGenerator(client)

        milestone = Milestone(name="Test", number="1")
        assert generator._get_thinking_budget(milestone) == 10000

        # Custom budget
        generator.configure_thinking_items(budgets={'milestone': 20000})
        assert generator._get_thinking_budget(milestone) == 20000

    def test_generate_with_thinking(self):
        """Test generate with thinking method."""
        client = self._create_mock_client()
        generator = self.RecursiveRoadmapGenerator(client, model_mode='standard')

        milestone = Milestone(name="Test", number="1")

        response = generator._generate_with_thinking(
            item=milestone,
            prompt="Generate milestone content"
        )

        assert response == "Response content"
        client.generate_with_thinking.assert_called_once()

    def test_generate_with_thinking_stores_thinking(self):
        """Test that thinking content is stored."""
        client = self._create_mock_client()
        generator = self.RecursiveRoadmapGenerator(client, model_mode='standard')

        milestone = Milestone(name="Test", number="1")

        generator._generate_with_thinking(
            item=milestone,
            prompt="Generate"
        )

        assert milestone.id in generator._stored_thinking
        assert generator._stored_thinking[milestone.id] == "Thinking content"
        assert generator._thinking_stats['items_with_thinking'] == 1

    def test_get_stored_thinking(self):
        """Test retrieving stored thinking."""
        client = self._create_mock_client()
        generator = self.RecursiveRoadmapGenerator(client)

        generator._stored_thinking['1'] = "Thinking for milestone 1"

        thinking = generator.get_stored_thinking('1')
        assert thinking == "Thinking for milestone 1"

        thinking_missing = generator.get_stored_thinking('99')
        assert thinking_missing is None

    def test_get_all_stored_thinking(self):
        """Test getting all stored thinking."""
        client = self._create_mock_client()
        generator = self.RecursiveRoadmapGenerator(client)

        generator._stored_thinking['1'] = "Thinking 1"
        generator._stored_thinking['2'] = "Thinking 2"

        all_thinking = generator.get_all_stored_thinking()

        assert len(all_thinking) == 2
        assert all_thinking['1'] == "Thinking 1"

    def test_clear_stored_thinking(self):
        """Test clearing stored thinking."""
        client = self._create_mock_client()
        generator = self.RecursiveRoadmapGenerator(client)

        generator._stored_thinking['1'] = "Thinking 1"
        generator._stored_thinking['2'] = "Thinking 2"

        count = generator.clear_stored_thinking()

        assert count == 2
        assert len(generator._stored_thinking) == 0

    def test_generate_with_thinking_fallback(self):
        """Test fallback when client doesn't support thinking."""
        client = MagicMock(spec=['generate', 'provider'])
        client.provider = 'openai'
        client.generate.return_value = "Regular response"

        generator = self.RecursiveRoadmapGenerator(client, model_mode='standard')

        milestone = Milestone(name="Test", number="1")

        response = generator._generate_with_thinking(
            item=milestone,
            prompt="Generate"
        )

        assert response == "Regular response"
        client.generate.assert_called_once()


class TestThinkingIntegration:
    """Integration tests for extended thinking."""

    @pytest.fixture(autouse=True)
    def setup_generator(self):
        """Import generator."""
        from arcane.engines.generation.recursive_generator import RecursiveRoadmapGenerator
        self.RecursiveRoadmapGenerator = RecursiveRoadmapGenerator

    def test_full_thinking_workflow(self):
        """Test full thinking workflow for milestone generation."""
        client = MagicMock()
        client.provider = 'claude'
        client.generate_with_thinking.side_effect = [
            ("Strategic thinking for M1...", "Milestone 1 content"),
            ("Strategic thinking for M2...", "Milestone 2 content"),
        ]

        generator = self.RecursiveRoadmapGenerator(client, model_mode='standard')

        m1 = Milestone(name="Foundation", number="1")
        m2 = Milestone(name="Features", number="2")

        # Generate both milestones
        response1 = generator._generate_with_thinking(m1, "Generate M1")
        response2 = generator._generate_with_thinking(m2, "Generate M2")

        assert response1 == "Milestone 1 content"
        assert response2 == "Milestone 2 content"

        # Verify thinking was stored
        assert len(generator._stored_thinking) == 2
        assert "Strategic thinking for M1" in generator._stored_thinking['1']

        # Check stats
        stats = generator.get_thinking_stats()
        assert stats['items_with_thinking'] == 2

    def test_mixed_thinking_workflow(self):
        """Test workflow with mix of thinking and non-thinking items."""
        client = MagicMock()
        client.provider = 'claude'
        client.generate.return_value = "Regular task content"
        client.generate_with_thinking.return_value = ("Thinking...", "Milestone content")

        generator = self.RecursiveRoadmapGenerator(client, model_mode='standard')

        milestone = Milestone(name="M1", number="1")
        task = Task(name="T1", number="1.0.1.1")

        # Milestone should use thinking
        assert generator._should_use_thinking(milestone) is True

        # Task should not use thinking
        assert generator._should_use_thinking(task) is False

        # Generate milestone with thinking
        m_response = generator._generate_with_thinking(milestone, "Generate M1")
        assert m_response == "Milestone content"
        assert milestone.id in generator._stored_thinking

        # Task would use regular generation (via _should_use_thinking check)
        # In actual usage, the generator would call generate() for tasks
