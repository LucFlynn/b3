import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def test_create_site(client: AsyncClient, user, auth_headers):
    resp = await client.post("/api/sites", json={
        "domain": "www.new-site.com",
        "name": "New Site",
    }, headers=auth_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["domain"] == "www.new-site.com"
    assert data["pixel_id"].startswith("px_")
    assert "pixel_snippet" in data
    assert data["pixel_id"] in data["pixel_snippet"]


async def test_list_sites(client: AsyncClient, site, user, auth_headers):
    resp = await client.get("/api/sites", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    assert data[0]["domain"] == "www.test-site.com"


async def test_sites_agency_isolation(client: AsyncClient, site, site_agency2, user2, auth_headers2):
    resp = await client.get("/api/sites", headers=auth_headers2)
    data = resp.json()
    domains = [s["domain"] for s in data]
    assert "www.test-site.com" not in domains
    assert "www.other-site.com" in domains


async def test_get_site_not_found(client: AsyncClient, user, auth_headers):
    resp = await client.get("/api/sites/00000000-0000-0000-0000-000000000099", headers=auth_headers)
    assert resp.status_code == 404
