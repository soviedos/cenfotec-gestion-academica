"""add gemini_audit_log table

Revision ID: 0005
Revises: 0004
Create Date: 2026-04-04
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: str = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "gemini_audit_log",
        sa.Column("id", sa.Uuid, primary_key=True),
        sa.Column("operation", sa.String(30), nullable=False),
        sa.Column(
            "evaluacion_id",
            sa.Uuid,
            sa.ForeignKey("evaluaciones.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("prompt_text", sa.Text, nullable=False),
        sa.Column("prompt_hash", sa.String(64), nullable=False),
        sa.Column("response_text", sa.Text, nullable=True),
        sa.Column("model_name", sa.String(50), nullable=False),
        sa.Column("tokens_input", sa.Integer, nullable=True),
        sa.Column("tokens_output", sa.Integer, nullable=True),
        sa.Column("latency_ms", sa.Integer, nullable=True),
        sa.Column("status", sa.String(10), nullable=False, server_default="ok"),
        sa.Column("error_detail", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_audit_operation", "gemini_audit_log", ["operation"])
    op.create_index("ix_audit_prompt_hash", "gemini_audit_log", ["prompt_hash"])


def downgrade() -> None:
    op.drop_index("ix_audit_prompt_hash", table_name="gemini_audit_log")
    op.drop_index("ix_audit_operation", table_name="gemini_audit_log")
    op.drop_table("gemini_audit_log")
