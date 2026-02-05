"""Tests for arcane.generators.skeletons module."""

import json

import pytest

from arcane.items.base import Priority
from arcane.generators.skeletons import (
    MilestoneSkeleton,
    MilestoneSkeletonList,
    EpicSkeleton,
    EpicSkeletonList,
    StorySkeleton,
    StorySkeletonList,
)


class TestMilestoneSkeleton:
    """Tests for MilestoneSkeleton model."""

    def test_create_milestone_skeleton(self):
        """MilestoneSkeleton can be created with valid data."""
        skeleton = MilestoneSkeleton(
            name="MVP Release",
            goal="Launch minimum viable product",
            description="First release with core features",
            priority=Priority.HIGH,
            suggested_epic_areas=["Authentication", "Core Features", "Basic UI"],
        )

        assert skeleton.name == "MVP Release"
        assert skeleton.goal == "Launch minimum viable product"
        assert skeleton.priority == Priority.HIGH
        assert len(skeleton.suggested_epic_areas) == 3

    def test_milestone_skeleton_serialization(self):
        """MilestoneSkeleton can be serialized to JSON and back."""
        skeleton = MilestoneSkeleton(
            name="MVP Release",
            goal="Launch MVP",
            description="First release",
            priority=Priority.HIGH,
            suggested_epic_areas=["Auth", "Core"],
        )

        json_str = skeleton.model_dump_json()
        parsed = json.loads(json_str)

        assert parsed["name"] == "MVP Release"
        assert parsed["priority"] == "high"

        # Deserialize back
        restored = MilestoneSkeleton.model_validate_json(json_str)
        assert restored.name == skeleton.name
        assert restored.priority == skeleton.priority


class TestMilestoneSkeletonList:
    """Tests for MilestoneSkeletonList model."""

    def test_create_list_with_multiple_skeletons(self):
        """MilestoneSkeletonList can hold multiple skeletons."""
        skeletons = MilestoneSkeletonList(
            milestones=[
                MilestoneSkeleton(
                    name="MVP",
                    goal="Launch MVP",
                    description="First release",
                    priority=Priority.CRITICAL,
                    suggested_epic_areas=["Core"],
                ),
                MilestoneSkeleton(
                    name="v1.0",
                    goal="Full feature set",
                    description="Complete product",
                    priority=Priority.HIGH,
                    suggested_epic_areas=["Advanced Features"],
                ),
            ]
        )

        assert len(skeletons.milestones) == 2
        assert skeletons.milestones[0].name == "MVP"
        assert skeletons.milestones[1].name == "v1.0"

    def test_list_serialization_roundtrip(self):
        """MilestoneSkeletonList survives JSON roundtrip."""
        original = MilestoneSkeletonList(
            milestones=[
                MilestoneSkeleton(
                    name="Phase 1",
                    goal="Foundation",
                    description="Build foundation",
                    priority=Priority.HIGH,
                    suggested_epic_areas=["Setup", "CI/CD"],
                ),
            ]
        )

        json_str = original.model_dump_json()
        restored = MilestoneSkeletonList.model_validate_json(json_str)

        assert len(restored.milestones) == 1
        assert restored.milestones[0].name == "Phase 1"


class TestEpicSkeleton:
    """Tests for EpicSkeleton model."""

    def test_create_epic_skeleton(self):
        """EpicSkeleton can be created with valid data."""
        skeleton = EpicSkeleton(
            name="User Authentication",
            goal="Secure user login system",
            description="Implement authentication flows",
            priority=Priority.CRITICAL,
            suggested_story_areas=["Login", "Registration", "Password Reset"],
        )

        assert skeleton.name == "User Authentication"
        assert skeleton.goal == "Secure user login system"
        assert len(skeleton.suggested_story_areas) == 3

    def test_epic_skeleton_serialization(self):
        """EpicSkeleton can be serialized to JSON and back."""
        skeleton = EpicSkeleton(
            name="Auth",
            goal="Auth system",
            description="Auth implementation",
            priority=Priority.HIGH,
            suggested_story_areas=["Login"],
        )

        json_str = skeleton.model_dump_json()
        restored = EpicSkeleton.model_validate_json(json_str)

        assert restored.name == skeleton.name
        assert restored.priority == skeleton.priority


class TestEpicSkeletonList:
    """Tests for EpicSkeletonList model."""

    def test_create_epic_list(self):
        """EpicSkeletonList can hold multiple epics."""
        epics = EpicSkeletonList(
            epics=[
                EpicSkeleton(
                    name="Auth",
                    goal="Authentication",
                    description="User auth",
                    priority=Priority.CRITICAL,
                    suggested_story_areas=["Login"],
                ),
                EpicSkeleton(
                    name="Dashboard",
                    goal="User dashboard",
                    description="Main dashboard",
                    priority=Priority.HIGH,
                    suggested_story_areas=["Widgets"],
                ),
            ]
        )

        assert len(epics.epics) == 2


class TestStorySkeleton:
    """Tests for StorySkeleton model."""

    def test_create_story_skeleton(self):
        """StorySkeleton can be created with valid data."""
        skeleton = StorySkeleton(
            name="User Login",
            description="Users can log in with email and password",
            priority=Priority.CRITICAL,
            acceptance_criteria=[
                "User can enter email and password",
                "Invalid credentials show error message",
                "Successful login redirects to dashboard",
            ],
        )

        assert skeleton.name == "User Login"
        assert len(skeleton.acceptance_criteria) == 3

    def test_story_skeleton_serialization(self):
        """StorySkeleton can be serialized to JSON and back."""
        skeleton = StorySkeleton(
            name="Login",
            description="Login feature",
            priority=Priority.HIGH,
            acceptance_criteria=["Can login"],
        )

        json_str = skeleton.model_dump_json()
        restored = StorySkeleton.model_validate_json(json_str)

        assert restored.name == skeleton.name
        assert restored.acceptance_criteria == skeleton.acceptance_criteria


class TestStorySkeletonList:
    """Tests for StorySkeletonList model."""

    def test_create_story_list(self):
        """StorySkeletonList can hold multiple stories."""
        stories = StorySkeletonList(
            stories=[
                StorySkeleton(
                    name="Login",
                    description="User login",
                    priority=Priority.CRITICAL,
                    acceptance_criteria=["Can login"],
                ),
                StorySkeleton(
                    name="Logout",
                    description="User logout",
                    priority=Priority.HIGH,
                    acceptance_criteria=["Can logout"],
                ),
            ]
        )

        assert len(stories.stories) == 2


class TestAllSkeletonsJsonRoundtrip:
    """Integration tests for JSON serialization of all skeleton types."""

    def test_all_skeletons_json_roundtrip(self):
        """All skeleton models survive JSON roundtrip."""
        milestone = MilestoneSkeleton(
            name="M1",
            goal="Goal 1",
            description="Desc 1",
            priority=Priority.HIGH,
            suggested_epic_areas=["E1"],
        )
        epic = EpicSkeleton(
            name="E1",
            goal="Goal E1",
            description="Desc E1",
            priority=Priority.MEDIUM,
            suggested_story_areas=["S1"],
        )
        story = StorySkeleton(
            name="S1",
            description="Desc S1",
            priority=Priority.LOW,
            acceptance_criteria=["AC1"],
        )

        # Roundtrip each
        for original in [milestone, epic, story]:
            json_str = original.model_dump_json()
            restored = type(original).model_validate_json(json_str)
            assert restored.name == original.name
            assert restored.priority == original.priority
