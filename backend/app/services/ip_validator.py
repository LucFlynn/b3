import logging

import httpx
import pybreaker
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.config import settings

logger = logging.getLogger(__name__)

_RETRYABLE = (httpx.ConnectError, httpx.TimeoutException, httpx.ReadError)

# Circuit breakers
_ipqs_ip_breaker = pybreaker.CircuitBreaker(fail_max=5, reset_timeout=60, name="ipqs_ip")
_abstractapi_ip_breaker = pybreaker.CircuitBreaker(fail_max=5, reset_timeout=60, name="abstractapi_ip")


# ── IPQS (preferred) ──

@_ipqs_ip_breaker
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=0.5, min=0.5, max=4),
    retry=retry_if_exception_type(_RETRYABLE),
    reraise=True,
)
async def _call_ipqs_ip(ip_address: str) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"https://www.ipqualityscore.com/api/json/ip/{settings.ipqs_api_key}/{ip_address}",
            params={"strictness": 1, "allow_public_access_points": "true"},
            timeout=15.0,
        )
        resp.raise_for_status()
        return resp.json()


# ── AbstractAPI (dormant fallback) ──

@_abstractapi_ip_breaker
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
    """Returns IP intelligence: is_vpn, is_proxy, is_tor, is_hosting, is_mobile, country."""
    if not ip_address or ip_address == "unknown":
        return {}

    # IPQS — preferred
    if settings.ipqs_api_key:
        try:
            data = await _call_ipqs_ip(ip_address)
            if not data.get("success", False):
                logger.warning("IPQS IP check returned success=false: %s", data.get("message"))
            else:
                return {
                    "is_vpn": data.get("vpn", False),
                    "is_proxy": data.get("proxy", False),
                    "is_tor": data.get("tor", False),
                    "is_hosting": data.get("host", False) or (data.get("connection_type", "") == "Data Center"),
                    "is_mobile": data.get("mobile", False),
                    "is_crawler": data.get("is_crawler", False),
                    "bot_status": data.get("bot_status", False),
                    "fraud_score": data.get("fraud_score", 0),
                    "country": data.get("country_code", ""),
                    "isp": data.get("ISP", ""),
                }
        except pybreaker.CircuitBreakerError:
            logger.warning("FALLBACK IP check: IPQS circuit breaker OPEN")
        except Exception:
            logger.exception("FALLBACK IP check: IPQS failed after retries")

    # AbstractAPI — dormant fallback
    if settings.abstractapi_ip_key:
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
        except pybreaker.CircuitBreakerError:
            logger.warning("FALLBACK IP check: AbstractAPI circuit breaker OPEN, skipping")
            return {}
        except Exception:
            logger.exception("FALLBACK IP check: AbstractAPI failed after retries, skipping")
            return {}

    return {}
