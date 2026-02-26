import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def test_event_accepted(client: AsyncClient, site):
    resp = await client.post("/api/event", json={
        "pixel_id": "px_test_001",
        "event_type": "pageview",
        "visitor_id": "v_123",
        "session_id": "s_456",
        "page_url": "https://www.test-site.com/landing",
        "referrer": "https://google.com",
        "user_agent": "Mozilla/5.0",
    })
    assert resp.status_code == 202
    data = resp.json()
    assert data["status"] == "accepted"


async def test_event_form_submit(client: AsyncClient, site):
    resp = await client.post("/api/event", json={
        "pixel_id": "px_test_001",
        "event_type": "form_submit",
        "visitor_id": "v_789",
        "session_id": "s_012",
        "page_url": "https://www.test-site.com/contact",
        "form_id": "contact-form",
        "form_data": {
            "email": "lead@example.com",
            "phone": "+15551234567",
            "name": "Jane Doe",
            "message": "Interested in services",
        },
        "form_fill_time_ms": 5000,
    })
    assert resp.status_code == 202


async def test_event_unknown_pixel(client: AsyncClient):
    resp = await client.post("/api/event", json={
        "pixel_id": "px_nonexistent",
        "event_type": "pageview",
        "visitor_id": "v_000",
        "session_id": "s_000",
        "page_url": "https://unknown.com",
    })
    # Still accepted (fire-and-forget), processing will skip
    assert resp.status_code == 202
