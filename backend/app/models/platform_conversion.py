import uuid
from datetime import datetime, date, timezone

import sqlalchemy as sa
from sqlalchemy import String, DateTime, ForeignKey, Date, Integer, Float

from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class PlatformConversion(Base):
    __tablename__ = "platform_conversions"

    id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    site_id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, ForeignKey("sites.id"), nullable=False)
    agency_id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, ForeignKey("agencies.id"), nullable=False)
    platform: Mapped[str] = mapped_column(String(50), nullable=False)  # google_ads, meta_ads
    campaign_id: Mapped[str | None] = mapped_column(String(255))
    campaign_name: Mapped[str | None] = mapped_column(String(255))
    ad_group_id: Mapped[str | None] = mapped_column(String(255))
    ad_group_name: Mapped[str | None] = mapped_column(String(255))
    conversion_action: Mapped[str | None] = mapped_column(String(255))
    conversions_reported: Mapped[int] = mapped_column(Integer, default=0)
    clicks: Mapped[int] = mapped_column(Integer, default=0)
    impressions: Mapped[int] = mapped_column(Integer, default=0)
    spend: Mapped[float] = mapped_column(Float, default=0.0)
    report_date: Mapped[date] = mapped_column(Date, nullable=False)
    pulled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
