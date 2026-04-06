"""add modalidad, año, periodo_orden to evaluaciones

Adds the three columns required by [BR-MOD-04] and [BR-AN-40]:

  • modalidad  — programme modality (CUATRIMESTRAL | MENSUAL | B2B | DESCONOCIDA).
                 Every analytics query, cache key, and alert MUST filter by this.
  • año        — integer year extracted from the normalized period string.
                 CHECK >= 2020 guards against garbage data.
  • periodo_orden — ordinal within the year (C2 → 2, M10 → 10).
                 Together with año enables ORDER BY (año, periodo_orden)
                 for correct chronological sorting without runtime parsing.

Backfill strategy
-----------------
Existing rows get modalidad = 'DESCONOCIDA', año = 2020, periodo_orden = 0
as safe defaults.  A one-off backfill script (to be run separately) will
apply `determinar_modalidad()` + `parse_periodo()` to populate real values.

Revision ID: 0007
Revises: 0006
Create Date: 2026-04-05
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0007"
down_revision: str = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── 1. New columns with safe server defaults for backfill ───────────
    op.add_column(
        "evaluaciones",
        sa.Column(
            "modalidad",
            sa.String(20),
            nullable=False,
            server_default="DESCONOCIDA",
        ),
    )
    op.add_column(
        "evaluaciones",
        sa.Column("año", sa.SmallInteger(), nullable=False, server_default="2020"),
    )
    op.add_column(
        "evaluaciones",
        sa.Column("periodo_orden", sa.SmallInteger(), nullable=False, server_default="0"),
    )

    # ── 2. Indexes — enable fast analytics-by-modalidad [BR-BE-10] ─────
    #
    #  ix_evaluaciones_modalidad          → WHERE modalidad = ?
    #  ix_evaluaciones_modalidad_periodo  → WHERE modalidad = ? AND periodo = ?
    #  ix_evaluaciones_modalidad_año_orden → ORDER BY año, periodo_orden
    op.create_index(
        "ix_evaluaciones_modalidad",
        "evaluaciones",
        ["modalidad"],
    )
    op.create_index(
        "ix_evaluaciones_modalidad_periodo",
        "evaluaciones",
        ["modalidad", "periodo"],
    )
    op.create_index(
        "ix_evaluaciones_modalidad_año_orden",
        "evaluaciones",
        ["modalidad", "año", "periodo_orden"],
    )

    # ── 3. CHECK constraints — guard domain invariants ──────────────────
    op.create_check_constraint(
        "ck_evaluaciones_modalidad",
        "evaluaciones",
        "modalidad IN ('CUATRIMESTRAL', 'MENSUAL', 'B2B', 'DESCONOCIDA')",
    )
    op.create_check_constraint(
        "ck_evaluaciones_año_min",
        "evaluaciones",
        "año >= 2020",
    )
    op.create_check_constraint(
        "ck_evaluaciones_puntaje_rango",
        "evaluaciones",
        "puntaje_general IS NULL OR (puntaje_general >= 0 AND puntaje_general <= 100)",
    )

    # ── 4. Drop server defaults — the application sets real values ──────
    #    We only needed them so the ADD COLUMN wouldn't fail on existing rows.
    op.alter_column("evaluaciones", "año", server_default=None)
    op.alter_column("evaluaciones", "periodo_orden", server_default=None)


def downgrade() -> None:
    op.drop_constraint("ck_evaluaciones_puntaje_rango", "evaluaciones", type_="check")
    op.drop_constraint("ck_evaluaciones_año_min", "evaluaciones", type_="check")
    op.drop_constraint("ck_evaluaciones_modalidad", "evaluaciones", type_="check")
    op.drop_index("ix_evaluaciones_modalidad_año_orden", table_name="evaluaciones")
    op.drop_index("ix_evaluaciones_modalidad_periodo", table_name="evaluaciones")
    op.drop_index("ix_evaluaciones_modalidad", table_name="evaluaciones")
    op.drop_column("evaluaciones", "periodo_orden")
    op.drop_column("evaluaciones", "año")
    op.drop_column("evaluaciones", "modalidad")
