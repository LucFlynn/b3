import logging

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.security import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/billing", tags=["billing"])


def _get_stripe():
    if not settings.stripe_secret_key:
        raise HTTPException(status_code=500, detail="Stripe not configured")
    stripe.api_key = settings.stripe_secret_key
    return stripe


@router.post("/create-checkout")
async def create_checkout_session(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    s = _get_stripe()

    # Create or reuse Stripe customer
    if not user.stripe_customer_id:
        customer = s.Customer.create(
            email=user.email,
            metadata={"user_id": str(user.id), "clerk_user_id": user.clerk_user_id or ""},
        )
        user.stripe_customer_id = customer.id
        db.add(user)
        await db.flush()

    session = s.checkout.Session.create(
        customer=user.stripe_customer_id,
        payment_method_types=["card"],
        line_items=[{"price": settings.stripe_price_id, "quantity": 1}],
        mode="subscription",
        success_url=f"{settings.frontend_url}/dashboard?upgraded=true",
        cancel_url=f"{settings.frontend_url}/dashboard",
    )
    return {"checkout_url": session.url}


@router.get("/portal")
async def billing_portal(
    user: User = Depends(get_current_user),
):
    s = _get_stripe()

    if not user.stripe_customer_id:
        raise HTTPException(status_code=400, detail="No billing account found")

    session = s.billing_portal.Session.create(
        customer=user.stripe_customer_id,
        return_url=f"{settings.frontend_url}/dashboard",
    )
    return {"portal_url": session.url}


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    s = _get_stripe()
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    try:
        event = s.Webhook.construct_event(
            payload, sig_header, settings.stripe_webhook_secret
        )
    except s.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        customer_id = session.get("customer")
        subscription_id = session.get("subscription")

        result = await db.execute(
            select(User).where(User.stripe_customer_id == customer_id)
        )
        user = result.scalar_one_or_none()
        if user:
            user.plan = "paid"
            user.stripe_subscription_id = subscription_id
            user.usage_limit = 999999  # effectively unlimited
            db.add(user)
            logger.info("User %s upgraded to paid plan", user.email)

    elif event["type"] == "invoice.payment_failed":
        session = event["data"]["object"]
        customer_id = session.get("customer")
        result = await db.execute(
            select(User).where(User.stripe_customer_id == customer_id)
        )
        user = result.scalar_one_or_none()
        if user:
            user.plan = "past_due"
            db.add(user)
            logger.warning("Payment failed for user %s", user.email)

    elif event["type"] == "customer.subscription.deleted":
        session = event["data"]["object"]
        customer_id = session.get("customer")
        result = await db.execute(
            select(User).where(User.stripe_customer_id == customer_id)
        )
        user = result.scalar_one_or_none()
        if user:
            user.plan = "free"
            user.usage_limit = 100
            user.stripe_subscription_id = None
            db.add(user)
            logger.info("Subscription cancelled for user %s", user.email)

    return {"status": "ok"}
