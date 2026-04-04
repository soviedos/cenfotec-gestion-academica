"""Evaluacion entity — extracted evaluation data from a PDF."""

from sqlalchemy import ForeignKey, Numeric, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.entities.base import Base, TimestampMixin, UUIDMixin


class Evaluacion(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "evaluaciones"

    documento_id: Mapped[str] = mapped_column(
        Uuid, ForeignKey("documentos.id", ondelete="CASCADE"), nullable=False
    )
    docente_nombre: Mapped[str] = mapped_column(String(300), nullable=False)
    periodo: Mapped[str] = mapped_column(String(50), nullable=False)
    materia: Mapped[str | None] = mapped_column(String(300), nullable=True)
    puntaje_general: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    resumen_ia: Mapped[str | None] = mapped_column(Text, nullable=True)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="pendiente")
    datos_completos: Mapped[str | None] = mapped_column(Text, nullable=True)

    documento = relationship("Documento", lazy="selectin")
