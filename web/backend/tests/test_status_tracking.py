"""Tests for status cascade, roadmap stats, and overdue detection."""

import pytest
from httpx import AsyncClient

from app.services.roadmap_items import compute_parent_status, cascade_status_update

pytestmark = pytest.mark.asyncio


# --- Unit tests for compute_parent_status ---


def test_compute_parent_status_all_completed():
    children = [{"status": "completed"}, {"status": "completed"}]
    assert compute_parent_status(children) == "completed"


def test_compute_parent_status_all_not_started():
    children = [{"status": "not_started"}, {"status": "not_started"}]
    assert compute_parent_status(children) == "not_started"


def test_compute_parent_status_mixed():
    children = [{"status": "completed"}, {"status": "not_started"}]
    assert compute_parent_status(children) == "in_progress"


def test_compute_parent_status_with_blocked():
    children = [{"status": "completed"}, {"status": "blocked"}]
    assert compute_parent_status(children) == "blocked"


def test_compute_parent_status_empty_children():
    assert compute_parent_status([]) == "not_started"


def test_compute_parent_status_missing_status_field():
    children = [{"name": "no status"}, {"status": "completed"}]
    assert compute_parent_status(children) == "in_progress"


# --- Unit tests for cascade_status_update ---


def _make_data():
    return {
        "milestones": [
            {
                "id": "ms-1",
                "name": "M1",
                "status": "not_started",
                "epics": [
                    {
                        "id": "ep-1",
                        "name": "E1",
                        "status": "not_started",
                        "stories": [
                            {
                                "id": "st-1",
                                "name": "S1",
                                "status": "not_started",
                                "tasks": [
                                    {"id": "tk-1", "status": "not_started", "estimated_hours": 4},
                                    {"id": "tk-2", "status": "not_started", "estimated_hours": 8},
                                ],
                            }
                        ],
                    }
                ],
            }
        ]
    }


def test_cascade_updates_parent_on_task_completed():
    data = _make_data()
    data["milestones"][0]["epics"][0]["stories"][0]["tasks"][0]["status"] = "completed"
    changed = cascade_status_update(data, "tk-1")
    # Story, epic, milestone should all become in_progress
    assert len(changed) == 3
    ids = [c["id"] for c in changed]
    assert "st-1" in ids
    assert "ep-1" in ids
    assert "ms-1" in ids
    for c in changed:
        assert c["status"] == "in_progress"


def test_cascade_all_tasks_completed():
    data = _make_data()
    for tk in data["milestones"][0]["epics"][0]["stories"][0]["tasks"]:
        tk["status"] = "completed"
    changed = cascade_status_update(data, "tk-1")
    for c in changed:
        assert c["status"] == "completed"


def test_cascade_no_change_when_already_correct():
    data = _make_data()
    # All not_started, cascade on a not_started task -> no change
    changed = cascade_status_update(data, "tk-1")
    assert changed == []


def test_cascade_story_status_change():
    data = _make_data()
    data["milestones"][0]["epics"][0]["stories"][0]["status"] = "completed"
    changed = cascade_status_update(data, "st-1")
    # Epic and milestone should update
    ids = [c["id"] for c in changed]
    assert "ep-1" in ids
    assert "ms-1" in ids


def test_cascade_milestone_returns_empty():
    data = _make_data()
    changed = cascade_status_update(data, "ms-1")
    assert changed == []


def test_cascade_item_not_found():
    data = _make_data()
    changed = cascade_status_update(data, "nonexistent-id")
    assert changed == []


# --- Integration tests via API ---


@pytest.fixture
async def user_and_headers(client: AsyncClient):
    resp = await client.post("/auth/register", json={
        "email": "statususer@example.com",
        "password": "securepassword",
    })
    assert resp.status_code == 201
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    return headers


@pytest.fixture
async def roadmap_with_hierarchy(client: AsyncClient, user_and_headers):
    headers = user_and_headers

    # Create project
    proj_resp = await client.post("/projects/", json={"name": "Status Test"}, headers=headers)
    proj_id = proj_resp.json()["id"]

    # Create roadmap
    rm_resp = await client.post(
        f"/projects/{proj_id}/roadmaps",
        json={"name": "Status Roadmap", "context": {"vision": "test"}},
        headers=headers,
    )
    rm_id = rm_resp.json()["id"]

    # milestone
    ms_resp = await client.post(
        f"/roadmaps/{rm_id}/items/root/children",
        json={"item_type": "milestone", "data": {
            "name": "M1", "description": "Milestone 1", "priority": "high",
            "goal": "G1", "target_date": "2020-01-01",
        }},
        headers=headers,
    )
    ms_id = ms_resp.json()["item_id"]

    # epic
    ep_resp = await client.post(
        f"/roadmaps/{rm_id}/items/{ms_id}/children",
        json={"item_type": "epic", "data": {
            "name": "E1", "description": "Epic 1", "priority": "medium", "goal": "EG1",
        }},
        headers=headers,
    )
    ep_id = ep_resp.json()["item_id"]

    # story
    st_resp = await client.post(
        f"/roadmaps/{rm_id}/items/{ep_id}/children",
        json={"item_type": "story", "data": {
            "name": "S1", "description": "Story 1", "priority": "low",
            "acceptance_criteria": ["AC1"],
        }},
        headers=headers,
    )
    st_id = st_resp.json()["item_id"]

    # task 1
    tk1_resp = await client.post(
        f"/roadmaps/{rm_id}/items/{st_id}/children",
        json={"item_type": "task", "data": {
            "name": "T1", "description": "Task 1", "priority": "medium", "estimated_hours": 4,
        }},
        headers=headers,
    )
    tk1_id = tk1_resp.json()["item_id"]

    # task 2
    tk2_resp = await client.post(
        f"/roadmaps/{rm_id}/items/{st_id}/children",
        json={"item_type": "task", "data": {
            "name": "T2", "description": "Task 2", "priority": "medium", "estimated_hours": 8,
        }},
        headers=headers,
    )
    tk2_id = tk2_resp.json()["item_id"]

    return {
        "headers": headers,
        "project_id": proj_id,
        "roadmap_id": rm_id,
        "milestone_id": ms_id,
        "epic_id": ep_id,
        "story_id": st_id,
        "task1_id": tk1_id,
        "task2_id": tk2_id,
    }


async def test_cascade_updates_parent_on_child_status_change(
    client: AsyncClient, roadmap_with_hierarchy
):
    h = roadmap_with_hierarchy
    headers = h["headers"]
    rm_id = h["roadmap_id"]

    # Complete task 1
    resp = await client.patch(
        f"/roadmaps/{rm_id}/items/{h['task1_id']}",
        json={"status": "completed"},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    cascaded = data.get("cascaded", [])
    # Parents should be in_progress (one task done, one not)
    cascaded_ids = [c["id"] for c in cascaded]
    assert h["story_id"] in cascaded_ids
    assert h["epic_id"] in cascaded_ids
    assert h["milestone_id"] in cascaded_ids
    for c in cascaded:
        assert c["status"] == "in_progress"


async def test_cascade_all_children_completed(
    client: AsyncClient, roadmap_with_hierarchy
):
    h = roadmap_with_hierarchy
    headers = h["headers"]
    rm_id = h["roadmap_id"]

    # Complete both tasks
    await client.patch(
        f"/roadmaps/{rm_id}/items/{h['task1_id']}",
        json={"status": "completed"},
        headers=headers,
    )
    resp = await client.patch(
        f"/roadmaps/{rm_id}/items/{h['task2_id']}",
        json={"status": "completed"},
        headers=headers,
    )
    assert resp.status_code == 200
    cascaded = resp.json().get("cascaded", [])
    for c in cascaded:
        assert c["status"] == "completed"


async def test_stats_endpoint_returns_milestone_breakdown(
    client: AsyncClient, roadmap_with_hierarchy
):
    h = roadmap_with_hierarchy
    resp = await client.get(
        f"/roadmaps/{h['roadmap_id']}/stats", headers=h["headers"]
    )
    assert resp.status_code == 200
    stats = resp.json()
    assert "milestones" in stats
    assert len(stats["milestones"]) == 1
    ms = stats["milestones"][0]
    assert ms["name"] == "M1"
    assert ms["epic_count"] == 1
    assert ms["story_count"] == 1
    assert ms["task_count"] == 2


async def test_stats_hours_tracking(
    client: AsyncClient, roadmap_with_hierarchy
):
    h = roadmap_with_hierarchy
    headers = h["headers"]
    rm_id = h["roadmap_id"]

    # Initially no hours completed
    resp = await client.get(f"/roadmaps/{rm_id}/stats", headers=headers)
    stats = resp.json()
    assert stats["hours_total"] == 12  # 4 + 8
    assert stats["hours_completed"] == 0
    assert stats["completion_percent"] == 0.0

    # Complete task 1 (4 hours)
    await client.patch(
        f"/roadmaps/{rm_id}/items/{h['task1_id']}",
        json={"status": "completed"},
        headers=headers,
    )
    resp = await client.get(f"/roadmaps/{rm_id}/stats", headers=headers)
    stats = resp.json()
    assert stats["hours_completed"] == 4
    assert stats["completion_percent"] == pytest.approx(33.3, abs=0.1)


async def test_stats_overdue_detection(
    client: AsyncClient, roadmap_with_hierarchy
):
    h = roadmap_with_hierarchy
    resp = await client.get(f"/roadmaps/{h['roadmap_id']}/stats", headers=h["headers"])
    stats = resp.json()
    ms = stats["milestones"][0]
    # target_date is 2020-01-01, which is in the past
    assert ms["is_overdue"] is True
    assert ms["target_date"] == "2020-01-01"


async def test_stats_no_data_returns_empty(client: AsyncClient, user_and_headers):
    headers = user_and_headers
    # Create project + empty roadmap
    proj_resp = await client.post("/projects/", json={"name": "Empty"}, headers=headers)
    proj_id = proj_resp.json()["id"]
    rm_resp = await client.post(
        f"/projects/{proj_id}/roadmaps",
        json={"name": "Empty Roadmap"},
        headers=headers,
    )
    rm_id = rm_resp.json()["id"]

    resp = await client.get(f"/roadmaps/{rm_id}/stats", headers=headers)
    assert resp.status_code == 200
    stats = resp.json()
    assert stats["hours_total"] == 0
    assert stats["hours_completed"] == 0
    assert stats["completion_percent"] == 0.0
    assert stats["milestones"] == []


async def test_roadmap_summary_includes_hours(
    client: AsyncClient, roadmap_with_hierarchy
):
    h = roadmap_with_hierarchy
    headers = h["headers"]

    # Complete a task first
    await client.patch(
        f"/roadmaps/{h['roadmap_id']}/items/{h['task1_id']}",
        json={"status": "completed"},
        headers=headers,
    )

    resp = await client.get(f"/projects/{h['project_id']}", headers=headers)
    assert resp.status_code == 200
    project = resp.json()
    rm_summary = project["roadmaps"][0]
    assert rm_summary["hours_total"] == 12
    assert rm_summary["hours_completed"] == 4
