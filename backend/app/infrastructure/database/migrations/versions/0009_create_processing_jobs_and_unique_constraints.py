"""create document_processing_jobs + add unique constraints on children

Two independent changes bundled in one migration (both are additive,
no data risk):

1. **document_processing_jobs** — separates processing traces from
   `documentos`, enabling reprocessing history and structured error/warning
   persistence via JSONB [BR-PROC-03].

2. **Unique constraints on evaluacion_dimensiones and evaluacion_cursos** —
   prevent duplicate rows that would corrupt analytics:
     • (evaluacion_id, nombre)          on evaluacion_dimensiones
     • (evaluacion_id, codigo, grupo)   on evaluacion_cursos

   If existing data has duplicates these will fail.  Run a dedup query
   first:
     DELETE FROM evaluacion_dimensiones a USING evaluacion_dimensiones b
     WHERE a.id > b.id
       AND a.evaluacion_id = b.evaluacion_id
       AND a.nombre = b.nombre;
   (analogous for evaluacion_cursos).

Revision ID: 0009
Revises: 0008
Create Date: 2026-04-05
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0009"
down_revision: str = "0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── 1. Processing jobs table ────────────────────────────────────────
    op.create_table(
        "document_processing_jobs",
        sa.Column("id", sa.Uuid, primary_key=True),
        sa.Column(
            "documento_id",
            sa.Uuid,
            sa.ForeignKey("documentos.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("estado", sa.String(20), nullable=False, server_default="pendiente"),
        sa.Column("parser_version", sa.String(20), nullable=False),
        sa.Column("pages_processed", sa.Integer, nullable=True),
        sa.Column("evaluaciones_creadas", sa.Integer, nullable=False, server_default="0"),
        # JSONB for structured ParseError/ParseWarning lists [BR-PROC-03]
        sa.Column("errors", JSONB(), nullable=True, server_default="[]"),
        sa.Column("warnings", JSONB(), nullable=True, server_default="[]"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
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
    op.create_index("ix_proc_jobs_documento", "document_processing_jobs", ["documento_id"])
    op.create_index("ix_proc_jobs_estado", "document_processing_jobs", ["estado"])
    op.create_check_constraint(
        "ck_processing_jobs_estado",
        "document_processing_jobs",
        "estado IN ('pendiente', 'procesando', 'completado', 'error')",
    )

    # ── 2. Unique constraint: one dimension-name per evaluation ─────────
    op.create_unique_constraint(
        "uq_eval_dim_eval_nombre",
        "evaluacion_dimensiones",
        ["evaluacion_id", "nombre"],
    )

    # ── 3. Unique constraint: one curso-grupo per evaluation ────────────
    op.create_unique_constraint(
        "uq_eval_curso_eval_cod_grupo",
        "evaluacion_cursos",
        ["evaluacion_id", "codigo", "grupo"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_eval_curso_eval_cod_grupo", "evaluacion_cursos", type_="unique")
    op.drop_constraint("uq_eval_dim_eval_nombre", "evaluacion_dimensiones", type_="unique")
    op.drop_constraint("ck_processing_jobs_estado", "document_processing_jobs", type_="check")
    op.drop_index("ix_proc_jobs_estado", table_name="document_processing_jobs")
    op.drop_index("ix_proc_jobs_documento", table_name="document_processing_jobs")
    op.drop_table("document_processing_jobs")
