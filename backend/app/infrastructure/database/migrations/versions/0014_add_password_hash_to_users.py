"""add password_hash to users

Revision ID: 0014
Revises: cd2f920b4325
Create Date: 2026-04-12 19:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0014"
down_revision: str | None = "cd2f920b4325"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "password_hash",
            sa.String(length=255),
            nullable=True,
            comment="bcrypt hash — NULL for Google-only users",
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "password_hash")
