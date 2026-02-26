import secrets
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.site import Site
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

    resp = SiteResponse.model_validate(site)
    resp.pixel_snippet = _pixel_snippet(pixel_id)
    return resp


@router.get("", response_model=list[SiteResponse])
async def list_sites(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Site).where(Site.agency_id == user.agency_id).order_by(Site.created_at.desc())
    )
    sites = result.scalars().all()
    return [
        SiteResponse(**{**SiteResponse.model_validate(s).model_dump(), "pixel_snippet": _pixel_snippet(s.pixel_id)})
        for s in sites
    ]


@router.get("/{site_id}", response_model=SiteResponse)
async def get_site(
    site_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Site).where(Site.id == site_id, Site.agency_id == user.agency_id)
    )
    site = result.scalar_one_or_none()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    resp = SiteResponse.model_validate(site)
    resp.pixel_snippet = _pixel_snippet(site.pixel_id)
    return resp
