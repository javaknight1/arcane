"""Tests for background generation endpoints and services."""

import copy
import uuid
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.main import app
from app.models.generation_job import GenerationJob
from app.models.roadmap import RoadmapRecord
from app.services.generation import WebStorageAdapter

pytestmark = pytest.mark.asyncio


# --- Fixtures ---


def _fake_settings(**overrides):
    """Return a Settings factory with a fake API key by default."""
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
    """Override settings to include a fake API key for all tests."""
    app.dependency_overrides[get_settings] = _fake_settings()
    yield
    app.dependency_overrides.pop(get_settings, None)


@pytest.fixture
async def user_and_headers(client: AsyncClient):
    resp = await client.post("/auth/register", json={
        "email": "genuser@example.com",
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
    resp = await client.post("/projects/", json={"name": "Gen Project"}, headers=headers)
    assert resp.status_code == 201
    return resp.json(), headers


@pytest.fixture
async def roadmap_with_context(client: AsyncClient, project):
    proj, headers = project
    context = {
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
    resp = await client.post(
        f"/projects/{proj['id']}/roadmaps",
        json={"name": "Gen Roadmap", "context": context},
        headers=headers,
    )
    assert resp.status_code == 201
    return resp.json(), headers


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


def _noop_run_generation(*args, **kwargs):
    """A no-op coroutine that replaces run_generation in tests."""
    import asyncio

    async def noop():
        pass

    return noop()


# --- Start Generation Tests ---


class TestStartGeneration:
    async def test_start_generation_returns_202(self, client: AsyncClient, roadmap_with_context):
        rm, headers = roadmap_with_context
        with patch("app.routers.generation.run_generation", side_effect=_noop_run_generation):
            resp = await client.post(f"/roadmaps/{rm['id']}/generate", headers=headers)
        assert resp.status_code == 202
        data = resp.json()
        assert data["status"] == "pending"
        assert data["roadmap_id"] == rm["id"]
        assert data["progress"] is None

    async def test_start_generation_with_body_context(self, client: AsyncClient, roadmap_no_context):
        rm, headers = roadmap_no_context
        body_context = {
            "project_name": "Override",
            "vision": "Overridden",
            "problem_statement": "Test",
            "target_users": ["users"],
            "timeline": "3 months",
            "team_size": 2,
            "developer_experience": "mid-level",
            "budget_constraints": "moderate",
            "must_have_features": ["feature1"],
        }
        with patch("app.routers.generation.run_generation", side_effect=_noop_run_generation):
            resp = await client.post(
                f"/roadmaps/{rm['id']}/generate",
                json={"context": body_context},
                headers=headers,
            )
        assert resp.status_code == 202

    async def test_start_generation_no_context_returns_400(self, client: AsyncClient, roadmap_no_context):
        rm, headers = roadmap_no_context
        resp = await client.post(f"/roadmaps/{rm['id']}/generate", headers=headers)
        assert resp.status_code == 400
        assert "context" in resp.json()["detail"].lower()

    async def test_start_generation_no_api_key_returns_503(self, client: AsyncClient, roadmap_with_context):
        rm, headers = roadmap_with_context
        app.dependency_overrides[get_settings] = _fake_settings(anthropic_api_key="")
        resp = await client.post(f"/roadmaps/{rm['id']}/generate", headers=headers)
        assert resp.status_code == 503
        assert "api key" in resp.json()["detail"].lower()

    async def test_start_generation_conflict_returns_409(self, client: AsyncClient, roadmap_with_context):
        rm, headers = roadmap_with_context
        # Start first generation
        with patch("app.routers.generation.run_generation", side_effect=_noop_run_generation):
            resp1 = await client.post(f"/roadmaps/{rm['id']}/generate", headers=headers)
        assert resp1.status_code == 202
        # Try to start second generation — should conflict
        with patch("app.routers.generation.run_generation", side_effect=_noop_run_generation):
            resp2 = await client.post(f"/roadmaps/{rm['id']}/generate", headers=headers)
        assert resp2.status_code == 409

    async def test_start_generation_sets_roadmap_status(self, client: AsyncClient, roadmap_with_context):
        rm, headers = roadmap_with_context
        with patch("app.routers.generation.run_generation", side_effect=_noop_run_generation):
            await client.post(f"/roadmaps/{rm['id']}/generate", headers=headers)
        # Fetch roadmap and check status
        resp = await client.get(f"/roadmaps/{rm['id']}", headers=headers)
        assert resp.json()["status"] == "generating"

    async def test_start_generation_ownership_check(self, client: AsyncClient, roadmap_with_context):
        rm, _ = roadmap_with_context
        # Register a different user
        resp = await client.post("/auth/register", json={
            "email": "othergen@example.com",
            "password": "otherpassword",
        })
        other_headers = {"Authorization": f"Bearer {resp.json()['access_token']}"}
        resp = await client.post(f"/roadmaps/{rm['id']}/generate", headers=other_headers)
        assert resp.status_code == 404

    async def test_start_generation_nonexistent_roadmap(self, client: AsyncClient, user_and_headers):
        _, headers = user_and_headers
        fake_id = str(uuid.uuid4())
        resp = await client.post(f"/roadmaps/{fake_id}/generate", headers=headers)
        assert resp.status_code == 404

    async def test_start_generation_no_auth(self, client: AsyncClient):
        fake_id = str(uuid.uuid4())
        resp = await client.post(f"/roadmaps/{fake_id}/generate")
        assert resp.status_code == 401


# --- Get Generation Job Tests ---


class TestGetGenerationJob:
    async def test_get_job_returns_status(self, client: AsyncClient, roadmap_with_context):
        rm, headers = roadmap_with_context
        with patch("app.routers.generation.run_generation", side_effect=_noop_run_generation):
            start_resp = await client.post(f"/roadmaps/{rm['id']}/generate", headers=headers)
        job_id = start_resp.json()["id"]

        resp = await client.get(f"/generation-jobs/{job_id}", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == job_id
        assert data["status"] == "pending"

    async def test_get_job_not_found(self, client: AsyncClient, user_and_headers):
        _, headers = user_and_headers
        fake_id = str(uuid.uuid4())
        resp = await client.get(f"/generation-jobs/{fake_id}", headers=headers)
        assert resp.status_code == 404

    async def test_get_job_ownership_isolation(self, client: AsyncClient, roadmap_with_context):
        rm, headers = roadmap_with_context
        with patch("app.routers.generation.run_generation", side_effect=_noop_run_generation):
            start_resp = await client.post(f"/roadmaps/{rm['id']}/generate", headers=headers)
        job_id = start_resp.json()["id"]

        # Different user shouldn't see the job
        resp = await client.post("/auth/register", json={
            "email": "jobother@example.com",
            "password": "otherpassword",
        })
        other_headers = {"Authorization": f"Bearer {resp.json()['access_token']}"}
        resp = await client.get(f"/generation-jobs/{job_id}", headers=other_headers)
        assert resp.status_code == 404


# --- WebStorageAdapter Unit Test ---


class TestWebStorageAdapter:
    async def test_save_updates_roadmap_data_and_progress(self, db_session: AsyncSession):
        from app.models.project import Project
        from app.models.user import User
        from app.services.auth import hash_password
        from tests.conftest import async_session_test

        # Set up user -> project -> roadmap -> job
        user = User(email="adapter@example.com", password_hash=hash_password("password"))
        db_session.add(user)
        await db_session.flush()

        project = Project(user_id=user.id, name="Adapter Test")
        db_session.add(project)
        await db_session.flush()

        roadmap = RoadmapRecord(
            project_id=project.id, name="Adapter RM", status="generating"
        )
        db_session.add(roadmap)
        await db_session.flush()

        job = GenerationJob(roadmap_id=roadmap.id, status="in_progress")
        db_session.add(job)
        await db_session.commit()
        await db_session.refresh(roadmap)
        await db_session.refresh(job)

        # Create a mock roadmap object with the interface the adapter expects
        class MockRoadmap:
            def __init__(self):
                self.milestones = []

            @property
            def total_items(self):
                return {"milestones": 1, "epics": 2, "stories": 3, "tasks": 0}

            def model_dump(self, mode=None):
                return {"milestones": [{"name": "M1", "epics": []}]}

        mock_roadmap = MockRoadmap()

        adapter = WebStorageAdapter(
            session_factory=async_session_test,
            roadmap_record_id=str(roadmap.id),
            job_id=str(job.id),
        )
        await adapter.save_roadmap(mock_roadmap)

        # Verify roadmap_data and progress were written
        await db_session.refresh(roadmap)
        await db_session.refresh(job)
        assert roadmap.roadmap_data is not None
        assert roadmap.roadmap_data["milestones"][0]["name"] == "M1"
        assert job.progress is not None
        assert job.progress["milestones"] == 1
        assert job.progress["epics"] == 2
        assert job.progress["stories"] == 3
        assert job.progress["phase"] == "tasks"
