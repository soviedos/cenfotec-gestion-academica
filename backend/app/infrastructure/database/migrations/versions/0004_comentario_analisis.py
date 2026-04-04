"""add comentario_analisis table

Revision ID: 0004
Revises: 0003
Create Date: 2026-04-03
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: str = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "comentario_analisis",
        sa.Column("id", sa.Uuid, primary_key=True),
        sa.Column(
            "evaluacion_id",
            sa.Uuid,
            sa.ForeignKey("evaluaciones.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("fuente", sa.String(20), nullable=False),
        sa.Column("asignatura", sa.String(300), nullable=False),
        sa.Column("tipo", sa.String(20), nullable=False),
        sa.Column("texto", sa.Text, nullable=False),
        sa.Column("tema", sa.String(50), nullable=False),
        sa.Column("tema_confianza", sa.String(10), nullable=False, server_default="regla"),
        sa.Column("sentimiento", sa.String(10), nullable=True),
        sa.Column("sent_score", sa.Numeric(3, 2), nullable=True),
        sa.Column("procesado_ia", sa.Boolean, nullable=False, server_default=sa.text("false")),
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
    op.create_index("ix_comentario_evaluacion", "comentario_analisis", ["evaluacion_id"])
    op.create_index("ix_comentario_tipo", "comentario_analisis", ["tipo"])
    op.create_index("ix_comentario_tema", "comentario_analisis", ["tema"])
    op.create_index("ix_comentario_sentimiento", "comentario_analisis", ["sentimiento"])


def downgrade() -> None:
    op.drop_index("ix_comentario_sentimiento", table_name="comentario_analisis")
    op.drop_index("ix_comentario_tema", table_name="comentario_analisis")
    op.drop_index("ix_comentario_tipo", table_name="comentario_analisis")
    op.drop_index("ix_comentario_evaluacion", table_name="comentario_analisis")
    op.drop_table("comentario_analisis")
