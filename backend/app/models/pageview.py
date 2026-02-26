import uuid
from datetime import datetime, timezone

import sqlalchemy as sa
from sqlalchemy import String, DateTime, ForeignKey, Text, Integer

from sqlalchemy import JSON as JSONB  # Use generic JSON for SQLite compat in tests
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Pageview(Base):
    __tablename__ = "pageviews"

    id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    site_id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, ForeignKey("sites.id"), nullable=False)
    agency_id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, ForeignKey("agencies.id"), nullable=False)
    visitor_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    session_id: Mapped[str] = mapped_column(String(64), nullable=False)
    page_url: Mapped[str] = mapped_column(Text, nullable=False)
    referrer: Mapped[str | None] = mapped_column(Text)
    ip_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    user_agent: Mapped[str | None] = mapped_column(Text)
    utm_source: Mapped[str | None] = mapped_column(String(255))
    utm_medium: Mapped[str | None] = mapped_column(String(255))
    utm_campaign: Mapped[str | None] = mapped_column(String(255))
    utm_content: Mapped[str | None] = mapped_column(String(255))
    utm_term: Mapped[str | None] = mapped_column(String(255))
    gclid: Mapped[str | None] = mapped_column(String(255), index=True)
    fbclid: Mapped[str | None] = mapped_column(String(255), index=True)
    fingerprint: Mapped[str | None] = mapped_column(String(64))
    extra_params: Mapped[dict | None] = mapped_column(JSONB)
    time_on_page: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    site = relationship("Site", back_populates="pageviews")
