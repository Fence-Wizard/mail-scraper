"""Add procurement webapp core tables

Revision ID: 20260224_0004
Revises: 20260224_0003
Create Date: 2026-02-24
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260224_0004"
down_revision: Union[str, None] = "20260224_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "app_users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=50), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index(op.f("ix_app_users_email"), "app_users", ["email"], unique=True)
    op.create_index(op.f("ix_app_users_role"), "app_users", ["role"], unique=False)
    op.create_index(op.f("ix_app_users_is_active"), "app_users", ["is_active"], unique=False)

    op.create_table(
        "rfq_quotes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("job_number", sa.String(length=100), nullable=True),
        sa.Column("vendor_reference_id", sa.Integer(), nullable=True),
        sa.Column("requested_by_actor_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("request_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("quote_amount", sa.Float(), nullable=True),
        sa.Column("currency", sa.String(length=20), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("source_task_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["vendor_reference_id"], ["vendor_references.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["requested_by_actor_id"], ["actors.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["source_task_id"], ["tasks.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_rfq_quotes_job_number"), "rfq_quotes", ["job_number"], unique=False)
    op.create_index(op.f("ix_rfq_quotes_vendor_reference_id"), "rfq_quotes", ["vendor_reference_id"], unique=False)
    op.create_index(op.f("ix_rfq_quotes_requested_by_actor_id"), "rfq_quotes", ["requested_by_actor_id"], unique=False)
    op.create_index(op.f("ix_rfq_quotes_status"), "rfq_quotes", ["status"], unique=False)
    op.create_index(op.f("ix_rfq_quotes_request_date"), "rfq_quotes", ["request_date"], unique=False)
    op.create_index(op.f("ix_rfq_quotes_source_task_id"), "rfq_quotes", ["source_task_id"], unique=False)

    op.create_table(
        "purchase_orders",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("po_number", sa.String(length=120), nullable=False),
        sa.Column("job_number", sa.String(length=100), nullable=True),
        sa.Column("vendor_reference_id", sa.Integer(), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("approved_by_user_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("total_amount", sa.Float(), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_task_id", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["vendor_reference_id"], ["vendor_references.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["app_users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["approved_by_user_id"], ["app_users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["source_task_id"], ["tasks.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("po_number"),
    )
    op.create_index(op.f("ix_purchase_orders_po_number"), "purchase_orders", ["po_number"], unique=True)
    op.create_index(op.f("ix_purchase_orders_job_number"), "purchase_orders", ["job_number"], unique=False)
    op.create_index(op.f("ix_purchase_orders_vendor_reference_id"), "purchase_orders", ["vendor_reference_id"], unique=False)
    op.create_index(op.f("ix_purchase_orders_created_by_user_id"), "purchase_orders", ["created_by_user_id"], unique=False)
    op.create_index(op.f("ix_purchase_orders_approved_by_user_id"), "purchase_orders", ["approved_by_user_id"], unique=False)
    op.create_index(op.f("ix_purchase_orders_status"), "purchase_orders", ["status"], unique=False)
    op.create_index(op.f("ix_purchase_orders_total_amount"), "purchase_orders", ["total_amount"], unique=False)
    op.create_index(op.f("ix_purchase_orders_approved_at"), "purchase_orders", ["approved_at"], unique=False)
    op.create_index(op.f("ix_purchase_orders_issued_at"), "purchase_orders", ["issued_at"], unique=False)
    op.create_index(op.f("ix_purchase_orders_source_task_id"), "purchase_orders", ["source_task_id"], unique=False)

    op.create_table(
        "order_confirmations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("purchase_order_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_document_id", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["purchase_order_id"], ["purchase_orders.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_document_id"], ["documents.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_order_confirmations_purchase_order_id"), "order_confirmations", ["purchase_order_id"], unique=False)
    op.create_index(op.f("ix_order_confirmations_status"), "order_confirmations", ["status"], unique=False)
    op.create_index(op.f("ix_order_confirmations_confirmed_at"), "order_confirmations", ["confirmed_at"], unique=False)
    op.create_index(op.f("ix_order_confirmations_source_document_id"), "order_confirmations", ["source_document_id"], unique=False)

    op.create_table(
        "invoice_matches",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("purchase_order_id", sa.Integer(), nullable=True),
        sa.Column("match_status", sa.String(length=50), nullable=False),
        sa.Column("variance_amount", sa.Float(), nullable=True),
        sa.Column("exception_reason", sa.Text(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["purchase_order_id"], ["purchase_orders.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("document_id"),
    )
    op.create_index(op.f("ix_invoice_matches_document_id"), "invoice_matches", ["document_id"], unique=True)
    op.create_index(op.f("ix_invoice_matches_purchase_order_id"), "invoice_matches", ["purchase_order_id"], unique=False)
    op.create_index(op.f("ix_invoice_matches_match_status"), "invoice_matches", ["match_status"], unique=False)
    op.create_index(op.f("ix_invoice_matches_resolved_at"), "invoice_matches", ["resolved_at"], unique=False)

    op.create_table(
        "vendor_kpis",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("vendor_reference_id", sa.Integer(), nullable=False),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("on_time_rate", sa.Float(), nullable=True),
        sa.Column("avg_cycle_days", sa.Float(), nullable=True),
        sa.Column("exception_rate", sa.Float(), nullable=True),
        sa.Column("total_spend", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["vendor_reference_id"], ["vendor_references.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_vendor_kpis_vendor_reference_id"), "vendor_kpis", ["vendor_reference_id"], unique=False)
    op.create_index(op.f("ix_vendor_kpis_period_start"), "vendor_kpis", ["period_start"], unique=False)
    op.create_index(op.f("ix_vendor_kpis_period_end"), "vendor_kpis", ["period_end"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_vendor_kpis_period_end"), table_name="vendor_kpis")
    op.drop_index(op.f("ix_vendor_kpis_period_start"), table_name="vendor_kpis")
    op.drop_index(op.f("ix_vendor_kpis_vendor_reference_id"), table_name="vendor_kpis")
    op.drop_table("vendor_kpis")

    op.drop_index(op.f("ix_invoice_matches_resolved_at"), table_name="invoice_matches")
    op.drop_index(op.f("ix_invoice_matches_match_status"), table_name="invoice_matches")
    op.drop_index(op.f("ix_invoice_matches_purchase_order_id"), table_name="invoice_matches")
    op.drop_index(op.f("ix_invoice_matches_document_id"), table_name="invoice_matches")
    op.drop_table("invoice_matches")

    op.drop_index(op.f("ix_order_confirmations_source_document_id"), table_name="order_confirmations")
    op.drop_index(op.f("ix_order_confirmations_confirmed_at"), table_name="order_confirmations")
    op.drop_index(op.f("ix_order_confirmations_status"), table_name="order_confirmations")
    op.drop_index(op.f("ix_order_confirmations_purchase_order_id"), table_name="order_confirmations")
    op.drop_table("order_confirmations")

    op.drop_index(op.f("ix_purchase_orders_source_task_id"), table_name="purchase_orders")
    op.drop_index(op.f("ix_purchase_orders_issued_at"), table_name="purchase_orders")
    op.drop_index(op.f("ix_purchase_orders_approved_at"), table_name="purchase_orders")
    op.drop_index(op.f("ix_purchase_orders_total_amount"), table_name="purchase_orders")
    op.drop_index(op.f("ix_purchase_orders_status"), table_name="purchase_orders")
    op.drop_index(op.f("ix_purchase_orders_approved_by_user_id"), table_name="purchase_orders")
    op.drop_index(op.f("ix_purchase_orders_created_by_user_id"), table_name="purchase_orders")
    op.drop_index(op.f("ix_purchase_orders_vendor_reference_id"), table_name="purchase_orders")
    op.drop_index(op.f("ix_purchase_orders_job_number"), table_name="purchase_orders")
    op.drop_index(op.f("ix_purchase_orders_po_number"), table_name="purchase_orders")
    op.drop_table("purchase_orders")

    op.drop_index(op.f("ix_rfq_quotes_source_task_id"), table_name="rfq_quotes")
    op.drop_index(op.f("ix_rfq_quotes_request_date"), table_name="rfq_quotes")
    op.drop_index(op.f("ix_rfq_quotes_status"), table_name="rfq_quotes")
    op.drop_index(op.f("ix_rfq_quotes_requested_by_actor_id"), table_name="rfq_quotes")
    op.drop_index(op.f("ix_rfq_quotes_vendor_reference_id"), table_name="rfq_quotes")
    op.drop_index(op.f("ix_rfq_quotes_job_number"), table_name="rfq_quotes")
    op.drop_table("rfq_quotes")

    op.drop_index(op.f("ix_app_users_is_active"), table_name="app_users")
    op.drop_index(op.f("ix_app_users_role"), table_name="app_users")
    op.drop_index(op.f("ix_app_users_email"), table_name="app_users")
    op.drop_table("app_users")
