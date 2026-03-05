import logging

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.config import settings

logger = logging.getLogger(__name__)

_RETRYABLE = (httpx.ConnectError, httpx.TimeoutException, httpx.ReadError)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=0.5, min=0.5, max=4),
    retry=retry_if_exception_type(_RETRYABLE),
    reraise=True,
)
async def _call_abstractapi_ip(ip_address: str) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://ip-intelligence.abstractapi.com/v1/",
            params={"api_key": settings.abstractapi_ip_key, "ip_address": ip_address},
            timeout=10.0,
        )
        resp.raise_for_status()
        return resp.json()


async def check_ip(ip_address: str) -> dict:
    """Returns IP intelligence: is_vpn, is_proxy, is_tor, is_hosting, is_mobile."""
    if not settings.abstractapi_ip_key or not ip_address or ip_address == "unknown":
        return {}

    try:
        data = await _call_abstractapi_ip(ip_address)
        security = data.get("security", {})
        return {
            "is_vpn": security.get("is_vpn", False),
            "is_proxy": security.get("is_proxy", False),
            "is_tor": security.get("is_tor", False),
            "is_hosting": security.get("is_hosting", False),
            "is_mobile": security.get("is_mobile", False),
            "country": data.get("location", {}).get("country_code", ""),
        }
    except Exception:
        logger.exception("AbstractAPI IP intelligence failed after retries")
        return {}
