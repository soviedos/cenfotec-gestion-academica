"""create alertas table

Implements the full alert system defined in [AL-10] through [AL-50]:

  • Granularity: docente + curso + periodo + modalidad [AL-10].
  • Four alert types: BAJO_DESEMPEÑO, CAIDA, SENTIMIENTO, PATRON [AL-20–23].
  • Three severity tiers: alta, media, baja.
  • Lifecycle FSM: activa → revisada → resuelta | descartada [AL-50].
  • Dedup via UNIQUE (docente_nombre, curso, periodo, tipo_alerta) [AL-40]:
    the service does an upsert — if the combination already exists it updates
    valor_actual / severidad / descripcion instead of inserting a duplicate.
  • FK to evaluaciones is SET NULL on delete so alerts survive reprocessing.
  • Alerts are NEVER generated for modalidad = 'DESCONOCIDA' [BR-MOD-05],
    enforced by a CHECK that only allows the three real modalities.

Revision ID: 0008
Revises: 0007
Create Date: 2026-04-05
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0008"
down_revision: str = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "alertas",
        sa.Column("id", sa.Uuid, primary_key=True),
        # Optional origin — survives evaluation reprocessing
        sa.Column(
            "evaluacion_id",
            sa.Uuid,
            sa.ForeignKey("evaluaciones.id", ondelete="SET NULL"),
            nullable=True,
        ),
        # ── Identity / dedup key ────────────────────────────────────────
        sa.Column("docente_nombre", sa.String(300), nullable=False),
        sa.Column("curso", sa.String(400), nullable=False),
        sa.Column("periodo", sa.String(50), nullable=False),
        sa.Column("tipo_alerta", sa.String(30), nullable=False),
        # ── Scope ───────────────────────────────────────────────────────
        sa.Column("modalidad", sa.String(20), nullable=False),
        # ── Metric data ─────────────────────────────────────────────────
        sa.Column("metrica_afectada", sa.String(50), nullable=False),
        sa.Column("valor_actual", sa.Numeric(7, 2), nullable=False),
        sa.Column("valor_anterior", sa.Numeric(7, 2), nullable=True),
        # ── Human-readable description ──────────────────────────────────
        sa.Column("descripcion", sa.Text, nullable=False),
        # ── Severity & lifecycle ────────────────────────────────────────
        sa.Column("severidad", sa.String(10), nullable=False),
        sa.Column("estado", sa.String(15), nullable=False, server_default="activa"),
        # ── Timestamps ──────────────────────────────────────────────────
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

    # ── Dedup constraint [AL-40] ────────────────────────────────────────
    # One alert per (docente, curso, periodo, type).
    # The alert service upserts: if found, it updates instead of inserting.
    op.create_unique_constraint(
        "uq_alertas_dedup",
        "alertas",
        ["docente_nombre", "curso", "periodo", "tipo_alerta"],
    )

    # ── Indexes for common query patterns ───────────────────────────────
    op.create_index("ix_alertas_modalidad", "alertas", ["modalidad"])
    op.create_index("ix_alertas_severidad", "alertas", ["severidad"])
    op.create_index("ix_alertas_estado", "alertas", ["estado"])
    # Composite: dashboard queries "active alerts for this modality"
    op.create_index("ix_alertas_modalidad_estado", "alertas", ["modalidad", "estado"])
    op.create_index("ix_alertas_docente", "alertas", ["docente_nombre"])

    # ── CHECK constraints — enforce domain invariants at DB level ───────
    op.create_check_constraint(
        "ck_alertas_modalidad",
        "alertas",
        "modalidad IN ('CUATRIMESTRAL', 'MENSUAL', 'B2B')",
    )
    op.create_check_constraint(
        "ck_alertas_tipo",
        "alertas",
        "tipo_alerta IN ('BAJO_DESEMPEÑO', 'CAIDA', 'SENTIMIENTO', 'PATRON')",
    )
    op.create_check_constraint(
        "ck_alertas_severidad",
        "alertas",
        "severidad IN ('alta', 'media', 'baja')",
    )
    op.create_check_constraint(
        "ck_alertas_estado",
        "alertas",
        "estado IN ('activa', 'revisada', 'resuelta', 'descartada')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_alertas_estado", "alertas", type_="check")
    op.drop_constraint("ck_alertas_severidad", "alertas", type_="check")
    op.drop_constraint("ck_alertas_tipo", "alertas", type_="check")
    op.drop_constraint("ck_alertas_modalidad", "alertas", type_="check")
    op.drop_index("ix_alertas_docente", table_name="alertas")
    op.drop_index("ix_alertas_modalidad_estado", table_name="alertas")
    op.drop_index("ix_alertas_estado", table_name="alertas")
    op.drop_index("ix_alertas_severidad", table_name="alertas")
    op.drop_index("ix_alertas_modalidad", table_name="alertas")
    op.drop_unique_constraint("uq_alertas_dedup", "alertas")
    op.drop_table("alertas")
