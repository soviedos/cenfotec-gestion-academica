"""add performance indexes for analytics and qualitative queries

Revision ID: 0006
Revises: 0005
Create Date: 2026-04-04
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index("ix_evaluaciones_periodo", "evaluaciones", ["periodo"])
    op.create_index("ix_evaluaciones_docente_nombre", "evaluaciones", ["docente_nombre"])
    op.create_index("ix_evaluaciones_estado", "evaluaciones", ["estado"])
    op.create_index("ix_comentario_analisis_asignatura", "comentario_analisis", ["asignatura"])
    op.create_index("ix_comentario_analisis_fuente", "comentario_analisis", ["fuente"])


def downgrade() -> None:
    op.drop_index("ix_comentario_analisis_fuente", table_name="comentario_analisis")
    op.drop_index("ix_comentario_analisis_asignatura", table_name="comentario_analisis")
    op.drop_index("ix_evaluaciones_estado", table_name="evaluaciones")
    op.drop_index("ix_evaluaciones_docente_nombre", table_name="evaluaciones")
    op.drop_index("ix_evaluaciones_periodo", table_name="evaluaciones")
