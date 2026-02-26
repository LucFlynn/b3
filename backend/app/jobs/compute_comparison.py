import logging
from datetime import date, timedelta
from uuid import UUID

from sqlalchemy import select

from app.database import _ensure_initialized
import app.database as _db
from app.models.agency import Agency
from app.models.site import Site
from app.services.comparison import compute_comparison_for_site

logger = logging.getLogger(__name__)


async def compute_comparison(agency_id: str | None = None):
    """Compute daily attribution comparison for one or all agencies."""
    yesterday = date.today() - timedelta(days=1)

    _ensure_initialized()
    async with _db.async_session() as db:
        q = select(Agency)
        if agency_id:
            q = q.where(Agency.id == UUID(agency_id))
        agencies = (await db.execute(q)).scalars().all()

        for agency in agencies:
            sites = (await db.execute(
                select(Site).where(Site.agency_id == agency.id)
            )).scalars().all()

            for site in sites:
                try:
                    for platform in ("google_ads", "meta_ads"):
                        await compute_comparison_for_site(
                            db, site.id, agency.id, platform, yesterday
                        )
                    await db.commit()
                    logger.info("Computed comparison for site %s", site.domain)
                except Exception:
                    logger.exception("Error computing comparison for site %s", site.domain)
                    await db.rollback()


async def compute_comparison_all():
    await compute_comparison()
