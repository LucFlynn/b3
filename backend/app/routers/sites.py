import secrets
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.site import Site
from app.models.lead import Lead
from app.models.pageview import Pageview
from app.models.user import User
from app.schemas.site import SiteCreate, SiteResponse
from app.security import get_current_user
from app.config import settings

router = APIRouter(prefix="/api/sites", tags=["sites"])


def _pixel_snippet(pixel_id: str) -> str:
    return (
        f'<script src="{settings.backend_url}/pixel/epi.min.js" '
        f'data-pixel-id="{pixel_id}" async></script>'
    )


def _site_response(site: Site, leads_count: int = 0) -> SiteResponse:
    resp = SiteResponse.model_validate(site)
    resp.pixel_snippet = _pixel_snippet(site.pixel_id)
    resp.leads_count = leads_count
    return resp


@router.post("", response_model=SiteResponse, status_code=201)
async def create_site(
    req: SiteCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    pixel_id = f"px_{secrets.token_urlsafe(12)}"
    site = Site(
        agency_id=user.agency_id,
        domain=req.domain,
        name=req.name,
        pixel_id=pixel_id,
        google_ads_customer_id=req.google_ads_customer_id,
        meta_ads_account_id=req.meta_ads_account_id,
    )
    db.add(site)
    await db.flush()
    return _site_response(site)


@router.get("", response_model=list[SiteResponse])
async def list_sites(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Fetch sites with lead counts in one query
    lead_counts = (
        select(Lead.site_id, func.count(Lead.id).label("cnt"))
        .group_by(Lead.site_id)
        .subquery()
    )
    stmt = (
        select(Site, func.coalesce(lead_counts.c.cnt, 0).label("leads_count"))
        .outerjoin(lead_counts, Site.id == lead_counts.c.site_id)
        .where(Site.agency_id == user.agency_id)
        .order_by(Site.created_at.desc())
    )
    result = await db.execute(stmt)
    return [_site_response(row.Site, row.leads_count) for row in result]


@router.get("/{site_id}", response_model=SiteResponse)
async def get_site(
    site_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    lead_counts = (
        select(Lead.site_id, func.count(Lead.id).label("cnt"))
        .where(Lead.site_id == site_id)
        .group_by(Lead.site_id)
        .subquery()
    )
    stmt = (
        select(Site, func.coalesce(lead_counts.c.cnt, 0).label("leads_count"))
        .outerjoin(lead_counts, Site.id == lead_counts.c.site_id)
        .where(Site.id == site_id, Site.agency_id == user.agency_id)
    )
    result = await db.execute(stmt)
    row = result.one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Site not found")
    return _site_response(row.Site, row.leads_count)


@router.get("/{site_id}/pixel-status")
async def pixel_status(
    site_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Verify ownership
    result = await db.execute(
        select(Site).where(Site.id == site_id, Site.agency_id == user.agency_id)
    )
    site = result.scalar_one_or_none()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    now = datetime.now(timezone.utc)

    # Last event
    last_event_result = await db.execute(
        select(func.max(Pageview.created_at)).where(Pageview.site_id == site_id)
    )
    last_event_at = last_event_result.scalar()

    # Page views today (UTC)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    pv_result = await db.execute(
        select(func.count()).select_from(Pageview).where(
            Pageview.site_id == site_id,
            Pageview.created_at >= today_start,
        )
    )
    page_views_today = pv_result.scalar() or 0

    # Determine status
    if last_event_at is None:
        status = "waiting"
    else:
        delta = now - last_event_at
        minutes = delta.total_seconds() / 60
        if minutes < 30:
            status = "active"
        elif minutes < 240:
            status = "idle"
        else:
            status = "inactive"

    return {
        "pixel_status": status,
        "last_event_at": last_event_at.isoformat() if last_event_at else None,
        "page_views_today": page_views_today,
    }
