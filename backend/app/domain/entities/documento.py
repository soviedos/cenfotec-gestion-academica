"""Documento entity — represents an uploaded PDF file."""

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.entities.base import Base, TimestampMixin, UUIDMixin


class Documento(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "documentos"

    nombre_archivo: Mapped[str] = mapped_column(String(500), nullable=False)
    hash_sha256: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    storage_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    estado: Mapped[str] = mapped_column(String(20), nullable=False, default="subido")
    tamano_bytes: Mapped[int] = mapped_column(nullable=True)
    error_detalle: Mapped[str | None] = mapped_column(Text, nullable=True)
