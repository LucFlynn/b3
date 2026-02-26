"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-02-26
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "agencies",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(255), nullable=False),
        sa.Column("google_ads_refresh_token", sa.String(512), nullable=True),
        sa.Column("meta_ads_access_token", sa.String(512), nullable=True),
        sa.Column("slack_workspace_id", sa.String(255), nullable=True),
        sa.Column("slack_channel_id", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("agency_id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("role", sa.String(50), nullable=False),
        sa.Column("api_key_hash", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["agency_id"], ["agencies.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("api_key_hash"),
    )

    op.create_table(
        "sites",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("agency_id", sa.Uuid(), nullable=False),
        sa.Column("domain", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("pixel_id", sa.String(64), nullable=False),
        sa.Column("google_ads_customer_id", sa.String(255), nullable=True),
        sa.Column("meta_ads_account_id", sa.String(255), nullable=True),
        sa.Column("pixel_verified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["agency_id"], ["agencies.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("pixel_id"),
    )

    op.create_table(
        "pageviews",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("site_id", sa.Uuid(), nullable=False),
        sa.Column("agency_id", sa.Uuid(), nullable=False),
        sa.Column("visitor_id", sa.String(64), nullable=False),
        sa.Column("session_id", sa.String(64), nullable=False),
        sa.Column("page_url", sa.Text(), nullable=False),
        sa.Column("referrer", sa.Text(), nullable=True),
        sa.Column("ip_hash", sa.String(64), nullable=False),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("utm_source", sa.String(255), nullable=True),
        sa.Column("utm_medium", sa.String(255), nullable=True),
        sa.Column("utm_campaign", sa.String(255), nullable=True),
        sa.Column("utm_content", sa.String(255), nullable=True),
        sa.Column("utm_term", sa.String(255), nullable=True),
        sa.Column("gclid", sa.String(255), nullable=True),
        sa.Column("fbclid", sa.String(255), nullable=True),
        sa.Column("fingerprint", sa.String(64), nullable=True),
        sa.Column("extra_params", postgresql.JSONB(), nullable=True),
        sa.Column("time_on_page", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["agency_id"], ["agencies.id"]),
        sa.ForeignKeyConstraint(["site_id"], ["sites.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_pageviews_visitor_id", "pageviews", ["visitor_id"])
    op.create_index("ix_pageviews_gclid", "pageviews", ["gclid"])
    op.create_index("ix_pageviews_fbclid", "pageviews", ["fbclid"])

    op.create_table(
        "leads",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("site_id", sa.Uuid(), nullable=False),
        sa.Column("agency_id", sa.Uuid(), nullable=False),
        sa.Column("pageview_id", sa.Uuid(), nullable=True),
        sa.Column("email_encrypted", sa.Text(), nullable=True),
        sa.Column("email_hash", sa.String(64), nullable=True),
        sa.Column("phone_encrypted", sa.Text(), nullable=True),
        sa.Column("phone_hash", sa.String(64), nullable=True),
        sa.Column("name_encrypted", sa.Text(), nullable=True),
        sa.Column("visitor_id", sa.String(64), nullable=False),
        sa.Column("ip_hash", sa.String(64), nullable=False),
        sa.Column("email_valid", sa.String(20), nullable=True),
        sa.Column("phone_valid", sa.String(20), nullable=True),
        sa.Column("is_bot", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("honeypot_triggered", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("form_fill_time_ms", sa.Integer(), nullable=True),
        sa.Column("quality_score", sa.Integer(), nullable=True),
        sa.Column("quality_label", sa.String(20), nullable=True),
        sa.Column("attribution_tier", sa.String(20), nullable=True),
        sa.Column("gclid", sa.String(255), nullable=True),
        sa.Column("fbclid", sa.String(255), nullable=True),
        sa.Column("utm_source", sa.String(255), nullable=True),
        sa.Column("utm_medium", sa.String(255), nullable=True),
        sa.Column("utm_campaign", sa.String(255), nullable=True),
        sa.Column("is_duplicate", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("form_id", sa.String(255), nullable=True),
        sa.Column("form_action", sa.Text(), nullable=True),
        sa.Column("extra_fields", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["agency_id"], ["agencies.id"]),
        sa.ForeignKeyConstraint(["pageview_id"], ["pageviews.id"]),
        sa.ForeignKeyConstraint(["site_id"], ["sites.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_leads_email_hash", "leads", ["email_hash"])
    op.create_index("ix_leads_phone_hash", "leads", ["phone_hash"])
    op.create_index("ix_leads_visitor_id", "leads", ["visitor_id"])
    op.create_index("ix_leads_gclid", "leads", ["gclid"])
    op.create_index("ix_leads_fbclid", "leads", ["fbclid"])

    op.create_table(
        "platform_conversions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("site_id", sa.Uuid(), nullable=False),
        sa.Column("agency_id", sa.Uuid(), nullable=False),
        sa.Column("platform", sa.String(50), nullable=False),
        sa.Column("campaign_id", sa.String(255), nullable=True),
        sa.Column("campaign_name", sa.String(255), nullable=True),
        sa.Column("ad_group_id", sa.String(255), nullable=True),
        sa.Column("ad_group_name", sa.String(255), nullable=True),
        sa.Column("conversion_action", sa.String(255), nullable=True),
        sa.Column("conversions_reported", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("clicks", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("impressions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("spend", sa.Float(), nullable=False, server_default="0"),
        sa.Column("report_date", sa.Date(), nullable=False),
        sa.Column("pulled_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["agency_id"], ["agencies.id"]),
        sa.ForeignKeyConstraint(["site_id"], ["sites.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "attribution_comparisons",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("site_id", sa.Uuid(), nullable=False),
        sa.Column("agency_id", sa.Uuid(), nullable=False),
        sa.Column("platform", sa.String(50), nullable=False),
        sa.Column("report_date", sa.Date(), nullable=False),
        sa.Column("platform_conversions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("platform_clicks", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("platform_spend", sa.Float(), nullable=False, server_default="0"),
        sa.Column("epi_total_leads", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("epi_verified_leads", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("epi_junk_leads", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("discrepancy_pct", sa.Float(), nullable=True),
        sa.Column("cost_per_verified_lead", sa.Float(), nullable=True),
        sa.Column("computed_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["agency_id"], ["agencies.id"]),
        sa.ForeignKeyConstraint(["site_id"], ["sites.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    # Row-Level Security policies
    for table in ["sites", "pageviews", "leads", "platform_conversions", "attribution_comparisons"]:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(
            f"CREATE POLICY {table}_agency_isolation ON {table} "
            f"USING (agency_id = current_agency_id())"
        )


def downgrade() -> None:
    for table in ["attribution_comparisons", "platform_conversions", "leads", "pageviews", "sites", "users", "agencies"]:
        op.drop_table(table)
