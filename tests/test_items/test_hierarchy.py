"""Tests for the full roadmap item hierarchy."""

from datetime import datetime, timezone

import pytest

from arcane.core.items import (
    Priority,
    Status,
    Task,
    Story,
    Epic,
    Milestone,
    Roadmap,
    ProjectContext,
)


def create_task(id: str, hours: int = 4) -> Task:
    """Helper to create a task with minimal required fields."""
    return Task(
        id=id,
        name=f"Task {id}",
        description=f"Description for {id}",
        priority=Priority.MEDIUM,
        estimated_hours=hours,
        acceptance_criteria=["Done"],
        implementation_notes="Notes",
        claude_code_prompt="Implement this",
    )


def create_context() -> ProjectContext:
    """Helper to create a minimal project context."""
    return ProjectContext(
        project_name="Test Project",
        vision="A test vision",
        problem_statement="Solving test problems",
        target_users=["developers"],
        timeline="3 months",
        team_size=2,
        developer_experience="mid-level",
        budget_constraints="moderate",
        must_have_features=["feature1"],
    )


class TestStoryHours:
    """Tests for Story.estimated_hours computed field."""

    def test_story_with_no_tasks(self):
        """Story with no tasks has 0 estimated hours."""
        story = Story(
            id="story-1",
            name="Empty Story",
            description="No tasks",
            priority=Priority.MEDIUM,
            acceptance_criteria=["Done"],
        )
        assert story.estimated_hours == 0

    def test_story_hours_sum_tasks(self):
        """Story estimated_hours sums all task hours."""
        story = Story(
            id="story-1",
            name="Story with tasks",
            description="Has tasks",
            priority=Priority.HIGH,
            acceptance_criteria=["Done"],
            tasks=[
                create_task("task-1", hours=4),
                create_task("task-2", hours=6),
                create_task("task-3", hours=2),
            ],
        )
        assert story.estimated_hours == 12  # 4 + 6 + 2


class TestEpicHours:
    """Tests for Epic.estimated_hours computed field."""

    def test_epic_with_no_stories(self):
        """Epic with no stories has 0 estimated hours."""
        epic = Epic(
            id="epic-1",
            name="Empty Epic",
            description="No stories",
            priority=Priority.MEDIUM,
            goal="Test goal",
        )
        assert epic.estimated_hours == 0

    def test_epic_hours_sum_stories(self):
        """Epic estimated_hours sums all story hours."""
        epic = Epic(
            id="epic-1",
            name="Epic with stories",
            description="Has stories",
            priority=Priority.HIGH,
            goal="Complete epic",
            stories=[
                Story(
                    id="story-1",
                    name="Story 1",
                    description="First story",
                    priority=Priority.MEDIUM,
                    acceptance_criteria=["Done"],
                    tasks=[create_task("task-1", 4), create_task("task-2", 6)],
                ),
                Story(
                    id="story-2",
                    name="Story 2",
                    description="Second story",
                    priority=Priority.MEDIUM,
                    acceptance_criteria=["Done"],
                    tasks=[create_task("task-3", 8)],
                ),
            ],
        )
        assert epic.estimated_hours == 18  # (4 + 6) + 8


class TestMilestoneHours:
    """Tests for Milestone.estimated_hours computed field."""

    def test_milestone_with_no_epics(self):
        """Milestone with no epics has 0 estimated hours."""
        milestone = Milestone(
            id="milestone-1",
            name="Empty Milestone",
            description="No epics",
            priority=Priority.MEDIUM,
            goal="Test goal",
        )
        assert milestone.estimated_hours == 0


class TestRoadmapHierarchy:
    """Tests for the full Roadmap hierarchy."""

    def test_full_hierarchy_hours_rollup(self):
        """Test estimated_hours rolls up correctly through entire tree."""
        roadmap = Roadmap(
            id="roadmap-1",
            project_name="Test Project",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            context=create_context(),
            milestones=[
                Milestone(
                    id="m1",
                    name="Milestone 1",
                    description="First milestone",
                    priority=Priority.HIGH,
                    goal="Complete M1",
                    epics=[
                        Epic(
                            id="e1",
                            name="Epic 1",
                            description="First epic",
                            priority=Priority.HIGH,
                            goal="Complete E1",
                            stories=[
                                Story(
                                    id="s1",
                                    name="Story 1",
                                    description="First story",
                                    priority=Priority.MEDIUM,
                                    acceptance_criteria=["Done"],
                                    tasks=[
                                        create_task("t1", 4),
                                        create_task("t2", 6),
                                    ],
                                ),
                            ],
                        ),
                        Epic(
                            id="e2",
                            name="Epic 2",
                            description="Second epic",
                            priority=Priority.MEDIUM,
                            goal="Complete E2",
                            stories=[
                                Story(
                                    id="s2",
                                    name="Story 2",
                                    description="Second story",
                                    priority=Priority.MEDIUM,
                                    acceptance_criteria=["Done"],
                                    tasks=[create_task("t3", 8)],
                                ),
                            ],
                        ),
                    ],
                ),
                Milestone(
                    id="m2",
                    name="Milestone 2",
                    description="Second milestone",
                    priority=Priority.MEDIUM,
                    goal="Complete M2",
                    epics=[
                        Epic(
                            id="e3",
                            name="Epic 3",
                            description="Third epic",
                            priority=Priority.LOW,
                            goal="Complete E3",
                            stories=[
                                Story(
                                    id="s3",
                                    name="Story 3",
                                    description="Third story",
                                    priority=Priority.LOW,
                                    acceptance_criteria=["Done"],
                                    tasks=[
                                        create_task("t4", 2),
                                        create_task("t5", 4),
                                        create_task("t6", 6),
                                    ],
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        )

        # Verify individual rollups
        assert roadmap.milestones[0].epics[0].stories[0].estimated_hours == 10  # 4 + 6
        assert roadmap.milestones[0].epics[0].estimated_hours == 10
        assert roadmap.milestones[0].epics[1].estimated_hours == 8
        assert roadmap.milestones[0].estimated_hours == 18  # 10 + 8
        assert roadmap.milestones[1].estimated_hours == 12  # 2 + 4 + 6

        # Verify total
        assert roadmap.total_hours == 30  # 18 + 12

    def test_total_items_counts(self):
        """Test total_items returns correct counts."""
        roadmap = Roadmap(
            id="roadmap-1",
            project_name="Test Project",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            context=create_context(),
            milestones=[
                Milestone(
                    id="m1",
                    name="M1",
                    description="M1",
                    priority=Priority.HIGH,
                    goal="G1",
                    epics=[
                        Epic(
                            id="e1",
                            name="E1",
                            description="E1",
                            priority=Priority.HIGH,
                            goal="G1",
                            stories=[
                                Story(
                                    id="s1",
                                    name="S1",
                                    description="S1",
                                    priority=Priority.MEDIUM,
                                    acceptance_criteria=["Done"],
                                    tasks=[create_task("t1"), create_task("t2")],
                                ),
                                Story(
                                    id="s2",
                                    name="S2",
                                    description="S2",
                                    priority=Priority.MEDIUM,
                                    acceptance_criteria=["Done"],
                                    tasks=[create_task("t3")],
                                ),
                            ],
                        ),
                        Epic(
                            id="e2",
                            name="E2",
                            description="E2",
                            priority=Priority.MEDIUM,
                            goal="G2",
                            stories=[
                                Story(
                                    id="s3",
                                    name="S3",
                                    description="S3",
                                    priority=Priority.LOW,
                                    acceptance_criteria=["Done"],
                                    tasks=[create_task("t4"), create_task("t5")],
                                ),
                            ],
                        ),
                    ],
                ),
                Milestone(
                    id="m2",
                    name="M2",
                    description="M2",
                    priority=Priority.MEDIUM,
                    goal="G2",
                    epics=[
                        Epic(
                            id="e3",
                            name="E3",
                            description="E3",
                            priority=Priority.LOW,
                            goal="G3",
                            stories=[
                                Story(
                                    id="s4",
                                    name="S4",
                                    description="S4",
                                    priority=Priority.LOW,
                                    acceptance_criteria=["Done"],
                                    tasks=[create_task("t6")],
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        )

        counts = roadmap.total_items
        assert counts["milestones"] == 2
        assert counts["epics"] == 3
        assert counts["stories"] == 4
        assert counts["tasks"] == 6

    def test_roadmap_serialization_roundtrip(self):
        """Test Roadmap serialization to JSON and back."""
        original = Roadmap(
            id="roadmap-test",
            project_name="Serialization Test",
            created_at=datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
            context=create_context(),
            milestones=[
                Milestone(
                    id="m1",
                    name="Milestone 1",
                    description="First milestone",
                    priority=Priority.HIGH,
                    goal="Complete M1",
                    target_date="2024-03-01",
                    epics=[
                        Epic(
                            id="e1",
                            name="Epic 1",
                            description="First epic",
                            priority=Priority.HIGH,
                            goal="Complete E1",
                            prerequisites=["e0"],
                            stories=[
                                Story(
                                    id="s1",
                                    name="Story 1",
                                    description="First story",
                                    priority=Priority.MEDIUM,
                                    status=Status.IN_PROGRESS,
                                    acceptance_criteria=["AC1", "AC2"],
                                    labels=["backend"],
                                    tasks=[
                                        Task(
                                            id="t1",
                                            name="Task 1",
                                            description="First task",
                                            priority=Priority.HIGH,
                                            status=Status.COMPLETED,
                                            estimated_hours=4,
                                            prerequisites=["t0"],
                                            acceptance_criteria=["TAC1"],
                                            implementation_notes="Use Python",
                                            claude_code_prompt="Implement...",
                                            labels=["python"],
                                        ),
                                    ],
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        )

        # Serialize to JSON
        json_str = original.model_dump_json()

        # Deserialize from JSON
        restored = Roadmap.model_validate_json(json_str)

        # Verify all fields
        assert restored.id == original.id
        assert restored.project_name == original.project_name
        assert restored.created_at == original.created_at
        assert restored.updated_at == original.updated_at
        assert restored.context.project_name == original.context.project_name

        # Verify hierarchy
        assert len(restored.milestones) == 1
        assert restored.milestones[0].name == "Milestone 1"
        assert restored.milestones[0].target_date == "2024-03-01"
        assert len(restored.milestones[0].epics) == 1
        assert restored.milestones[0].epics[0].prerequisites == ["e0"]
        assert len(restored.milestones[0].epics[0].stories) == 1
        assert restored.milestones[0].epics[0].stories[0].status == Status.IN_PROGRESS
        assert len(restored.milestones[0].epics[0].stories[0].tasks) == 1
        assert restored.milestones[0].epics[0].stories[0].tasks[0].estimated_hours == 4

        # Verify computed fields still work
        assert restored.total_hours == 4
        assert restored.total_items == {
            "milestones": 1,
            "epics": 1,
            "stories": 1,
            "tasks": 1,
        }
