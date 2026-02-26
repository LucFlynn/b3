import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lead import Lead
from app.models.pageview import Pageview
from app.models.site import Site
from app.schemas.event import EventPayload
from app.security import encrypt_pii, hash_pii, hash_ip
from app.services.email_validator import validate_email
from app.services.phone_validator import validate_phone
from app.services.bot_detector import detect_bot
from app.services.lead_scorer import score_lead
from app.services.attribution import determine_attribution

logger = logging.getLogger(__name__)


def _extract_field(form_data: dict, field_names: list[str]) -> str | None:
    """Try to find a field value by multiple possible names."""
    for name in field_names:
        for key, value in form_data.items():
            if name in key.lower() and value:
                return str(value).strip()
    return None


async def _check_duplicate(db: AsyncSession, agency_id, email_hash: str | None, phone_hash: str | None, visitor_id: str, page_url: str) -> bool:
    """Check for duplicates: same email/phone within 24h, or same visitor+page within 5min."""
    now = datetime.now(timezone.utc)

    # Same email within 24h
    if email_hash:
        cutoff = now - timedelta(hours=24)
        result = await db.execute(
            select(func.count()).select_from(Lead).where(
                Lead.agency_id == agency_id,
                Lead.email_hash == email_hash,
                Lead.created_at >= cutoff,
            )
        )
        if (result.scalar() or 0) > 0:
            return True

    # Same phone within 24h
    if phone_hash:
        cutoff = now - timedelta(hours=24)
        result = await db.execute(
            select(func.count()).select_from(Lead).where(
                Lead.agency_id == agency_id,
                Lead.phone_hash == phone_hash,
                Lead.created_at >= cutoff,
            )
        )
        if (result.scalar() or 0) > 0:
            return True

    # Same visitor + same page within 5 min
    cutoff = now - timedelta(minutes=5)
    result = await db.execute(
        select(func.count()).select_from(Lead).where(
            Lead.agency_id == agency_id,
            Lead.visitor_id == visitor_id,
            Lead.created_at >= cutoff,
        )
    )
    if (result.scalar() or 0) > 0:
        return True

    return False


async def process_lead(
    db: AsyncSession,
    site: Site,
    pageview: Pageview,
    event: EventPayload,
):
    """Full lead processing pipeline: dedup → verify → score → attribute."""
    form_data = event.form_data or {}

    # Extract PII fields using heuristics
    email = _extract_field(form_data, ["email", "e-mail", "mail"])
    phone = _extract_field(form_data, ["phone", "tel", "mobile", "cell"])
    name = _extract_field(form_data, ["name", "full_name", "fullname", "first_name"])

    # Encrypt PII
    email_encrypted = encrypt_pii(email) if email else None
    email_hash = hash_pii(email) if email else None
    phone_encrypted = encrypt_pii(phone) if phone else None
    phone_hash = hash_pii(phone) if phone else None
    name_encrypted = encrypt_pii(name) if name else None

    # Step 1: Dedup check
    is_duplicate = await _check_duplicate(
        db, site.agency_id, email_hash, phone_hash, event.visitor_id, event.page_url
    )

    # Step 2: Validate email & phone
    email_valid = None
    phone_valid = None
    if email:
        email_valid = await validate_email(email)
    if phone:
        phone_valid = await validate_phone(phone)

    # Step 3: Bot detection
    is_bot, bot_reasons = detect_bot(
        honeypot_value=event.honeypot_value,
        form_fill_time_ms=event.form_fill_time_ms,
        user_agent=event.user_agent,
    )

    # Step 4: Attribution
    attribution_tier = determine_attribution(
        gclid=event.gclid,
        fbclid=event.fbclid,
        utm_source=event.utm_source,
        utm_medium=event.utm_medium,
        referrer=event.referrer,
    )

    # Step 5: Quality scoring
    quality_score, quality_label = score_lead(
        email_valid=email_valid,
        phone_valid=phone_valid,
        is_bot=is_bot,
        is_duplicate=is_duplicate,
        honeypot_triggered=bool(event.honeypot_value),
        form_fill_time_ms=event.form_fill_time_ms,
        has_gclid=bool(event.gclid),
        has_fbclid=bool(event.fbclid),
    )

    lead = Lead(
        site_id=site.id,
        agency_id=site.agency_id,
        pageview_id=pageview.id,
        email_encrypted=email_encrypted,
        email_hash=email_hash,
        phone_encrypted=phone_encrypted,
        phone_hash=phone_hash,
        name_encrypted=name_encrypted,
        visitor_id=event.visitor_id,
        ip_hash=pageview.ip_hash,
        email_valid=email_valid,
        phone_valid=phone_valid,
        is_bot=is_bot,
        honeypot_triggered=bool(event.honeypot_value),
        form_fill_time_ms=event.form_fill_time_ms,
        quality_score=quality_score,
        quality_label=quality_label,
        attribution_tier=attribution_tier,
        gclid=event.gclid,
        fbclid=event.fbclid,
        utm_source=event.utm_source,
        utm_medium=event.utm_medium,
        utm_campaign=event.utm_campaign,
        is_duplicate=is_duplicate,
        form_id=event.form_id,
        form_action=event.form_action,
        extra_fields={k: v for k, v in form_data.items() if k not in ("email", "phone", "name")},
    )
    db.add(lead)
    await db.flush()
    logger.info("Lead processed: id=%s score=%d label=%s", lead.id, quality_score, quality_label)
    return lead
