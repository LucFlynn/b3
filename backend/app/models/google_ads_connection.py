"""Google Ads OAuth connections — stores encrypted tokens per user."""

import uuid
from datetime import datetime, timezone

import sqlalchemy as sa
from sqlalchemy import String, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class GoogleAdsConnection(Base):
    __tablename__ = "google_ads_connections"

    id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)  # Clerk user ID
    google_ads_customer_id: Mapped[str | None] = mapped_column(String(50))  # e.g. 123-456-7890
    account_name: Mapped[str | None] = mapped_column(String(255))
    access_token_encrypted: Mapped[str | None] = mapped_column(Text)
    refresh_token_encrypted: Mapped[str | None] = mapped_column(Text)
    token_expiry: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    connected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(20), default="active")  # active, revoked, expired
