"""Auth API routes.

Endpoints:
    GET  /auth/login          → redirige a Google OAuth consent screen
    GET  /auth/callback       → intercambia code por tokens, crea sesión
    POST /auth/logout         → invalida sesión activa
    GET  /auth/me             → retorna perfil y roles del usuario actual
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/me")
async def me():
    """Placeholder — retorna perfil del usuario autenticado."""
    # TODO: implementar con dependencia de sesión
    return {"detail": "Not implemented"}
