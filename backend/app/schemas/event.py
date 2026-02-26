from typing import Optional
from pydantic import BaseModel


class EventPayload(BaseModel):
    pixel_id: str
    event_type: str  # pageview, form_submit, track
    visitor_id: str
    session_id: str
    page_url: str
    referrer: Optional[str] = None
    user_agent: Optional[str] = None
    fingerprint: Optional[str] = None
    timestamp: Optional[int] = None

    # URL params
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    utm_content: Optional[str] = None
    utm_term: Optional[str] = None
    gclid: Optional[str] = None
    fbclid: Optional[str] = None

    # Form data (for form_submit / track events)
    form_id: Optional[str] = None
    form_action: Optional[str] = None
    form_data: Optional[dict] = None

    # Bot detection signals
    honeypot_value: Optional[str] = None
    form_fill_time_ms: Optional[int] = None

    # Extra
    extra: Optional[dict] = None


class EventResponse(BaseModel):
    status: str = "accepted"
    event_id: Optional[str] = None
