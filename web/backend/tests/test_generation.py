"""Tests for background generation endpoints and services."""

import asyncio
import copy
import json
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
from app.services import event_bus
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


# --- Event Bus Unit Tests ---


class TestEventBus:
    def setup_method(self):
        """Clear event bus state between tests."""
        event_bus._subscribers.clear()

    def test_publish_subscribe(self):
        queue = event_bus.subscribe("job-1")
        event_bus.publish("job-1", {"event": "progress", "data": {"phase": "tasks"}})
        assert not queue.empty()
        item = queue.get_nowait()
        assert item["event"] == "progress"
        assert item["data"]["phase"] == "tasks"

    def test_multiple_subscribers(self):
        q1 = event_bus.subscribe("job-2")
        q2 = event_bus.subscribe("job-2")
        event_bus.publish("job-2", {"event": "progress", "data": {}})
        assert not q1.empty()
        assert not q2.empty()
        assert q1.get_nowait() == q2.get_nowait()

    def test_cleanup_removes_subscribers(self):
        event_bus.subscribe("job-3")
        event_bus.subscribe("job-3")
        assert "job-3" in event_bus._subscribers
        event_bus.cleanup("job-3")
        assert "job-3" not in event_bus._subscribers

    def test_unsubscribe_removes_single_queue(self):
        q1 = event_bus.subscribe("job-4")
        q2 = event_bus.subscribe("job-4")
        event_bus.unsubscribe("job-4", q1)
        assert len(event_bus._subscribers["job-4"]) == 1
        # Publishing should only reach q2
        event_bus.publish("job-4", {"event": "test", "data": {}})
        assert q1.empty()
        assert not q2.empty()


# --- SSE Streaming Endpoint Tests ---


@pytest.fixture
async def job_with_status(client: AsyncClient, roadmap_with_context, db_session: AsyncSession):
    """Create a job and return a helper to set its status directly."""
    rm, headers = roadmap_with_context
    with patch("app.routers.generation.run_generation", side_effect=_noop_run_generation):
        resp = await client.post(f"/roadmaps/{rm['id']}/generate", headers=headers)
    job_id = resp.json()["id"]

    async def _set_status(status, error=None, progress=None):
        result = await db_session.execute(
            select(GenerationJob).where(GenerationJob.id == uuid.UUID(job_id))
        )
        job = result.scalar_one()
        job.status = status
        if error:
            job.error = error
        if progress is not None:
            job.progress = copy.deepcopy(progress)
        await db_session.commit()

    return job_id, headers, _set_status


class TestStreamGeneration:
    async def test_stream_completed_job(self, client: AsyncClient, job_with_status):
        job_id, headers, set_status = job_with_status
        progress = {"milestones": 2, "epics": 4, "stories": 8, "tasks": 16}
        await set_status("completed", progress=progress)

        async with client.stream(
            "GET", f"/generation-jobs/{job_id}/stream", headers=headers
        ) as resp:
            assert resp.status_code == 200
            body = b""
            async for chunk in resp.aiter_bytes():
                body += chunk

        text = body.decode()
        assert "event: complete" in text
        # Parse the data line
        for line in text.split("\n"):
            if line.startswith("data: "):
                data = json.loads(line[6:])
                assert "roadmap_id" in data
                break

    async def test_stream_failed_job(self, client: AsyncClient, job_with_status):
        job_id, headers, set_status = job_with_status
        await set_status("failed", error="Something went wrong")

        async with client.stream(
            "GET", f"/generation-jobs/{job_id}/stream", headers=headers
        ) as resp:
            assert resp.status_code == 200
            body = b""
            async for chunk in resp.aiter_bytes():
                body += chunk

        text = body.decode()
        assert "event: error" in text
        for line in text.split("\n"):
            if line.startswith("data: "):
                data = json.loads(line[6:])
                assert "Something went wrong" in data["message"]
                break

    async def test_stream_not_found(self, client: AsyncClient, user_and_headers):
        _, headers = user_and_headers
        fake_id = str(uuid.uuid4())
        resp = await client.get(f"/generation-jobs/{fake_id}/stream", headers=headers)
        assert resp.status_code == 404

    async def test_stream_ownership_isolation(self, client: AsyncClient, job_with_status):
        job_id, _, _ = job_with_status
        # Register a different user
        resp = await client.post("/auth/register", json={
            "email": "streamother@example.com",
            "password": "otherpassword",
        })
        other_headers = {"Authorization": f"Bearer {resp.json()['access_token']}"}
        resp = await client.get(f"/generation-jobs/{job_id}/stream", headers=other_headers)
        assert resp.status_code == 404

    async def test_stream_no_auth(self, client: AsyncClient):
        fake_id = str(uuid.uuid4())
        resp = await client.get(f"/generation-jobs/{fake_id}/stream")
        assert resp.status_code == 401


# --- Adapter Event Emission Test ---


class TestAdapterEventEmission:
    def setup_method(self):
        event_bus._subscribers.clear()

    async def test_adapter_publishes_progress_event(self, db_session: AsyncSession):
        from app.models.project import Project
        from app.models.user import User
        from app.services.auth import hash_password
        from tests.conftest import async_session_test

        # Set up DB chain
        user = User(email="eventadapter@example.com", password_hash=hash_password("password"))
        db_session.add(user)
        await db_session.flush()

        project = Project(user_id=user.id, name="Event Test")
        db_session.add(project)
        await db_session.flush()

        roadmap = RoadmapRecord(
            project_id=project.id, name="Event RM", status="generating"
        )
        db_session.add(roadmap)
        await db_session.flush()

        job = GenerationJob(roadmap_id=roadmap.id, status="in_progress")
        db_session.add(job)
        await db_session.commit()
        await db_session.refresh(roadmap)
        await db_session.refresh(job)

        job_id_str = str(job.id)

        # Subscribe to events before saving
        queue = event_bus.subscribe(job_id_str)

        class MockMilestone:
            def __init__(self, name):
                self.name = name
                self.epics = []

        class MockRoadmap:
            def __init__(self):
                self.milestones = [MockMilestone("M1")]

            @property
            def total_items(self):
                return {"milestones": 1, "epics": 0, "stories": 0, "tasks": 0}

            def model_dump(self, mode=None):
                return {"milestones": [{"name": "M1", "epics": []}]}

        adapter = WebStorageAdapter(
            session_factory=async_session_test,
            roadmap_record_id=str(roadmap.id),
            job_id=job_id_str,
        )
        await adapter.save_roadmap(MockRoadmap())

        # Should receive item_created + progress events
        events = []
        while not queue.empty():
            events.append(queue.get_nowait())

        event_types = [e["event"] for e in events]
        assert "item_created" in event_types
        assert "progress" in event_types

        # Check item_created event
        item_event = next(e for e in events if e["event"] == "item_created")
        assert item_event["data"]["type"] == "milestone"
        assert item_event["data"]["name"] == "M1"

        # Check progress event
        progress_event = next(e for e in events if e["event"] == "progress")
        assert progress_event["data"]["milestones"] == 1
        assert progress_event["data"]["phase"] == "epics"


# --- Regenerate Endpoint Tests ---


def _noop_run_regeneration(*args, **kwargs):
    """A no-op coroutine that replaces run_regeneration in tests."""
    async def noop():
        pass
    return noop()


@pytest.fixture
async def roadmap_with_generated_items(client: AsyncClient, project, db_session: AsyncSession):
    """Create a roadmap with stored context and manually set roadmap_data with a hierarchy."""
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
        json={"name": "Regen Roadmap", "context": context},
        headers=headers,
    )
    assert resp.status_code == 201
    rm = resp.json()

    # Manually set roadmap_data with a known hierarchy
    rm_uuid = uuid.UUID(rm["id"])
    result = await db_session.execute(
        select(RoadmapRecord).where(RoadmapRecord.id == rm_uuid)
    )
    record = result.scalar_one()
    record.roadmap_data = copy.deepcopy({
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
                        "implementation_notes": "",
                        "claude_code_prompt": "",
                    }],
                }],
            }],
        }],
    })
    record.status = "generated"
    await db_session.commit()

    return rm, headers


class TestRegenerateEndpoint:
    async def test_regenerate_returns_202(self, client: AsyncClient, roadmap_with_generated_items):
        rm, headers = roadmap_with_generated_items
        with patch("app.routers.generation.run_regeneration", side_effect=_noop_run_regeneration):
            resp = await client.post(
                f"/roadmaps/{rm['id']}/items/ep-1/regenerate",
                headers=headers,
            )
        assert resp.status_code == 202
        data = resp.json()
        assert data["status"] == "pending"
        assert data["roadmap_id"] == rm["id"]

    async def test_regenerate_task_returns_400(self, client: AsyncClient, roadmap_with_generated_items):
        rm, headers = roadmap_with_generated_items
        resp = await client.post(
            f"/roadmaps/{rm['id']}/items/tk-1/regenerate",
            headers=headers,
        )
        assert resp.status_code == 400
        assert "task" in resp.json()["detail"].lower()

    async def test_regenerate_nonexistent_item_returns_404(self, client: AsyncClient, roadmap_with_generated_items):
        rm, headers = roadmap_with_generated_items
        resp = await client.post(
            f"/roadmaps/{rm['id']}/items/nonexistent-id/regenerate",
            headers=headers,
        )
        assert resp.status_code == 404

    async def test_regenerate_no_context_returns_400(self, client: AsyncClient, roadmap_no_context):
        rm, headers = roadmap_no_context
        resp = await client.post(
            f"/roadmaps/{rm['id']}/items/some-id/regenerate",
            headers=headers,
        )
        assert resp.status_code == 400
        assert "context" in resp.json()["detail"].lower()

    async def test_regenerate_no_api_key_returns_503(self, client: AsyncClient, roadmap_with_generated_items):
        rm, headers = roadmap_with_generated_items
        app.dependency_overrides[get_settings] = _fake_settings(anthropic_api_key="")
        resp = await client.post(
            f"/roadmaps/{rm['id']}/items/ep-1/regenerate",
            headers=headers,
        )
        assert resp.status_code == 503
        assert "api key" in resp.json()["detail"].lower()

    async def test_regenerate_conflict_returns_409(self, client: AsyncClient, roadmap_with_generated_items):
        rm, headers = roadmap_with_generated_items
        # Start a first regeneration
        with patch("app.routers.generation.run_regeneration", side_effect=_noop_run_regeneration):
            resp1 = await client.post(
                f"/roadmaps/{rm['id']}/items/ep-1/regenerate",
                headers=headers,
            )
        assert resp1.status_code == 202
        # Second should conflict
        with patch("app.routers.generation.run_regeneration", side_effect=_noop_run_regeneration):
            resp2 = await client.post(
                f"/roadmaps/{rm['id']}/items/ms-1/regenerate",
                headers=headers,
            )
        assert resp2.status_code == 409

    async def test_regenerate_ownership_check(self, client: AsyncClient, roadmap_with_generated_items):
        rm, _ = roadmap_with_generated_items
        # Register a different user
        resp = await client.post("/auth/register", json={
            "email": "regenother@example.com",
            "password": "otherpassword",
        })
        other_headers = {"Authorization": f"Bearer {resp.json()['access_token']}"}
        resp = await client.post(
            f"/roadmaps/{rm['id']}/items/ep-1/regenerate",
            headers=other_headers,
        )
        assert resp.status_code == 404
