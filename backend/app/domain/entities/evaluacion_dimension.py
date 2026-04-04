"""EvaluacionDimension entity — one row per dimension per evaluation."""

from sqlalchemy import ForeignKey, Numeric, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.entities.base import Base, TimestampMixin, UUIDMixin


class EvaluacionDimension(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "evaluacion_dimensiones"

    evaluacion_id: Mapped[str] = mapped_column(
        Uuid, ForeignKey("evaluaciones.id", ondelete="CASCADE"), nullable=False, index=True
    )
    nombre: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    pct_estudiante: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    pct_director: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    pct_autoeval: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    pct_promedio: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
