import httpx
from datetime import date

from app.config import settings


async def pull_google_ads_data(refresh_token: str, customer_id: str, report_date: date) -> list[dict]:
    """Pull conversion data from Google Ads API (mock)."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{settings.google_ads_api_url}/conversions",
            params={
                "customer_id": customer_id,
                "date": report_date.isoformat(),
            },
            headers={"Authorization": f"Bearer {refresh_token}"},
            timeout=10.0,
        )
        resp.raise_for_status()
        return resp.json().get("data", [])
