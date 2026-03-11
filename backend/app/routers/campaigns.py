from datetime import date, timedelta, timezone, datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, case
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

    # Leads grouped by utm_campaign for EPI verified/junk counts
    cutoff_dt = datetime(cutoff.year, cutoff.month, cutoff.day, tzinfo=timezone.utc)
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
        .where(
            Lead.agency_id == user.agency_id,
            Lead.created_at >= cutoff_dt,
        )
        .group_by(Lead.utm_campaign)
    )
    if site_id:
        lead_q = lead_q.where(Lead.site_id == site_id)

    lead_result = await db.execute(lead_q)
    lead_map = {}
    for row in lead_result.all():
        lead_map[row.utm_campaign] = {
            "verified": row.verified or 0,
            "junk": row.junk or 0,
        }

    # Build campaign rows
    campaigns = []
    total_spend = 0.0
    total_google_reported = 0
    total_epi_verified = 0
    total_junk = 0

    for row in pc_rows:
        spend = float(row.spend or 0)
        clicks = int(row.clicks or 0)
        google_reported = int(row.google_reported or 0)
        lead_data = lead_map.get(row.campaign_name, {"verified": 0, "junk": 0})
        epi_verified = int(lead_data["verified"])
        junk = int(lead_data["junk"])
        real_cpl = round(spend / epi_verified, 2) if epi_verified > 0 else None

        campaigns.append(
            CampaignRow(
                campaign_name=row.campaign_name,
                ad_group_name=row.ad_group_name,
                spend=round(spend, 2),
                clicks=clicks,
                google_reported=google_reported,
                epi_verified=epi_verified,
                junk=junk,
                real_cpl=real_cpl,
            )
        )

        total_spend += spend
        total_google_reported += google_reported
        total_epi_verified += epi_verified
        total_junk += junk

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
