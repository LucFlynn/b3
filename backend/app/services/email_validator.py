import logging
import re

import httpx
import pybreaker
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.config import settings

logger = logging.getLogger(__name__)

_EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

_RETRYABLE = (httpx.ConnectError, httpx.TimeoutException, httpx.ReadError)

# Circuit breaker: after 5 consecutive failures, stop calling AbstractAPI for 60s
_email_breaker = pybreaker.CircuitBreaker(fail_max=5, reset_timeout=60, name="abstractapi_email")


@_email_breaker
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=0.5, min=0.5, max=4),
    retry=retry_if_exception_type(_RETRYABLE),
    reraise=True,
)
async def _call_abstractapi_email(email: str) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://emailreputation.abstractapi.com/v1/",
            params={"api_key": settings.abstractapi_email_key, "email": email},
            timeout=10.0,
        )
        resp.raise_for_status()
        return resp.json()


async def validate_email(email: str) -> str:
    """Returns: valid, invalid, catch_all, disposable."""

    # AbstractAPI Email Reputation — preferred
    if settings.abstractapi_email_key:
        try:
            data = await _call_abstractapi_email(email)
            quality = data.get("email_quality", {})
            deliverability = data.get("email_deliverability", {})
            if quality.get("is_disposable"):
                return "disposable"
            if quality.get("is_catchall"):
                return "catch_all"
            status = deliverability.get("status", "unknown")
            if status == "deliverable":
                return "valid"
            if status == "undeliverable":
                return "invalid"
            return "unknown"
        except pybreaker.CircuitBreakerError:
            logger.warning("FALLBACK email validation: circuit breaker OPEN, using regex")
        except Exception:
            logger.exception("FALLBACK email validation: AbstractAPI failed after retries, using regex")

    # Legacy external URL (mock server / custom service)
    if settings.email_validation_url:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    settings.email_validation_url,
                    json={"email": email},
                    timeout=5.0,
                )
                data = resp.json()
                return data.get("result", "invalid")
        except Exception:
            logger.warning("FALLBACK email validation: legacy URL failed, using regex")

    # Regex fallback
    logger.info("FALLBACK email validation: using regex for %s", email.split("@")[-1])
    return "valid" if _EMAIL_RE.match(email) else "invalid"
