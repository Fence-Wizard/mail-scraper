"""Add role graph foundation tables

Revision ID: 20260224_0003
Revises: 20260223_0002
Create Date: 2026-02-24
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260224_0003"
down_revision: Union[str, None] = "20260223_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "vendor_references",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("vendor_code", sa.String(length=100), nullable=False),
        sa.Column("vendor_name", sa.String(length=300), nullable=False),
        sa.Column("vendor_name_canonical", sa.String(length=300), nullable=False),
        sa.Column("vendor_class", sa.String(length=100), nullable=True),
        sa.Column("vendor_status", sa.String(length=100), nullable=True),
        sa.Column("country", sa.String(length=100), nullable=True),
        sa.Column("city", sa.String(length=200), nullable=True),
        sa.Column("state", sa.String(length=100), nullable=True),
        sa.Column("currency_id", sa.String(length=50), nullable=True),
        sa.Column("terms", sa.String(length=100), nullable=True),
        sa.Column("default_contact", sa.String(length=100), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_vendor_references_vendor_code"), "vendor_references", ["vendor_code"], unique=True)
    op.create_index(op.f("ix_vendor_references_vendor_name"), "vendor_references", ["vendor_name"], unique=False)
    op.create_index(
        op.f("ix_vendor_references_vendor_name_canonical"), "vendor_references", ["vendor_name_canonical"], unique=False
    )
    op.create_index(op.f("ix_vendor_references_vendor_class"), "vendor_references", ["vendor_class"], unique=False)
    op.create_index(op.f("ix_vendor_references_vendor_status"), "vendor_references", ["vendor_status"], unique=False)

    op.create_table(
        "actors",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("actor_key", sa.String(length=400), nullable=False),
        sa.Column("display_name", sa.String(length=300), nullable=False),
        sa.Column("actor_type", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=True),
        sa.Column("email_domain", sa.String(length=200), nullable=True),
        sa.Column("vendor_reference_id", sa.Integer(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["vendor_reference_id"], ["vendor_references.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_actors_actor_key"), "actors", ["actor_key"], unique=True)
    op.create_index(op.f("ix_actors_actor_type"), "actors", ["actor_type"], unique=False)
    op.create_index(op.f("ix_actors_display_name"), "actors", ["display_name"], unique=False)
    op.create_index(op.f("ix_actors_email"), "actors", ["email"], unique=False)
    op.create_index(op.f("ix_actors_email_domain"), "actors", ["email_domain"], unique=False)

    op.create_table(
        "actor_aliases",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("actor_id", sa.Integer(), nullable=False),
        sa.Column("alias", sa.String(length=400), nullable=False),
        sa.Column("alias_type", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["actor_id"], ["actors.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("alias", name="uq_actor_alias_alias"),
    )
    op.create_index(op.f("ix_actor_aliases_actor_id"), "actor_aliases", ["actor_id"], unique=False)
    op.create_index(op.f("ix_actor_aliases_alias"), "actor_aliases", ["alias"], unique=False)
    op.create_index(op.f("ix_actor_aliases_alias_type"), "actor_aliases", ["alias_type"], unique=False)

    op.create_table(
        "interactions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("mailbox_id", sa.Integer(), nullable=True),
        sa.Column("message_id", sa.Integer(), nullable=True),
        sa.Column("document_id", sa.Integer(), nullable=True),
        sa.Column("from_actor_id", sa.Integer(), nullable=True),
        sa.Column("to_actor_id", sa.Integer(), nullable=True),
        sa.Column("channel", sa.String(length=100), nullable=False),
        sa.Column("interaction_type", sa.String(length=100), nullable=False),
        sa.Column("direction", sa.String(length=50), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("subject", sa.Text(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["mailbox_id"], ["mailboxes.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["message_id"], ["messages.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["from_actor_id"], ["actors.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["to_actor_id"], ["actors.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_interactions_mailbox_id"), "interactions", ["mailbox_id"], unique=False)
    op.create_index(op.f("ix_interactions_message_id"), "interactions", ["message_id"], unique=False)
    op.create_index(op.f("ix_interactions_document_id"), "interactions", ["document_id"], unique=False)
    op.create_index(op.f("ix_interactions_from_actor_id"), "interactions", ["from_actor_id"], unique=False)
    op.create_index(op.f("ix_interactions_to_actor_id"), "interactions", ["to_actor_id"], unique=False)
    op.create_index(op.f("ix_interactions_channel"), "interactions", ["channel"], unique=False)
    op.create_index(op.f("ix_interactions_interaction_type"), "interactions", ["interaction_type"], unique=False)
    op.create_index(op.f("ix_interactions_direction"), "interactions", ["direction"], unique=False)
    op.create_index(op.f("ix_interactions_occurred_at"), "interactions", ["occurred_at"], unique=False)

    op.create_table(
        "tasks",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("mailbox_id", sa.Integer(), nullable=True),
        sa.Column("task_type", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("priority", sa.String(length=50), nullable=False),
        sa.Column("job_number", sa.String(length=100), nullable=True),
        sa.Column("owner_actor_id", sa.Integer(), nullable=True),
        sa.Column("counterparty_actor_id", sa.Integer(), nullable=True),
        sa.Column("source_message_id", sa.Integer(), nullable=True),
        sa.Column("source_document_id", sa.Integer(), nullable=True),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_event_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("details_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["mailbox_id"], ["mailboxes.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["owner_actor_id"], ["actors.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["counterparty_actor_id"], ["actors.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["source_message_id"], ["messages.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["source_document_id"], ["documents.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source_message_id", "task_type", name="uq_task_message_type"),
        sa.UniqueConstraint("source_document_id", "task_type", name="uq_task_document_type"),
    )
    op.create_index(op.f("ix_tasks_mailbox_id"), "tasks", ["mailbox_id"], unique=False)
    op.create_index(op.f("ix_tasks_task_type"), "tasks", ["task_type"], unique=False)
    op.create_index(op.f("ix_tasks_status"), "tasks", ["status"], unique=False)
    op.create_index(op.f("ix_tasks_priority"), "tasks", ["priority"], unique=False)
    op.create_index(op.f("ix_tasks_job_number"), "tasks", ["job_number"], unique=False)
    op.create_index(op.f("ix_tasks_owner_actor_id"), "tasks", ["owner_actor_id"], unique=False)
    op.create_index(op.f("ix_tasks_counterparty_actor_id"), "tasks", ["counterparty_actor_id"], unique=False)
    op.create_index(op.f("ix_tasks_source_message_id"), "tasks", ["source_message_id"], unique=False)
    op.create_index(op.f("ix_tasks_source_document_id"), "tasks", ["source_document_id"], unique=False)
    op.create_index(op.f("ix_tasks_due_at"), "tasks", ["due_at"], unique=False)
    op.create_index(op.f("ix_tasks_completed_at"), "tasks", ["completed_at"], unique=False)
    op.create_index(op.f("ix_tasks_last_event_at"), "tasks", ["last_event_at"], unique=False)

    op.create_table(
        "task_events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("task_id", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("event_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("message_id", sa.Integer(), nullable=True),
        sa.Column("document_id", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("payload_json", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["message_id"], ["messages.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_task_events_task_id"), "task_events", ["task_id"], unique=False)
    op.create_index(op.f("ix_task_events_event_type"), "task_events", ["event_type"], unique=False)
    op.create_index(op.f("ix_task_events_event_at"), "task_events", ["event_at"], unique=False)
    op.create_index(op.f("ix_task_events_message_id"), "task_events", ["message_id"], unique=False)
    op.create_index(op.f("ix_task_events_document_id"), "task_events", ["document_id"], unique=False)

    op.create_table(
        "decision_scores",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("task_id", sa.Integer(), nullable=False),
        sa.Column("scored_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("action_label", sa.String(length=200), nullable=False),
        sa.Column("score_total", sa.Float(), nullable=False),
        sa.Column("score_speed", sa.Float(), nullable=False),
        sa.Column("score_risk", sa.Float(), nullable=False),
        sa.Column("score_cash", sa.Float(), nullable=False),
        sa.Column("score_relationship", sa.Float(), nullable=False),
        sa.Column("score_rework", sa.Float(), nullable=False),
        sa.Column("weights_json", sa.JSON(), nullable=True),
        sa.Column("rationale", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_decision_scores_task_id"), "decision_scores", ["task_id"], unique=False)
    op.create_index(op.f("ix_decision_scores_scored_at"), "decision_scores", ["scored_at"], unique=False)
    op.create_index(op.f("ix_decision_scores_action_label"), "decision_scores", ["action_label"], unique=False)
    op.create_index(op.f("ix_decision_scores_score_total"), "decision_scores", ["score_total"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_decision_scores_score_total"), table_name="decision_scores")
    op.drop_index(op.f("ix_decision_scores_action_label"), table_name="decision_scores")
    op.drop_index(op.f("ix_decision_scores_scored_at"), table_name="decision_scores")
    op.drop_index(op.f("ix_decision_scores_task_id"), table_name="decision_scores")
    op.drop_table("decision_scores")

    op.drop_index(op.f("ix_task_events_document_id"), table_name="task_events")
    op.drop_index(op.f("ix_task_events_message_id"), table_name="task_events")
    op.drop_index(op.f("ix_task_events_event_at"), table_name="task_events")
    op.drop_index(op.f("ix_task_events_event_type"), table_name="task_events")
    op.drop_index(op.f("ix_task_events_task_id"), table_name="task_events")
    op.drop_table("task_events")

    op.drop_index(op.f("ix_tasks_last_event_at"), table_name="tasks")
    op.drop_index(op.f("ix_tasks_completed_at"), table_name="tasks")
    op.drop_index(op.f("ix_tasks_due_at"), table_name="tasks")
    op.drop_index(op.f("ix_tasks_source_document_id"), table_name="tasks")
    op.drop_index(op.f("ix_tasks_source_message_id"), table_name="tasks")
    op.drop_index(op.f("ix_tasks_counterparty_actor_id"), table_name="tasks")
    op.drop_index(op.f("ix_tasks_owner_actor_id"), table_name="tasks")
    op.drop_index(op.f("ix_tasks_job_number"), table_name="tasks")
    op.drop_index(op.f("ix_tasks_priority"), table_name="tasks")
    op.drop_index(op.f("ix_tasks_status"), table_name="tasks")
    op.drop_index(op.f("ix_tasks_task_type"), table_name="tasks")
    op.drop_index(op.f("ix_tasks_mailbox_id"), table_name="tasks")
    op.drop_table("tasks")

    op.drop_index(op.f("ix_interactions_occurred_at"), table_name="interactions")
    op.drop_index(op.f("ix_interactions_direction"), table_name="interactions")
    op.drop_index(op.f("ix_interactions_interaction_type"), table_name="interactions")
    op.drop_index(op.f("ix_interactions_channel"), table_name="interactions")
    op.drop_index(op.f("ix_interactions_to_actor_id"), table_name="interactions")
    op.drop_index(op.f("ix_interactions_from_actor_id"), table_name="interactions")
    op.drop_index(op.f("ix_interactions_document_id"), table_name="interactions")
    op.drop_index(op.f("ix_interactions_message_id"), table_name="interactions")
    op.drop_index(op.f("ix_interactions_mailbox_id"), table_name="interactions")
    op.drop_table("interactions")

    op.drop_index(op.f("ix_actor_aliases_alias_type"), table_name="actor_aliases")
    op.drop_index(op.f("ix_actor_aliases_alias"), table_name="actor_aliases")
    op.drop_index(op.f("ix_actor_aliases_actor_id"), table_name="actor_aliases")
    op.drop_table("actor_aliases")

    op.drop_index(op.f("ix_actors_email_domain"), table_name="actors")
    op.drop_index(op.f("ix_actors_email"), table_name="actors")
    op.drop_index(op.f("ix_actors_display_name"), table_name="actors")
    op.drop_index(op.f("ix_actors_actor_type"), table_name="actors")
    op.drop_index(op.f("ix_actors_actor_key"), table_name="actors")
    op.drop_table("actors")

    op.drop_index(op.f("ix_vendor_references_vendor_status"), table_name="vendor_references")
    op.drop_index(op.f("ix_vendor_references_vendor_class"), table_name="vendor_references")
    op.drop_index(op.f("ix_vendor_references_vendor_name_canonical"), table_name="vendor_references")
    op.drop_index(op.f("ix_vendor_references_vendor_name"), table_name="vendor_references")
    op.drop_index(op.f("ix_vendor_references_vendor_code"), table_name="vendor_references")
    op.drop_table("vendor_references")
