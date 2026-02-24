"""Phase 1 schema

Revision ID: 20260223_0001
Revises:
Create Date: 2026-02-23
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260223_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "mailboxes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("mailbox_key", sa.String(length=200), nullable=False),
        sa.Column("user_id", sa.String(length=320), nullable=False),
        sa.Column("root_folder_name", sa.String(length=200), nullable=False),
        sa.Column("include_filters", sa.JSON(), nullable=False),
        sa.Column("exclude_filters", sa.JSON(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("mailbox_key"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index("ix_mailboxes_mailbox_key", "mailboxes", ["mailbox_key"], unique=False)
    op.create_index("ix_mailboxes_user_id", "mailboxes", ["user_id"], unique=False)

    op.create_table(
        "pipeline_runs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("pipeline_name", sa.String(length=100), nullable=False),
        sa.Column("mailbox_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("processed_count", sa.Integer(), nullable=False),
        sa.Column("error_count", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["mailbox_id"], ["mailboxes.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_pipeline_runs_pipeline_name", "pipeline_runs", ["pipeline_name"], unique=False)
    op.create_index("ix_pipeline_runs_mailbox_id", "pipeline_runs", ["mailbox_id"], unique=False)
    op.create_index("ix_pipeline_runs_status", "pipeline_runs", ["status"], unique=False)
    op.create_index("ix_pipeline_runs_started_at", "pipeline_runs", ["started_at"], unique=False)

    op.create_table(
        "folders",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("mailbox_id", sa.Integer(), nullable=False),
        sa.Column("graph_folder_id", sa.String(length=256), nullable=False),
        sa.Column("parent_graph_folder_id", sa.String(length=256), nullable=True),
        sa.Column("display_name", sa.String(length=512), nullable=False),
        sa.Column("path", sa.Text(), nullable=False),
        sa.Column("total_item_count", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["mailbox_id"], ["mailboxes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("mailbox_id", "graph_folder_id", name="uq_folder_mailbox_graph"),
    )
    op.create_index("ix_folders_mailbox_id", "folders", ["mailbox_id"], unique=False)
    op.create_index("ix_folders_graph_folder_id", "folders", ["graph_folder_id"], unique=False)

    op.create_table(
        "messages",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("mailbox_id", sa.Integer(), nullable=False),
        sa.Column("graph_message_id", sa.String(length=256), nullable=False),
        sa.Column("graph_folder_id", sa.String(length=256), nullable=True),
        sa.Column("conversation_id", sa.String(length=256), nullable=True),
        sa.Column("source_sender", sa.String(length=320), nullable=True),
        sa.Column("source_subject", sa.Text(), nullable=True),
        sa.Column("source_received_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("body_preview", sa.Text(), nullable=True),
        sa.Column("has_attachments", sa.Boolean(), nullable=False),
        sa.Column("raw_json", sa.JSON(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["mailbox_id"], ["mailboxes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("mailbox_id", "graph_message_id", name="uq_message_mailbox_graph"),
    )
    op.create_index("ix_messages_mailbox_id", "messages", ["mailbox_id"], unique=False)
    op.create_index("ix_messages_graph_message_id", "messages", ["graph_message_id"], unique=False)
    op.create_index("ix_messages_graph_folder_id", "messages", ["graph_folder_id"], unique=False)
    op.create_index("ix_messages_conversation_id", "messages", ["conversation_id"], unique=False)
    op.create_index("ix_messages_source_sender", "messages", ["source_sender"], unique=False)
    op.create_index("ix_messages_source_received_at", "messages", ["source_received_at"], unique=False)

    op.create_table(
        "attachments",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("mailbox_id", sa.Integer(), nullable=False),
        sa.Column("message_id", sa.Integer(), nullable=True),
        sa.Column("graph_attachment_id", sa.String(length=256), nullable=False),
        sa.Column("graph_message_id", sa.String(length=256), nullable=False),
        sa.Column("name", sa.Text(), nullable=True),
        sa.Column("content_type", sa.String(length=200), nullable=True),
        sa.Column("size_bytes", sa.Integer(), nullable=True),
        sa.Column("file_path", sa.Text(), nullable=True),
        sa.Column("download_status", sa.String(length=50), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["mailbox_id"], ["mailboxes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["message_id"], ["messages.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("mailbox_id", "graph_attachment_id", name="uq_attachment_mailbox_graph"),
    )
    op.create_index("ix_attachments_mailbox_id", "attachments", ["mailbox_id"], unique=False)
    op.create_index("ix_attachments_message_id", "attachments", ["message_id"], unique=False)
    op.create_index("ix_attachments_graph_attachment_id", "attachments", ["graph_attachment_id"], unique=False)
    op.create_index("ix_attachments_graph_message_id", "attachments", ["graph_message_id"], unique=False)

    op.create_table(
        "documents",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("message_id", sa.Integer(), nullable=True),
        sa.Column("file_path", sa.Text(), nullable=True),
        sa.Column("vendor", sa.String(length=200), nullable=True),
        sa.Column("vendor_canonical", sa.String(length=200), nullable=True),
        sa.Column("po_number", sa.String(length=100), nullable=True),
        sa.Column("job_number", sa.String(length=100), nullable=True),
        sa.Column("invoice_number", sa.String(length=100), nullable=True),
        sa.Column("invoice_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("subtotal", sa.Float(), nullable=True),
        sa.Column("tax", sa.Float(), nullable=True),
        sa.Column("total", sa.Float(), nullable=True),
        sa.Column("source_sender", sa.String(length=320), nullable=True),
        sa.Column("source_received_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source_subject", sa.Text(), nullable=True),
        sa.Column("extract_notes", sa.Text(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["message_id"], ["messages.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("file_path"),
    )
    op.create_index("ix_documents_message_id", "documents", ["message_id"], unique=False)
    op.create_index("ix_documents_vendor", "documents", ["vendor"], unique=False)
    op.create_index("ix_documents_vendor_canonical", "documents", ["vendor_canonical"], unique=False)
    op.create_index("ix_documents_po_number", "documents", ["po_number"], unique=False)
    op.create_index("ix_documents_job_number", "documents", ["job_number"], unique=False)
    op.create_index("ix_documents_invoice_number", "documents", ["invoice_number"], unique=False)
    op.create_index("ix_documents_invoice_date", "documents", ["invoice_date"], unique=False)
    op.create_index("ix_documents_total", "documents", ["total"], unique=False)

    op.create_table(
        "line_items",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("line_no", sa.Integer(), nullable=False),
        sa.Column("vendor_sku", sa.String(length=200), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("qty", sa.Float(), nullable=True),
        sa.Column("uom", sa.String(length=50), nullable=True),
        sa.Column("unit_price", sa.Float(), nullable=True),
        sa.Column("line_total", sa.Float(), nullable=True),
        sa.Column("category_guess", sa.String(length=200), nullable=True),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("document_id", "line_no", name="uq_line_item_doc_line"),
    )
    op.create_index("ix_line_items_document_id", "line_items", ["document_id"], unique=False)

    op.create_table(
        "pipeline_errors",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("run_id", sa.Integer(), nullable=True),
        sa.Column("mailbox_id", sa.Integer(), nullable=True),
        sa.Column("message_graph_id", sa.String(length=256), nullable=True),
        sa.Column("stage", sa.String(length=100), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=False),
        sa.Column("payload_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["mailbox_id"], ["mailboxes.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["run_id"], ["pipeline_runs.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_pipeline_errors_run_id", "pipeline_errors", ["run_id"], unique=False)
    op.create_index("ix_pipeline_errors_mailbox_id", "pipeline_errors", ["mailbox_id"], unique=False)
    op.create_index("ix_pipeline_errors_message_graph_id", "pipeline_errors", ["message_graph_id"], unique=False)
    op.create_index("ix_pipeline_errors_stage", "pipeline_errors", ["stage"], unique=False)
    op.create_index("ix_pipeline_errors_created_at", "pipeline_errors", ["created_at"], unique=False)

    op.create_table(
        "pipeline_checkpoints",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("mailbox_id", sa.Integer(), nullable=False),
        sa.Column("pipeline_name", sa.String(length=100), nullable=False),
        sa.Column("last_successful_sync_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_run_id", sa.Integer(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["last_run_id"], ["pipeline_runs.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["mailbox_id"], ["mailboxes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("mailbox_id", "pipeline_name", name="uq_checkpoint_mailbox_pipeline"),
    )
    op.create_index("ix_pipeline_checkpoints_mailbox_id", "pipeline_checkpoints", ["mailbox_id"], unique=False)
    op.create_index("ix_pipeline_checkpoints_pipeline_name", "pipeline_checkpoints", ["pipeline_name"], unique=False)
    op.create_index(
        "ix_pipeline_checkpoints_last_successful_sync_at",
        "pipeline_checkpoints",
        ["last_successful_sync_at"],
        unique=False,
    )

    op.create_table(
        "dead_letters",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("mailbox_id", sa.Integer(), nullable=True),
        sa.Column("stage", sa.String(length=100), nullable=False),
        sa.Column("payload_json", sa.JSON(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["mailbox_id"], ["mailboxes.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_dead_letters_mailbox_id", "dead_letters", ["mailbox_id"], unique=False)
    op.create_index("ix_dead_letters_stage", "dead_letters", ["stage"], unique=False)
    op.create_index("ix_dead_letters_next_retry_at", "dead_letters", ["next_retry_at"], unique=False)
    op.create_index("ix_dead_letters_last_seen_at", "dead_letters", ["last_seen_at"], unique=False)
    op.create_index("ix_dead_letters_resolved_at", "dead_letters", ["resolved_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_dead_letters_resolved_at", table_name="dead_letters")
    op.drop_index("ix_dead_letters_last_seen_at", table_name="dead_letters")
    op.drop_index("ix_dead_letters_next_retry_at", table_name="dead_letters")
    op.drop_index("ix_dead_letters_stage", table_name="dead_letters")
    op.drop_index("ix_dead_letters_mailbox_id", table_name="dead_letters")
    op.drop_table("dead_letters")

    op.drop_index("ix_pipeline_checkpoints_last_successful_sync_at", table_name="pipeline_checkpoints")
    op.drop_index("ix_pipeline_checkpoints_pipeline_name", table_name="pipeline_checkpoints")
    op.drop_index("ix_pipeline_checkpoints_mailbox_id", table_name="pipeline_checkpoints")
    op.drop_table("pipeline_checkpoints")

    op.drop_index("ix_pipeline_errors_created_at", table_name="pipeline_errors")
    op.drop_index("ix_pipeline_errors_stage", table_name="pipeline_errors")
    op.drop_index("ix_pipeline_errors_message_graph_id", table_name="pipeline_errors")
    op.drop_index("ix_pipeline_errors_mailbox_id", table_name="pipeline_errors")
    op.drop_index("ix_pipeline_errors_run_id", table_name="pipeline_errors")
    op.drop_table("pipeline_errors")

    op.drop_index("ix_line_items_document_id", table_name="line_items")
    op.drop_table("line_items")

    op.drop_index("ix_documents_total", table_name="documents")
    op.drop_index("ix_documents_invoice_date", table_name="documents")
    op.drop_index("ix_documents_invoice_number", table_name="documents")
    op.drop_index("ix_documents_job_number", table_name="documents")
    op.drop_index("ix_documents_po_number", table_name="documents")
    op.drop_index("ix_documents_vendor_canonical", table_name="documents")
    op.drop_index("ix_documents_vendor", table_name="documents")
    op.drop_index("ix_documents_message_id", table_name="documents")
    op.drop_table("documents")

    op.drop_index("ix_attachments_graph_message_id", table_name="attachments")
    op.drop_index("ix_attachments_graph_attachment_id", table_name="attachments")
    op.drop_index("ix_attachments_message_id", table_name="attachments")
    op.drop_index("ix_attachments_mailbox_id", table_name="attachments")
    op.drop_table("attachments")

    op.drop_index("ix_messages_source_received_at", table_name="messages")
    op.drop_index("ix_messages_source_sender", table_name="messages")
    op.drop_index("ix_messages_conversation_id", table_name="messages")
    op.drop_index("ix_messages_graph_folder_id", table_name="messages")
    op.drop_index("ix_messages_graph_message_id", table_name="messages")
    op.drop_index("ix_messages_mailbox_id", table_name="messages")
    op.drop_table("messages")

    op.drop_index("ix_folders_graph_folder_id", table_name="folders")
    op.drop_index("ix_folders_mailbox_id", table_name="folders")
    op.drop_table("folders")

    op.drop_index("ix_pipeline_runs_started_at", table_name="pipeline_runs")
    op.drop_index("ix_pipeline_runs_status", table_name="pipeline_runs")
    op.drop_index("ix_pipeline_runs_mailbox_id", table_name="pipeline_runs")
    op.drop_index("ix_pipeline_runs_pipeline_name", table_name="pipeline_runs")
    op.drop_table("pipeline_runs")

    op.drop_index("ix_mailboxes_user_id", table_name="mailboxes")
    op.drop_index("ix_mailboxes_mailbox_key", table_name="mailboxes")
    op.drop_table("mailboxes")
