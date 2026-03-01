import re

import httpx
from app.config import settings

_PHONE_RE = re.compile(r"^\+?1?\d{7,15}$")


async def validate_phone(phone: str) -> str:
    """Returns: valid, invalid, voip, mobile, landline."""
    if not settings.phone_validation_url:
        cleaned = re.sub(r"[\s\-().]", "", phone)
        return "valid" if _PHONE_RE.match(cleaned) else "invalid"

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
        return "unknown"
