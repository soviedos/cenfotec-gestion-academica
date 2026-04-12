"""DuplicadoProbable entity — records a probable-duplicate finding.

Two documents share the same content_fingerprint (logical signature
built from docente + periodo + modalidad + cursos + puntaje) but have
different SHA-256 hashes.  This means the same evaluation was likely
uploaded twice from different PDF exports.

The finding is **non-blocking**: both documents remain fully usable.
A human reviewer can later confirm or discard the finding.
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
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.domain.entities.base import Base, TimestampMixin, UUIDMixin


class DuplicadoProbable(UUIDMixin, TimestampMixin, Base):
    """A probable-duplicate finding between two documents."""

    __tablename__ = "duplicados_probables"

    # ── Pair of documents ───────────────────────────────────────────
    documento_id: Mapped[str] = mapped_column(
        Uuid,
        ForeignKey("documentos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    documento_coincidente_id: Mapped[str] = mapped_column(
        Uuid,
        ForeignKey("documentos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── Match evidence ──────────────────────────────────────────────
    fingerprint: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )
    score: Mapped[float] = mapped_column(
        Numeric(3, 2),
        nullable=False,
        default=1.0,
    )
    criterios: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
    )

    # ── Resolution ──────────────────────────────────────────────────
    estado: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pendiente",
    )
    notas: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Relationships ───────────────────────────────────────────────
    documento = relationship(
        "Documento",
        foreign_keys=[documento_id],
        lazy="selectin",
    )
    documento_coincidente = relationship(
        "Documento",
        foreign_keys=[documento_coincidente_id],
        lazy="selectin",
    )

    # ── Constraints ─────────────────────────────────────────────────
    __table_args__ = (
        # Prevent recording the same pair twice (order-independent).
        # Convention: documento_id < documento_coincidente_id enforced at app layer.
        UniqueConstraint(
            "documento_id",
            "documento_coincidente_id",
            name="uq_duplicados_par",
        ),
        CheckConstraint(
            "documento_id != documento_coincidente_id",
            name="ck_duplicados_no_self",
        ),
        CheckConstraint(
            "estado IN ('pendiente', 'confirmado', 'descartado')",
            name="ck_duplicados_estado",
        ),
        CheckConstraint(
            "score >= 0.0 AND score <= 1.0",
            name="ck_duplicados_score_rango",
        ),
        Index(
            "ix_duplicados_estado_pendiente",
            "estado",
            postgresql_where="estado = 'pendiente'",
        ),
    )
