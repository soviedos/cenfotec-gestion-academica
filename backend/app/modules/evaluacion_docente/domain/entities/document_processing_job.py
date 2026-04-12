"""DocumentProcessingJob entity — one row per pipeline execution.

Separates processing trace from the document itself, enabling
reprocessing history, ParseError/ParseWarning persistence [BR-PROC-03],
and parser-version tracking.
"""

from datetime import datetime
from typing import Any

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.domain.entities.base import Base, TimestampMixin, UUIDMixin


class DocumentProcessingJob(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "document_processing_jobs"

    documento_id: Mapped[str] = mapped_column(
        Uuid,
        ForeignKey("documentos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="pendiente", index=True)
    parser_version: Mapped[str] = mapped_column(String(20), nullable=False)

    # ── Execution metadata ──────────────────────────────────────────────
    pages_processed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    evaluaciones_creadas: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # ── Structured logs [BR-PROC-03] ────────────────────────────────────
    errors: Mapped[list[Any] | None] = mapped_column(JSONB, nullable=True, default=list)
    warnings: Mapped[list[Any] | None] = mapped_column(JSONB, nullable=True, default=list)

    # ── Timing ──────────────────────────────────────────────────────────
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # ── Relationships ───────────────────────────────────────────────────
    documento = relationship("Documento", lazy="selectin")

    __table_args__ = (
        CheckConstraint(
            "estado IN ('pendiente', 'procesando', 'completado', 'error')",
            name="ck_processing_jobs_estado",
        ),
    )
