from datetime import date
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.attribution_comparison import AttributionComparison
from app.models.user import User
from app.schemas.site import ComparisonResponse
from app.security import get_current_user

router = APIRouter(prefix="/api/comparison", tags=["comparison"])


@router.get("", response_model=list[ComparisonResponse])
async def get_comparison(
    site_id: Optional[UUID] = None,
    platform: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    q = select(AttributionComparison).where(AttributionComparison.agency_id == user.agency_id)
    if site_id:
        q = q.where(AttributionComparison.site_id == site_id)
    if platform:
        q = q.where(AttributionComparison.platform == platform)
    if date_from:
        q = q.where(AttributionComparison.report_date >= date_from)
    if date_to:
        q = q.where(AttributionComparison.report_date <= date_to)

    q = q.order_by(AttributionComparison.report_date.desc())
    result = await db.execute(q)
    rows = result.scalars().all()

    return [
        ComparisonResponse(
            site_id=r.site_id,
            platform=r.platform,
            report_date=r.report_date.isoformat(),
            platform_conversions=r.platform_conversions,
            platform_clicks=r.platform_clicks,
            platform_spend=r.platform_spend,
            epi_total_leads=r.epi_total_leads,
            epi_verified_leads=r.epi_verified_leads,
            epi_junk_leads=r.epi_junk_leads,
            discrepancy_pct=r.discrepancy_pct,
            cost_per_verified_lead=r.cost_per_verified_lead,
        )
        for r in rows
    ]
