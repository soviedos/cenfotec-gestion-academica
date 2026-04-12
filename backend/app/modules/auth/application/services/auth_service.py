"""Authentication service — JWT token management and user lookup.

Responsibilities:
    - Create JWT access tokens for authenticated users
    - Decode and validate JWT tokens
    - Look up or provision user records from Google OAuth claims
    - Provide the current user from a valid token
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt

from app.modules.auth.domain.entities.enums import Role
from app.modules.auth.domain.entities.user import User
from app.modules.auth.infrastructure.repositories.user_repo import UserRepository
from app.shared.core.config import settings
from app.shared.core.logging import get_logger
from app.shared.domain.exceptions import NotFoundError, ValidationError

logger = get_logger(__name__)


class AuthService:
    """Handles JWT token lifecycle and user resolution."""

    def __init__(self, user_repo: UserRepository) -> None:
        self._repo = user_repo

    # ── Token creation ───────────────────────────────────────────────

    def create_access_token(self, user: User) -> str:
        """Issue a signed JWT for *user*."""
        now = datetime.now(UTC)
        payload = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role,
            "iat": now,
            "exp": now + timedelta(minutes=settings.jwt_expiration_minutes),
        }
        return jwt.encode(
            payload,
            settings.secret_key.get_secret_value(),
            algorithm=settings.jwt_algorithm,
        )

    # ── Token validation ─────────────────────────────────────────────

    @staticmethod
    def decode_token(token: str) -> dict:
        """Decode and validate a JWT. Raises ``ValidationError`` on failure."""
        try:
            return jwt.decode(
                token,
                settings.secret_key.get_secret_value(),
                algorithms=[settings.jwt_algorithm],
            )
        except jwt.ExpiredSignatureError:
            raise ValidationError("Token expirado")
        except jwt.InvalidTokenError:
            raise ValidationError("Token inválido")

    # ── User resolution ──────────────────────────────────────────────

    async def get_current_user(self, token: str) -> User:
        """Resolve a JWT to the corresponding ``User``. Raises on invalid/inactive."""
        payload = self.decode_token(token)
        user_id = payload.get("sub")
        if not user_id:
            raise ValidationError("Token sin identificador de usuario")

        user = await self._repo.get_by_id(UUID(user_id))
        if user is None:
            raise NotFoundError("Usuario", user_id)
        if not user.activo:
            raise ValidationError("Cuenta de usuario desactivada")
        return user

    async def get_or_create_from_google(
        self,
        *,
        google_sub: str,
        email: str,
        nombre: str,
        avatar_url: str | None = None,
    ) -> User:
        """Find existing user by ``google_sub`` or create a new one.

        Called after Google OAuth token verification.
        """
        user = await self._repo.get_by_google_sub(google_sub)
        if user is not None:
            logger.info("google_login | existing user=%s", user.email)
            return user

        user = User(
            email=email,
            nombre=nombre,
            avatar_url=avatar_url,
            google_sub=google_sub,
            role=Role.CONSULTOR,
        )
        user = await self._repo.create(user)
        logger.info("google_login | new user=%s role=%s", user.email, user.role)
        return user
