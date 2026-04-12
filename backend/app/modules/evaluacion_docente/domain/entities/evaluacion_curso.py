"""EvaluacionCurso entity — one row per course-group per evaluation.

Granularity unit for alerts [AL-10]: docente + curso + periodo + modalidad.
"""

from sqlalchemy import ForeignKey, Integer, Numeric, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.domain.entities.base import Base, TimestampMixin, UUIDMixin


class EvaluacionCurso(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "evaluacion_cursos"

    evaluacion_id: Mapped[str] = mapped_column(
        Uuid, ForeignKey("evaluaciones.id", ondelete="CASCADE"), nullable=False, index=True
    )
    escuela: Mapped[str | None] = mapped_column(String(200), nullable=True)
    codigo: Mapped[str | None] = mapped_column(String(50), nullable=True)
    nombre: Mapped[str | None] = mapped_column(String(300), nullable=True)
    grupo: Mapped[str | None] = mapped_column(String(50), nullable=True)
    respondieron: Mapped[int | None] = mapped_column(Integer, nullable=True)
    matriculados: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pct_estudiante: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    pct_director: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    pct_autoeval: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    pct_promedio: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)

    # ── Relationships ───────────────────────────────────────────────────
    evaluacion = relationship("Evaluacion", back_populates="cursos")

    __table_args__ = (
        UniqueConstraint("evaluacion_id", "codigo", "grupo", name="uq_eval_curso_eval_cod_grupo"),
    )
