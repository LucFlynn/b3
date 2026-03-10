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
from app.services.ip_validator import check_ip
from app.services.email_notifier import send_lead_notification

from urllib.parse import urlparse, urlencode, parse_qs

logger = logging.getLogger(__name__)

# Query params worth keeping in the displayed page URL
_MARKETING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term",
    "gclid", "gbraid", "wbraid", "fbclid", "fbc", "fbp",
    "msclkid", "ttclid", "twclid", "li_fat_id", "mc_cid", "mc_eid",
    "hsa_acc", "hsa_cam", "hsa_grp", "hsa_ad", "hsa_src", "hsa_net",
    "hsa_ver", "hsa_la", "hsa_ol", "hsa_mt", "hsa_kw",
    "ref", "source", "campaign",
}


def _clean_page_url(raw_url: str) -> str:
    """Strip non-marketing query params from a page URL."""
    try:
        parsed = urlparse(raw_url)
        qs = parse_qs(parsed.query, keep_blank_values=False)
        kept = {k: v for k, v in qs.items() if k.lower() in _MARKETING_PARAMS}
        clean_query = urlencode(kept, doseq=True) if kept else ""
        return parsed._replace(query=clean_query, fragment="").geturl()
    except Exception:
        return raw_url


def _extract_field(form_data: dict, field_names: list[str]) -> str | None:
    """Try to find a field value by multiple possible names."""
    for name in field_names:
        for key, value in form_data.items():
            if name in key.lower() and value:
                return str(value).strip()
    return None


async def _check_duplicate(db: AsyncSession, agency_id, email_hash: str | None, phone_hash: str | None, visitor_id: str, page_url: str) -> tuple[bool, dict]:
    """Check for duplicates. Returns (is_duplicate, dedup_details)."""
    now = datetime.now(timezone.utc)

    # Same email within 24h
    if email_hash:
        cutoff = now - timedelta(hours=24)
        count_result = await db.execute(
            select(func.count()).select_from(Lead).where(
                Lead.agency_id == agency_id,
                Lead.email_hash == email_hash,
                Lead.created_at >= cutoff,
            )
        )
        count = count_result.scalar() or 0
        if count > 0:
            first_result = await db.execute(
                select(Lead.created_at).where(
                    Lead.agency_id == agency_id,
                    Lead.email_hash == email_hash,
                    Lead.created_at >= cutoff,
                ).order_by(Lead.created_at.asc()).limit(1)
            )
            first_seen = first_result.scalar()
            return True, {
                "is_duplicate": True,
                "reason": "same_email",
                "first_seen": first_seen.isoformat() if first_seen else None,
                "count": count + 1,
            }

    # Same phone within 24h
    if phone_hash:
        cutoff = now - timedelta(hours=24)
        count_result = await db.execute(
            select(func.count()).select_from(Lead).where(
                Lead.agency_id == agency_id,
                Lead.phone_hash == phone_hash,
                Lead.created_at >= cutoff,
            )
        )
        count = count_result.scalar() or 0
        if count > 0:
            first_result = await db.execute(
                select(Lead.created_at).where(
                    Lead.agency_id == agency_id,
                    Lead.phone_hash == phone_hash,
                    Lead.created_at >= cutoff,
                ).order_by(Lead.created_at.asc()).limit(1)
            )
            first_seen = first_result.scalar()
            return True, {
                "is_duplicate": True,
                "reason": "same_phone",
                "first_seen": first_seen.isoformat() if first_seen else None,
                "count": count + 1,
            }

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
        return True, {
            "is_duplicate": True,
            "reason": "same_visitor",
            "first_seen": None,
            "count": None,
        }

    return False, {"is_duplicate": False}


async def process_lead(
    db: AsyncSession,
    site: Site,
    pageview: Pageview,
    event: EventPayload,
    client_ip: str = "",
):
    """Full lead processing pipeline: dedup → verify → score → attribute."""
    # Usage enforcement — check if the site owner has remaining lead quota
    from app.models.user import User
    user_result = await db.execute(
        select(User).where(User.agency_id == site.agency_id)
    )
    site_owner = user_result.scalar_one_or_none()
    if site_owner and site_owner.usage_count >= site_owner.usage_limit:
        logger.info(
            "Usage limit reached for agency %s (%d/%d) — lead logged but not scored",
            site.agency_id, site_owner.usage_count, site_owner.usage_limit,
        )
        lead = Lead(
            site_id=site.id,
            agency_id=site.agency_id,
            pageview_id=pageview.id,
            visitor_id=event.visitor_id,
            ip_hash=pageview.ip_hash,
            page_url=event.page_url,
            form_id=event.form_id,
            form_action=event.form_action,
            quality_label="paused",
            created_at=datetime.now(timezone.utc),
        )
        db.add(lead)
        await db.flush()
        return lead

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
    is_duplicate, dedup_info = await _check_duplicate(
        db, site.agency_id, email_hash, phone_hash, event.visitor_id, event.page_url
    )

    # Step 2: Validate email & phone (skip API calls for duplicates)
    email_valid = None
    phone_valid = None
    if not is_duplicate:
        if email:
            email_valid = await validate_email(email)
        if phone:
            phone_valid = await validate_phone(phone)

    # Step 3: Bot detection + IP intelligence
    is_bot, bot_reasons = detect_bot(
        honeypot_value=event.honeypot_value,
        form_fill_time_ms=event.form_fill_time_ms,
        user_agent=event.user_agent,
    )
    ip_info = await check_ip(client_ip) if not is_duplicate else {}
    is_vpn_or_proxy = ip_info.get("is_vpn") or ip_info.get("is_proxy") or ip_info.get("is_tor")
    is_datacenter = ip_info.get("is_hosting", False)
    if is_vpn_or_proxy:
        bot_reasons.append("vpn_or_proxy")
    if is_datacenter:
        bot_reasons.append("datacenter_ip")
        is_bot = True

    # Step 4: Attribution
    attribution_tier = determine_attribution(
        gclid=event.gclid,
        fbclid=event.fbclid,
        utm_source=event.utm_source,
        utm_medium=event.utm_medium,
        referrer=event.referrer,
    )

    # Step 5: Quality scoring (now returns signals)
    quality_score, quality_label, signals_fired = score_lead(
        email_valid=email_valid,
        phone_valid=phone_valid,
        is_bot=is_bot,
        is_duplicate=is_duplicate,
        honeypot_triggered=bool(event.honeypot_value),
        form_fill_time_ms=event.form_fill_time_ms,
        has_gclid=bool(event.gclid),
        has_fbclid=bool(event.fbclid),
        is_vpn_or_proxy=is_vpn_or_proxy,
        is_datacenter=is_datacenter,
    )

    # Build the full scoring signals blob
    scoring_signals = {
        "signals_fired": signals_fired,
        "checks": {
            "email": {
                "status": email_valid,
                "provided": bool(email),
            },
            "phone": {
                "status": phone_valid,
                "provided": bool(phone),
            },
            "bot": {
                "is_bot": is_bot,
                "honeypot": bool(event.honeypot_value),
                "form_fill_ms": event.form_fill_time_ms,
                "user_agent_bot": any("bot_user_agent" in r for r in bot_reasons),
                "reasons": bot_reasons,
            },
            "ip": {
                "vpn": ip_info.get("is_vpn", False),
                "proxy": ip_info.get("is_proxy", False),
                "tor": ip_info.get("is_tor", False),
                "datacenter": ip_info.get("is_hosting", False),
                "country": ip_info.get("country", ""),
            },
            "attribution": {
                "tier": attribution_tier,
                "gclid": event.gclid or None,
                "fbclid": event.fbclid or None,
                "utm_source": event.utm_source or None,
                "utm_medium": event.utm_medium or None,
                "utm_campaign": event.utm_campaign or None,
                "referrer": event.referrer or None,
            },
        },
        "dedup": dedup_info,
    }

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
        page_url=_clean_page_url(event.page_url) if event.page_url else None,
        form_id=event.form_id,
        form_action=event.form_action,
        extra_fields={k: v for k, v in form_data.items() if k not in ("email", "phone", "name")},
        scoring_signals=scoring_signals,
    )
    db.add(lead)
    await db.flush()
    logger.info("Lead processed: id=%s score=%d label=%s", lead.id, quality_score, quality_label)

    if not is_duplicate:
        await send_lead_notification(lead, site)

    # Increment usage count
    if site_owner:
        site_owner.usage_count += 1
        db.add(site_owner)

    return lead
