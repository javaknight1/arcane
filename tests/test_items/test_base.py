"""Tests for arcane.items.base module."""

import pytest

from arcane.items import Priority, Status, BaseItem


class TestPriorityEnum:
    """Tests for the Priority enum."""

    def test_priority_values(self):
        """Verify all Priority enum values exist."""
        assert Priority.CRITICAL == "critical"
        assert Priority.HIGH == "high"
        assert Priority.MEDIUM == "medium"
        assert Priority.LOW == "low"

    def test_priority_is_string_enum(self):
        """Verify Priority values are strings."""
        assert isinstance(Priority.CRITICAL.value, str)
        assert Priority.HIGH.value == "high"


class TestStatusEnum:
    """Tests for the Status enum."""

    def test_status_values(self):
        """Verify all Status enum values exist."""
        assert Status.NOT_STARTED == "not_started"
        assert Status.IN_PROGRESS == "in_progress"
        assert Status.BLOCKED == "blocked"
        assert Status.COMPLETED == "completed"

    def test_status_is_string_enum(self):
        """Verify Status values are strings."""
        assert isinstance(Status.NOT_STARTED.value, str)
        assert Status.IN_PROGRESS.value == "in_progress"


class TestBaseItem:
    """Tests for the BaseItem model."""

    def test_base_item_creation(self):
        """Test creating a BaseItem with required fields."""
        item = BaseItem(
            id="item-123",
            name="Test Item",
            description="A test item",
            priority=Priority.MEDIUM,
        )

        assert item.id == "item-123"
        assert item.name == "Test Item"
        assert item.description == "A test item"
        assert item.priority == Priority.MEDIUM
        assert item.status == Status.NOT_STARTED  # default
        assert item.labels == []  # default

    def test_base_item_with_all_fields(self):
        """Test creating a BaseItem with all fields specified."""
        item = BaseItem(
            id="item-456",
            name="Full Item",
            description="An item with all fields",
            priority=Priority.HIGH,
            status=Status.IN_PROGRESS,
            labels=["backend", "urgent"],
        )

        assert item.status == Status.IN_PROGRESS
        assert item.labels == ["backend", "urgent"]

    def test_base_item_serialization(self):
        """Test BaseItem serialization to dict and back."""
        item = BaseItem(
            id="item-789",
            name="Serializable Item",
            description="Test serialization",
            priority=Priority.LOW,
            labels=["test"],
        )

        # Serialize to dict
        data = item.model_dump()
        assert data["id"] == "item-789"
        assert data["priority"] == "low"
        assert data["status"] == "not_started"

        # Deserialize back
        restored = BaseItem.model_validate(data)
        assert restored.id == item.id
        assert restored.priority == item.priority

    def test_base_item_json_serialization(self):
        """Test BaseItem serialization to JSON and back."""
        item = BaseItem(
            id="item-json",
            name="JSON Item",
            description="Test JSON",
            priority=Priority.CRITICAL,
        )

        # Serialize to JSON
        json_str = item.model_dump_json()
        assert '"priority":"critical"' in json_str

        # Deserialize from JSON
        restored = BaseItem.model_validate_json(json_str)
        assert restored.id == item.id
        assert restored.priority == Priority.CRITICAL
