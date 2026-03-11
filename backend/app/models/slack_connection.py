"""Slack workspace connections — stores bot tokens per user."""

import uuid
from datetime import datetime, timezone

import sqlalchemy as sa
from sqlalchemy import String, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class SlackConnection(Base):
    __tablename__ = "slack_connections"

    id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)  # Clerk user ID
    workspace_id: Mapped[str | None] = mapped_column(String(50))  # Slack team ID
    workspace_name: Mapped[str | None] = mapped_column(String(255))
    channel_id: Mapped[str | None] = mapped_column(String(50))  # Default channel for notifications
    channel_name: Mapped[str | None] = mapped_column(String(255))
    bot_token_encrypted: Mapped[str | None] = mapped_column(Text)  # xoxb-... token
    bot_user_id: Mapped[str | None] = mapped_column(String(50))
    connected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(20), default="active")
