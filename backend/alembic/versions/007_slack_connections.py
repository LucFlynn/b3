"""Add slack_connections table

Revision ID: 007
Revises: 006
Create Date: 2026-03-08
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "slack_connections",
        sa.Column("id", sa.Uuid, primary_key=True),
        sa.Column("user_id", sa.String(255), nullable=False, index=True),
        sa.Column("workspace_id", sa.String(50), nullable=True),
        sa.Column("workspace_name", sa.String(255), nullable=True),
        sa.Column("channel_id", sa.String(50), nullable=True),
        sa.Column("channel_name", sa.String(255), nullable=True),
        sa.Column("bot_token_encrypted", sa.Text, nullable=True),
        sa.Column("bot_user_id", sa.String(50), nullable=True),
        sa.Column("connected_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(20), server_default="active"),
    )


def downgrade() -> None:
    op.drop_table("slack_connections")
