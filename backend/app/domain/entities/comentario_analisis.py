"""ComentarioAnalisis entity — one row per classified comment."""

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Numeric, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.entities.base import Base, TimestampMixin, UUIDMixin


class ComentarioAnalisis(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "comentario_analisis"
    __table_args__ = (
        CheckConstraint(
            "sent_score IS NULL OR (sent_score >= -1 AND sent_score <= 1)",
            name="ck_comentario_sent_score_range",
        ),
    )

    evaluacion_id: Mapped[str] = mapped_column(
        Uuid, ForeignKey("evaluaciones.id", ondelete="CASCADE"), nullable=False, index=True
    )
    fuente: Mapped[str] = mapped_column(String(20), nullable=False)
    asignatura: Mapped[str] = mapped_column(String(300), nullable=False)
    tipo: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    texto: Mapped[str] = mapped_column(Text, nullable=False)
    tema: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    tema_confianza: Mapped[str] = mapped_column(String(10), nullable=False, default="regla")
    sentimiento: Mapped[str | None] = mapped_column(String(10), nullable=True, index=True)
    sent_score: Mapped[float | None] = mapped_column(Numeric(3, 2), nullable=True)
    procesado_ia: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # ── Relationships ───────────────────────────────────────────────────
    evaluacion = relationship("Evaluacion", back_populates="comentarios")
