"""Meta (Facebook) Ads API integration — pulls campaign-level performance data."""

from __future__ import annotations

import logging
from datetime import date

import httpx

logger = logging.getLogger(__name__)

_GRAPH_API_VERSION = "v21.0"
_BASE_URL = f"https://graph.facebook.com/{_GRAPH_API_VERSION}"

# Fields we pull at the campaign level
_FIELDS = "campaign_id,campaign_name,adset_id,adset_name,clicks,impressions,spend,actions"


async def pull_meta_ads_data(
    access_token: str,
    account_id: str,
    report_date: date,
) -> list[dict]:
    """Pull campaign-level insights from Meta Ads for a single day.

    Returns a list of dicts matching the shape expected by pull_meta.py:
        campaign_id, campaign_name, adset_id, adset_name,
        action_type, conversions, clicks, impressions, spend
    """
    # Ensure account_id has the act_ prefix
    if not account_id.startswith("act_"):
        account_id = f"act_{account_id}"

    url = f"{_BASE_URL}/{account_id}/insights"
    params = {
        "access_token": access_token,
        "fields": _FIELDS,
        "level": "adset",
        "time_range": f'{{"since":"{report_date.isoformat()}","until":"{report_date.isoformat()}"}}',
        "limit": 500,
    }

    rows: list[dict] = []
    async with httpx.AsyncClient(timeout=30.0) as client:
        while url:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            body = resp.json()

            for entry in body.get("data", []):
                # Extract lead/conversion count from actions array
                conversions = 0
                action_type = None
                for action in entry.get("actions") or []:
                    if action.get("action_type") in (
                        "offsite_conversion.fb_pixel_lead",
                        "lead",
                        "onsite_conversion.lead_grouped",
                    ):
                        conversions = int(action.get("value", 0))
                        action_type = action["action_type"]
                        break

                rows.append(
                    {
                        "campaign_id": entry.get("campaign_id"),
                        "campaign_name": entry.get("campaign_name"),
                        "adset_id": entry.get("adset_id"),
                        "adset_name": entry.get("adset_name"),
                        "action_type": action_type,
                        "conversions": conversions,
                        "clicks": int(entry.get("clicks", 0)),
                        "impressions": int(entry.get("impressions", 0)),
                        "spend": float(entry.get("spend", 0.0)),
                    }
                )

            # Handle pagination
            paging = body.get("paging", {})
            url = paging.get("next")
            params = {}  # next URL already has params baked in

    logger.info(
        "Meta Ads: pulled %d rows for account %s on %s",
        len(rows), account_id, report_date,
    )
    return rows
