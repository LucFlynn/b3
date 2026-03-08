"""Add Clerk/Stripe fields to users, add delivery_channels table

Revision ID: 003
Revises: 002
Create Date: 2026-03-05
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add Clerk/Stripe/usage columns to users
    op.add_column("users", sa.Column("clerk_user_id", sa.String(255), nullable=True))
    op.add_column("users", sa.Column("plan", sa.String(20), nullable=False, server_default="free"))
    op.add_column("users", sa.Column("usage_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("users", sa.Column("usage_limit", sa.Integer(), nullable=False, server_default="100"))
    op.add_column("users", sa.Column("stripe_customer_id", sa.String(255), nullable=True))
    op.add_column("users", sa.Column("stripe_subscription_id", sa.String(255), nullable=True))
    op.create_unique_constraint("uq_users_clerk_user_id", "users", ["clerk_user_id"])
    op.create_unique_constraint("uq_users_stripe_customer_id", "users", ["stripe_customer_id"])

    # Make hashed_password nullable (Clerk handles auth now)
    op.alter_column("users", "hashed_password", nullable=True)

    # Create delivery_channels table
    op.create_table(
        "delivery_channels",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("site_id", sa.Uuid(), nullable=False),
        sa.Column("channel_type", sa.String(20), nullable=False),
        sa.Column("config", postgresql.JSONB(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["site_id"], ["sites.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("delivery_channels")
    op.drop_constraint("uq_users_stripe_customer_id", "users", type_="unique")
    op.drop_constraint("uq_users_clerk_user_id", "users", type_="unique")
    op.drop_column("users", "stripe_subscription_id")
    op.drop_column("users", "stripe_customer_id")
    op.drop_column("users", "usage_limit")
    op.drop_column("users", "usage_count")
    op.drop_column("users", "plan")
    op.drop_column("users", "clerk_user_id")
    op.alter_column("users", "hashed_password", nullable=False)
