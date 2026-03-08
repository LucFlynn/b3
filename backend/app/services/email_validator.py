import logging
import re

import httpx
import pybreaker
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.config import settings

logger = logging.getLogger(__name__)

_EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

_RETRYABLE = (httpx.ConnectError, httpx.TimeoutException, httpx.ReadError)

# Circuit breakers
_ipqs_email_breaker = pybreaker.CircuitBreaker(fail_max=5, reset_timeout=60, name="ipqs_email")
_abstractapi_email_breaker = pybreaker.CircuitBreaker(fail_max=5, reset_timeout=60, name="abstractapi_email")


# ── IPQS (preferred) ──

@_ipqs_email_breaker
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=0.5, min=0.5, max=4),
    retry=retry_if_exception_type(_RETRYABLE),
    reraise=True,
)
async def _call_ipqs_email(email: str) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"https://www.ipqualityscore.com/api/json/email/{settings.ipqs_api_key}/{email}",
            params={"timeout": 10, "abuse_strictness": 1},
            timeout=15.0,
        )
        resp.raise_for_status()
        return resp.json()


# ── AbstractAPI (dormant fallback) ──

@_abstractapi_email_breaker
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

    # IPQS — preferred
    if settings.ipqs_api_key:
        try:
            data = await _call_ipqs_email(email)
            if not data.get("success", False):
                logger.warning("IPQS email check returned success=false: %s", data.get("message"))
            else:
                if data.get("disposable"):
                    return "disposable"
                if not data.get("valid"):
                    return "invalid"
                if data.get("catch_all"):
                    return "catch_all"
                deliverability = data.get("deliverability", "")
                if deliverability == "low":
                    return "invalid"
                return "valid"
        except pybreaker.CircuitBreakerError:
            logger.warning("FALLBACK email validation: IPQS circuit breaker OPEN")
        except Exception:
            logger.exception("FALLBACK email validation: IPQS failed after retries")

    # AbstractAPI — dormant fallback
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
            logger.warning("FALLBACK email validation: AbstractAPI circuit breaker OPEN, using regex")
        except Exception:
            logger.exception("FALLBACK email validation: AbstractAPI failed after retries, using regex")

    # Regex fallback
    logger.info("FALLBACK email validation: using regex for %s", email.split("@")[-1])
    return "valid" if _EMAIL_RE.match(email) else "invalid"
