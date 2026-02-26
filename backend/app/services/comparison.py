from datetime import date
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lead import Lead
from app.models.platform_conversion import PlatformConversion
from app.models.attribution_comparison import AttributionComparison


async def compute_comparison_for_site(
    db: AsyncSession,
    site_id: UUID,
    agency_id: UUID,
    platform: str,
    report_date: date,
):
    """Compute EPI ground truth vs platform-reported conversions for a given day."""

    # Get platform-reported numbers
    pc_q = select(
        func.sum(PlatformConversion.conversions_reported),
        func.sum(PlatformConversion.clicks),
        func.sum(PlatformConversion.spend),
    ).where(
        PlatformConversion.site_id == site_id,
        PlatformConversion.platform == platform,
        PlatformConversion.report_date == report_date,
    )
    pc_result = await db.execute(pc_q)
    row = pc_result.one()
    platform_conversions = row[0] or 0
    platform_clicks = row[1] or 0
    platform_spend = row[2] or 0.0

    # Get EPI ground truth
    lead_base = select(Lead).where(
        Lead.site_id == site_id,
        func.date(Lead.created_at) == report_date,
    )

    total_q = select(func.count()).select_from(lead_base.subquery())
    total = (await db.execute(total_q)).scalar() or 0

    verified_q = select(func.count()).select_from(
        lead_base.where(Lead.quality_label == "verified").subquery()
    )
    verified = (await db.execute(verified_q)).scalar() or 0

    junk_q = select(func.count()).select_from(
        lead_base.where(Lead.quality_label == "junk").subquery()
    )
    junk = (await db.execute(junk_q)).scalar() or 0

    # Compute discrepancy
    discrepancy_pct = None
    if platform_conversions > 0:
        discrepancy_pct = round((platform_conversions - verified) / platform_conversions * 100, 1)

    cost_per_verified = None
    if verified > 0:
        cost_per_verified = round(platform_spend / verified, 2)

    # Upsert comparison
    existing_q = select(AttributionComparison).where(
        AttributionComparison.site_id == site_id,
        AttributionComparison.platform == platform,
        AttributionComparison.report_date == report_date,
    )
    existing = (await db.execute(existing_q)).scalar_one_or_none()

    if existing:
        existing.platform_conversions = platform_conversions
        existing.platform_clicks = platform_clicks
        existing.platform_spend = platform_spend
        existing.epi_total_leads = total
        existing.epi_verified_leads = verified
        existing.epi_junk_leads = junk
        existing.discrepancy_pct = discrepancy_pct
        existing.cost_per_verified_lead = cost_per_verified
    else:
        comparison = AttributionComparison(
            site_id=site_id,
            agency_id=agency_id,
            platform=platform,
            report_date=report_date,
            platform_conversions=platform_conversions,
            platform_clicks=platform_clicks,
            platform_spend=platform_spend,
            epi_total_leads=total,
            epi_verified_leads=verified,
            epi_junk_leads=junk,
            discrepancy_pct=discrepancy_pct,
            cost_per_verified_lead=cost_per_verified,
        )
        db.add(comparison)
