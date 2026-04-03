"""initial schema — documentos and evaluaciones

Revision ID: 0001
Revises:
Create Date: 2026-04-03
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "documentos",
        sa.Column("id", sa.Uuid, primary_key=True),
        sa.Column("nombre_archivo", sa.String(500), nullable=False),
        sa.Column(
            "hash_sha256", sa.String(64), nullable=False, unique=True, index=True
        ),
        sa.Column("storage_path", sa.String(1000), nullable=False),
        sa.Column(
            "estado", sa.String(20), nullable=False, server_default="subido"
        ),
        sa.Column("tamano_bytes", sa.Integer(), nullable=True),
        sa.Column("error_detalle", sa.Text(), nullable=True),
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

    op.create_table(
        "evaluaciones",
        sa.Column("id", sa.Uuid, primary_key=True),
        sa.Column(
            "documento_id",
            sa.Uuid,
            sa.ForeignKey("documentos.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("docente_nombre", sa.String(300), nullable=False),
        sa.Column("periodo", sa.String(50), nullable=False),
        sa.Column("materia", sa.String(300), nullable=True),
        sa.Column("puntaje_general", sa.Numeric(5, 2), nullable=True),
        sa.Column("resumen_ia", sa.Text(), nullable=True),
        sa.Column(
            "estado", sa.String(20), nullable=False, server_default="pendiente"
        ),
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

    # Index for fast lookups by documento
    op.create_index(
        "ix_evaluaciones_documento_id", "evaluaciones", ["documento_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_evaluaciones_documento_id", table_name="evaluaciones")
    op.drop_table("evaluaciones")
    op.drop_table("documentos")
