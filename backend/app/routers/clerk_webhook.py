import logging

from fastapi import APIRouter, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from standardwebhooks.webhooks import Webhook, WebhookVerificationError

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.models.agency import Agency

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/clerk", tags=["clerk"])


@router.post("/webhook")
async def clerk_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    payload = await request.body()
    headers = dict(request.headers)

    if settings.clerk_webhook_secret:
        try:
            wh = Webhook(settings.clerk_webhook_secret)
            event = wh.verify(payload, headers)
        except WebhookVerificationError:
            raise HTTPException(status_code=400, detail="Invalid webhook signature")
    else:
        import json
        event = json.loads(payload)

    event_type = event.get("type", "")

    if event_type == "user.created":
        data = event.get("data", {})
        clerk_user_id = data.get("id", "")
        email_addresses = data.get("email_addresses", [])
        email = email_addresses[0]["email_address"] if email_addresses else ""

        if not clerk_user_id or not email:
            logger.warning("Clerk user.created webhook missing user_id or email")
            return {"status": "skipped"}

        # Check if already exists
        result = await db.execute(
            select(User).where(User.clerk_user_id == clerk_user_id)
        )
        if result.scalar_one_or_none():
            return {"status": "already_exists"}

        # Create agency + user
        agency = Agency(name=email.split("@")[0], slug=f"user-{clerk_user_id}")
        db.add(agency)
        await db.flush()

        user = User(
            agency_id=agency.id,
            email=email,
            clerk_user_id=clerk_user_id,
            role="admin",
        )
        db.add(user)
        logger.info("Created user from Clerk webhook: %s", email)

    return {"status": "ok"}
