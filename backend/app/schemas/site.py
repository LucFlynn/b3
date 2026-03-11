from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class SiteCreate(BaseModel):
    domain: str
    name: str
    google_ads_customer_id: Optional[str] = None
    meta_ads_account_id: Optional[str] = None


class SiteUpdate(BaseModel):
    google_ads_customer_id: Optional[str] = None
    meta_ads_account_id: Optional[str] = None


class SiteResponse(BaseModel):
    id: UUID
    agency_id: UUID
    domain: str
    name: str
    pixel_id: str
    google_ads_customer_id: Optional[str] = None
    meta_ads_account_id: Optional[str] = None
    pixel_verified: bool
    created_at: datetime
    pixel_snippet: Optional[str] = None
    leads_count: int = 0

    model_config = {"from_attributes": True}


class ComparisonResponse(BaseModel):
    site_id: UUID
    platform: str
    report_date: str
    platform_conversions: int
    platform_clicks: int
    platform_spend: float
    epi_total_leads: int
    epi_verified_leads: int
    epi_junk_leads: int
    discrepancy_pct: Optional[float] = None
    cost_per_verified_lead: Optional[float] = None
    last_synced: Optional[str] = None

    model_config = {"from_attributes": True}
