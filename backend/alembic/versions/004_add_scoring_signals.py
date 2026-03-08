"""Add scoring_signals JSONB column to leads

Revision ID: 004
Revises: 003
Create Date: 2026-03-05
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("leads", sa.Column("scoring_signals", postgresql.JSONB(), nullable=True))


def downgrade() -> None:
    op.drop_column("leads", "scoring_signals")
