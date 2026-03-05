import logging
from uuid import UUID

from fastapi import APIRouter, Depends, Request, BackgroundTasks
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db, _ensure_initialized
import app.database as _db
from app.models.site import Site
from app.models.pageview import Pageview
from app.schemas.event import EventPayload, EventResponse
from app.security import hash_ip

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["events"])

# Maximum retries for background event processing
_MAX_RETRIES = 3
_RETRY_DELAYS = [1, 3, 8]  # seconds between retries


async def _process_event(event: EventPayload, client_ip: str, ip_hash: str):
    """Process event asynchronously after returning 202, with retries."""
    import asyncio
    from app.services.lead_pipeline import process_lead

    last_error = None
    for attempt in range(1, _MAX_RETRIES + 1):
        _ensure_initialized()
        async with _db.async_session() as db:
            try:
                result = await db.execute(select(Site).where(Site.pixel_id == event.pixel_id))
                site = result.scalar_one_or_none()
                if not site:
                    logger.warning("Unknown pixel_id: %s", event.pixel_id)
                    return  # not retryable

                # Mark pixel as verified on first event
                if not site.pixel_verified:
                    site.pixel_verified = True
                    db.add(site)

                pageview = Pageview(
                    site_id=site.id,
                    agency_id=site.agency_id,
                    visitor_id=event.visitor_id,
                    session_id=event.session_id,
                    page_url=event.page_url,
                    referrer=event.referrer,
                    ip_hash=ip_hash,
                    user_agent=event.user_agent,
                    utm_source=event.utm_source,
                    utm_medium=event.utm_medium,
                    utm_campaign=event.utm_campaign,
                    utm_content=event.utm_content,
                    utm_term=event.utm_term,
                    gclid=event.gclid,
                    fbclid=event.fbclid,
                    fingerprint=event.fingerprint,
                    extra_params=event.extra,
                )
                db.add(pageview)
                await db.flush()

                if event.event_type in ("form_submit", "track") and event.form_data:
                    await process_lead(db, site, pageview, event, client_ip=client_ip)

                await db.commit()
                return  # success — exit retry loop

            except Exception as exc:
                last_error = exc
                await db.rollback()
                if attempt < _MAX_RETRIES:
                    delay = _RETRY_DELAYS[attempt - 1]
                    logger.warning(
                        "Event processing attempt %d/%d failed (pixel=%s, type=%s): %s — retrying in %ds",
                        attempt, _MAX_RETRIES, event.pixel_id, event.event_type, exc, delay,
                    )
                    await asyncio.sleep(delay)

    # All retries exhausted — structured dead-letter log for investigation
    logger.error(
        "EVENT_DEAD_LETTER: All %d attempts failed | pixel_id=%s | event_type=%s | "
        "visitor_id=%s | error=%s",
        _MAX_RETRIES,
        event.pixel_id,
        event.event_type,
        event.visitor_id,
        last_error,
    )


@router.post("/event", response_model=EventResponse, status_code=202)
async def ingest_event(
    event: EventPayload,
    request: Request,
    background_tasks: BackgroundTasks,
):
    client_ip = request.headers.get("x-forwarded-for", "").split(",")[0].strip() or (
        request.client.host if request.client else "unknown"
    )
    ip_hash = hash_ip(client_ip)
    background_tasks.add_task(_process_event, event, client_ip, ip_hash)
    return EventResponse(status="accepted")
