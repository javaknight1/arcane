"""Shared fixtures for project management tests."""

from datetime import datetime, timezone

import pytest

from arcane.core.items import (
    Epic,
    Milestone,
    Priority,
    ProjectContext,
    Roadmap,
    Status,
    Story,
    Task,
)


@pytest.fixture
def sample_context():
    """Sample ProjectContext for testing."""
    return ProjectContext(
        project_name="Test Project",
        vision="A test application",
        problem_statement="Testing is important",
        target_users=["developers"],
        timeline="3 months",
        team_size=2,
        developer_experience="senior",
        budget_constraints="moderate",
        tech_stack=["Python", "React"],
        infrastructure_preferences="AWS",
        existing_codebase=False,
        must_have_features=["auth", "dashboard"],
        nice_to_have_features=["dark mode"],
        out_of_scope=["mobile app"],
        similar_products=["other apps"],
        notes="Test notes",
    )


@pytest.fixture
def sample_roadmap(sample_context):
    """Sample Roadmap with full hierarchy for testing."""
    task1 = Task(
        id="task-001",
        name="Create login form",
        description="Build the login form component",
        priority=Priority.HIGH,
        status=Status.NOT_STARTED,
        estimated_hours=4,
        acceptance_criteria=["Form renders", "Validates input"],
        implementation_notes="Use React Hook Form",
        claude_code_prompt="Create a login form with email and password fields...",
    )
    task2 = Task(
        id="task-002",
        name="Add form validation",
        description="Validate form inputs",
        priority=Priority.MEDIUM,
        status=Status.NOT_STARTED,
        estimated_hours=2,
        prerequisites=["task-001"],
        acceptance_criteria=["Email validated", "Password validated"],
        implementation_notes="Use Zod for validation",
        claude_code_prompt="Add Zod validation to the login form...",
    )

    story = Story(
        id="story-001",
        name="User Login",
        description="Users can log in with email/password",
        priority=Priority.CRITICAL,
        status=Status.NOT_STARTED,
        acceptance_criteria=["Can enter credentials", "Error on invalid"],
        tasks=[task1, task2],
    )

    epic = Epic(
        id="epic-001",
        name="Authentication",
        goal="Secure user authentication",
        description="User login and registration",
        priority=Priority.CRITICAL,
        status=Status.NOT_STARTED,
        stories=[story],
    )

    milestone = Milestone(
        id="milestone-001",
        name="MVP",
        goal="Launch minimum viable product",
        description="First release with core features",
        priority=Priority.CRITICAL,
        status=Status.NOT_STARTED,
        epics=[epic],
    )

    return Roadmap(
        id="roadmap-001",
        project_name="Test Project",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        context=sample_context,
        milestones=[milestone],
    )
