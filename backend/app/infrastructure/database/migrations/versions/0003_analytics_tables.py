"""add evaluacion_dimensiones and evaluacion_cursos tables

Revision ID: 0003
Revises: 0002
Create Date: 2026-04-03
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "evaluacion_dimensiones",
        sa.Column("id", sa.Uuid, primary_key=True),
        sa.Column(
            "evaluacion_id",
            sa.Uuid,
            sa.ForeignKey("evaluaciones.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("nombre", sa.String(100), nullable=False),
        sa.Column("pct_estudiante", sa.Numeric(5, 2), nullable=True),
        sa.Column("pct_director", sa.Numeric(5, 2), nullable=True),
        sa.Column("pct_autoeval", sa.Numeric(5, 2), nullable=True),
        sa.Column("pct_promedio", sa.Numeric(5, 2), nullable=True),
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
    op.create_index("ix_eval_dim_evaluacion", "evaluacion_dimensiones", ["evaluacion_id"])
    op.create_index("ix_eval_dim_nombre", "evaluacion_dimensiones", ["nombre"])

    op.create_table(
        "evaluacion_cursos",
        sa.Column("id", sa.Uuid, primary_key=True),
        sa.Column(
            "evaluacion_id",
            sa.Uuid,
            sa.ForeignKey("evaluaciones.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("escuela", sa.String(200), nullable=True),
        sa.Column("codigo", sa.String(50), nullable=True),
        sa.Column("nombre", sa.String(300), nullable=True),
        sa.Column("grupo", sa.String(50), nullable=True),
        sa.Column("respondieron", sa.Integer(), nullable=True),
        sa.Column("matriculados", sa.Integer(), nullable=True),
        sa.Column("pct_estudiante", sa.Numeric(5, 2), nullable=True),
        sa.Column("pct_director", sa.Numeric(5, 2), nullable=True),
        sa.Column("pct_autoeval", sa.Numeric(5, 2), nullable=True),
        sa.Column("pct_promedio", sa.Numeric(5, 2), nullable=True),
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
    op.create_index("ix_eval_curso_evaluacion", "evaluacion_cursos", ["evaluacion_id"])


def downgrade() -> None:
    op.drop_index("ix_eval_curso_evaluacion", table_name="evaluacion_cursos")
    op.drop_table("evaluacion_cursos")
    op.drop_index("ix_eval_dim_nombre", table_name="evaluacion_dimensiones")
    op.drop_index("ix_eval_dim_evaluacion", table_name="evaluacion_dimensiones")
    op.drop_table("evaluacion_dimensiones")
