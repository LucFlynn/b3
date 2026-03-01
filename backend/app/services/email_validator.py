import re

import httpx
from app.config import settings

_EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


async def validate_email(email: str) -> str:
    """Returns: valid, invalid, catch_all, disposable."""
    if not settings.email_validation_url:
        return "valid" if _EMAIL_RE.match(email) else "invalid"

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
