"""Initial schema: all tables for UPS pricing intelligence tool.

Revision ID: 001
Revises:
Create Date: 2026-02-19
"""

from alembic import op
import sqlalchemy as sa

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "stores",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("store_number", sa.String(), nullable=False, unique=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("address", sa.String()),
        sa.Column("city", sa.String()),
        sa.Column("state", sa.String()),
        sa.Column("phone", sa.String()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("email", sa.String(), nullable=False, unique=True),
        sa.Column("full_name", sa.String(), nullable=False),
        sa.Column("hashed_password", sa.String(), nullable=False),
        sa.Column("role", sa.String(), nullable=False, server_default="staff"),
        sa.Column("store_id", sa.Integer(), sa.ForeignKey("stores.id")),
        sa.Column("is_active", sa.Boolean(), server_default="1"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        "upload_batches",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("store_id", sa.Integer(), sa.ForeignKey("stores.id"), nullable=False),
        sa.Column("uploaded_by", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("filename", sa.String(), nullable=False),
        sa.Column("row_count", sa.Integer()),
        sa.Column("status", sa.String(), server_default="pending"),
        sa.Column("error_message", sa.String()),
        sa.Column("date_range_start", sa.Date()),
        sa.Column("date_range_end", sa.Date()),
        sa.Column("uploaded_at", sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        "transactions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("store_id", sa.Integer(), sa.ForeignKey("stores.id"), nullable=False),
        sa.Column("upload_batch_id", sa.Integer(), sa.ForeignKey("upload_batches.id")),
        sa.Column("connectsuite_txn_id", sa.String()),
        sa.Column("transaction_date", sa.Date(), nullable=False),
        sa.Column("transaction_time", sa.String()),
        sa.Column("service_category", sa.String(), nullable=False),
        sa.Column("service_code", sa.String()),
        sa.Column("service_description", sa.String()),
        sa.Column("quantity", sa.Numeric(10, 3)),
        sa.Column("unit_price", sa.Numeric(10, 4)),
        sa.Column("extended_price", sa.Numeric(10, 4)),
        sa.Column("discount_amount", sa.Numeric(10, 4), server_default="0"),
        sa.Column("net_revenue", sa.Numeric(10, 4)),
        sa.Column("carrier", sa.String()),
        sa.Column("service_level", sa.String()),
        sa.Column("weight_lbs", sa.Numeric(8, 3)),
        sa.Column("zone", sa.Integer()),
        sa.Column("destination_state", sa.String()),
        sa.Column("customer_ref", sa.String()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index(
        "ix_txn_store_date_service",
        "transactions",
        ["store_id", "transaction_date", "service_category"],
    )

    op.create_table(
        "service_taxonomy",
        sa.Column("service_code", sa.String(), primary_key=True),
        sa.Column("service_category", sa.String(), nullable=False),
        sa.Column("service_name", sa.String(), nullable=False),
        sa.Column("unit", sa.String()),
        sa.Column("description", sa.String()),
        sa.Column("connectsuite_codes", sa.String()),
    )

    op.create_table(
        "our_prices",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("store_id", sa.Integer(), sa.ForeignKey("stores.id"), nullable=False),
        sa.Column("service_code", sa.String(), nullable=False),
        sa.Column("service_category", sa.String(), nullable=False),
        sa.Column("service_name", sa.String(), nullable=False),
        sa.Column("unit", sa.String()),
        sa.Column("price", sa.Numeric(10, 4), nullable=False),
        sa.Column("effective_date", sa.Date(), nullable=False),
        sa.Column("notes", sa.String()),
        sa.Column("updated_by", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
        sa.UniqueConstraint("store_id", "service_code", "effective_date", name="uq_our_price"),
    )

    op.create_table(
        "competitor_prices",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("competitor_name", sa.String(), nullable=False),
        sa.Column("service_code", sa.String(), nullable=False),
        sa.Column("service_category", sa.String(), nullable=False),
        sa.Column("service_name", sa.String(), nullable=False),
        sa.Column("unit", sa.String()),
        sa.Column("price", sa.Numeric(10, 4), nullable=False),
        sa.Column("effective_date", sa.Date(), nullable=False),
        sa.Column("source_notes", sa.String()),
        sa.Column("entered_by", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
        sa.UniqueConstraint("competitor_name", "service_code", "effective_date", name="uq_competitor_price"),
    )

    op.create_table(
        "pricing_gaps",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("store_id", sa.Integer(), sa.ForeignKey("stores.id"), nullable=False),
        sa.Column("service_code", sa.String(), nullable=False),
        sa.Column("service_category", sa.String(), nullable=False),
        sa.Column("service_name", sa.String()),
        sa.Column("our_price", sa.Numeric(10, 4)),
        sa.Column("competitor_name", sa.String(), nullable=False),
        sa.Column("competitor_price", sa.Numeric(10, 4)),
        sa.Column("gap_amount", sa.Numeric(10, 4)),
        sa.Column("gap_pct", sa.Numeric(6, 4)),
        sa.Column("direction", sa.String()),
        sa.Column("transaction_volume", sa.Integer()),
        sa.Column("revenue_impact", sa.Numeric(12, 4)),
        sa.Column("analysis_date", sa.Date(), nullable=False),
        sa.Column("period_start", sa.Date()),
        sa.Column("period_end", sa.Date()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        "upsell_opportunities",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("store_id", sa.Integer(), sa.ForeignKey("stores.id"), nullable=False),
        sa.Column("rule_id", sa.String(), nullable=False),
        sa.Column("opportunity_type", sa.String()),
        sa.Column("trigger_service", sa.String()),
        sa.Column("trigger_category", sa.String()),
        sa.Column("recommended_service", sa.String()),
        sa.Column("recommended_service_code", sa.String()),
        sa.Column("price_delta", sa.Numeric(10, 4)),
        sa.Column("conversion_rate_est", sa.Numeric(6, 4)),
        sa.Column("monthly_volume", sa.Integer()),
        sa.Column("monthly_impact_est", sa.Numeric(12, 4)),
        sa.Column("priority", sa.String()),
        sa.Column("staff_script", sa.String()),
        sa.Column("is_dismissed", sa.Boolean(), server_default="0"),
        sa.Column("dismissed_by", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("dismissed_at", sa.DateTime()),
        sa.Column("analysis_date", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("upsell_opportunities")
    op.drop_table("pricing_gaps")
    op.drop_table("competitor_prices")
    op.drop_table("our_prices")
    op.drop_table("service_taxonomy")
    op.drop_index("ix_txn_store_date_service", table_name="transactions")
    op.drop_table("transactions")
    op.drop_table("upload_batches")
    op.drop_table("users")
    op.drop_table("stores")
