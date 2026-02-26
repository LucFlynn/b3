import uuid
from datetime import datetime, timezone

import sqlalchemy as sa
from sqlalchemy import String, DateTime

from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Agency(Base):
    __tablename__ = "agencies"

    id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    google_ads_refresh_token: Mapped[str | None] = mapped_column(String(512))
    meta_ads_access_token: Mapped[str | None] = mapped_column(String(512))
    slack_workspace_id: Mapped[str | None] = mapped_column(String(255))
    slack_channel_id: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    users = relationship("User", back_populates="agency")
    sites = relationship("Site", back_populates="agency")
