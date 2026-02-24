"""Add progress cursor to pipeline checkpoints

Revision ID: 20260223_0002
Revises: 20260223_0001
Create Date: 2026-02-23
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260223_0002"
down_revision: Union[str, None] = "20260223_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("pipeline_checkpoints", sa.Column("progress_cursor", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("pipeline_checkpoints", "progress_cursor")
