from datetime import date, timedelta, timezone, datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, case, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.lead import Lead
from app.models.platform_conversion import PlatformConversion
from app.models.user import User
from app.schemas.campaign import CampaignPerformanceResponse, CampaignRow
from app.security import get_current_user

router = APIRouter(prefix="/api/campaigns", tags=["campaigns"])


@router.get("/performance", response_model=CampaignPerformanceResponse)
async def campaign_performance(
    site_id: Optional[UUID] = None,
    days: int = Query(30, ge=1, le=365),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    cutoff = date.today() - timedelta(days=days)

    # Platform conversions grouped by campaign + ad group
    pc_q = (
        select(
            PlatformConversion.campaign_name,
            PlatformConversion.ad_group_name,
            func.sum(PlatformConversion.spend).label("spend"),
            func.sum(PlatformConversion.clicks).label("clicks"),
            func.sum(PlatformConversion.conversions_reported).label("google_reported"),
        )
        .where(
            PlatformConversion.agency_id == user.agency_id,
            PlatformConversion.platform == "google_ads",
            PlatformConversion.report_date >= cutoff,
        )
        .group_by(PlatformConversion.campaign_name, PlatformConversion.ad_group_name)
    )
    if site_id:
        pc_q = pc_q.where(PlatformConversion.site_id == site_id)

    pc_result = await db.execute(pc_q)
    pc_rows = pc_result.all()

    # Collect all campaign names from platform data
    campaign_names = {row.campaign_name for row in pc_rows if row.campaign_name}

    # Leads matched to Google Ads campaigns:
    # - via utm_campaign matching a known campaign name, OR
    # - via gclid being present (definitive Google Ads attribution)
    # Group by utm_campaign so we can map back to campaign rows.
    # Leads with gclid but no utm_campaign go into a NULL bucket.
    cutoff_dt = datetime(cutoff.year, cutoff.month, cutoff.day, tzinfo=timezone.utc)
    lead_filters = [
        Lead.agency_id == user.agency_id,
        Lead.created_at >= cutoff_dt,
        or_(
            Lead.utm_campaign.in_(campaign_names) if campaign_names else False,
            Lead.gclid.isnot(None),
        ),
    ]
    if site_id:
        lead_filters.append(Lead.site_id == site_id)

    lead_q = (
        select(
            Lead.utm_campaign,
            func.sum(
                case(
                    (Lead.quality_label.in_(["verified", "likely_real"]), 1),
                    else_=0,
                )
            ).label("verified"),
            func.sum(
                case(
                    (Lead.quality_label.in_(["suspicious", "junk"]), 1),
                    else_=0,
                )
            ).label("junk"),
        )
        .where(*lead_filters)
        .group_by(Lead.utm_campaign)
    )

    lead_result = await db.execute(lead_q)
    lead_map: dict[str | None, dict[str, int]] = {}
    for row in lead_result.all():
        lead_map[row.utm_campaign] = {
            "verified": int(row.verified or 0),
            "junk": int(row.junk or 0),
        }

    # Leads with gclid but NULL utm_campaign — attribute to "google_ads" generically
    gclid_no_campaign = lead_map.get(None, {"verified": 0, "junk": 0})

    # Build campaign rows; track seen campaigns to avoid double-counting EPI totals
    campaigns = []
    total_spend = 0.0
    total_google_reported = 0
    total_epi_verified = 0
    total_junk = 0
    seen_campaigns: set[str | None] = set()

    for row in pc_rows:
        spend = float(row.spend or 0)
        clicks = int(row.clicks or 0)
        google_reported = int(row.google_reported or 0)

        # Get EPI data for this campaign
        lead_data = lead_map.get(row.campaign_name, {"verified": 0, "junk": 0})
        epi_verified = lead_data["verified"]
        junk_count = lead_data["junk"]
        real_cpl = round(spend / epi_verified, 2) if epi_verified > 0 else None

        campaigns.append(
            CampaignRow(
                campaign_name=row.campaign_name,
                ad_group_name=row.ad_group_name,
                spend=round(spend, 2),
                clicks=clicks,
                google_reported=google_reported,
                epi_verified=epi_verified,
                junk=junk_count,
                real_cpl=real_cpl,
            )
        )

        total_spend += spend
        total_google_reported += google_reported

        # Only count each campaign's EPI numbers once for totals
        if row.campaign_name not in seen_campaigns:
            seen_campaigns.add(row.campaign_name)
            total_epi_verified += epi_verified
            total_junk += junk_count

    # Add gclid-only leads (NULL utm_campaign) that weren't already counted
    if None not in seen_campaigns:
        total_epi_verified += gclid_no_campaign["verified"]
        total_junk += gclid_no_campaign["junk"]

    discrepancy_pct = None
    if total_google_reported > 0:
        discrepancy_pct = round(
            (total_google_reported - total_epi_verified) / total_google_reported * 100, 1
        )

    return CampaignPerformanceResponse(
        total_spend=round(total_spend, 2),
        total_google_reported=total_google_reported,
        total_epi_verified=total_epi_verified,
        total_junk=total_junk,
        discrepancy_pct=discrepancy_pct,
        campaigns=campaigns,
    )
