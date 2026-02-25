"""Add decision-gate workflow fields to tasks table

Revision ID: 20260225_0006
Revises: 20260224_0005
Create Date: 2026-02-25
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260225_0006"
down_revision: Union[str, None] = "20260224_0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("tasks", sa.Column("assigned_purchaser_email", sa.String(320), nullable=True, index=True))
    op.add_column("tasks", sa.Column("assigned_by_email", sa.String(320), nullable=True))
    op.add_column("tasks", sa.Column("material_in_stock", sa.Boolean(), nullable=True))
    op.add_column("tasks", sa.Column("can_pull_extra", sa.Boolean(), nullable=True))
    op.add_column("tasks", sa.Column("po_provided", sa.Boolean(), nullable=True))
    op.add_column("tasks", sa.Column("prices_valid", sa.Boolean(), nullable=True))
    op.add_column("tasks", sa.Column("all_material_present", sa.Boolean(), nullable=True))
    op.add_column("tasks", sa.Column("vendor_coord_price", sa.Text(), nullable=True))
    op.add_column("tasks", sa.Column("vendor_coord_delivery_time", sa.Text(), nullable=True))
    op.add_column("tasks", sa.Column("vendor_coord_delivery_location", sa.Text(), nullable=True))
    op.add_column("tasks", sa.Column("expected_delivery_date", sa.DateTime(timezone=True), nullable=True))
    op.add_column("tasks", sa.Column("backorder_notes", sa.Text(), nullable=True))
    op.add_column("tasks", sa.Column("decision_path", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("tasks", "decision_path")
    op.drop_column("tasks", "backorder_notes")
    op.drop_column("tasks", "expected_delivery_date")
    op.drop_column("tasks", "vendor_coord_delivery_location")
    op.drop_column("tasks", "vendor_coord_delivery_time")
    op.drop_column("tasks", "vendor_coord_price")
    op.drop_column("tasks", "all_material_present")
    op.drop_column("tasks", "prices_valid")
    op.drop_column("tasks", "po_provided")
    op.drop_column("tasks", "can_pull_extra")
    op.drop_column("tasks", "material_in_stock")
    op.drop_column("tasks", "assigned_by_email")
    op.drop_column("tasks", "assigned_purchaser_email")
