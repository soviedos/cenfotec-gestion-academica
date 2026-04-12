"""Alerta entity — persistent academic/operational alerts.

Granularity: docente + curso + periodo + modalidad [AL-10].
Lifecycle:   activa → revisada → resuelta | descartada [AL-50].
Dedup:       UNIQUE (docente_nombre, curso, periodo, tipo_alerta) [AL-40].
"""

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.domain.entities.base import Base, TimestampMixin, UUIDMixin


class Alerta(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "alertas"

    # ── Optional origin ─────────────────────────────────────────────────
    # SET NULL on delete: alerts survive evaluation reprocessing.
    evaluacion_id: Mapped[str | None] = mapped_column(
        Uuid,
        ForeignKey("evaluaciones.id", ondelete="SET NULL"),
        nullable=True,
    )

    # ── Identity fields (form the dedup key) ────────────────────────────
    docente_nombre: Mapped[str] = mapped_column(String(300), nullable=False)
    curso: Mapped[str] = mapped_column(String(400), nullable=False)
    periodo: Mapped[str] = mapped_column(String(50), nullable=False)
    tipo_alerta: Mapped[str] = mapped_column(String(30), nullable=False)

    # ── Scope ───────────────────────────────────────────────────────────
    modalidad: Mapped[str] = mapped_column(String(20), nullable=False)

    # ── Metric data ─────────────────────────────────────────────────────
    metrica_afectada: Mapped[str] = mapped_column(String(50), nullable=False)
    valor_actual: Mapped[float] = mapped_column(Numeric(7, 2), nullable=False)
    valor_anterior: Mapped[float | None] = mapped_column(Numeric(7, 2), nullable=True)

    # ── Human-readable ──────────────────────────────────────────────────
    descripcion: Mapped[str] = mapped_column(Text, nullable=False)

    # ── Severity & lifecycle ────────────────────────────────────────────
    severidad: Mapped[str] = mapped_column(String(10), nullable=False)
    estado: Mapped[str] = mapped_column(String(15), nullable=False, default="activa")

    # ── Relationships ───────────────────────────────────────────────────
    evaluacion = relationship("Evaluacion", back_populates="alertas")

    # ── Table-level constraints & indexes ───────────────────────────────
    __table_args__ = (
        # Dedup [AL-40] + [AL-10]: one alert per docente+curso+periodo+tipo+modalidad
        UniqueConstraint(
            "docente_nombre",
            "curso",
            "periodo",
            "tipo_alerta",
            "modalidad",
            name="uq_alertas_dedup",
        ),
        # Query patterns
        Index("ix_alertas_modalidad", "modalidad"),
        Index("ix_alertas_severidad", "severidad"),
        Index("ix_alertas_estado", "estado"),
        Index("ix_alertas_modalidad_estado", "modalidad", "estado"),
        Index("ix_alertas_docente", "docente_nombre"),
        # Domain constraints
        CheckConstraint(
            "modalidad IN ('CUATRIMESTRAL', 'MENSUAL', 'B2B')",
            name="ck_alertas_modalidad",
        ),
        CheckConstraint(
            "tipo_alerta IN ('BAJO_DESEMPEÑO', 'CAIDA', 'SENTIMIENTO', 'PATRON')",
            name="ck_alertas_tipo",
        ),
        CheckConstraint(
            "severidad IN ('alta', 'media', 'baja')",
            name="ck_alertas_severidad",
        ),
        CheckConstraint(
            "estado IN ('activa', 'revisada', 'resuelta', 'descartada')",
            name="ck_alertas_estado",
        ),
    )
