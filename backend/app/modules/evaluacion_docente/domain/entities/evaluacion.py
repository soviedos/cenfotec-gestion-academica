"""Evaluacion entity — extracted evaluation data from a PDF.

Central table of the system.  Analytics, alerts, rankings and dashboards
are all computed from rows in this table.
"""

from sqlalchemy import CheckConstraint, ForeignKey, Index, Numeric, SmallInteger, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.domain.entities.base import Base, TimestampMixin, UUIDMixin


class Evaluacion(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "evaluaciones"

    # ── Foreign keys ────────────────────────────────────────────────────
    documento_id: Mapped[str] = mapped_column(
        Uuid, ForeignKey("documentos.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # ── Header fields ───────────────────────────────────────────────────
    docente_nombre: Mapped[str] = mapped_column(String(300), nullable=False, index=True)
    periodo: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # ── Modalidad & temporal ordering [BR-MOD-04, BR-AN-40] ─────────────
    modalidad: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="DESCONOCIDA",
        index=True,
    )
    año: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    periodo_orden: Mapped[int] = mapped_column(SmallInteger, nullable=False)

    # ── Metrics ─────────────────────────────────────────────────────────
    materia: Mapped[str | None] = mapped_column(String(300), nullable=True)
    puntaje_general: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    resumen_ia: Mapped[str | None] = mapped_column(Text, nullable=True)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="pendiente", index=True)
    datos_completos: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Relationships ───────────────────────────────────────────────────
    documento = relationship("Documento", lazy="selectin")
    dimensiones = relationship(
        "EvaluacionDimension",
        back_populates="evaluacion",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    cursos = relationship(
        "EvaluacionCurso",
        back_populates="evaluacion",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    comentarios = relationship(
        "ComentarioAnalisis",
        back_populates="evaluacion",
        cascade="all, delete-orphan",
        lazy="noload",
    )
    alertas = relationship(
        "Alerta",
        back_populates="evaluacion",
        lazy="noload",
    )

    # ── Table-level indexes & constraints ───────────────────────────────
    __table_args__ = (
        Index("ix_evaluaciones_modalidad_periodo", "modalidad", "periodo"),
        Index("ix_evaluaciones_modalidad_año_orden", "modalidad", "año", "periodo_orden"),
        CheckConstraint(
            "modalidad IN ('CUATRIMESTRAL', 'MENSUAL', 'B2B', 'DESCONOCIDA')",
            name="ck_evaluaciones_modalidad",
        ),
        CheckConstraint("año >= 2020", name="ck_evaluaciones_año_min"),
        CheckConstraint(
            "puntaje_general IS NULL OR (puntaje_general >= 0 AND puntaje_general <= 100)",
            name="ck_evaluaciones_puntaje_rango",
        ),
    )
