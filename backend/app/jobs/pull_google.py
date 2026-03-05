import logging
from datetime import date, timedelta
from uuid import UUID

from sqlalchemy import select, and_

from app.config import settings
from app.database import _ensure_initialized
import app.database as _db
from app.models.agency import Agency
from app.models.site import Site
from app.models.platform_conversion import PlatformConversion
from app.services.google_ads import pull_google_ads_data

logger = logging.getLogger(__name__)

BACKFILL_DAYS = 7


async def pull_google_ads(agency_id: str | None = None):
    """Pull Google Ads data for one or all agencies."""
    if not settings.google_ads_refresh_token:
        logger.info("No GOOGLE_ADS_REFRESH_TOKEN set, skipping Google Ads pull")
        return

    _ensure_initialized()
    async with _db.async_session() as db:
        q = select(Agency)
        if agency_id:
            q = q.where(Agency.id == UUID(agency_id))
        agencies = (await db.execute(q)).scalars().all()

        for agency in agencies:
            sites_q = select(Site).where(
                Site.agency_id == agency.id,
                Site.google_ads_customer_id.isnot(None),
            )
            sites = (await db.execute(sites_q)).scalars().all()

            for site in sites:
                existing = (await db.execute(
                    select(PlatformConversion.id).where(
                        PlatformConversion.site_id == site.id,
                        PlatformConversion.platform == "google_ads",
                    ).limit(1)
                )).scalar_one_or_none()

                if existing is None:
                    dates = [date.today() - timedelta(days=i) for i in range(BACKFILL_DAYS, 0, -1)]
                    logger.info("Backfilling Google Ads for site %s: %d days", site.domain, len(dates))
                else:
                    dates = [date.today() - timedelta(days=1)]

                for report_date in dates:
                    try:
                        data = await pull_google_ads_data(
                            settings.google_ads_refresh_token,
                            site.google_ads_customer_id,
                            report_date,
                        )
                        for row in data:
                            existing_row = (await db.execute(
                                select(PlatformConversion).where(and_(
                                    PlatformConversion.site_id == site.id,
                                    PlatformConversion.platform == "google_ads",
                                    PlatformConversion.campaign_id == row.get("campaign_id"),
                                    PlatformConversion.ad_group_id == row.get("ad_group_id"),
                                    PlatformConversion.report_date == report_date,
                                ))
                            )).scalar_one_or_none()

                            if existing_row:
                                existing_row.conversions_reported = row.get("conversions", 0)
                                existing_row.clicks = row.get("clicks", 0)
                                existing_row.impressions = row.get("impressions", 0)
                                existing_row.spend = row.get("spend", 0.0)
                                existing_row.campaign_name = row.get("campaign_name")
                                existing_row.ad_group_name = row.get("ad_group_name")
                                existing_row.conversion_action = row.get("conversion_action")
                            else:
                                db.add(PlatformConversion(
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
                                    report_date=report_date,
                                ))
                        await db.commit()
                        logger.info("Pulled Google Ads for site %s on %s: %d rows", site.domain, report_date, len(data))
                    except Exception:
                        logger.exception("Error pulling Google Ads for site %s on %s", site.domain, report_date)
                        await db.rollback()


async def pull_google_ads_all():
    await pull_google_ads()
