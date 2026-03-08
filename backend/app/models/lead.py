import uuid
from datetime import datetime, timezone

import sqlalchemy as sa
from sqlalchemy import String, DateTime, ForeignKey, Text, Integer, Float, Boolean

from sqlalchemy import JSON as JSONB  # Use generic JSON for SQLite compat in tests
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    site_id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, ForeignKey("sites.id"), nullable=False)
    agency_id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, ForeignKey("agencies.id"), nullable=False)
    pageview_id: Mapped[uuid.UUID | None] = mapped_column(sa.Uuid, ForeignKey("pageviews.id"))

    # PII — encrypted at rest, hash columns for lookups
    email_encrypted: Mapped[str | None] = mapped_column(Text)
    email_hash: Mapped[str | None] = mapped_column(String(64), index=True)
    phone_encrypted: Mapped[str | None] = mapped_column(Text)
    phone_hash: Mapped[str | None] = mapped_column(String(64), index=True)
    name_encrypted: Mapped[str | None] = mapped_column(Text)

    # Visitor tracking
    visitor_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    ip_hash: Mapped[str] = mapped_column(String(64), nullable=False)

    # Validation results
    email_valid: Mapped[str | None] = mapped_column(String(20))  # valid, invalid, catch_all, disposable
    phone_valid: Mapped[str | None] = mapped_column(String(20))  # valid, invalid, voip, mobile, landline

    # Bot detection
    is_bot: Mapped[bool] = mapped_column(Boolean, default=False)
    honeypot_triggered: Mapped[bool] = mapped_column(Boolean, default=False)
    form_fill_time_ms: Mapped[int | None] = mapped_column(Integer)

    # Quality scoring
    quality_score: Mapped[int | None] = mapped_column(Integer)  # 0-100
    quality_label: Mapped[str | None] = mapped_column(String(20))  # verified, likely_real, suspicious, junk

    # Attribution
    attribution_tier: Mapped[str | None] = mapped_column(String(20))  # definitive, high_confidence, probable, unattributed
    gclid: Mapped[str | None] = mapped_column(String(255), index=True)
    fbclid: Mapped[str | None] = mapped_column(String(255), index=True)
    utm_source: Mapped[str | None] = mapped_column(String(255))
    utm_medium: Mapped[str | None] = mapped_column(String(255))
    utm_campaign: Mapped[str | None] = mapped_column(String(255))

    # Dedup
    is_duplicate: Mapped[bool] = mapped_column(Boolean, default=False)

    # Form metadata
    page_url: Mapped[str | None] = mapped_column(Text)
    form_id: Mapped[str | None] = mapped_column(String(255))
    form_action: Mapped[str | None] = mapped_column(Text)
    extra_fields: Mapped[dict | None] = mapped_column(JSONB)
    scoring_signals: Mapped[dict | None] = mapped_column(JSONB)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    site = relationship("Site", back_populates="leads")
