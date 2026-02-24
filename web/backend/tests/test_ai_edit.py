"""Tests for AI-assisted editing endpoint."""

import copy
import uuid
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.main import app
from app.models.roadmap import RoadmapRecord

pytestmark = pytest.mark.asyncio


# --- Helpers ---


def _fake_settings(**overrides):
    defaults = {
        "database_url": "sqlite+aiosqlite://",
        "anthropic_api_key": "sk-fake-test-key",
    }
    defaults.update(overrides)

    def factory():
        return Settings(**defaults)

    return factory


@pytest.fixture(autouse=True)
def fake_api_key():
    app.dependency_overrides[get_settings] = _fake_settings()
    yield
    app.dependency_overrides.pop(get_settings, None)


@pytest.fixture
async def user_and_headers(client: AsyncClient):
    resp = await client.post("/auth/register", json={
        "email": "aiedituser@example.com",
        "password": "securepassword",
    })
    assert resp.status_code == 201
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    me = await client.get("/auth/me", headers=headers)
    return me.json(), headers


@pytest.fixture
async def project(client: AsyncClient, user_and_headers):
    _, headers = user_and_headers
    resp = await client.post("/projects/", json={"name": "Edit Project"}, headers=headers)
    assert resp.status_code == 201
    return resp.json(), headers


SAMPLE_CONTEXT = {
    "project_name": "Test",
    "vision": "A test project",
    "problem_statement": "Testing",
    "target_users": ["devs"],
    "timeline": "1 month MVP",
    "team_size": 1,
    "developer_experience": "senior",
    "budget_constraints": "minimal (free tier everything)",
    "must_have_features": ["auth"],
}

SAMPLE_ROADMAP_DATA = {
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
                "acceptance_criteria": ["AC1"],
                "tasks": [{
                    "id": "tk-1",
                    "name": "T1",
                    "description": "Task 1",
                    "priority": "medium",
                    "status": "not_started",
                    "labels": [],
                    "estimated_hours": 4,
                    "prerequisites": [],
                    "acceptance_criteria": ["AC1"],
                    "implementation_notes": "Some notes",
                    "claude_code_prompt": "Do the thing",
                }],
            }],
        }],
    }],
}


@pytest.fixture
async def roadmap_with_items(client: AsyncClient, project, db_session: AsyncSession):
    proj, headers = project
    resp = await client.post(
        f"/projects/{proj['id']}/roadmaps",
        json={"name": "Edit Roadmap", "context": SAMPLE_CONTEXT},
        headers=headers,
    )
    assert resp.status_code == 201
    rm = resp.json()

    rm_uuid = uuid.UUID(rm["id"])
    result = await db_session.execute(
        select(RoadmapRecord).where(RoadmapRecord.id == rm_uuid)
    )
    record = result.scalar_one()
    record.roadmap_data = copy.deepcopy(SAMPLE_ROADMAP_DATA)
    record.status = "generated"
    await db_session.commit()

    return rm, headers


@pytest.fixture
async def roadmap_no_context(client: AsyncClient, project):
    proj, headers = project
    resp = await client.post(
        f"/projects/{proj['id']}/roadmaps",
        json={"name": "No Ctx Roadmap"},
        headers=headers,
    )
    assert resp.status_code == 201
    return resp.json(), headers


def _mock_run_ai_edit(item, item_type, command, context_dict, parent_context, anthropic_api_key, model):
    """Return a modified copy of the item."""
    edited = dict(item)
    edited["name"] = f"[Edited] {item['name']}"
    edited["description"] = f"AI edited: {command}"
    return edited


# --- Tests ---


class TestAiEdit:
    async def test_ai_edit_returns_200(self, client: AsyncClient, roadmap_with_items):
        rm, headers = roadmap_with_items
        with patch("app.routers.roadmaps.run_ai_edit", side_effect=_mock_run_ai_edit):
            resp = await client.post(
                f"/roadmaps/{rm['id']}/items/ep-1/ai-edit",
                json={"command": "Make this more detailed"},
                headers=headers,
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["item_id"] == "ep-1"
        assert data["item_type"] == "epic"
        assert data["original"]["name"] == "E1"
        assert data["edited"]["name"] == "[Edited] E1"
        assert "AI edited:" in data["edited"]["description"]

    async def test_ai_edit_task(self, client: AsyncClient, roadmap_with_items):
        rm, headers = roadmap_with_items
        with patch("app.routers.roadmaps.run_ai_edit", side_effect=_mock_run_ai_edit):
            resp = await client.post(
                f"/roadmaps/{rm['id']}/items/tk-1/ai-edit",
                json={"command": "Add more detail to the prompt"},
                headers=headers,
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["item_type"] == "task"
        assert data["edited"]["name"] == "[Edited] T1"

    async def test_ai_edit_persists_changes(self, client: AsyncClient, roadmap_with_items):
        rm, headers = roadmap_with_items
        with patch("app.routers.roadmaps.run_ai_edit", side_effect=_mock_run_ai_edit):
            await client.post(
                f"/roadmaps/{rm['id']}/items/ep-1/ai-edit",
                json={"command": "Rename this"},
                headers=headers,
            )
        # Fetch the roadmap and verify the change was saved
        resp = await client.get(f"/roadmaps/{rm['id']}", headers=headers)
        data = resp.json()
        epic = data["roadmap_data"]["milestones"][0]["epics"][0]
        assert epic["name"] == "[Edited] E1"

    async def test_ai_edit_item_not_found(self, client: AsyncClient, roadmap_with_items):
        rm, headers = roadmap_with_items
        resp = await client.post(
            f"/roadmaps/{rm['id']}/items/nonexistent-id/ai-edit",
            json={"command": "Edit this"},
            headers=headers,
        )
        assert resp.status_code == 404

    async def test_ai_edit_no_context(self, client: AsyncClient, roadmap_no_context):
        rm, headers = roadmap_no_context
        resp = await client.post(
            f"/roadmaps/{rm['id']}/items/some-id/ai-edit",
            json={"command": "Edit this"},
            headers=headers,
        )
        assert resp.status_code == 400
        assert "context" in resp.json()["detail"].lower()

    async def test_ai_edit_no_api_key(self, client: AsyncClient, roadmap_with_items):
        rm, headers = roadmap_with_items
        app.dependency_overrides[get_settings] = _fake_settings(anthropic_api_key="")
        resp = await client.post(
            f"/roadmaps/{rm['id']}/items/ep-1/ai-edit",
            json={"command": "Edit this"},
            headers=headers,
        )
        assert resp.status_code == 503
        assert "api key" in resp.json()["detail"].lower()

    async def test_ai_edit_ownership_check(self, client: AsyncClient, roadmap_with_items):
        rm, _ = roadmap_with_items
        resp = await client.post("/auth/register", json={
            "email": "otheredituser@example.com",
            "password": "otherpassword",
        })
        other_headers = {"Authorization": f"Bearer {resp.json()['access_token']}"}
        resp = await client.post(
            f"/roadmaps/{rm['id']}/items/ep-1/ai-edit",
            json={"command": "Edit this"},
            headers=other_headers,
        )
        assert resp.status_code == 404

    async def test_ai_edit_empty_command(self, client: AsyncClient, roadmap_with_items):
        rm, headers = roadmap_with_items
        resp = await client.post(
            f"/roadmaps/{rm['id']}/items/ep-1/ai-edit",
            json={"command": ""},
            headers=headers,
        )
        assert resp.status_code == 422

    async def test_ai_edit_milestone(self, client: AsyncClient, roadmap_with_items):
        rm, headers = roadmap_with_items
        with patch("app.routers.roadmaps.run_ai_edit", side_effect=_mock_run_ai_edit):
            resp = await client.post(
                f"/roadmaps/{rm['id']}/items/ms-1/ai-edit",
                json={"command": "Simplify the goal"},
                headers=headers,
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["item_type"] == "milestone"

    async def test_ai_edit_story(self, client: AsyncClient, roadmap_with_items):
        rm, headers = roadmap_with_items
        with patch("app.routers.roadmaps.run_ai_edit", side_effect=_mock_run_ai_edit):
            resp = await client.post(
                f"/roadmaps/{rm['id']}/items/st-1/ai-edit",
                json={"command": "Split acceptance criteria"},
                headers=headers,
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["item_type"] == "story"
