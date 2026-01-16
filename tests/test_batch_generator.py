"""Tests for batch task generation."""

import pytest
from unittest.mock import MagicMock, patch

from arcane.engines.generation.batch_generator import BatchTaskGenerator
from arcane.items.milestone import Milestone
from arcane.items.epic import Epic
from arcane.items.story import Story
from arcane.items.task import Task
from arcane.items.base import ItemStatus


class TestBatchTaskGeneratorInit:
    """Tests for BatchTaskGenerator initialization."""

    def test_init_with_llm_client(self):
        """Test initialization with LLM client."""
        mock_client = MagicMock()
        generator = BatchTaskGenerator(mock_client)

        assert generator.llm_client is mock_client
        assert generator.BATCH_THRESHOLD == 3


class TestShouldUseBatch:
    """Tests for should_use_batch decision logic."""

    @pytest.fixture
    def generator(self):
        """Create generator with mock client."""
        return BatchTaskGenerator(MagicMock())

    @pytest.fixture
    def epic_with_stories(self):
        """Create epic with stories ready for task generation."""
        epic = Epic(name="Auth Epic", number="1.0")

        for i in range(5):
            story = Story(name=f"Story {i}", number=f"1.0.{i}")
            story.description = f"Description for story {i}"
            story.acceptance_criteria = [f"AC1 for story {i}", f"AC2 for story {i}"]
            epic.add_child(story)

        return epic

    def test_should_use_batch_with_many_stories(self, generator, epic_with_stories):
        """Test batch mode is used with 3+ ready stories."""
        assert generator.should_use_batch(epic_with_stories) is True

    def test_should_not_use_batch_with_few_stories(self, generator):
        """Test batch mode is not used with fewer than 3 stories."""
        epic = Epic(name="Small Epic", number="1.0")

        # Add only 2 stories
        for i in range(2):
            story = Story(name=f"Story {i}", number=f"1.0.{i}")
            story.description = "Description"
            story.acceptance_criteria = ["AC1"]
            epic.add_child(story)

        assert generator.should_use_batch(epic) is False

    def test_should_not_use_batch_if_stories_not_ready(self, generator):
        """Test batch mode is not used if stories lack Pass 1 data."""
        epic = Epic(name="Incomplete Epic", number="1.0")

        # Add stories without Pass 1 data
        for i in range(5):
            story = Story(name=f"Story {i}", number=f"1.0.{i}")
            # No description or acceptance criteria
            epic.add_child(story)

        assert generator.should_use_batch(epic) is False


class TestStoryReadyForTasks:
    """Tests for _story_ready_for_tasks check."""

    @pytest.fixture
    def generator(self):
        """Create generator with mock client."""
        return BatchTaskGenerator(MagicMock())

    def test_story_ready_with_description_and_criteria(self, generator):
        """Test story is ready when it has description and AC."""
        story = Story(name="Ready Story", number="1.0.1")
        story.description = "This story implements login"
        story.acceptance_criteria = ["AC1: User can log in", "AC2: Error shown on failure"]

        assert generator._story_ready_for_tasks(story) is True

    def test_story_not_ready_without_description(self, generator):
        """Test story is not ready without description."""
        story = Story(name="No Desc", number="1.0.1")
        story.acceptance_criteria = ["AC1"]

        assert generator._story_ready_for_tasks(story) is False

    def test_story_not_ready_without_criteria(self, generator):
        """Test story is not ready without acceptance criteria."""
        story = Story(name="No AC", number="1.0.1")
        story.description = "Has description"
        story.acceptance_criteria = []

        assert generator._story_ready_for_tasks(story) is False


class TestBuildStoriesContext:
    """Tests for building stories context."""

    @pytest.fixture
    def generator(self):
        """Create generator with mock client."""
        return BatchTaskGenerator(MagicMock())

    def test_builds_context_for_all_stories(self, generator):
        """Test context includes all stories."""
        stories = []
        for i in range(3):
            story = Story(name=f"Story {i}", number=f"1.0.{i}")
            story.description = f"Description {i}"
            story.user_value = f"User value {i}"
            story.acceptance_criteria = [f"AC1 for {i}"]
            stories.append(story)

        context = generator._build_stories_context(stories)

        assert "STORY 1.0.0" in context
        assert "STORY 1.0.1" in context
        assert "STORY 1.0.2" in context
        assert "Description 0" in context
        assert "Description 1" in context
        assert "Description 2" in context

    def test_includes_acceptance_criteria(self, generator):
        """Test context includes acceptance criteria."""
        story = Story(name="Test Story", number="1.0.1")
        story.description = "Test description"
        story.acceptance_criteria = ["Can log in", "Gets error on failure"]

        context = generator._build_stories_context([story])

        assert "AC1:" in context
        assert "AC2:" in context
        assert "Can log in" in context
        assert "Gets error on failure" in context

    def test_includes_scope_boundaries(self, generator):
        """Test context includes scope boundaries."""
        story = Story(name="Scoped Story", number="1.0.1")
        story.description = "Test"
        story.acceptance_criteria = ["AC1"]
        story.scope_in = ["Login form", "Password validation"]
        story.scope_out = ["Password reset"]

        context = generator._build_stories_context([story])

        assert "IN SCOPE" in context
        assert "Login form" in context
        assert "OUT OF SCOPE" in context
        assert "Password reset" in context


class TestBuildBatchPrompt:
    """Tests for building batch prompt."""

    @pytest.fixture
    def generator(self):
        """Create generator with mock client."""
        return BatchTaskGenerator(MagicMock())

    @pytest.fixture
    def epic_with_ready_stories(self):
        """Create epic with stories ready for generation."""
        epic = Epic(name="Auth Epic", number="1.0")
        epic.description = "Authentication features"

        for i in range(3):
            story = Story(name=f"Story {i}", number=f"1.0.{i}")
            story.description = f"Description {i}"
            story.acceptance_criteria = [f"AC1 for {i}"]
            epic.add_child(story)

        return epic

    def test_prompt_includes_epic_info(self, generator, epic_with_ready_stories):
        """Test prompt includes epic information."""
        stories = epic_with_ready_stories.get_children_by_type('Story')

        prompt = generator._build_batch_prompt(
            epic_with_ready_stories, stories, "Context", "Overview"
        )

        assert "1.0" in prompt
        assert "Auth Epic" in prompt

    def test_prompt_includes_cascading_context(self, generator, epic_with_ready_stories):
        """Test prompt includes cascading context."""
        stories = epic_with_ready_stories.get_children_by_type('Story')

        prompt = generator._build_batch_prompt(
            epic_with_ready_stories, stories, "Prior decisions here", ""
        )

        assert "Prior decisions here" in prompt

    def test_prompt_includes_all_stories(self, generator, epic_with_ready_stories):
        """Test prompt includes all story details."""
        stories = epic_with_ready_stories.get_children_by_type('Story')

        prompt = generator._build_batch_prompt(
            epic_with_ready_stories, stories, "", ""
        )

        for story in stories:
            assert story.id in prompt


class TestParseBatchResponse:
    """Tests for parsing batch response."""

    @pytest.fixture
    def generator(self):
        """Create generator with mock client."""
        return BatchTaskGenerator(MagicMock())

    @pytest.fixture
    def epic_with_stories(self):
        """Create epic with stories."""
        epic = Epic(name="Auth", number="1.0")

        story1 = Story(name="Login", number="1.0.1")
        story1.description = "Login functionality"
        story1.acceptance_criteria = ["AC1"]
        epic.add_child(story1)

        story2 = Story(name="Register", number="1.0.2")
        story2.description = "Registration functionality"
        story2.acceptance_criteria = ["AC1"]
        epic.add_child(story2)

        return epic

    def test_parses_tasks_for_multiple_stories(self, generator, epic_with_stories):
        """Test parsing tasks for multiple stories."""
        response = """
###STORY_TASKS_START### 1.0.1

###TASK_START### 1.0.1.1
:::TASK_TITLE:::
Create login form

:::TASK_GOAL:::
Create the login form component.

:::TASK_WORK_TYPE:::
implementation

:::TASK_COMPLEXITY:::
moderate

:::TASK_DURATION_HOURS:::
4

:::TASK_PRIORITY:::
High

###TASK_END###

###STORY_TASKS_END###

###STORY_TASKS_START### 1.0.2

###TASK_START### 1.0.2.1
:::TASK_TITLE:::
Create registration form

:::TASK_GOAL:::
Create the registration form component.

:::TASK_WORK_TYPE:::
implementation

:::TASK_COMPLEXITY:::
moderate

:::TASK_DURATION_HOURS:::
6

:::TASK_PRIORITY:::
High

###TASK_END###

###STORY_TASKS_END###
"""
        stories = epic_with_stories.get_children_by_type('Story')
        result = generator._parse_batch_response(response, epic_with_stories, stories)

        assert '1.0.1' in result
        assert '1.0.2' in result
        assert len(result['1.0.1']) == 1
        assert len(result['1.0.2']) == 1

    def test_parses_task_fields_correctly(self, generator, epic_with_stories):
        """Test task fields are parsed correctly."""
        response = """
###STORY_TASKS_START### 1.0.1

###TASK_START### 1.0.1.1
:::TASK_TITLE:::
Implement authentication endpoint

:::TASK_GOAL:::
Create the backend authentication API endpoint.

:::TASK_SATISFIES_AC:::
- AC1: Enables user login

:::TASK_CLAUDE_CODE_PROMPT:::
Create an authentication endpoint at /api/auth/login that accepts POST requests.

:::TASK_TECHNICAL_REQUIREMENTS:::
- Use JWT tokens
- Hash passwords with bcrypt

:::TASK_PREREQUISITES:::
None

:::TASK_WORK_TYPE:::
implementation

:::TASK_COMPLEXITY:::
moderate

:::TASK_DURATION_HOURS:::
8

:::TASK_PRIORITY:::
Critical

:::TASK_TAGS:::
backend, api, security

###TASK_END###

###STORY_TASKS_END###
"""
        stories = epic_with_stories.get_children_by_type('Story')
        result = generator._parse_batch_response(response, epic_with_stories, stories)

        assert '1.0.1' in result
        task = result['1.0.1'][0]

        assert task.id == '1.0.1.1'
        assert 'Implement authentication endpoint' in task.name
        assert 'backend authentication' in task.description
        assert 'JWT tokens' in task.technical_requirements
        assert task.work_type == 'implementation'
        assert task.complexity == 'moderate'
        assert task.duration == 8
        assert task.priority == 'Critical'
        assert 'backend' in task.tags

    def test_marks_story_pass2_complete(self, generator, epic_with_stories):
        """Test that story pass2_complete is set after parsing."""
        response = """
###STORY_TASKS_START### 1.0.1

###TASK_START### 1.0.1.1
:::TASK_TITLE:::
Test task

:::TASK_GOAL:::
Test goal.

:::TASK_WORK_TYPE:::
implementation

:::TASK_COMPLEXITY:::
simple

:::TASK_DURATION_HOURS:::
2

:::TASK_PRIORITY:::
Medium

###TASK_END###

###STORY_TASKS_END###
"""
        stories = epic_with_stories.get_children_by_type('Story')
        story1 = stories[0]

        assert story1.pass2_complete is False

        generator._parse_batch_response(response, epic_with_stories, stories)

        assert story1.pass2_complete is True


class TestGenerateEpicTasksBatch:
    """Tests for the main generate_epic_tasks_batch method."""

    @pytest.fixture
    def mock_llm_client(self):
        """Create mock LLM client."""
        client = MagicMock()
        client.generate.return_value = """
###STORY_TASKS_START### 1.0.1

###TASK_START### 1.0.1.1
:::TASK_TITLE:::
Test task 1

:::TASK_GOAL:::
Goal for task 1.

:::TASK_WORK_TYPE:::
implementation

:::TASK_COMPLEXITY:::
simple

:::TASK_DURATION_HOURS:::
2

:::TASK_PRIORITY:::
High

###TASK_END###

###STORY_TASKS_END###

###STORY_TASKS_START### 1.0.2

###TASK_START### 1.0.2.1
:::TASK_TITLE:::
Test task 2

:::TASK_GOAL:::
Goal for task 2.

:::TASK_WORK_TYPE:::
implementation

:::TASK_COMPLEXITY:::
moderate

:::TASK_DURATION_HOURS:::
4

:::TASK_PRIORITY:::
Medium

###TASK_END###

###STORY_TASKS_END###

###STORY_TASKS_START### 1.0.3

###TASK_START### 1.0.3.1
:::TASK_TITLE:::
Test task 3

:::TASK_GOAL:::
Goal for task 3.

:::TASK_WORK_TYPE:::
testing

:::TASK_COMPLEXITY:::
simple

:::TASK_DURATION_HOURS:::
1

:::TASK_PRIORITY:::
Low

###TASK_END###

###STORY_TASKS_END###
"""
        return client

    @pytest.fixture
    def epic_with_ready_stories(self):
        """Create epic with stories ready for generation."""
        epic = Epic(name="Auth Epic", number="1.0")
        epic.description = "Authentication features"

        for i in range(1, 4):
            story = Story(name=f"Story {i}", number=f"1.0.{i}")
            story.description = f"Description for story {i}"
            story.acceptance_criteria = [f"AC1 for story {i}"]
            epic.add_child(story)

        return epic

    def test_generates_tasks_for_all_stories(self, mock_llm_client, epic_with_ready_stories):
        """Test batch generation creates tasks for all stories."""
        generator = BatchTaskGenerator(mock_llm_client)

        result = generator.generate_epic_tasks_batch(epic_with_ready_stories)

        assert '1.0.1' in result
        assert '1.0.2' in result
        assert '1.0.3' in result
        assert len(result['1.0.1']) == 1
        assert len(result['1.0.2']) == 1
        assert len(result['1.0.3']) == 1

    def test_calls_llm_once(self, mock_llm_client, epic_with_ready_stories):
        """Test only one LLM call is made for all stories."""
        generator = BatchTaskGenerator(mock_llm_client)

        generator.generate_epic_tasks_batch(epic_with_ready_stories)

        assert mock_llm_client.generate.call_count == 1

    def test_returns_empty_if_no_ready_stories(self, mock_llm_client):
        """Test returns empty dict if no stories are ready."""
        epic = Epic(name="Empty Epic", number="1.0")

        # Add stories without Pass 1 data
        story = Story(name="Incomplete", number="1.0.1")
        epic.add_child(story)

        generator = BatchTaskGenerator(mock_llm_client)
        result = generator.generate_epic_tasks_batch(epic)

        assert result == {}
        assert mock_llm_client.generate.call_count == 0


class TestGetBatchStats:
    """Tests for batch statistics."""

    @pytest.fixture
    def generator(self):
        """Create generator with mock client."""
        return BatchTaskGenerator(MagicMock())

    def test_calculates_correct_stats(self, generator):
        """Test statistics are calculated correctly."""
        epic = Epic(name="Test Epic", number="1.0")

        # Mock result with tasks
        result = {
            '1.0.1': [MagicMock(), MagicMock(), MagicMock()],  # 3 tasks
            '1.0.2': [MagicMock(), MagicMock()],  # 2 tasks
            '1.0.3': [MagicMock()],  # 1 task
        }

        stats = generator.get_batch_stats(epic, result)

        assert stats['epic_id'] == '1.0'
        assert stats['stories_processed'] == 3
        assert stats['total_tasks_generated'] == 6
        assert stats['avg_tasks_per_story'] == 2.0
        assert stats['api_calls_saved'] == 2  # Would have been 3 calls, saved 2

    def test_handles_empty_result(self, generator):
        """Test handles empty result dict."""
        epic = Epic(name="Test Epic", number="1.0")
        result = {}

        stats = generator.get_batch_stats(epic, result)

        assert stats['stories_processed'] == 0
        assert stats['total_tasks_generated'] == 0
        assert stats['avg_tasks_per_story'] == 0
        assert stats['api_calls_saved'] == 0


class TestExtractFields:
    """Tests for field extraction."""

    @pytest.fixture
    def generator(self):
        """Create generator with mock client."""
        return BatchTaskGenerator(MagicMock())

    def test_extracts_all_fields(self, generator):
        """Test all fields are extracted correctly."""
        content = """
:::TASK_TITLE:::
My Task Title

:::TASK_GOAL:::
This is the goal of the task.

:::TASK_WORK_TYPE:::
implementation

:::TASK_COMPLEXITY:::
moderate

:::TASK_DURATION_HOURS:::
6

:::TASK_PRIORITY:::
High

:::TASK_TAGS:::
backend, api
"""
        fields = generator._extract_fields(content)

        assert fields['TASK_TITLE'] == 'My Task Title'
        assert 'goal of the task' in fields['TASK_GOAL']
        assert fields['TASK_WORK_TYPE'] == 'implementation'
        assert fields['TASK_COMPLEXITY'] == 'moderate'
        assert fields['TASK_DURATION_HOURS'] == '6'
        assert fields['TASK_PRIORITY'] == 'High'
        assert 'backend' in fields['TASK_TAGS']

    def test_handles_missing_fields(self, generator):
        """Test handles missing fields gracefully."""
        content = """
:::TASK_TITLE:::
Only Title

:::TASK_WORK_TYPE:::
testing
"""
        fields = generator._extract_fields(content)

        assert fields['TASK_TITLE'] == 'Only Title'
        assert fields['TASK_WORK_TYPE'] == 'testing'
        assert 'TASK_GOAL' not in fields


class TestNormalizeSelectField:
    """Tests for field normalization."""

    @pytest.fixture
    def generator(self):
        """Create generator with mock client."""
        return BatchTaskGenerator(MagicMock())

    def test_normalizes_work_type(self, generator):
        """Test work type normalization."""
        options = ['implementation', 'design', 'testing']

        assert generator._normalize_select_field('Implementation', options, 'implementation') == 'implementation'
        assert generator._normalize_select_field('TESTING', options, 'implementation') == 'testing'
        assert generator._normalize_select_field('invalid', options, 'design') == 'design'

    def test_normalizes_complexity(self, generator):
        """Test complexity normalization."""
        options = ['simple', 'moderate', 'complex']

        assert generator._normalize_select_field('Simple', options, 'moderate') == 'simple'
        assert generator._normalize_select_field('complex task', options, 'moderate') == 'complex'

    def test_normalizes_priority(self, generator):
        """Test priority normalization."""
        options = ['Critical', 'High', 'Medium', 'Low']

        assert generator._normalize_select_field('critical', options, 'Medium') == 'Critical'
        assert generator._normalize_select_field('HIGH priority', options, 'Medium') == 'High'


class TestParseDuration:
    """Tests for duration parsing."""

    @pytest.fixture
    def generator(self):
        """Create generator with mock client."""
        return BatchTaskGenerator(MagicMock())

    def test_parses_simple_number(self, generator):
        """Test parsing simple number."""
        assert generator._parse_duration('4') == 4
        assert generator._parse_duration('12') == 12

    def test_parses_number_with_text(self, generator):
        """Test parsing number with surrounding text."""
        assert generator._parse_duration('4 hours') == 4
        assert generator._parse_duration('approximately 8 hours') == 8

    def test_returns_default_for_invalid(self, generator):
        """Test returns default for invalid input."""
        assert generator._parse_duration('no number') == 4
        assert generator._parse_duration('') == 4


class TestParseCommaList:
    """Tests for comma list parsing."""

    @pytest.fixture
    def generator(self):
        """Create generator with mock client."""
        return BatchTaskGenerator(MagicMock())

    def test_parses_comma_list(self, generator):
        """Test parsing comma-separated values."""
        result = generator._parse_comma_list('backend, api, testing')

        assert len(result) == 3
        assert 'backend' in result
        assert 'api' in result
        assert 'testing' in result

    def test_handles_empty_string(self, generator):
        """Test handles empty string."""
        assert generator._parse_comma_list('') == []

    def test_trims_whitespace(self, generator):
        """Test trims whitespace from items."""
        result = generator._parse_comma_list('  backend  ,  api  ')

        assert result == ['backend', 'api']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
