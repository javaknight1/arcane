import pytest


@pytest.mark.asyncio
async def test_health_returns_200(client):
    resp = await client.get("/health")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_health_response_fields(client):
    resp = await client.get("/health")
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["database"] == "healthy"
    assert data["version"] == "0.1.0"
