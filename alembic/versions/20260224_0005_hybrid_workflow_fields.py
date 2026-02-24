"""Add hybrid workflow fields and action audit table

Revision ID: 20260224_0005
Revises: 20260224_0004
Create Date: 2026-02-24
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260224_0005"
down_revision: Union[str, None] = "20260224_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("tasks", sa.Column("workflow_spine", sa.String(length=50), nullable=False, server_default="hybrid"))
    op.add_column("tasks", sa.Column("workflow_stage", sa.String(length=100), nullable=False, server_default="triage"))
    op.add_column("tasks", sa.Column("human_required", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("tasks", sa.Column("auto_allowed", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("tasks", sa.Column("blocked_reason", sa.Text(), nullable=True))
    op.add_column("tasks", sa.Column("source_folder_path", sa.Text(), nullable=True))

    op.create_index(op.f("ix_tasks_workflow_spine"), "tasks", ["workflow_spine"], unique=False)
    op.create_index(op.f("ix_tasks_workflow_stage"), "tasks", ["workflow_stage"], unique=False)
    op.create_index(op.f("ix_tasks_human_required"), "tasks", ["human_required"], unique=False)
    op.create_index(op.f("ix_tasks_auto_allowed"), "tasks", ["auto_allowed"], unique=False)

    op.create_table(
        "workflow_actions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("task_id", sa.Integer(), nullable=True),
        sa.Column("action_type", sa.String(length=100), nullable=False),
        sa.Column("action_mode", sa.String(length=30), nullable=False),
        sa.Column("action_status", sa.String(length=30), nullable=False),
        sa.Column("actor_email", sa.String(length=320), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("payload_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_workflow_actions_task_id"), "workflow_actions", ["task_id"], unique=False)
    op.create_index(op.f("ix_workflow_actions_action_type"), "workflow_actions", ["action_type"], unique=False)
    op.create_index(op.f("ix_workflow_actions_action_mode"), "workflow_actions", ["action_mode"], unique=False)
    op.create_index(op.f("ix_workflow_actions_action_status"), "workflow_actions", ["action_status"], unique=False)
    op.create_index(op.f("ix_workflow_actions_actor_email"), "workflow_actions", ["actor_email"], unique=False)
    op.create_index(op.f("ix_workflow_actions_created_at"), "workflow_actions", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_workflow_actions_created_at"), table_name="workflow_actions")
    op.drop_index(op.f("ix_workflow_actions_actor_email"), table_name="workflow_actions")
    op.drop_index(op.f("ix_workflow_actions_action_status"), table_name="workflow_actions")
    op.drop_index(op.f("ix_workflow_actions_action_mode"), table_name="workflow_actions")
    op.drop_index(op.f("ix_workflow_actions_action_type"), table_name="workflow_actions")
    op.drop_index(op.f("ix_workflow_actions_task_id"), table_name="workflow_actions")
    op.drop_table("workflow_actions")

    op.drop_index(op.f("ix_tasks_auto_allowed"), table_name="tasks")
    op.drop_index(op.f("ix_tasks_human_required"), table_name="tasks")
    op.drop_index(op.f("ix_tasks_workflow_stage"), table_name="tasks")
    op.drop_index(op.f("ix_tasks_workflow_spine"), table_name="tasks")
    op.drop_column("tasks", "source_folder_path")
    op.drop_column("tasks", "blocked_reason")
    op.drop_column("tasks", "auto_allowed")
    op.drop_column("tasks", "human_required")
    op.drop_column("tasks", "workflow_stage")
    op.drop_column("tasks", "workflow_spine")
