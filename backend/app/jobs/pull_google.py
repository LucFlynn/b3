import logging
from datetime import date, timedelta
from uuid import UUID

from sqlalchemy import select

from app.database import _ensure_initialized
import app.database as _db
from app.models.agency import Agency
from app.models.site import Site
from app.models.platform_conversion import PlatformConversion
from app.services.google_ads import pull_google_ads_data

logger = logging.getLogger(__name__)


async def pull_google_ads(agency_id: str | None = None):
    """Pull Google Ads data for one or all agencies."""
    yesterday = date.today() - timedelta(days=1)

    _ensure_initialized()
    async with _db.async_session() as db:
        q = select(Agency)
        if agency_id:
            q = q.where(Agency.id == UUID(agency_id))
        agencies = (await db.execute(q)).scalars().all()

        for agency in agencies:
            if not agency.google_ads_refresh_token:
                continue

            sites_q = select(Site).where(
                Site.agency_id == agency.id,
                Site.google_ads_customer_id.isnot(None),
            )
            sites = (await db.execute(sites_q)).scalars().all()

            for site in sites:
                try:
                    data = await pull_google_ads_data(
                        agency.google_ads_refresh_token,
                        site.google_ads_customer_id,
                        yesterday,
                    )
                    for row in data:
                        conv = PlatformConversion(
                            site_id=site.id,
                            agency_id=agency.id,
                            platform="google_ads",
                            campaign_id=row.get("campaign_id"),
                            campaign_name=row.get("campaign_name"),
                            ad_group_id=row.get("ad_group_id"),
                            ad_group_name=row.get("ad_group_name"),
                            conversion_action=row.get("conversion_action"),
                            conversions_reported=row.get("conversions", 0),
                            clicks=row.get("clicks", 0),
                            impressions=row.get("impressions", 0),
                            spend=row.get("spend", 0.0),
                            report_date=yesterday,
                        )
                        db.add(conv)
                    await db.commit()
                    logger.info("Pulled Google Ads for site %s: %d rows", site.domain, len(data))
                except Exception:
                    logger.exception("Error pulling Google Ads for site %s", site.domain)
                    await db.rollback()


async def pull_google_ads_all():
    await pull_google_ads()
