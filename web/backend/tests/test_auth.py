import pytest
from cryptography.fernet import Fernet

from app.services.auth import (
    create_access_token,
    create_refresh_token,
    decrypt_credentials,
    encrypt_credentials,
    hash_password,
    verify_password,
)
from app.config import get_settings


# ── Registration ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_register_success(client):
    resp = await client.post("/auth/register", json={
        "email": "new@example.com",
        "password": "strongpassword",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_register_duplicate_email(client):
    payload = {"email": "dup@example.com", "password": "strongpassword"}
    await client.post("/auth/register", json=payload)
    resp = await client.post("/auth/register", json=payload)
    assert resp.status_code == 409
    assert "already registered" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_register_short_password(client):
    resp = await client.post("/auth/register", json={
        "email": "short@example.com",
        "password": "1234567",
    })
    assert resp.status_code == 422


# ── Login ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_login_success(client, test_user):
    resp = await client.post("/auth/login", json={
        "email": "test@example.com",
        "password": "testpassword123",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_login_wrong_password(client, test_user):
    resp = await client.post("/auth/login", json={
        "email": "test@example.com",
        "password": "wrongpassword",
    })
    assert resp.status_code == 401
    assert "Invalid email or password" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_login_nonexistent_email(client):
    resp = await client.post("/auth/login", json={
        "email": "nobody@example.com",
        "password": "anypassword",
    })
    assert resp.status_code == 401


# ── Refresh ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_refresh_success(client):
    reg = await client.post("/auth/register", json={
        "email": "refresh@example.com",
        "password": "strongpassword",
    })
    refresh_token = reg.json()["refresh_token"]

    resp = await client.post("/auth/refresh", json={
        "refresh_token": refresh_token,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_refresh_invalid_token(client):
    resp = await client.post("/auth/refresh", json={
        "refresh_token": "totally.invalid.token",
    })
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_refresh_with_access_token_rejected(client):
    reg = await client.post("/auth/register", json={
        "email": "wrongtype@example.com",
        "password": "strongpassword",
    })
    access_token = reg.json()["access_token"]

    resp = await client.post("/auth/refresh", json={
        "refresh_token": access_token,
    })
    assert resp.status_code == 401
    assert "Invalid token type" in resp.json()["detail"]


# ── GET /me ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_me_success(client, auth_headers):
    resp = await client.get("/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "authed@example.com"
    assert "id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_me_no_token(client):
    resp = await client.get("/auth/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_invalid_token(client):
    resp = await client.get("/auth/me", headers={"Authorization": "Bearer bad.token.here"})
    assert resp.status_code == 401


# ── Fernet encryption ────────────────────────────────────────


def test_encrypt_decrypt_roundtrip():
    key = Fernet.generate_key().decode()
    data = {"api_key": "sk-123", "workspace": "my-team"}
    encrypted = encrypt_credentials(data, key)
    assert encrypted != str(data)
    decrypted = decrypt_credentials(encrypted, key)
    assert decrypted == data


# ── Password hashing ─────────────────────────────────────────


def test_hash_and_verify_password():
    hashed = hash_password("mysecretpassword")
    assert hashed != "mysecretpassword"
    assert verify_password("mysecretpassword", hashed)
    assert not verify_password("wrongpassword", hashed)
