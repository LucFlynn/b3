import httpx
from app.config import settings


async def validate_email(email: str) -> str:
    """Returns: valid, invalid, catch_all, disposable."""
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
