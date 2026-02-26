from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.lead import Lead
from app.models.user import User
from app.schemas.lead import LeadResponse, LeadStatsResponse
from app.security import get_current_user

router = APIRouter(prefix="/api/leads", tags=["leads"])


def _base_query(user: User):
    return select(Lead).where(Lead.agency_id == user.agency_id)


@router.get("", response_model=list[LeadResponse])
async def list_leads(
    site_id: Optional[UUID] = None,
    quality_label: Optional[str] = None,
    attribution_tier: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    q = _base_query(user)
    if site_id:
        q = q.where(Lead.site_id == site_id)
    if quality_label:
        q = q.where(Lead.quality_label == quality_label)
    if attribution_tier:
        q = q.where(Lead.attribution_tier == attribution_tier)
    if date_from:
        q = q.where(Lead.created_at >= date_from)
    if date_to:
        q = q.where(Lead.created_at <= date_to)

    q = q.order_by(Lead.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/stats", response_model=LeadStatsResponse)
async def lead_stats(
    site_id: Optional[UUID] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    base = select(Lead).where(Lead.agency_id == user.agency_id)
    if site_id:
        base = base.where(Lead.site_id == site_id)
    if date_from:
        base = base.where(Lead.created_at >= date_from)
    if date_to:
        base = base.where(Lead.created_at <= date_to)

    total_q = select(func.count()).select_from(base.subquery())
    total = (await db.execute(total_q)).scalar() or 0

    def _count_q(col, val):
        return select(func.count()).select_from(base.where(col == val).subquery())

    verified = (await db.execute(_count_q(Lead.quality_label, "verified"))).scalar() or 0
    likely_real = (await db.execute(_count_q(Lead.quality_label, "likely_real"))).scalar() or 0
    suspicious = (await db.execute(_count_q(Lead.quality_label, "suspicious"))).scalar() or 0
    junk = (await db.execute(_count_q(Lead.quality_label, "junk"))).scalar() or 0
    duplicates = (await db.execute(_count_q(Lead.is_duplicate, True))).scalar() or 0

    attributed_q = select(func.count()).select_from(
        base.where(Lead.attribution_tier != "unattributed", Lead.attribution_tier.isnot(None)).subquery()
    )
    attributed = (await db.execute(attributed_q)).scalar() or 0
    unattributed = total - attributed

    avg_q = select(func.avg(Lead.quality_score)).select_from(base.subquery())
    avg_score = (await db.execute(avg_q)).scalar()

    return LeadStatsResponse(
        total_leads=total,
        verified=verified,
        likely_real=likely_real,
        suspicious=suspicious,
        junk=junk,
        duplicates=duplicates,
        attributed=attributed,
        unattributed=unattributed,
        avg_quality_score=round(avg_score, 1) if avg_score else None,
    )
