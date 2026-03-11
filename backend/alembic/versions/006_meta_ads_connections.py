"""Add meta_ads_connections table

Revision ID: 006
Revises: 005
Create Date: 2026-03-08
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "meta_ads_connections",
        sa.Column("id", sa.Uuid, primary_key=True),
        sa.Column("user_id", sa.String(255), nullable=False, index=True),
        sa.Column("meta_ads_account_id", sa.String(50), nullable=True),
        sa.Column("account_name", sa.String(255), nullable=True),
        sa.Column("access_token_encrypted", sa.Text, nullable=True),
        sa.Column("token_expiry", sa.DateTime(timezone=True), nullable=True),
        sa.Column("connected_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(20), server_default="active"),
    )


def downgrade() -> None:
    op.drop_table("meta_ads_connections")
