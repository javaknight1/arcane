"""Tests for PM credential management and roadmap export endpoints."""

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
    resp = await client.post("/auth/register", json={
        "email": "exportuser@example.com",
        "password": "securepassword",
    })
    assert resp.status_code == 201
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    return headers


@pytest.fixture
async def project(client: AsyncClient, user_and_headers):
    headers = user_and_headers
    resp = await client.post("/projects/", json={"name": "Export Test"}, headers=headers)
    assert resp.status_code == 201
    return resp.json(), headers


@pytest.fixture
async def roadmap(client: AsyncClient, project):
    proj, headers = project
    context = {
        "project_name": "Export Test",
        "vision": "A test project",
        "problem_statement": "Testing exports",
        "target_users": ["developers"],
        "timeline": "1 month MVP",
        "team_size": 1,
        "developer_experience": "senior",
        "budget_constraints": "minimal (free tier everything)",
        "must_have_features": ["export"],
    }
    resp = await client.post(
        f"/projects/{proj['id']}/roadmaps",
        json={"name": "Test Roadmap", "context": context},
        headers=headers,
    )
    assert resp.status_code == 201
    return resp.json(), headers


@pytest.fixture
async def roadmap_with_items(client: AsyncClient, roadmap):
    rm, headers = roadmap
    rm_id = rm["id"]

    ms_resp = await client.post(
        f"/roadmaps/{rm_id}/items/root/children",
        json={"item_type": "milestone", "data": {
            "name": "M1", "description": "Milestone 1", "priority": "high", "goal": "Goal 1",
        }},
        headers=headers,
    )
    assert ms_resp.status_code == 201
    ms_id = ms_resp.json()["item_id"]

    ep_resp = await client.post(
        f"/roadmaps/{rm_id}/items/{ms_id}/children",
        json={"item_type": "epic", "data": {
            "name": "E1", "description": "Epic 1", "priority": "medium", "goal": "EGoal",
        }},
        headers=headers,
    )
    assert ep_resp.status_code == 201
    ep_id = ep_resp.json()["item_id"]

    st_resp = await client.post(
        f"/roadmaps/{rm_id}/items/{ep_id}/children",
        json={"item_type": "story", "data": {
            "name": "S1", "description": "Story 1", "priority": "low",
            "acceptance_criteria": ["AC1"],
        }},
        headers=headers,
    )
    assert st_resp.status_code == 201
    st_id = st_resp.json()["item_id"]

    tk_resp = await client.post(
        f"/roadmaps/{rm_id}/items/{st_id}/children",
        json={"item_type": "task", "data": {
            "name": "T1", "description": "Task 1", "priority": "medium",
            "estimated_hours": 4, "acceptance_criteria": ["done"],
            "implementation_notes": "impl", "claude_code_prompt": "do it",
        }},
        headers=headers,
    )
    assert tk_resp.status_code == 201

    return rm, headers


# --- Credential CRUD ---


class TestCredentials:
    async def test_save_and_list_credentials(self, client: AsyncClient, user_and_headers):
        headers = user_and_headers

        # Save
        resp = await client.post("/credentials", json={
            "service": "linear",
            "credentials": {"api_key": "lin_test_key"},
        }, headers=headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["service"] == "linear"
        assert "id" in data
        # Should NOT expose actual secrets
        assert "api_key" not in data

        # List
        resp = await client.get("/credentials", headers=headers)
        assert resp.status_code == 200
        creds = resp.json()
        assert len(creds) == 1
        assert creds[0]["service"] == "linear"

    async def test_save_credential_upsert(self, client: AsyncClient, user_and_headers):
        headers = user_and_headers

        # First save
        await client.post("/credentials", json={
            "service": "linear",
            "credentials": {"api_key": "key1"},
        }, headers=headers)

        # Second save — should upsert, not create duplicate
        await client.post("/credentials", json={
            "service": "linear",
            "credentials": {"api_key": "key2"},
        }, headers=headers)

        resp = await client.get("/credentials", headers=headers)
        creds = resp.json()
        assert len(creds) == 1

    async def test_save_invalid_service(self, client: AsyncClient, user_and_headers):
        headers = user_and_headers
        resp = await client.post("/credentials", json={
            "service": "github",
            "credentials": {"token": "xyz"},
        }, headers=headers)
        assert resp.status_code == 400

    async def test_delete_credential(self, client: AsyncClient, user_and_headers):
        headers = user_and_headers

        await client.post("/credentials", json={
            "service": "jira",
            "credentials": {"domain": "x.atlassian.net", "email": "a@b.com", "api_token": "tok"},
        }, headers=headers)

        resp = await client.delete("/credentials/jira", headers=headers)
        assert resp.status_code == 204

        resp = await client.get("/credentials", headers=headers)
        assert len(resp.json()) == 0

    async def test_delete_nonexistent(self, client: AsyncClient, user_and_headers):
        headers = user_and_headers
        resp = await client.delete("/credentials/linear", headers=headers)
        assert resp.status_code == 404


# --- CSV Export ---


class TestCSVExport:
    async def test_csv_export_returns_content(self, client: AsyncClient, roadmap_with_items):
        rm, headers = roadmap_with_items
        resp = await client.post(
            f"/roadmaps/{rm['id']}/export",
            json={"service": "csv"},
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "csv_content" in data
        assert "filename" in data
        assert data["filename"].endswith(".csv")
        # Should contain CSV headers and item rows
        assert "Type,ID,Name" in data["csv_content"]
        assert "M1" in data["csv_content"]
        assert "T1" in data["csv_content"]

    async def test_csv_export_empty_roadmap(self, client: AsyncClient, roadmap):
        rm, headers = roadmap
        resp = await client.post(
            f"/roadmaps/{rm['id']}/export",
            json={"service": "csv"},
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        # Should still return valid CSV with headers
        assert "csv_content" in data
        assert "Type,ID,Name" in data["csv_content"]


# --- Export Job Lifecycle ---


class TestExportJobs:
    async def test_export_without_credentials_fails(self, client: AsyncClient, roadmap_with_items):
        rm, headers = roadmap_with_items
        resp = await client.post(
            f"/roadmaps/{rm['id']}/export",
            json={"service": "linear"},
            headers=headers,
        )
        assert resp.status_code == 400
        assert "credentials" in resp.json()["detail"].lower()

    async def test_export_creates_job(self, client: AsyncClient, roadmap_with_items):
        rm, headers = roadmap_with_items

        # Save credentials first
        await client.post("/credentials", json={
            "service": "linear",
            "credentials": {"api_key": "lin_test"},
        }, headers=headers)

        resp = await client.post(
            f"/roadmaps/{rm['id']}/export",
            json={"service": "linear", "workspace_params": {"team_id": "TEAM1"}},
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["service"] == "linear"
        assert data["status"] == "pending"
        assert "id" in data

    async def test_export_history(self, client: AsyncClient, roadmap_with_items):
        rm, headers = roadmap_with_items

        # Save creds and start an export
        await client.post("/credentials", json={
            "service": "linear",
            "credentials": {"api_key": "lin_test"},
        }, headers=headers)

        await client.post(
            f"/roadmaps/{rm['id']}/export",
            json={"service": "linear"},
            headers=headers,
        )

        resp = await client.get(
            f"/roadmaps/{rm['id']}/exports",
            headers=headers,
        )
        assert resp.status_code == 200
        exports = resp.json()
        assert len(exports) >= 1
        assert exports[0]["service"] == "linear"

    async def test_get_export_job(self, client: AsyncClient, roadmap_with_items):
        rm, headers = roadmap_with_items

        await client.post("/credentials", json={
            "service": "notion",
            "credentials": {"api_key": "ntn_test"},
        }, headers=headers)

        create_resp = await client.post(
            f"/roadmaps/{rm['id']}/export",
            json={"service": "notion"},
            headers=headers,
        )
        job_id = create_resp.json()["id"]

        resp = await client.get(f"/export-jobs/{job_id}", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["id"] == job_id

    async def test_get_nonexistent_job(self, client: AsyncClient, user_and_headers):
        headers = user_and_headers
        fake_id = str(pytest.importorskip("uuid").uuid4())
        resp = await client.get(f"/export-jobs/{fake_id}", headers=headers)
        assert resp.status_code == 404

    async def test_invalid_service(self, client: AsyncClient, roadmap_with_items):
        rm, headers = roadmap_with_items
        resp = await client.post(
            f"/roadmaps/{rm['id']}/export",
            json={"service": "trello"},
            headers=headers,
        )
        assert resp.status_code == 400


# --- Reconstruct Roadmap ---


class TestReconstructRoadmap:
    async def test_reconstruct_from_db(self, client: AsyncClient, roadmap_with_items, db_session: AsyncSession):
        rm, headers = roadmap_with_items
        from app.models.roadmap import RoadmapRecord
        from app.services.export import reconstruct_roadmap
        from sqlalchemy import select
        import uuid

        result = await db_session.execute(
            select(RoadmapRecord).where(RoadmapRecord.id == uuid.UUID(rm["id"]))
        )
        record = result.scalar_one()
        roadmap = reconstruct_roadmap(record)

        assert roadmap.project_name == "Test Roadmap"
        assert len(roadmap.milestones) == 1
        assert roadmap.milestones[0].name == "M1"
        assert len(roadmap.milestones[0].epics) == 1
        assert len(roadmap.milestones[0].epics[0].stories) == 1
        assert len(roadmap.milestones[0].epics[0].stories[0].tasks) == 1
