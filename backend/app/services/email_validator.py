import logging
import re

import httpx
from app.config import settings

logger = logging.getLogger(__name__)

_EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


async def validate_email(email: str) -> str:
    """Returns: valid, invalid, catch_all, disposable."""

    # AbstractAPI Email Reputation — preferred
    if settings.abstractapi_email_key:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    "https://emailreputation.abstractapi.com/v1/",
                    params={"api_key": settings.abstractapi_email_key, "email": email},
                    timeout=10.0,
                )
                data = resp.json()
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
        except Exception:
            logger.exception("AbstractAPI email validation failed, falling back")

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
            return "unknown"

    # Regex fallback
    return "valid" if _EMAIL_RE.match(email) else "invalid"
