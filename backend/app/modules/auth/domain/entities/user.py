"""User entity — authenticated platform user.

Maps to the ``users`` table. Created on first successful Google login.
"""

from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.domain.entities.base import Base, TimestampMixin, UUIDMixin


class User(UUIDMixin, TimestampMixin, Base):
    """Registered platform user (sourced from Google OAuth)."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False, index=True)
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    google_sub: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        comment="Google 'sub' claim — stable user identifier",
    )
    role: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="consultor",
        comment="RBAC role: admin | coordinador | consultor",
    )
    activo: Mapped[bool] = mapped_column(default=True)
