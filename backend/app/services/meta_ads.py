import httpx
from datetime import date

from app.config import settings


async def pull_meta_ads_data(access_token: str, account_id: str, report_date: date) -> list[dict]:
    """Pull conversion data from Meta Ads API (mock)."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{settings.meta_ads_api_url}/conversions",
            params={
                "account_id": account_id,
                "date": report_date.isoformat(),
            },
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10.0,
        )
        resp.raise_for_status()
        return resp.json().get("data", [])
