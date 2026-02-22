import uuid

import pytest
from sqlalchemy import select

from app.models import GenerationJob, PMCredential, Project, RoadmapRecord, User


@pytest.mark.asyncio
async def test_create_user(db_session):
    user = User(email="test@example.com", password_hash="hashed_pw")
    db_session.add(user)
    await db_session.commit()

    result = await db_session.execute(select(User).where(User.email == "test@example.com"))
    fetched = result.scalar_one()
    assert isinstance(fetched.id, uuid.UUID)
    assert fetched.email == "test@example.com"
    assert fetched.created_at is not None


@pytest.mark.asyncio
async def test_user_project_relationship(db_session):
    user = User(email="rel@example.com", password_hash="hashed_pw")
    db_session.add(user)
    await db_session.flush()

    project = Project(user_id=user.id, name="Test Project")
    db_session.add(project)
    await db_session.commit()

    result = await db_session.execute(select(Project).where(Project.user_id == user.id))
    fetched = result.scalar_one()
    assert fetched.name == "Test Project"
    assert fetched.user_id == user.id


@pytest.mark.asyncio
async def test_roadmap_json_columns(db_session):
    user = User(email="json@example.com", password_hash="hashed_pw")
    db_session.add(user)
    await db_session.flush()

    project = Project(user_id=user.id, name="JSON Project")
    db_session.add(project)
    await db_session.flush()

    context_data = {"project_name": "Test", "vision": "A test project"}
    roadmap_data = {"milestones": [{"name": "M1"}]}

    roadmap = RoadmapRecord(
        project_id=project.id,
        name="Test Roadmap",
        context=context_data,
        roadmap_data=roadmap_data,
        status="draft",
    )
    db_session.add(roadmap)
    await db_session.commit()

    result = await db_session.execute(select(RoadmapRecord).where(RoadmapRecord.project_id == project.id))
    fetched = result.scalar_one()
    assert fetched.context == context_data
    assert fetched.roadmap_data == roadmap_data


@pytest.mark.asyncio
async def test_cascade_delete_user_deletes_projects(db_session):
    user = User(email="cascade@example.com", password_hash="hashed_pw")
    db_session.add(user)
    await db_session.flush()

    project = Project(user_id=user.id, name="Will Be Deleted")
    db_session.add(project)
    await db_session.commit()

    await db_session.delete(user)
    await db_session.commit()

    result = await db_session.execute(select(Project))
    assert result.scalars().all() == []


@pytest.mark.asyncio
async def test_generation_job_creation(db_session):
    user = User(email="job@example.com", password_hash="hashed_pw")
    db_session.add(user)
    await db_session.flush()

    project = Project(user_id=user.id, name="Job Project")
    db_session.add(project)
    await db_session.flush()

    roadmap = RoadmapRecord(
        project_id=project.id, name="Job Roadmap", status="generating"
    )
    db_session.add(roadmap)
    await db_session.flush()

    job = GenerationJob(roadmap_id=roadmap.id, status="pending")
    db_session.add(job)
    await db_session.commit()

    result = await db_session.execute(select(GenerationJob).where(GenerationJob.roadmap_id == roadmap.id))
    fetched = result.scalar_one()
    assert fetched.status == "pending"
    assert fetched.progress is None
    assert fetched.error is None
    assert fetched.started_at is None


@pytest.mark.asyncio
async def test_pm_credential_creation(db_session):
    user = User(email="cred@example.com", password_hash="hashed_pw")
    db_session.add(user)
    await db_session.flush()

    cred = PMCredential(
        user_id=user.id,
        service="linear",
        credentials={"api_key": "lin_test_123"},
    )
    db_session.add(cred)
    await db_session.commit()

    result = await db_session.execute(select(PMCredential).where(PMCredential.user_id == user.id))
    fetched = result.scalar_one()
    assert fetched.service == "linear"
    assert fetched.credentials == {"api_key": "lin_test_123"}
