"""Tests for Notion field mapping functionality."""

import pytest
from arcane.engines.export.notion_field_mapper import (
    NotionFieldMapper,
    NotionPropertyType,
    FieldMapping,
    get_mappings_for_item_type,
)
from arcane.items.task import Task
from arcane.items.story import Story
from arcane.items.epic import Epic
from arcane.items.milestone import Milestone


class TestNotionFieldMapper:
    """Tests for NotionFieldMapper class."""

    def test_task_properties_complete(self):
        """Test that task properties are completely mapped."""
        task = Task(
            name="Create login form",
            number="1.0.1.1",
            duration=8,
            priority="High",
            description="Build the login form component",
            benefits="- Enables user authentication\n- Improves security",
            prerequisites="Story 1.0.1 complete",
            technical_requirements="React, TypeScript",
            claude_code_prompt="Create a React component for login...",
            tags=["frontend", "authentication"],
            work_type="implementation",
            complexity="moderate"
        )

        mapper = NotionFieldMapper()
        properties = mapper.item_to_notion_properties(task)

        # Verify all expected properties are present
        assert "Name" in properties
        assert "Type" in properties
        assert "Status" in properties
        assert "Priority" in properties
        assert "Duration" in properties
        assert "Goal/Description" in properties
        assert "Benefits" in properties
        assert "Prerequisites" in properties
        assert "Technical Requirements" in properties
        assert "Claude Code Prompt" in properties
        assert "Work Type" in properties
        assert "Complexity" in properties
        assert "Tags" in properties

        # Verify property formats
        assert properties["Name"]["title"][0]["text"]["content"] == "Task 1.0.1.1: Create login form"
        assert properties["Type"]["select"]["name"] == "Task"
        assert properties["Priority"]["select"]["name"] == "High"
        assert properties["Duration"]["number"] == 8
        assert properties["Work Type"]["select"]["name"] == "Implementation"
        assert properties["Complexity"]["select"]["name"] == "Moderate"

        # Verify tags are multi-select
        assert "multi_select" in properties["Tags"]
        tag_names = [t["name"] for t in properties["Tags"]["multi_select"]]
        assert "frontend" in tag_names
        assert "authentication" in tag_names

    def test_story_properties_with_user_value(self):
        """Test that story properties include user value."""
        story = Story(
            name="User Authentication",
            number="1.0.1",
            duration=24,
            priority="Critical",
            description="Implement user authentication flow",
        )
        story.user_value = "As a user, I want to log in securely so that I can access my data"
        story.acceptance_criteria = [
            "Users can register with email",
            "Users can log in with valid credentials",
            "Error messages are clear"
        ]

        mapper = NotionFieldMapper()
        properties = mapper.item_to_notion_properties(story)

        # Verify User Value is mapped
        assert "User Value" in properties
        assert "As a user" in properties["User Value"]["rich_text"][0]["text"]["content"]

    def test_milestone_properties_with_goal(self):
        """Test that milestone properties include goal."""
        milestone = Milestone(
            name="Foundation",
            number="1",
            duration=320,
            priority="Critical",
            description="Set up project foundation"
        )
        milestone.goal = "Deliver working prototype with authentication"
        milestone.risks_if_delayed = "- All subsequent work blocked\n- Technical debt accumulation"

        mapper = NotionFieldMapper()
        properties = mapper.item_to_notion_properties(milestone)

        # Verify Milestone Goal is mapped
        assert "Milestone Goal" in properties
        assert "prototype" in properties["Milestone Goal"]["rich_text"][0]["text"]["content"]

        # Verify Risks is mapped
        assert "Risks" in properties
        assert "blocked" in properties["Risks"]["rich_text"][0]["text"]["content"]

    def test_epic_properties_with_risks(self):
        """Test that epic properties include risks."""
        epic = Epic(
            name="Authentication System",
            number="1.0",
            duration=120,
            priority="Critical"
        )
        epic.risks_and_mitigations = "OAuth downtime -> Use fallback auth"

        mapper = NotionFieldMapper()
        properties = mapper.item_to_notion_properties(epic)

        # Verify Risks is mapped
        assert "Risks" in properties
        assert "OAuth" in properties["Risks"]["rich_text"][0]["text"]["content"]

    def test_text_truncation(self):
        """Test that long text is properly truncated."""
        long_text = "x" * 3000  # Exceeds 2000 char limit

        task = Task(
            name="Test Task",
            number="1.0.1.1",
            description=long_text
        )

        mapper = NotionFieldMapper()
        properties = mapper.item_to_notion_properties(task)

        # Should be split into multiple text blocks
        rich_text = properties["Goal/Description"]["rich_text"]
        assert len(rich_text) >= 2  # Should have multiple blocks

        # Verify truncation was logged
        assert len(mapper.truncation_log) > 0

    def test_empty_fields_use_defaults(self):
        """Test that empty fields use default values."""
        task = Task(
            name="Minimal Task",
            number="1.0.1.1"
        )

        mapper = NotionFieldMapper()
        properties = mapper.item_to_notion_properties(task)

        # Should have default values for select fields (capitalized by mapper)
        assert properties["Status"]["select"]["name"] == "Not started"
        assert properties["Work Type"]["select"]["name"] == "Implementation"
        assert properties["Complexity"]["select"]["name"] == "Moderate"

    def test_select_field_capitalization(self):
        """Test that select fields are properly capitalized."""
        task = Task(
            name="Test Task",
            number="1.0.1.1",
            work_type="implementation",  # lowercase
            complexity="complex",  # lowercase
            priority="high"  # lowercase
        )

        mapper = NotionFieldMapper()
        properties = mapper.item_to_notion_properties(task)

        # All should be capitalized
        assert properties["Work Type"]["select"]["name"] == "Implementation"
        assert properties["Complexity"]["select"]["name"] == "Complex"
        assert properties["Priority"]["select"]["name"] == "High"

    def test_tags_from_list(self):
        """Test that tags list is converted to multi-select."""
        task = Task(
            name="Test Task",
            number="1.0.1.1",
            tags=["frontend", "api", "database"]
        )

        mapper = NotionFieldMapper()
        properties = mapper.item_to_notion_properties(task)

        tag_names = [t["name"] for t in properties["Tags"]["multi_select"]]
        assert "frontend" in tag_names
        assert "api" in tag_names
        assert "database" in tag_names


class TestPageContentBlocks:
    """Tests for page content block generation."""

    def test_acceptance_criteria_as_todo_items(self):
        """Test that acceptance criteria become to-do items."""
        story = Story(name="Test Story", number="1.0.1")
        story.acceptance_criteria = [
            "Users can register",
            "Users can log in",
            "Password reset works"
        ]

        mapper = NotionFieldMapper()
        blocks = mapper.build_page_content_blocks(story)

        # Should have heading + 3 to-do items
        assert len(blocks) >= 4

        # First block should be heading
        assert blocks[0]["type"] == "heading_2"
        assert "Acceptance Criteria" in blocks[0]["heading_2"]["rich_text"][0]["text"]["content"]

        # Following blocks should be to-do items
        todo_blocks = [b for b in blocks if b["type"] == "to_do"]
        assert len(todo_blocks) == 3
        assert all(b["to_do"]["checked"] is False for b in todo_blocks)

    def test_claude_prompt_as_code_block(self):
        """Test that Claude prompts become code blocks."""
        task = Task(name="Test Task", number="1.0.1.1")
        task.claude_code_prompt = "Create a component at src/Login.tsx with..."

        mapper = NotionFieldMapper()
        blocks = mapper.build_page_content_blocks(task)

        # Should have heading + code block
        code_blocks = [b for b in blocks if b["type"] == "code"]
        assert len(code_blocks) == 1
        assert code_blocks[0]["code"]["language"] == "markdown"
        assert "Login.tsx" in code_blocks[0]["code"]["rich_text"][0]["text"]["content"]

    def test_key_deliverables_as_bullet_list(self):
        """Test that key deliverables become bullet items."""
        milestone = Milestone(name="Test Milestone", number="1")
        milestone.key_deliverables = [
            "Working auth system",
            "Database schema",
            "API endpoints"
        ]

        mapper = NotionFieldMapper()
        blocks = mapper.build_page_content_blocks(milestone)

        # Should have heading + bullet items
        bullet_blocks = [b for b in blocks if b["type"] == "bulleted_list_item"]
        assert len(bullet_blocks) == 3

    def test_goals_as_bullet_list(self):
        """Test that epic goals become bullet items."""
        epic = Epic(name="Test Epic", number="1.0")
        epic.goals = [
            "Implement secure auth",
            "Build user profiles",
            "Create admin panel"
        ]

        mapper = NotionFieldMapper()
        blocks = mapper.build_page_content_blocks(epic)

        # Should have heading + bullet items
        bullet_blocks = [b for b in blocks if b["type"] == "bulleted_list_item"]
        assert len(bullet_blocks) == 3

    def test_user_value_as_callout(self):
        """Test that user value becomes a callout block."""
        story = Story(name="Test Story", number="1.0.1")
        story.user_value = "As a user, I want to login so I can access features"

        mapper = NotionFieldMapper()
        blocks = mapper.build_page_content_blocks(story)

        # Should have user value callout
        callout_blocks = [b for b in blocks if b["type"] == "callout"]
        assert len(callout_blocks) == 1
        assert callout_blocks[0]["callout"]["icon"]["emoji"] == "👤"

    def test_empty_item_no_blocks(self):
        """Test that empty items produce no content blocks."""
        task = Task(name="Empty Task", number="1.0.1.1")

        mapper = NotionFieldMapper()
        blocks = mapper.build_page_content_blocks(task)

        # Should be empty since no special content
        assert len(blocks) == 0


class TestGetMappingsForItemType:
    """Tests for mapping registry."""

    def test_task_mappings_include_claude_prompt(self):
        """Test that task mappings include Claude Code Prompt."""
        mappings = get_mappings_for_item_type('Task')
        attributes = [m.item_attribute for m in mappings]
        assert 'claude_code_prompt' in attributes

    def test_story_mappings_include_user_value(self):
        """Test that story mappings include user value."""
        mappings = get_mappings_for_item_type('Story')
        attributes = [m.item_attribute for m in mappings]
        assert 'user_value' in attributes

    def test_milestone_mappings_include_goal(self):
        """Test that milestone mappings include goal."""
        mappings = get_mappings_for_item_type('Milestone')
        attributes = [m.item_attribute for m in mappings]
        assert 'goal' in attributes

    def test_epic_mappings_include_risks(self):
        """Test that epic mappings include risks."""
        mappings = get_mappings_for_item_type('Epic')
        attributes = [m.item_attribute for m in mappings]
        assert 'risks_and_mitigations' in attributes

    def test_unknown_type_returns_base_mappings(self):
        """Test that unknown types return base mappings."""
        mappings = get_mappings_for_item_type('Unknown')
        # Should return some mappings (base)
        assert len(mappings) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
