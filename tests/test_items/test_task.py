"""Tests for arcane.items.task module."""

import pytest
from pydantic import ValidationError

from arcane.items import Task, Priority, Status


class TestTask:
    """Tests for the Task model."""

    def test_task_creation(self):
        """Test creating a Task with all required fields."""
        task = Task(
            id="task-123",
            name="Implement login",
            description="Create the login functionality",
            priority=Priority.HIGH,
            estimated_hours=4,
            acceptance_criteria=["User can log in", "Error messages shown"],
            implementation_notes="Use OAuth2",
            claude_code_prompt="Implement a login form with email/password",
        )

        assert task.id == "task-123"
        assert task.name == "Implement login"
        assert task.estimated_hours == 4
        assert len(task.acceptance_criteria) == 2
        assert task.prerequisites == []  # default
        assert task.status == Status.NOT_STARTED  # inherited default

    def test_task_with_prerequisites(self):
        """Test Task with prerequisites specified."""
        task = Task(
            id="task-456",
            name="Add validation",
            description="Add form validation",
            priority=Priority.MEDIUM,
            estimated_hours=2,
            prerequisites=["task-123", "task-124"],
            acceptance_criteria=["Fields are validated"],
            implementation_notes="Use Zod",
            claude_code_prompt="Add validation to the form",
        )

        assert task.prerequisites == ["task-123", "task-124"]

    def test_estimated_hours_min_validation(self):
        """Test that estimated_hours must be at least 1."""
        with pytest.raises(ValidationError) as exc_info:
            Task(
                id="task-invalid",
                name="Invalid Task",
                description="Too short",
                priority=Priority.LOW,
                estimated_hours=0,  # Invalid: must be >= 1
                acceptance_criteria=["Done"],
                implementation_notes="Notes",
                claude_code_prompt="Prompt",
            )

        assert "greater than or equal to 1" in str(exc_info.value)

    def test_estimated_hours_max_validation(self):
        """Test that estimated_hours must be at most 40."""
        with pytest.raises(ValidationError) as exc_info:
            Task(
                id="task-invalid",
                name="Invalid Task",
                description="Too long",
                priority=Priority.LOW,
                estimated_hours=41,  # Invalid: must be <= 40
                acceptance_criteria=["Done"],
                implementation_notes="Notes",
                claude_code_prompt="Prompt",
            )

        assert "less than or equal to 40" in str(exc_info.value)

    def test_estimated_hours_boundary_values(self):
        """Test boundary values for estimated_hours."""
        # Minimum valid
        task_min = Task(
            id="task-min",
            name="Min Task",
            description="Minimum hours",
            priority=Priority.LOW,
            estimated_hours=1,
            acceptance_criteria=["Done"],
            implementation_notes="Notes",
            claude_code_prompt="Prompt",
        )
        assert task_min.estimated_hours == 1

        # Maximum valid
        task_max = Task(
            id="task-max",
            name="Max Task",
            description="Maximum hours",
            priority=Priority.LOW,
            estimated_hours=40,
            acceptance_criteria=["Done"],
            implementation_notes="Notes",
            claude_code_prompt="Prompt",
        )
        assert task_max.estimated_hours == 40

    def test_task_json_serialization(self):
        """Test Task serialization to JSON and back."""
        task = Task(
            id="task-json",
            name="JSON Task",
            description="Test JSON serialization",
            priority=Priority.CRITICAL,
            status=Status.IN_PROGRESS,
            estimated_hours=8,
            prerequisites=["task-prev"],
            acceptance_criteria=["Criterion 1", "Criterion 2"],
            implementation_notes="Use TypeScript",
            claude_code_prompt="Create a component that...",
            labels=["frontend", "urgent"],
        )

        # Serialize to JSON
        json_str = task.model_dump_json()

        # Deserialize from JSON
        restored = Task.model_validate_json(json_str)

        assert restored.id == task.id
        assert restored.name == task.name
        assert restored.estimated_hours == 8
        assert restored.prerequisites == ["task-prev"]
        assert restored.acceptance_criteria == ["Criterion 1", "Criterion 2"]
        assert restored.priority == Priority.CRITICAL
        assert restored.status == Status.IN_PROGRESS
        assert restored.labels == ["frontend", "urgent"]
