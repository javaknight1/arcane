"""Tests for two-pass story generation."""

import pytest
from unittest.mock import MagicMock, patch
from arcane.items.story import Story
from arcane.items.epic import Epic
from arcane.items.milestone import Milestone
from arcane.items.task import Task
from arcane.items.base import ItemStatus
from arcane.engines.generation.recursive_generator import RecursiveRoadmapGenerator
from arcane.utils.cost_estimator import LLMCostEstimator


class TestStoryTwoPassMethods:
    """Tests for Story class two-pass generation methods."""

    @pytest.fixture
    def story_with_tasks(self):
        """Create a story with placeholder tasks."""
        epic = Epic(name="Auth", number="1.0")
        story = Story(name="Login", number="1.0.1", parent=epic)
        epic.add_child(story)

        # Add placeholder tasks
        task1 = Task(name="Create form", number="1.0.1.1", parent=story)
        task2 = Task(name="Add validation", number="1.0.1.2", parent=story)
        story.add_child(task1)
        story.add_child(task2)

        return story

    def test_generate_description_prompt(self, story_with_tasks):
        """Test Pass 1 prompt generation."""
        prompt = story_with_tasks.generate_description_prompt(
            project_context="Test project",
            epic_context="Epic 1.0: Authentication",
            cascading_context="Previous: Using PostgreSQL",
            roadmap_overview="Milestone 1 in progress",
            semantic_description="Implements user login"
        )

        assert "Story ID: 1.0.1" in prompt
        assert "Test project" in prompt
        assert "Authentication" in prompt
        assert "PostgreSQL" in prompt
        assert "DO NOT generate tasks" in prompt

    def test_generate_tasks_prompt_requires_pass1(self, story_with_tasks):
        """Test Pass 2 prompt includes story details from Pass 1."""
        # Simulate Pass 1 completion
        story_with_tasks.description = "User login functionality"
        story_with_tasks.user_value = "As a user, I want to log in"
        story_with_tasks.acceptance_criteria = [
            "User can enter credentials",
            "System validates credentials",
            "Session is created on success"
        ]
        story_with_tasks.scope_in = ["Login form", "Validation"]
        story_with_tasks.scope_out = ["Registration", "Password reset"]
        story_with_tasks.duration = 16
        story_with_tasks.pass1_complete = True

        prompt = story_with_tasks.generate_tasks_prompt(
            cascading_context="Previous decisions",
            sibling_context="Story 1.0.2: Registration",
            roadmap_overview="Overview"
        )

        assert "User login functionality" in prompt
        assert "As a user, I want to log in" in prompt
        assert "AC1:" in prompt
        assert "AC2:" in prompt
        assert "Task 1.0.1.1" in prompt
        assert "Task 1.0.1.2" in prompt

    def test_parse_description_content(self, story_with_tasks):
        """Test parsing Pass 1 response."""
        response = """
:::STORY_DESCRIPTION:::
This story implements secure user authentication with email and password.

:::USER_VALUE:::
As a user, I want to securely log in so that I can access my account.

:::ACCEPTANCE_CRITERIA:::
- [ ] AC1: User can enter email and password
- [ ] AC2: Invalid credentials show error message
- [ ] AC3: Successful login creates session
- [ ] AC4: Session persists across page refreshes

:::TECHNICAL_CONSIDERATIONS:::
- Use bcrypt for password hashing
- JWT tokens for session management
- Rate limiting on login attempts

:::SCOPE_BOUNDARIES:::
IN SCOPE:
- Email/password login
- Session management
- Error handling

OUT OF SCOPE:
- OAuth providers
- Password reset
- Two-factor auth

:::PREREQUISITES:::
Story 1.0.0: Database setup

:::BENEFITS:::
- Secure user access
- Session persistence
- Error feedback

:::WORK_TYPE:::
implementation

:::COMPLEXITY:::
moderate

:::PRIORITY:::
High

:::DURATION_HOURS:::
16

:::TAGS:::
authentication, backend, security
"""
        story_with_tasks.parse_description_content(response)

        assert story_with_tasks.pass1_complete is True
        assert "secure user authentication" in story_with_tasks.description
        assert "securely log in" in story_with_tasks.user_value
        assert len(story_with_tasks.acceptance_criteria) == 4
        assert "bcrypt" in story_with_tasks.technical_considerations
        assert len(story_with_tasks.scope_in) == 3
        assert len(story_with_tasks.scope_out) == 3
        assert story_with_tasks.duration == 16
        assert story_with_tasks.work_type == "implementation"
        assert story_with_tasks.complexity == "moderate"

    def test_parse_tasks_content(self, story_with_tasks):
        """Test parsing Pass 2 response with tasks."""
        response = """
###TASK_START### 1.0.1.1
:::TASK_TITLE:::
Implement Login Form UI

:::TASK_GOAL:::
Create the login form component with email and password fields.

:::TASK_SATISFIES_AC:::
- AC1: User can enter email and password

:::TASK_CLAUDE_CODE_PROMPT:::
Create src/components/LoginForm.tsx with:
- Email input with validation
- Password input with masking
- Submit button
- Error message display

:::TASK_TECHNICAL_REQUIREMENTS:::
- Use React Hook Form
- Implement field validation
- Style with Tailwind CSS

:::TASK_PREREQUISITES:::
None

:::TASK_WORK_TYPE:::
implementation

:::TASK_COMPLEXITY:::
simple

:::TASK_DURATION_HOURS:::
4

:::TASK_PRIORITY:::
High

:::TASK_TAGS:::
frontend, ui, forms
###TASK_END###

###TASK_START### 1.0.1.2
:::TASK_TITLE:::
Add Form Validation

:::TASK_GOAL:::
Implement client-side validation for login form inputs.

:::TASK_SATISFIES_AC:::
- AC1: User can enter email and password
- AC2: Invalid credentials show error message

:::TASK_CLAUDE_CODE_PROMPT:::
Update src/components/LoginForm.tsx to add:
- Email format validation
- Password minimum length check
- Error message display logic

:::TASK_TECHNICAL_REQUIREMENTS:::
- Use zod for schema validation
- Display inline error messages
- Disable submit when invalid

:::TASK_PREREQUISITES:::
- Task 1.0.1.1: Create form UI first

:::TASK_WORK_TYPE:::
implementation

:::TASK_COMPLEXITY:::
simple

:::TASK_DURATION_HOURS:::
3

:::TASK_PRIORITY:::
High

:::TASK_TAGS:::
frontend, validation
###TASK_END###

:::AC_COVERAGE:::
- AC1: Covered by Task(s) [1.0.1.1, 1.0.1.2]
- AC2: Covered by Task(s) [1.0.1.2]

:::UNCOVERED_AC:::
None - all AC covered
"""
        story_with_tasks.parse_tasks_content(response)

        assert story_with_tasks.pass2_complete is True

        tasks = story_with_tasks.get_children_by_type('Task')
        assert len(tasks) == 2

        task1 = next(t for t in tasks if t.id == "1.0.1.1")
        assert "Login Form UI" in task1.name
        assert "login form component" in task1.description
        assert "AC1:" in task1.satisfies_criteria
        assert "React Hook Form" in task1.technical_requirements
        assert task1.duration == 4

        task2 = next(t for t in tasks if t.id == "1.0.1.2")
        assert "Form Validation" in task2.name
        assert task2.duration == 3

    def test_is_two_pass_complete(self, story_with_tasks):
        """Test two-pass completion check."""
        assert story_with_tasks.is_two_pass_complete() is False

        story_with_tasks.pass1_complete = True
        assert story_with_tasks.is_two_pass_complete() is False

        story_with_tasks.pass2_complete = True
        assert story_with_tasks.is_two_pass_complete() is True

    def test_parse_acceptance_criteria_formats(self, story_with_tasks):
        """Test parsing various AC formats."""
        # Format 1: Checkbox with AC prefix
        ac_raw1 = """
- [ ] AC1: User can log in
- [x] AC2: Error shown on failure
"""
        result1 = story_with_tasks._parse_acceptance_criteria(ac_raw1)
        assert len(result1) == 2
        assert "User can log in" in result1[0]
        assert "Error shown on failure" in result1[1]

        # Format 2: Plain bullets
        ac_raw2 = """
- User can enter credentials
- System validates input
- Session created
"""
        result2 = story_with_tasks._parse_acceptance_criteria(ac_raw2)
        assert len(result2) == 3

    def test_parse_scope_boundaries(self, story_with_tasks):
        """Test parsing scope in/out sections."""
        scope_raw = """
IN SCOPE:
- Login functionality
- Session management

OUT OF SCOPE:
- OAuth integration
- Password reset
"""
        scope_in, scope_out = story_with_tasks._parse_scope(scope_raw)

        assert len(scope_in) == 2
        assert "Login functionality" in scope_in
        assert len(scope_out) == 2
        assert "OAuth integration" in scope_out

    def test_format_scope(self, story_with_tasks):
        """Test formatting scope for prompt injection."""
        story_with_tasks.scope_in = ["Login", "Sessions"]
        story_with_tasks.scope_out = ["OAuth", "Reset"]

        formatted = story_with_tasks._format_scope()

        assert "IN SCOPE:" in formatted
        assert "- Login" in formatted
        assert "OUT OF SCOPE:" in formatted
        assert "- OAuth" in formatted


class TestRecursiveGeneratorTwoPass:
    """Tests for RecursiveRoadmapGenerator two-pass story generation."""

    @pytest.fixture
    def mock_llm_client(self):
        """Create mock LLM client."""
        client = MagicMock()
        client.provider = 'claude'

        # Track call count to return different responses
        call_count = [0]

        pass1_response = """
:::STORY_DESCRIPTION:::
Login story description.

:::USER_VALUE:::
As a user, I want to log in.

:::ACCEPTANCE_CRITERIA:::
- [ ] AC1: Can enter credentials
- [ ] AC2: Gets error feedback
- [ ] AC3: Session created

:::TECHNICAL_CONSIDERATIONS:::
- Use JWT tokens

:::SCOPE_BOUNDARIES:::
IN SCOPE:
- Login form

OUT OF SCOPE:
- Registration

:::PREREQUISITES:::
None

:::BENEFITS:::
- User access

:::WORK_TYPE:::
implementation

:::COMPLEXITY:::
moderate

:::PRIORITY:::
High

:::DURATION_HOURS:::
12

:::TAGS:::
auth
"""

        pass2_response = """
###TASK_START### 1.0.1.1
:::TASK_TITLE:::
Create Login Form

:::TASK_GOAL:::
Build the login form UI.

:::TASK_SATISFIES_AC:::
- AC1: Can enter credentials

:::TASK_CLAUDE_CODE_PROMPT:::
Create the form component.

:::TASK_TECHNICAL_REQUIREMENTS:::
- React component

:::TASK_PREREQUISITES:::
None

:::TASK_WORK_TYPE:::
implementation

:::TASK_COMPLEXITY:::
simple

:::TASK_DURATION_HOURS:::
4

:::TASK_PRIORITY:::
High

:::TASK_TAGS:::
frontend
###TASK_END###

:::AC_COVERAGE:::
- AC1: Covered by Task(s) [1.0.1.1]

:::UNCOVERED_AC:::
AC2, AC3 - would need more tasks
"""

        def generate_response(prompt):
            call_count[0] += 1
            # Odd calls (1, 3, 5...) are Pass 1, even calls (2, 4, 6...) are Pass 2
            if call_count[0] % 2 == 1:
                return pass1_response
            else:
                return pass2_response

        client.generate.side_effect = generate_response
        return client

    @pytest.fixture
    def generator(self, mock_llm_client):
        """Create generator with mock LLM.

        Uses premium mode to ensure mock client is used for all operations
        rather than creating real clients from factory in tiered mode.
        """
        return RecursiveRoadmapGenerator(mock_llm_client, model_mode='premium')

    @pytest.fixture
    def sample_hierarchy(self):
        """Create sample milestone/epic/story hierarchy."""
        milestone = Milestone(name="Foundation", number="1")
        epic = Epic(name="Auth", number="1.0", parent=milestone)
        milestone.add_child(epic)

        story = Story(name="Login", number="1.0.1", parent=epic)
        epic.add_child(story)

        task = Task(name="Form", number="1.0.1.1", parent=story)
        story.add_child(task)

        return [milestone]

    def test_two_pass_called_for_stories(self, generator, mock_llm_client, sample_hierarchy):
        """Test that two-pass is used for story generation."""
        story = sample_hierarchy[0].get_children_by_type('Epic')[0].get_children_by_type('Story')[0]

        # Manually call two-pass generation
        with patch.object(generator, '_build_roadmap_overview_with_status', return_value="Overview"):
            generator._generate_story_two_pass(
                story,
                project_context="Test project",
                milestones=sample_hierarchy,
                progress=MagicMock(),
                task=MagicMock(),
                interactive_mode=False
            )

        # Should have made 2 LLM calls (Pass 1 + Pass 2)
        assert mock_llm_client.generate.call_count == 2

        # Story should be fully generated
        assert story.pass1_complete is True
        assert story.pass2_complete is True
        assert story.generation_status == ItemStatus.GENERATED

    def test_pass1_populates_story_fields(self, generator, mock_llm_client, sample_hierarchy):
        """Test that Pass 1 populates story description fields."""
        story = sample_hierarchy[0].get_children_by_type('Epic')[0].get_children_by_type('Story')[0]

        with patch.object(generator, '_build_roadmap_overview_with_status', return_value="Overview"):
            generator._generate_story_two_pass(
                story,
                project_context="Test",
                milestones=sample_hierarchy,
                progress=MagicMock(),
                task=MagicMock(),
                interactive_mode=False
            )

        assert story.description is not None
        assert len(story.acceptance_criteria) > 0
        assert story.user_value is not None

    def test_pass2_generates_tasks(self, generator, mock_llm_client, sample_hierarchy):
        """Test that Pass 2 generates task content."""
        story = sample_hierarchy[0].get_children_by_type('Epic')[0].get_children_by_type('Story')[0]

        with patch.object(generator, '_build_roadmap_overview_with_status', return_value="Overview"):
            generator._generate_story_two_pass(
                story,
                project_context="Test",
                milestones=sample_hierarchy,
                progress=MagicMock(),
                task=MagicMock(),
                interactive_mode=False
            )

        tasks = story.get_children_by_type('Task')
        # Task should be populated
        task = tasks[0]
        assert task.generation_status == ItemStatus.GENERATED

    def test_story_content_combines_both_passes(self, generator, mock_llm_client, sample_hierarchy):
        """Test that story.content contains both pass responses."""
        story = sample_hierarchy[0].get_children_by_type('Epic')[0].get_children_by_type('Story')[0]

        with patch.object(generator, '_build_roadmap_overview_with_status', return_value="Overview"):
            generator._generate_story_two_pass(
                story,
                project_context="Test",
                milestones=sample_hierarchy,
                progress=MagicMock(),
                task=MagicMock(),
                interactive_mode=False
            )

        # Content should have both parts
        assert "STORY_DESCRIPTION" in story.content
        assert "TASK_START" in story.content


class TestCostEstimatorTwoPass:
    """Tests for cost estimator with two-pass story generation."""

    @pytest.fixture
    def estimator(self):
        """Create cost estimator."""
        return LLMCostEstimator()

    def test_story_has_two_api_calls(self, estimator):
        """Test that stories are counted as 2 API calls."""
        item_counts = {
            'milestones': 1,
            'epics': 2,
            'stories': 3,
            'tasks': 6
        }

        result = estimator.estimate_individual_item_costs(
            provider='claude',
            item_counts=item_counts,
            idea_content="Test idea"
        )

        # 1 milestone + 2 epics + 3 stories * 2 = 9 API calls
        assert result['total_api_calls'] == 9

    def test_story_estimate_includes_api_calls_field(self, estimator):
        """Test that story estimate has api_calls_per_item field."""
        item_counts = {
            'milestones': 1,
            'epics': 1,
            'stories': 2,
            'tasks': 4
        }

        result = estimator.estimate_individual_item_costs(
            provider='claude',
            item_counts=item_counts,
            idea_content="Test"
        )

        story_estimate = next(
            e for e in result['item_estimates'] if e['item_type'] == 'stories'
        )
        assert story_estimate['api_calls_per_item'] == 2

    def test_format_shows_two_api_calls_for_stories(self, estimator):
        """Test that formatted output shows 2 API calls for stories."""
        item_counts = {
            'milestones': 1,
            'epics': 1,
            'stories': 2,
            'tasks': 4
        }

        result = estimator.estimate_individual_item_costs(
            provider='claude',
            item_counts=item_counts,
            idea_content="Test"
        )

        formatted = estimator.format_individual_item_costs(result)

        assert "2 API calls each" in formatted
        assert "Two-pass" in formatted or "two-pass" in formatted

    def test_tasks_still_no_additional_cost(self, estimator):
        """Test that tasks are still shown as generated with stories."""
        item_counts = {
            'milestones': 1,
            'epics': 1,
            'stories': 1,
            'tasks': 3
        }

        result = estimator.estimate_individual_item_costs(
            provider='claude',
            item_counts=item_counts,
            idea_content="Test"
        )

        task_estimate = next(
            e for e in result['item_estimates'] if e['item_type'] == 'tasks'
        )
        assert task_estimate['total_cost'] == 0
        assert "Generated with stories" in task_estimate['description']


class TestTwoPassIntegration:
    """Integration tests for two-pass story generation flow."""

    @pytest.fixture
    def full_hierarchy(self):
        """Create a full roadmap hierarchy."""
        milestone = Milestone(name="MVP", number="1")
        milestone.generation_status = ItemStatus.GENERATED
        milestone.content = "MVP milestone content"

        epic = Epic(name="User Auth", number="1.0", parent=milestone)
        epic.generation_status = ItemStatus.GENERATED
        epic.content = "Auth epic content"
        milestone.add_child(epic)

        story1 = Story(name="Login", number="1.0.1", parent=epic)
        story1.outline_description = "Implement user login"
        epic.add_child(story1)

        story2 = Story(name="Logout", number="1.0.2", parent=epic)
        story2.outline_description = "Implement user logout"
        epic.add_child(story2)

        # Add tasks to stories
        for i, story in enumerate([story1, story2], 1):
            task1 = Task(name="UI", number=f"1.0.{i}.1", parent=story)
            task2 = Task(name="API", number=f"1.0.{i}.2", parent=story)
            story.add_child(task1)
            story.add_child(task2)

        return [milestone]

    def test_sibling_context_available_for_pass2(self, full_hierarchy):
        """Test that sibling story context is available during Pass 2."""
        mock_llm = MagicMock()
        mock_llm.provider = 'claude'
        generator = RecursiveRoadmapGenerator(mock_llm)

        story1 = full_hierarchy[0].get_children_by_type('Epic')[0].get_children_by_type('Story')[0]

        # Simulate story1 being generated
        story1.description = "Login functionality"
        story1.generation_status = ItemStatus.GENERATED

        # Get sibling context for story2
        story2 = full_hierarchy[0].get_children_by_type('Epic')[0].get_children_by_type('Story')[1]
        sibling_context = generator.context_summarizer.get_sibling_context(story2)

        assert "Story 1.0.1" in sibling_context
        assert "Login" in sibling_context

    def test_acceptance_criteria_passed_to_pass2(self, full_hierarchy):
        """Test that acceptance criteria from Pass 1 are available in Pass 2."""
        story = full_hierarchy[0].get_children_by_type('Epic')[0].get_children_by_type('Story')[0]

        # Simulate Pass 1
        story.description = "Login functionality"
        story.user_value = "As a user, I want to log in"
        story.acceptance_criteria = [
            "User can enter credentials",
            "Invalid credentials show error",
            "Successful login creates session"
        ]
        story.pass1_complete = True

        # Generate Pass 2 prompt
        prompt = story.generate_tasks_prompt(
            cascading_context="Context",
            sibling_context="Siblings",
            roadmap_overview="Overview"
        )

        assert "AC1:" in prompt
        assert "AC2:" in prompt
        assert "AC3:" in prompt
        assert "credentials" in prompt


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
