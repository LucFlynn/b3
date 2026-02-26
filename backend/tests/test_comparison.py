import uuid
from datetime import date, datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lead import Lead
from app.models.platform_conversion import PlatformConversion
from app.services.comparison import compute_comparison_for_site

pytestmark = pytest.mark.asyncio


async def test_compute_comparison(db_session: AsyncSession, site):
    today = date.today()

    # Add platform conversions
    pc = PlatformConversion(
        site_id=site.id,
        agency_id=site.agency_id,
        platform="google_ads",
        campaign_id="gc_001",
        conversions_reported=20,
        clicks=100,
        spend=500.0,
        report_date=today,
    )
    db_session.add(pc)

    # Add EPI leads
    for i in range(10):
        lead = Lead(
            site_id=site.id,
            agency_id=site.agency_id,
            visitor_id=f"v_{i}",
            ip_hash=f"h_{i}",
            quality_label="verified" if i < 7 else "junk",
            quality_score=80 if i < 7 else 10,
            created_at=datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc),
        )
        db_session.add(lead)

    await db_session.flush()

    await compute_comparison_for_site(db_session, site.id, site.agency_id, "google_ads", today)
    await db_session.flush()

    from app.models.attribution_comparison import AttributionComparison
    from sqlalchemy import select

    result = await db_session.execute(
        select(AttributionComparison).where(
            AttributionComparison.site_id == site.id,
            AttributionComparison.platform == "google_ads",
        )
    )
    comp = result.scalar_one()

    assert comp.platform_conversions == 20
    assert comp.epi_total_leads == 10
    assert comp.epi_verified_leads == 7
    assert comp.epi_junk_leads == 3
    assert comp.discrepancy_pct == 65.0  # (20-7)/20 * 100
    assert comp.cost_per_verified_lead == pytest.approx(71.43, abs=0.01)
