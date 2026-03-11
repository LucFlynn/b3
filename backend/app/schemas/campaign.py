from typing import Optional

from pydantic import BaseModel


class CampaignRow(BaseModel):
    campaign_name: Optional[str] = None
    ad_group_name: Optional[str] = None
    spend: float
    clicks: int
    google_reported: int
    epi_verified: int
    junk: int
    real_cpl: Optional[float] = None


class CampaignPerformanceResponse(BaseModel):
    total_spend: float
    total_google_reported: int
    total_epi_verified: int
    total_junk: int
    discrepancy_pct: Optional[float] = None
    campaigns: list[CampaignRow]
