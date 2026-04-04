"""add datos_completos to evaluaciones

Revision ID: 0002
Revises: 0001
Create Date: 2026-04-03
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: str = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "evaluaciones",
        sa.Column("datos_completos", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("evaluaciones", "datos_completos")
