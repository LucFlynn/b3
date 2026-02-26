import httpx
from app.config import settings


async def validate_phone(phone: str) -> str:
    """Returns: valid, invalid, voip, mobile, landline."""
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
