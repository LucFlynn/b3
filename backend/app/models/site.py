import uuid
from datetime import datetime, timezone

import sqlalchemy as sa
from sqlalchemy import String, DateTime, ForeignKey, Boolean

from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Site(Base):
    __tablename__ = "sites"

    id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    agency_id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, ForeignKey("agencies.id"), nullable=False)
    domain: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    pixel_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    google_ads_customer_id: Mapped[str | None] = mapped_column(String(255))
    meta_ads_account_id: Mapped[str | None] = mapped_column(String(255))
    pixel_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    agency = relationship("Agency", back_populates="sites")
    pageviews = relationship("Pageview", back_populates="site")
    leads = relationship("Lead", back_populates="site")
