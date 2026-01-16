"""Tests for structured outputs using Claude's tool use feature."""

import pytest
import sys
from unittest.mock import MagicMock, patch
from typing import Dict, Any

# Create mock anthropic module before importing Claude client
mock_anthropic = MagicMock()
sys.modules['anthropic'] = mock_anthropic

from arcane.clients.claude import (
    ClaudeLLMClient,
    TASK_SCHEMA,
    STORY_SCHEMA,
    EPIC_SCHEMA,
    MILESTONE_SCHEMA
)
from arcane.items.task import Task
from arcane.items.story import Story
from arcane.items.epic import Epic
from arcane.items.milestone import Milestone
from arcane.items.base import ItemStatus


class MockToolUseBlock:
    """Mock tool use block from Claude API."""
    def __init__(self, input_data: Dict[str, Any]):
        self.type = "tool_use"
        self.input = input_data


class MockTextBlock:
    """Mock text block from Claude API."""
    def __init__(self, text: str):
        self.type = "text"
        self.text = text


class MockResponse:
    """Mock Claude API response with tool use."""
    def __init__(self, blocks):
        self.content = blocks


class TestSchemas:
    """Tests for JSON schemas."""

    def test_task_schema_structure(self):
        """Test TASK_SCHEMA has expected structure."""
        assert TASK_SCHEMA["type"] == "object"
        assert "properties" in TASK_SCHEMA
        assert "required" in TASK_SCHEMA

        # Check required fields
        required = TASK_SCHEMA["required"]
        assert "title" in required
        assert "description" in required
        assert "work_type" in required
        assert "complexity" in required
        assert "duration_hours" in required

    def test_task_schema_enums(self):
        """Test TASK_SCHEMA has correct enum values."""
        work_type = TASK_SCHEMA["properties"]["work_type"]
        assert "enum" in work_type
        assert "implementation" in work_type["enum"]
        assert "testing" in work_type["enum"]

        complexity = TASK_SCHEMA["properties"]["complexity"]
        assert "enum" in complexity
        assert "simple" in complexity["enum"]
        assert "moderate" in complexity["enum"]
        assert "complex" in complexity["enum"]

    def test_story_schema_structure(self):
        """Test STORY_SCHEMA has expected structure."""
        assert STORY_SCHEMA["type"] == "object"
        assert "acceptance_criteria" in STORY_SCHEMA["properties"]
        assert STORY_SCHEMA["properties"]["acceptance_criteria"]["type"] == "array"

        # Check required fields
        required = STORY_SCHEMA["required"]
        assert "title" in required
        assert "user_value" in required
        assert "acceptance_criteria" in required

    def test_story_schema_scope_fields(self):
        """Test STORY_SCHEMA has scope fields."""
        props = STORY_SCHEMA["properties"]
        assert "scope_in" in props
        assert "scope_out" in props
        assert props["scope_in"]["type"] == "array"
        assert props["scope_out"]["type"] == "array"

    def test_epic_schema_structure(self):
        """Test EPIC_SCHEMA has expected structure."""
        assert EPIC_SCHEMA["type"] == "object"
        assert "goals" in EPIC_SCHEMA["properties"]
        assert "risks_and_mitigations" in EPIC_SCHEMA["properties"]

        # Check required fields
        required = EPIC_SCHEMA["required"]
        assert "title" in required
        assert "goals" in required

    def test_milestone_schema_structure(self):
        """Test MILESTONE_SCHEMA has expected structure."""
        assert MILESTONE_SCHEMA["type"] == "object"
        assert "key_deliverables" in MILESTONE_SCHEMA["properties"]
        assert "success_criteria" in MILESTONE_SCHEMA["properties"]

        # Check required fields
        required = MILESTONE_SCHEMA["required"]
        assert "title" in required
        assert "goal" in required
        assert "key_deliverables" in required


class TestClaudeGenerateStructured:
    """Tests for ClaudeLLMClient.generate_structured method."""

    @patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'})
    def test_generate_structured_basic(self):
        """Test basic structured generation."""
        mock_client = MagicMock()
        tool_data = {
            "title": "Test Task",
            "description": "Test description",
            "work_type": "implementation",
            "complexity": "moderate",
            "duration_hours": 4
        }
        mock_client.messages.create.return_value = MockResponse([
            MockToolUseBlock(tool_data)
        ])
        mock_anthropic.Anthropic.return_value = mock_client

        client = ClaudeLLMClient()

        result = client.generate_structured(
            prompt="Generate a task",
            schema=TASK_SCHEMA
        )

        assert result == tool_data
        assert result["title"] == "Test Task"

    @patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'})
    def test_generate_structured_tool_choice(self):
        """Test that tool_choice is set correctly."""
        mock_client = MagicMock()
        mock_client.messages.create.return_value = MockResponse([
            MockToolUseBlock({"title": "Test"})
        ])
        mock_anthropic.Anthropic.return_value = mock_client

        client = ClaudeLLMClient()

        client.generate_structured(
            prompt="Generate",
            schema=TASK_SCHEMA,
            tool_name="custom_tool",
            tool_description="Custom description"
        )

        # Verify API call
        call_args = mock_client.messages.create.call_args
        assert call_args.kwargs["tool_choice"] == {"type": "tool", "name": "custom_tool"}
        assert call_args.kwargs["tools"][0]["name"] == "custom_tool"
        assert call_args.kwargs["tools"][0]["description"] == "Custom description"

    @patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'})
    def test_generate_structured_no_tool_use(self):
        """Test error when no tool use in response."""
        mock_client = MagicMock()
        mock_client.messages.create.return_value = MockResponse([
            MockTextBlock("Just text, no tool use")
        ])
        mock_anthropic.Anthropic.return_value = mock_client

        client = ClaudeLLMClient()

        with pytest.raises(ValueError, match="No tool use found"):
            client.generate_structured(
                prompt="Generate",
                schema=TASK_SCHEMA
            )

    @patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'})
    def test_generate_structured_with_system(self):
        """Test structured generation with system prompt."""
        mock_client = MagicMock()
        tool_data = {"title": "Cached Test"}
        mock_client.messages.create.return_value = MockResponse([
            MockToolUseBlock(tool_data)
        ])
        mock_anthropic.Anthropic.return_value = mock_client

        client = ClaudeLLMClient()

        result = client.generate_structured_with_system(
            system_prompt="You are a roadmap generator",
            user_prompt="Generate a task",
            schema=TASK_SCHEMA,
            cache_system=True
        )

        assert result["title"] == "Cached Test"

        # Verify system prompt with cache control
        call_args = mock_client.messages.create.call_args
        system_config = call_args.kwargs["system"][0]
        assert system_config["cache_control"] == {"type": "ephemeral"}

    @patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'})
    def test_generate_structured_retry_on_error(self):
        """Test retry logic on recoverable errors."""
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = [
            Exception("overloaded error"),
            MockResponse([MockToolUseBlock({"title": "Success"})])
        ]
        mock_anthropic.Anthropic.return_value = mock_client

        client = ClaudeLLMClient()

        with patch('time.sleep'):  # Skip actual sleep
            result = client.generate_structured(
                prompt="Generate",
                schema=TASK_SCHEMA
            )

        assert result["title"] == "Success"
        assert mock_client.messages.create.call_count == 2


class TestTaskParseStructuredContent:
    """Tests for Task.parse_structured_content method."""

    def test_parse_basic_fields(self):
        """Test parsing basic task fields."""
        task = Task(name="Test Task", number="1.0.1.1")

        data = {
            "title": "Updated Title",
            "description": "Main description",
            "goal_description": "Goal description",
            "work_type": "implementation",
            "complexity": "moderate",
            "duration_hours": 8,
            "priority": "High"
        }

        task.parse_structured_content(data)

        assert task.description == "Goal description"  # goal_description takes priority
        assert task.work_type == "implementation"
        assert task.complexity == "moderate"
        assert task.duration == 8
        assert task.priority == "High"
        assert task.generation_status == ItemStatus.GENERATED

    def test_parse_list_fields(self):
        """Test parsing list fields converted to strings."""
        task = Task(name="Test", number="1.0.1.1")

        data = {
            "title": "Test",
            "description": "Desc",
            "work_type": "testing",
            "complexity": "simple",
            "duration_hours": 2,
            "benefits": ["Benefit 1", "Benefit 2"],
            "prerequisites": ["Prereq 1"],
            "technical_requirements": ["Req 1", "Req 2"]
        }

        task.parse_structured_content(data)

        assert "- Benefit 1" in task.benefits
        assert "- Benefit 2" in task.benefits
        assert "- Prereq 1" in task.prerequisites
        assert "- Req 1" in task.technical_requirements

    def test_parse_tags(self):
        """Test parsing tags."""
        task = Task(name="Test", number="1.0.1.1")

        data = {
            "title": "Test",
            "description": "Desc",
            "work_type": "implementation",
            "complexity": "moderate",
            "duration_hours": 4,
            "tags": ["Backend", "API", "Database"]
        }

        task.parse_structured_content(data)

        assert "backend" in task.tags
        assert "api" in task.tags
        assert "database" in task.tags

    def test_parse_claude_code_prompt(self):
        """Test parsing Claude Code prompt."""
        task = Task(name="Test", number="1.0.1.1")

        data = {
            "title": "Test",
            "description": "Desc",
            "work_type": "implementation",
            "complexity": "moderate",
            "duration_hours": 4,
            "claude_code_prompt": "Implement the API endpoint for user authentication"
        }

        task.parse_structured_content(data)

        assert "API endpoint" in task.claude_code_prompt

    def test_parse_duration_fallback(self):
        """Test duration parsing with invalid value."""
        task = Task(name="Test", number="1.0.1.1")

        data = {
            "title": "Test",
            "description": "Desc",
            "work_type": "implementation",
            "complexity": "moderate",
            "duration_hours": "invalid"
        }

        task.parse_structured_content(data)

        assert task.duration == 4  # Default value

    def test_get_structured_schema(self):
        """Test getting structured schema."""
        schema = Task.get_structured_schema()

        assert schema == TASK_SCHEMA


class TestStoryParseStructuredContent:
    """Tests for Story.parse_structured_content method."""

    def test_parse_basic_fields(self):
        """Test parsing basic story fields."""
        story = Story(name="Test Story", number="1.0.1")

        data = {
            "title": "Updated Story",
            "description": "Story description",
            "user_value": "As a user, I want to...",
            "acceptance_criteria": ["AC1", "AC2", "AC3"],
            "work_type": "feature",
            "complexity": "moderate",
            "duration_hours": 16,
            "priority": "High"
        }

        story.parse_structured_content(data)

        assert story.description == "Story description"
        assert story.user_value == "As a user, I want to..."
        assert len(story.acceptance_criteria) == 3
        assert "AC1" in story.acceptance_criteria
        assert story.work_type == "feature"
        assert story.complexity == "moderate"
        assert story.duration == 16
        assert story.pass1_complete is True
        assert story.generation_status == ItemStatus.GENERATED

    def test_parse_scope_fields(self):
        """Test parsing scope boundaries."""
        story = Story(name="Test", number="1.0.1")

        data = {
            "title": "Test",
            "description": "Desc",
            "user_value": "User value",
            "acceptance_criteria": ["AC1"],
            "work_type": "feature",
            "scope_in": ["Feature A", "Feature B"],
            "scope_out": ["Feature C", "Feature D"]
        }

        story.parse_structured_content(data)

        assert len(story.scope_in) == 2
        assert "Feature A" in story.scope_in
        assert len(story.scope_out) == 2
        assert "Feature C" in story.scope_out

    def test_parse_list_fields(self):
        """Test parsing list fields converted to strings."""
        story = Story(name="Test", number="1.0.1")

        data = {
            "title": "Test",
            "description": "Desc",
            "user_value": "User value",
            "acceptance_criteria": ["AC1"],
            "work_type": "feature",
            "benefits": ["Benefit 1", "Benefit 2"],
            "technical_requirements": ["Tech req 1"],
            "prerequisites": ["Prereq 1"]
        }

        story.parse_structured_content(data)

        assert "- Benefit 1" in story.benefits
        assert "- Tech req 1" in story.technical_requirements
        assert "- Prereq 1" in story.prerequisites

    def test_parse_tags(self):
        """Test parsing tags."""
        story = Story(name="Test", number="1.0.1")

        data = {
            "title": "Test",
            "description": "Desc",
            "user_value": "User value",
            "acceptance_criteria": ["AC1"],
            "work_type": "feature",
            "tags": ["Frontend", "UX", "Dashboard"]
        }

        story.parse_structured_content(data)

        assert "frontend" in story.tags
        assert "ux" in story.tags
        assert "dashboard" in story.tags

    def test_get_structured_schema(self):
        """Test getting structured schema."""
        schema = Story.get_structured_schema()

        assert schema == STORY_SCHEMA


class TestStructuredOutputIntegration:
    """Integration tests for structured output workflow."""

    @patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'})
    def test_full_task_workflow(self):
        """Test full workflow: generate structured -> parse."""
        mock_client = MagicMock()
        tool_data = {
            "title": "Implement Auth",
            "description": "Implement user authentication",
            "goal_description": "Create secure authentication system",
            "benefits": ["Secure access", "User management"],
            "claude_code_prompt": "Implement JWT-based auth with bcrypt",
            "work_type": "implementation",
            "complexity": "complex",
            "duration_hours": 16,
            "priority": "Critical",
            "prerequisites": ["Database setup"],
            "technical_requirements": ["bcrypt", "JWT library"],
            "tags": ["security", "auth", "backend"]
        }
        mock_client.messages.create.return_value = MockResponse([
            MockToolUseBlock(tool_data)
        ])
        mock_anthropic.Anthropic.return_value = mock_client

        # Generate structured output
        client = ClaudeLLMClient()
        result = client.generate_structured(
            prompt="Generate an authentication task",
            schema=TASK_SCHEMA,
            tool_name="create_task"
        )

        # Parse into task
        task = Task(name="Auth Task", number="1.0.1.1")
        task.parse_structured_content(result)

        # Verify
        assert task.description == "Create secure authentication system"
        assert "Secure access" in task.benefits
        assert task.work_type == "implementation"
        assert task.complexity == "complex"
        assert task.duration == 16
        assert "security" in task.tags

    @patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'})
    def test_full_story_workflow(self):
        """Test full workflow: generate structured -> parse."""
        mock_client = MagicMock()
        tool_data = {
            "title": "User Profile",
            "description": "Allow users to view and edit their profile",
            "user_value": "As a user, I want to edit my profile so I can keep my info updated",
            "acceptance_criteria": [
                "User can view their profile",
                "User can edit their name and email",
                "Changes are saved and persisted"
            ],
            "scope_in": ["Profile viewing", "Basic editing"],
            "scope_out": ["Password change", "Account deletion"],
            "benefits": ["Better user experience", "Data accuracy"],
            "work_type": "feature",
            "complexity": "moderate",
            "duration_hours": 24,
            "priority": "High",
            "tags": ["user", "profile", "frontend"]
        }
        mock_client.messages.create.return_value = MockResponse([
            MockToolUseBlock(tool_data)
        ])
        mock_anthropic.Anthropic.return_value = mock_client

        # Generate structured output
        client = ClaudeLLMClient()
        result = client.generate_structured(
            prompt="Generate a user profile story",
            schema=STORY_SCHEMA,
            tool_name="create_story"
        )

        # Parse into story
        story = Story(name="Profile Story", number="1.0.1")
        story.parse_structured_content(result)

        # Verify
        assert "edit my profile" in story.user_value
        assert len(story.acceptance_criteria) == 3
        assert "Profile viewing" in story.scope_in
        assert "Password change" in story.scope_out
        assert story.work_type == "feature"
        assert story.pass1_complete is True
