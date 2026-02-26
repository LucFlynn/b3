import uuid
from datetime import datetime, date, timezone

import sqlalchemy as sa
from sqlalchemy import String, DateTime, ForeignKey, Date, Integer, Float

from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AttributionComparison(Base):
    __tablename__ = "attribution_comparisons"

    id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    site_id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, ForeignKey("sites.id"), nullable=False)
    agency_id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, ForeignKey("agencies.id"), nullable=False)
    platform: Mapped[str] = mapped_column(String(50), nullable=False)
    report_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Platform-reported numbers
    platform_conversions: Mapped[int] = mapped_column(Integer, default=0)
    platform_clicks: Mapped[int] = mapped_column(Integer, default=0)
    platform_spend: Mapped[float] = mapped_column(Float, default=0.0)

    # EPI ground truth
    epi_total_leads: Mapped[int] = mapped_column(Integer, default=0)
    epi_verified_leads: Mapped[int] = mapped_column(Integer, default=0)
    epi_junk_leads: Mapped[int] = mapped_column(Integer, default=0)

    # Comparison metrics
    discrepancy_pct: Mapped[float | None] = mapped_column(Float)  # (platform - epi_verified) / platform * 100
    cost_per_verified_lead: Mapped[float | None] = mapped_column(Float)

    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
