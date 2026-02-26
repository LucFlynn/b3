import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lead import Lead

pytestmark = pytest.mark.asyncio


async def _create_leads(db: AsyncSession, site_id, agency_id, count=5):
    leads = []
    for i in range(count):
        lead = Lead(
            site_id=site_id,
            agency_id=agency_id,
            visitor_id=f"v_{i}",
            ip_hash=f"hash_{i}",
            quality_score=50 + i * 10,
            quality_label=["junk", "suspicious", "likely_real", "verified", "verified"][i % 5],
            attribution_tier=["unattributed", "probable", "high_confidence", "definitive", "definitive"][i % 5],
            is_duplicate=(i == 0),
        )
        db.add(lead)
        leads.append(lead)
    await db.flush()
    return leads


async def test_list_leads(client: AsyncClient, db_session, site, user, auth_headers):
    await _create_leads(db_session, site.id, site.agency_id)
    resp = await client.get("/api/leads", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 5


async def test_leads_agency_isolation(client: AsyncClient, db_session, site, site_agency2, user, user2, auth_headers, auth_headers2):
    """Cross-agency queries return nothing."""
    await _create_leads(db_session, site.id, site.agency_id, 3)
    await _create_leads(db_session, site_agency2.id, site_agency2.agency_id, 2)

    # Agency 1 sees only their leads
    resp1 = await client.get("/api/leads", headers=auth_headers)
    assert len(resp1.json()) == 3

    # Agency 2 sees only their leads
    resp2 = await client.get("/api/leads", headers=auth_headers2)
    assert len(resp2.json()) == 2


async def test_leads_filter_quality(client: AsyncClient, db_session, site, user, auth_headers):
    await _create_leads(db_session, site.id, site.agency_id)
    resp = await client.get("/api/leads?quality_label=verified", headers=auth_headers)
    assert resp.status_code == 200
    for lead in resp.json():
        assert lead["quality_label"] == "verified"


async def test_leads_stats(client: AsyncClient, db_session, site, user, auth_headers):
    await _create_leads(db_session, site.id, site.agency_id)
    resp = await client.get("/api/leads/stats", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_leads"] == 5
    assert data["duplicates"] == 1
