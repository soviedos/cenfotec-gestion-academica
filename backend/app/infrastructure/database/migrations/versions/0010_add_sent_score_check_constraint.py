"""add CHECK constraint on sent_score [-1, 1]

Enforces BR-AN-30: sentiment scores must be in range [-1, 1] or NULL.

Revision ID: 0010
Revises: 0009
Create Date: 2026-04-06
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0010"
down_revision: str = "0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_check_constraint(
        "ck_comentario_sent_score_range",
        "comentario_analisis",
        "sent_score IS NULL OR (sent_score >= -1 AND sent_score <= 1)",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_comentario_sent_score_range",
        "comentario_analisis",
        type_="check",
    )
