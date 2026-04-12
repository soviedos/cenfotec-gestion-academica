"""Auth API routes.

Endpoints:
    GET  /auth/me             → retorna perfil, roles y módulos accesibles
    POST /auth/dev-token      → (dev only) genera un JWT para pruebas locales

Google OAuth endpoints (login, callback) se agregarán cuando se integre
el flujo completo con google-auth.
"""

from __future__ import annotations

import bcrypt
from fastapi import APIRouter, Depends

from app.modules.auth.api.deps import get_current_user
from app.modules.auth.application.services.auth_service import AuthService
from app.modules.auth.application.services.authorization_service import AuthorizationService
from app.modules.auth.domain.entities.user import User
from app.modules.auth.domain.schemas.auth import TokenResponse, UserRead
from app.modules.auth.infrastructure.repositories.user_repo import UserRepository
from app.shared.core.config import settings
from app.shared.domain.exceptions import ValidationError
from app.shared.infrastructure.database.session import get_db

router = APIRouter()


@router.get("/me", response_model=UserRead)
async def me(current_user: User = Depends(get_current_user)):
    """Return profile, role, and accessible modules for the authenticated user."""
    modulos = AuthorizationService.list_modules(current_user)
    return UserRead(
        id=current_user.id,
        email=current_user.email,
        nombre=current_user.nombre,
        avatar_url=current_user.avatar_url,
        role=current_user.role,
        activo=current_user.activo,
        modulos=modulos,
    )


@router.post("/dev-token", response_model=TokenResponse)
async def dev_token(
    email: str,
    password: str,
    db=Depends(get_db),
):
    """Authenticate with email + password. In dev mode, auto-creates the user if missing."""
    if not settings.is_development:
        raise ValidationError("Endpoint disponible solo en entorno de desarrollo")

    repo = UserRepository(db)
    auth = AuthService(repo)

    user = await repo.get_by_email(email)

    if user is None:
        # Dev convenience: auto-create with hashed password
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        user = User(
            email=email,
            nombre="Dev User",
            avatar_url=None,
            google_sub=f"dev-{email}",
            role="admin",
            password_hash=hashed,
        )
        user = await repo.create(user)
    else:
        # Validate password
        if not user.password_hash:
            raise ValidationError("Usuario no tiene contraseña configurada")
        if not bcrypt.checkpw(password.encode(), user.password_hash.encode()):
            raise ValidationError("Credenciales inválidas")

    if not user.activo:
        raise ValidationError("Cuenta de usuario desactivada")

    token = auth.create_access_token(user)
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=settings.jwt_expiration_minutes * 60,
    )
