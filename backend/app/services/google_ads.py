"""Google Ads API integration — pulls campaign-level performance data."""

from __future__ import annotations

import logging
from datetime import date

from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException

from app.config import settings

logger = logging.getLogger(__name__)

# GAQL query: campaign-level metrics for a single day
_QUERY = """
    SELECT
        campaign.id,
        campaign.name,
        ad_group.id,
        ad_group.name,
        metrics.clicks,
        metrics.impressions,
        metrics.cost_micros,
        metrics.conversions,
        segments.conversion_action_name,
        segments.date
    FROM ad_group
    WHERE segments.date = '{report_date}'
    AND metrics.impressions > 0
"""


def _build_client(refresh_token: str) -> GoogleAdsClient:
    """Build a GoogleAdsClient from per-agency refresh token + global app creds."""
    return GoogleAdsClient.load_from_dict(
        {
            "developer_token": settings.google_ads_developer_token,
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "refresh_token": refresh_token,
            "login_customer_id": settings.google_ads_login_customer_id or None,
            "use_proto_plus": True,
        }
    )


async def pull_google_ads_data(
    refresh_token: str,
    customer_id: str,
    report_date: date,
) -> list[dict]:
    """Pull campaign performance from Google Ads for a single day.

    Returns a list of dicts matching the shape expected by pull_google.py:
        campaign_id, campaign_name, ad_group_id, ad_group_name,
        conversion_action, conversions, clicks, impressions, spend
    """
    # Strip dashes from customer ID (Google Ads wants plain digits)
    customer_id = customer_id.replace("-", "")

    client = _build_client(refresh_token)
    ga_service = client.get_service("GoogleAdsService")

    query = _QUERY.format(report_date=report_date.isoformat())

    rows: list[dict] = []
    try:
        response = ga_service.search(customer_id=customer_id, query=query)
        for row in response:
            rows.append(
                {
                    "campaign_id": str(row.campaign.id),
                    "campaign_name": row.campaign.name,
                    "ad_group_id": str(row.ad_group.id),
                    "ad_group_name": row.ad_group.name,
                    "conversion_action": row.segments.conversion_action_name or None,
                    "conversions": int(row.metrics.conversions),
                    "clicks": row.metrics.clicks,
                    "impressions": row.metrics.impressions,
                    "spend": row.metrics.cost_micros / 1_000_000,  # micros → dollars
                }
            )
    except GoogleAdsException as ex:
        logger.error(
            "Google Ads API error for customer %s: %s",
            customer_id,
            ex.failure.errors[0].message if ex.failure.errors else str(ex),
        )
        raise

    logger.info(
        "Google Ads: pulled %d rows for customer %s on %s",
        len(rows), customer_id, report_date,
    )
    return rows
