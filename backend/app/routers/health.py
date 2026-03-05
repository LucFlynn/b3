from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db

router = APIRouter(tags=["health"])


@router.get("/api/health")
async def health(db: AsyncSession = Depends(get_db)):
    # Verify database connection
    db_status = "connected"
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        db_status = "unreachable"

    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "db": db_status,
        "email_service": "configured" if settings.resend_api_key else "not_configured",
        "email_validation": "abstractapi" if settings.abstractapi_email_key else "regex_fallback",
        "phone_validation": "abstractapi" if settings.abstractapi_phone_key else "regex_fallback",
        "ip_intelligence": "configured" if settings.abstractapi_ip_key else "disabled",
    }
