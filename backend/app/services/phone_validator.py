import logging
import re

import httpx
import pybreaker
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.config import settings

logger = logging.getLogger(__name__)

_PHONE_RE = re.compile(r"^\+?1?\d{7,15}$")

_RETRYABLE = (httpx.ConnectError, httpx.TimeoutException, httpx.ReadError)

# Circuit breaker: after 5 consecutive failures, stop calling AbstractAPI for 60s
_phone_breaker = pybreaker.CircuitBreaker(fail_max=5, reset_timeout=60, name="abstractapi_phone")


@_phone_breaker
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=0.5, min=0.5, max=4),
    retry=retry_if_exception_type(_RETRYABLE),
    reraise=True,
)
async def _call_abstractapi_phone(phone: str) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://phoneintelligence.abstractapi.com/v1/",
            params={"api_key": settings.abstractapi_phone_key, "phone": phone},
            timeout=10.0,
        )
        resp.raise_for_status()
        return resp.json()


async def validate_phone(phone: str) -> str:
    """Returns: valid, invalid, voip, mobile, landline."""

    # AbstractAPI Phone Intelligence — preferred
    if settings.abstractapi_phone_key:
        try:
            data = await _call_abstractapi_phone(phone)
            validation = data.get("phone_validation", {})
            carrier = data.get("phone_carrier", {})
            if not validation.get("is_valid", False):
                return "invalid"
            if validation.get("is_voip"):
                return "voip"
            line_type = (carrier.get("line_type") or "").lower()
            if line_type == "mobile":
                return "mobile"
            if line_type in ("fixed_line", "landline"):
                return "landline"
            return "valid"
        except pybreaker.CircuitBreakerError:
            logger.warning("FALLBACK phone validation: circuit breaker OPEN, using regex")
        except Exception:
            logger.exception("FALLBACK phone validation: AbstractAPI failed after retries, using regex")

    # Legacy external URL (mock server / custom service)
    if settings.phone_validation_url:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    settings.phone_validation_url,
                    json={"phone": phone},
                    timeout=5.0,
                )
                data = resp.json()
                return data.get("result", "invalid")
        except Exception:
            logger.warning("FALLBACK phone validation: legacy URL failed, using regex")

    # Regex fallback
    cleaned = re.sub(r"[\s\-().]", "", phone)
    logger.info("FALLBACK phone validation: using regex")
    return "valid" if _PHONE_RE.match(cleaned) else "invalid"
