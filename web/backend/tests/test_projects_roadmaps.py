"""Tests for project, roadmap, and item CRUD endpoints."""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.roadmap import RoadmapRecord
from app.models.user import User
from app.services.auth import hash_password

pytestmark = pytest.mark.asyncio


# --- Fixtures ---


@pytest.fixture
async def user_and_headers(client: AsyncClient):
    """Register a user and return (user_response, auth_headers)."""
    resp = await client.post("/auth/register", json={
        "email": "projuser@example.com",
        "password": "securepassword",
    })
    assert resp.status_code == 201
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    me = await client.get("/auth/me", headers=headers)
    return me.json(), headers


@pytest.fixture
async def project(client: AsyncClient, user_and_headers):
    """Create and return a project."""
    _, headers = user_and_headers
    resp = await client.post("/projects/", json={"name": "Test Project"}, headers=headers)
    assert resp.status_code == 201
    return resp.json(), headers


@pytest.fixture
async def roadmap(client: AsyncClient, project):
    """Create and return a roadmap under the project."""
    proj, headers = project
    resp = await client.post(
        f"/projects/{proj['id']}/roadmaps",
        json={"name": "Test Roadmap", "context": {"vision": "test"}},
        headers=headers,
    )
    assert resp.status_code == 201
    return resp.json(), headers


@pytest.fixture
async def roadmap_with_items(client: AsyncClient, roadmap):
    """Create a roadmap with a milestone->epic->story->task hierarchy."""
    rm, headers = roadmap
    rm_id = rm["id"]

    # Add milestone at root
    ms_resp = await client.post(
        f"/roadmaps/{rm_id}/items/root/children",
        json={"item_type": "milestone", "data": {"name": "M1", "description": "Milestone 1", "priority": "high", "goal": "G1"}},
        headers=headers,
    )
    assert ms_resp.status_code == 201
    ms_id = ms_resp.json()["item_id"]

    # Add epic under milestone
    ep_resp = await client.post(
        f"/roadmaps/{rm_id}/items/{ms_id}/children",
        json={"item_type": "epic", "data": {"name": "E1", "description": "Epic 1", "priority": "medium", "goal": "EG1"}},
        headers=headers,
    )
    assert ep_resp.status_code == 201
    ep_id = ep_resp.json()["item_id"]

    # Add story under epic
    st_resp = await client.post(
        f"/roadmaps/{rm_id}/items/{ep_id}/children",
        json={"item_type": "story", "data": {"name": "S1", "description": "Story 1", "priority": "low", "acceptance_criteria": ["AC1"]}},
        headers=headers,
    )
    assert st_resp.status_code == 201
    st_id = st_resp.json()["item_id"]

    # Add task under story
    tk_resp = await client.post(
        f"/roadmaps/{rm_id}/items/{st_id}/children",
        json={"item_type": "task", "data": {"name": "T1", "description": "Task 1", "priority": "medium", "estimated_hours": 4}},
        headers=headers,
    )
    assert tk_resp.status_code == 201
    tk_id = tk_resp.json()["item_id"]

    return {
        "roadmap": rm,
        "headers": headers,
        "milestone_id": ms_id,
        "epic_id": ep_id,
        "story_id": st_id,
        "task_id": tk_id,
    }


# --- Project CRUD ---


class TestProjectCRUD:
    async def test_create_project(self, client: AsyncClient, user_and_headers):
        _, headers = user_and_headers
        resp = await client.post("/projects/", json={"name": "My Project"}, headers=headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "My Project"
        assert data["roadmaps"] == []
        assert "id" in data

    async def test_create_project_empty_name(self, client: AsyncClient, user_and_headers):
        _, headers = user_and_headers
        resp = await client.post("/projects/", json={"name": ""}, headers=headers)
        assert resp.status_code == 422

    async def test_list_projects(self, client: AsyncClient, project):
        _, headers = project
        resp = await client.get("/projects/", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["name"] == "Test Project"
        assert data[0]["roadmap_count"] == 0

    async def test_list_projects_with_roadmap_count(self, client: AsyncClient, roadmap):
        rm, headers = roadmap
        resp = await client.get("/projects/", headers=headers)
        data = resp.json()
        assert data[0]["roadmap_count"] == 1

    async def test_get_project(self, client: AsyncClient, project):
        proj, headers = project
        resp = await client.get(f"/projects/{proj['id']}", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Test Project"
        assert data["roadmaps"] == []

    async def test_get_project_with_roadmaps(self, client: AsyncClient, roadmap):
        rm, headers = roadmap
        resp = await client.get(f"/projects/{rm['project_id']}", headers=headers)
        data = resp.json()
        assert len(data["roadmaps"]) == 1
        assert data["roadmaps"][0]["name"] == "Test Roadmap"

    async def test_roadmap_summary_no_data(self, client: AsyncClient, roadmap):
        """Draft roadmap with no roadmap_data returns null counts."""
        rm, headers = roadmap
        resp = await client.get(f"/projects/{rm['project_id']}", headers=headers)
        data = resp.json()
        summary = data["roadmaps"][0]
        assert summary["item_counts"] is None
        assert summary["completion_percent"] is None

    async def test_roadmap_summary_with_items(self, client: AsyncClient, roadmap_with_items):
        """Roadmap with items returns correct counts and completion percent."""
        ctx = roadmap_with_items
        rm = ctx["roadmap"]
        headers = ctx["headers"]
        resp = await client.get(f"/projects/{rm['project_id']}", headers=headers)
        data = resp.json()
        summary = data["roadmaps"][0]
        # 1 milestone + 1 epic + 1 story + 1 task = 4 items
        assert summary["item_counts"] == {
            "milestones": 1,
            "epics": 1,
            "stories": 1,
            "tasks": 1,
        }
        # All items default to not_started, so 0% completed
        assert summary["completion_percent"] == 0.0

    async def test_roadmap_summary_completion_percent(self, client: AsyncClient, roadmap_with_items):
        """Marking items as completed updates completion_percent."""
        ctx = roadmap_with_items
        rm_id = ctx["roadmap"]["id"]
        project_id = ctx["roadmap"]["project_id"]
        tk_id = ctx["task_id"]
        headers = ctx["headers"]

        # Mark task as completed
        resp = await client.patch(
            f"/roadmaps/{rm_id}/items/{tk_id}",
            json={"status": "completed"},
            headers=headers,
        )
        assert resp.status_code == 200

        # Fetch project and check completion
        resp = await client.get(f"/projects/{project_id}", headers=headers)
        data = resp.json()
        summary = data["roadmaps"][0]
        assert summary["item_counts"]["tasks"] == 1
        # 1 of 4 items completed = 25%
        assert summary["completion_percent"] == 25.0

    async def test_get_project_not_found(self, client: AsyncClient, user_and_headers):
        _, headers = user_and_headers
        fake_id = str(uuid.uuid4())
        resp = await client.get(f"/projects/{fake_id}", headers=headers)
        assert resp.status_code == 404

    async def test_update_project(self, client: AsyncClient, project):
        proj, headers = project
        resp = await client.patch(
            f"/projects/{proj['id']}", json={"name": "Updated Name"}, headers=headers
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "Updated Name"

    async def test_delete_project(self, client: AsyncClient, project):
        proj, headers = project
        resp = await client.delete(f"/projects/{proj['id']}", headers=headers)
        assert resp.status_code == 204
        # Verify it's gone
        resp = await client.get(f"/projects/{proj['id']}", headers=headers)
        assert resp.status_code == 404

    async def test_delete_project_cascades_roadmaps(self, client: AsyncClient, roadmap):
        rm, headers = roadmap
        project_id = rm["project_id"]
        roadmap_id = rm["id"]
        # Delete project
        resp = await client.delete(f"/projects/{project_id}", headers=headers)
        assert resp.status_code == 204
        # Roadmap should be gone
        resp = await client.get(f"/roadmaps/{roadmap_id}", headers=headers)
        assert resp.status_code == 404

    async def test_project_ownership_isolation(self, client: AsyncClient, project):
        """A different user cannot see another user's project."""
        proj, _ = project
        # Register a different user
        resp = await client.post("/auth/register", json={
            "email": "other@example.com",
            "password": "otherpassword",
        })
        other_token = resp.json()["access_token"]
        other_headers = {"Authorization": f"Bearer {other_token}"}
        # Should not be able to get the project
        resp = await client.get(f"/projects/{proj['id']}", headers=other_headers)
        assert resp.status_code == 404

    async def test_no_auth_returns_401(self, client: AsyncClient):
        resp = await client.get("/projects/")
        assert resp.status_code == 401


# --- Roadmap CRUD ---


class TestRoadmapCRUD:
    async def test_create_roadmap(self, client: AsyncClient, project):
        proj, headers = project
        resp = await client.post(
            f"/projects/{proj['id']}/roadmaps",
            json={"name": "Roadmap 1", "context": {"key": "value"}},
            headers=headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Roadmap 1"
        assert data["status"] == "draft"
        assert data["context"] == {"key": "value"}
        assert data["project_id"] == proj["id"]

    async def test_create_roadmap_no_context(self, client: AsyncClient, project):
        proj, headers = project
        resp = await client.post(
            f"/projects/{proj['id']}/roadmaps",
            json={"name": "Roadmap No Ctx"},
            headers=headers,
        )
        assert resp.status_code == 201
        assert resp.json()["context"] is None

    async def test_list_roadmaps(self, client: AsyncClient, roadmap):
        rm, headers = roadmap
        resp = await client.get(f"/projects/{rm['project_id']}/roadmaps", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["name"] == "Test Roadmap"

    async def test_get_roadmap(self, client: AsyncClient, roadmap):
        rm, headers = roadmap
        resp = await client.get(f"/roadmaps/{rm['id']}", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Test Roadmap"
        assert data["context"] == {"vision": "test"}

    async def test_get_roadmap_not_found(self, client: AsyncClient, user_and_headers):
        _, headers = user_and_headers
        fake_id = str(uuid.uuid4())
        resp = await client.get(f"/roadmaps/{fake_id}", headers=headers)
        assert resp.status_code == 404

    async def test_delete_roadmap(self, client: AsyncClient, roadmap):
        rm, headers = roadmap
        resp = await client.delete(f"/roadmaps/{rm['id']}", headers=headers)
        assert resp.status_code == 204
        resp = await client.get(f"/roadmaps/{rm['id']}", headers=headers)
        assert resp.status_code == 404

    async def test_roadmap_ownership_isolation(self, client: AsyncClient, roadmap):
        rm, _ = roadmap
        # Register a different user
        resp = await client.post("/auth/register", json={
            "email": "roadmapother@example.com",
            "password": "otherpassword",
        })
        other_headers = {"Authorization": f"Bearer {resp.json()['access_token']}"}
        resp = await client.get(f"/roadmaps/{rm['id']}", headers=other_headers)
        assert resp.status_code == 404


# --- Item Endpoints ---


class TestItemUpdate:
    async def test_partial_update_item(self, client: AsyncClient, roadmap_with_items):
        ctx = roadmap_with_items
        rm_id = ctx["roadmap"]["id"]
        ms_id = ctx["milestone_id"]
        headers = ctx["headers"]

        resp = await client.patch(
            f"/roadmaps/{rm_id}/items/{ms_id}",
            json={"name": "Updated Milestone", "priority": "critical"},
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"]["name"] == "Updated Milestone"
        assert data["data"]["priority"] == "critical"
        # Other fields preserved
        assert data["data"]["description"] == "Milestone 1"
        assert data["item_type"] == "milestone"

    async def test_update_item_not_found(self, client: AsyncClient, roadmap):
        rm, headers = roadmap
        resp = await client.patch(
            f"/roadmaps/{rm['id']}/items/nonexistent-id",
            json={"name": "X"},
            headers=headers,
        )
        assert resp.status_code == 404

    async def test_update_task_fields(self, client: AsyncClient, roadmap_with_items):
        ctx = roadmap_with_items
        rm_id = ctx["roadmap"]["id"]
        tk_id = ctx["task_id"]
        headers = ctx["headers"]

        resp = await client.patch(
            f"/roadmaps/{rm_id}/items/{tk_id}",
            json={"estimated_hours": 8, "claude_code_prompt": "Do the thing"},
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["estimated_hours"] == 8
        assert data["claude_code_prompt"] == "Do the thing"


class TestItemDelete:
    async def test_delete_leaf_item(self, client: AsyncClient, roadmap_with_items):
        ctx = roadmap_with_items
        rm_id = ctx["roadmap"]["id"]
        tk_id = ctx["task_id"]
        headers = ctx["headers"]

        resp = await client.delete(f"/roadmaps/{rm_id}/items/{tk_id}", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["deleted_id"] == tk_id
        assert data["deleted_type"] == "task"
        assert data["children_deleted"] == 0

    async def test_delete_item_with_children(self, client: AsyncClient, roadmap_with_items):
        ctx = roadmap_with_items
        rm_id = ctx["roadmap"]["id"]
        ms_id = ctx["milestone_id"]
        headers = ctx["headers"]

        resp = await client.delete(f"/roadmaps/{rm_id}/items/{ms_id}", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["deleted_type"] == "milestone"
        # milestone has 1 epic -> 1 story -> 1 task = 3 descendants
        assert data["children_deleted"] == 3

    async def test_delete_item_not_found(self, client: AsyncClient, roadmap):
        rm, headers = roadmap
        resp = await client.delete(f"/roadmaps/{rm['id']}/items/nope", headers=headers)
        assert resp.status_code == 404


class TestItemAddChild:
    async def test_add_milestone_at_root(self, client: AsyncClient, roadmap):
        rm, headers = roadmap
        resp = await client.post(
            f"/roadmaps/{rm['id']}/items/root/children",
            json={"item_type": "milestone", "data": {"name": "M1", "description": "d", "priority": "high", "goal": "g"}},
            headers=headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["item_type"] == "milestone"
        assert data["data"]["name"] == "M1"
        assert data["item_id"].startswith("milestone-")

    async def test_add_epic_under_milestone(self, client: AsyncClient, roadmap_with_items):
        ctx = roadmap_with_items
        rm_id = ctx["roadmap"]["id"]
        ms_id = ctx["milestone_id"]
        headers = ctx["headers"]

        resp = await client.post(
            f"/roadmaps/{rm_id}/items/{ms_id}/children",
            json={"item_type": "epic", "data": {"name": "E2", "description": "d", "priority": "low", "goal": "g2"}},
            headers=headers,
        )
        assert resp.status_code == 201
        assert resp.json()["item_type"] == "epic"

    async def test_invalid_child_type_for_parent(self, client: AsyncClient, roadmap_with_items):
        """Cannot add a task directly under a milestone."""
        ctx = roadmap_with_items
        rm_id = ctx["roadmap"]["id"]
        ms_id = ctx["milestone_id"]
        headers = ctx["headers"]

        resp = await client.post(
            f"/roadmaps/{rm_id}/items/{ms_id}/children",
            json={"item_type": "task", "data": {"name": "T", "description": "d", "priority": "low"}},
            headers=headers,
        )
        assert resp.status_code == 400

    async def test_cannot_add_children_to_task(self, client: AsyncClient, roadmap_with_items):
        ctx = roadmap_with_items
        rm_id = ctx["roadmap"]["id"]
        tk_id = ctx["task_id"]
        headers = ctx["headers"]

        resp = await client.post(
            f"/roadmaps/{rm_id}/items/{tk_id}/children",
            json={"item_type": "task", "data": {"name": "Sub", "description": "d", "priority": "low"}},
            headers=headers,
        )
        assert resp.status_code == 400

    async def test_parent_not_found(self, client: AsyncClient, roadmap):
        rm, headers = roadmap
        resp = await client.post(
            f"/roadmaps/{rm['id']}/items/nonexistent/children",
            json={"item_type": "epic", "data": {"name": "E", "description": "d", "priority": "low", "goal": "g"}},
            headers=headers,
        )
        assert resp.status_code == 404

    async def test_non_milestone_at_root_rejected(self, client: AsyncClient, roadmap):
        rm, headers = roadmap
        resp = await client.post(
            f"/roadmaps/{rm['id']}/items/root/children",
            json={"item_type": "epic", "data": {"name": "E", "description": "d", "priority": "low", "goal": "g"}},
            headers=headers,
        )
        assert resp.status_code == 400

    async def test_invalid_item_type_rejected(self, client: AsyncClient, roadmap):
        rm, headers = roadmap
        resp = await client.post(
            f"/roadmaps/{rm['id']}/items/root/children",
            json={"item_type": "bogus", "data": {"name": "X"}},
            headers=headers,
        )
        assert resp.status_code == 422


class TestItemReorder:
    async def test_reorder_milestones(self, client: AsyncClient, roadmap):
        rm, headers = roadmap
        rm_id = rm["id"]

        # Create two milestones
        r1 = await client.post(
            f"/roadmaps/{rm_id}/items/root/children",
            json={"item_type": "milestone", "data": {"name": "M1", "description": "d", "priority": "high", "goal": "g"}},
            headers=headers,
        )
        r2 = await client.post(
            f"/roadmaps/{rm_id}/items/root/children",
            json={"item_type": "milestone", "data": {"name": "M2", "description": "d", "priority": "low", "goal": "g"}},
            headers=headers,
        )
        id1 = r1.json()["item_id"]
        id2 = r2.json()["item_id"]

        # Reorder: swap
        resp = await client.put(
            f"/roadmaps/{rm_id}/items/reorder",
            json={"parent_id": "root", "item_ids": [id2, id1]},
            headers=headers,
        )
        assert resp.status_code == 200

        # Verify order
        rm_resp = await client.get(f"/roadmaps/{rm_id}", headers=headers)
        milestones = rm_resp.json()["roadmap_data"]["milestones"]
        assert milestones[0]["id"] == id2
        assert milestones[1]["id"] == id1

    async def test_reorder_mismatched_ids(self, client: AsyncClient, roadmap):
        rm, headers = roadmap
        rm_id = rm["id"]

        # Create one milestone
        r1 = await client.post(
            f"/roadmaps/{rm_id}/items/root/children",
            json={"item_type": "milestone", "data": {"name": "M1", "description": "d", "priority": "high", "goal": "g"}},
            headers=headers,
        )
        id1 = r1.json()["item_id"]

        # Reorder with wrong IDs
        resp = await client.put(
            f"/roadmaps/{rm_id}/items/reorder",
            json={"parent_id": "root", "item_ids": [id1, "fake-id"]},
            headers=headers,
        )
        assert resp.status_code == 400

    async def test_reorder_parent_not_found(self, client: AsyncClient, roadmap):
        rm, headers = roadmap
        resp = await client.put(
            f"/roadmaps/{rm['id']}/items/reorder",
            json={"parent_id": "nonexistent", "item_ids": []},
            headers=headers,
        )
        assert resp.status_code == 404


# --- find_parent_chain unit tests ---


class TestFindParentChain:
    """Unit tests for the find_parent_chain helper."""

    def _make_data(self):
        return {
            "milestones": [{
                "id": "ms-1",
                "name": "M1",
                "description": "Milestone 1",
                "priority": "high",
                "goal": "G1",
                "status": "not_started",
                "labels": [],
                "epics": [{
                    "id": "ep-1",
                    "name": "E1",
                    "description": "Epic 1",
                    "priority": "medium",
                    "goal": "EG1",
                    "status": "not_started",
                    "labels": [],
                    "stories": [{
                        "id": "st-1",
                        "name": "S1",
                        "description": "Story 1",
                        "priority": "low",
                        "status": "not_started",
                        "labels": [],
                        "tasks": [{
                            "id": "tk-1",
                            "name": "T1",
                            "description": "Task 1",
                            "priority": "medium",
                            "status": "not_started",
                            "labels": [],
                        }],
                    }],
                }],
            }],
        }

    def test_find_parent_chain_milestone(self):
        from app.services.roadmap_items import find_parent_chain

        data = self._make_data()
        result = find_parent_chain(data, "ms-1")
        assert result == {}

    def test_find_parent_chain_epic(self):
        from app.services.roadmap_items import find_parent_chain

        data = self._make_data()
        result = find_parent_chain(data, "ep-1")
        assert result is not None
        assert "milestone" in result
        assert result["milestone"]["name"] == "M1"
        assert result["milestone"]["goal"] == "G1"
        assert "epic" not in result

    def test_find_parent_chain_story(self):
        from app.services.roadmap_items import find_parent_chain

        data = self._make_data()
        result = find_parent_chain(data, "st-1")
        assert result is not None
        assert "milestone" in result
        assert "epic" in result
        assert result["milestone"]["name"] == "M1"
        assert result["epic"]["name"] == "E1"
        assert result["epic"]["goal"] == "EG1"

    def test_find_parent_chain_task(self):
        from app.services.roadmap_items import find_parent_chain

        data = self._make_data()
        result = find_parent_chain(data, "tk-1")
        assert result is not None
        assert "milestone" in result
        assert "epic" in result
        assert "story" in result
        assert result["story"]["name"] == "S1"
        # story entries should not have 'goal'
        assert "goal" not in result["story"]

    def test_find_parent_chain_not_found(self):
        from app.services.roadmap_items import find_parent_chain

        data = self._make_data()
        result = find_parent_chain(data, "nonexistent")
        assert result is None
