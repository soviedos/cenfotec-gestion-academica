"""Auth DTOs — request/response schemas for authentication endpoints."""

from __future__ import annotations

from pydantic import BaseModel


class UserRead(BaseModel):
    """Public user profile returned by GET /auth/me."""

    id: str
    email: str
    nombre: str
    avatar_url: str | None = None
    role: str
    activo: bool

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    """OAuth token exchange response (future use)."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int
