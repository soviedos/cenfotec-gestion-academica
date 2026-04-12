"""GeminiAuditLog entity — one row per Gemini API call for traceability."""

from sqlalchemy import ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.domain.entities.base import Base, TimestampMixin, UUIDMixin


class GeminiAuditLog(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "gemini_audit_log"

    operation: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    evaluacion_id: Mapped[str | None] = mapped_column(
        Uuid, ForeignKey("evaluaciones.id", ondelete="SET NULL"), nullable=True
    )
    prompt_text: Mapped[str] = mapped_column(Text, nullable=False)
    prompt_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    response_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    model_name: Mapped[str] = mapped_column(String(50), nullable=False)
    tokens_input: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tokens_output: Mapped[int | None] = mapped_column(Integer, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(10), nullable=False, default="ok")
    error_detail: Mapped[str | None] = mapped_column(Text, nullable=True)
