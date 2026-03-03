import pytest
from httpx import AsyncClient

from tests.conftest import INVITE_RAW

pytestmark = pytest.mark.asyncio


async def test_register(client: AsyncClient, invite_code):
    resp = await client.post("/api/auth/register", json={
        "email": "new@agency.com",
        "password": "securepass123",
        "agency_name": "New Agency",
        "invite_code": INVITE_RAW,
    })
    assert resp.status_code == 201
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["agency_id"]
    assert data["user_id"]


async def test_register_duplicate_email(client: AsyncClient, user, invite_code):
    resp = await client.post("/api/auth/register", json={
        "email": "test@example.com",
        "password": "securepass123",
        "agency_name": "Dup Agency",
        "invite_code": INVITE_RAW,
    })
    assert resp.status_code == 400


async def test_register_invalid_invite(client: AsyncClient):
    resp = await client.post("/api/auth/register", json={
        "email": "new@agency.com",
        "password": "securepass123",
        "agency_name": "New Agency",
        "invite_code": "epi-invite-does-not-exist",
    })
    assert resp.status_code == 400
    assert "Invalid invite code" in resp.json()["detail"]


async def test_register_used_invite(client: AsyncClient, used_invite_code):
    resp = await client.post("/api/auth/register", json={
        "email": "new@agency.com",
        "password": "securepass123",
        "agency_name": "New Agency",
        "invite_code": "epi-invite-used",
    })
    assert resp.status_code == 400
    assert "already used" in resp.json()["detail"]


async def test_login(client: AsyncClient, user):
    resp = await client.post("/api/auth/login", json={
        "email": "test@example.com",
        "password": "password123",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data


async def test_login_wrong_password(client: AsyncClient, user):
    resp = await client.post("/api/auth/login", json={
        "email": "test@example.com",
        "password": "wrongpassword",
    })
    assert resp.status_code == 401


async def test_get_me(client: AsyncClient, user, auth_headers):
    resp = await client.get("/api/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "test@example.com"


async def test_get_me_no_auth(client: AsyncClient):
    resp = await client.get("/api/auth/me")
    assert resp.status_code == 401


async def test_jwt_roundtrip(client: AsyncClient, invite_code):
    """JWT round-trip: register -> use token -> access protected endpoint."""
    reg = await client.post("/api/auth/register", json={
        "email": "jwt@test.com",
        "password": "pass123",
        "agency_name": "JWT Agency",
        "invite_code": INVITE_RAW,
    })
    token = reg.json()["access_token"]
    me = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "jwt@test.com"
