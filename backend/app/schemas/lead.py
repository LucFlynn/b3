from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class LeadResponse(BaseModel):
    id: UUID
    site_id: UUID
    visitor_id: str
    email_valid: Optional[str] = None
    phone_valid: Optional[str] = None
    is_bot: bool
    quality_score: Optional[int] = None
    quality_label: Optional[str] = None
    attribution_tier: Optional[str] = None
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    gclid: Optional[str] = None
    fbclid: Optional[str] = None
    is_duplicate: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class LeadDetailResponse(BaseModel):
    id: UUID
    site_id: UUID
    visitor_id: str
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    email_valid: Optional[str] = None
    phone_valid: Optional[str] = None
    is_bot: bool
    quality_score: Optional[int] = None
    quality_label: Optional[str] = None
    attribution_tier: Optional[str] = None
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    gclid: Optional[str] = None
    fbclid: Optional[str] = None
    is_duplicate: bool
    form_id: Optional[str] = None
    form_action: Optional[str] = None
    extra_fields: Optional[dict] = None
    created_at: datetime


class LeadStatsResponse(BaseModel):
    total_leads: int
    verified: int
    likely_real: int
    suspicious: int
    junk: int
    duplicates: int
    attributed: int
    unattributed: int
    avg_quality_score: Optional[float] = None


class LeadFilters(BaseModel):
    site_id: Optional[UUID] = None
    quality_label: Optional[str] = None
    attribution_tier: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    page: int = 1
    per_page: int = 50
