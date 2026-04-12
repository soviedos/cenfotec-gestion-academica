"""Auth dependencies for FastAPI route injection.

Usage in any route::

    from app.modules.auth.api.deps import CurrentUser, require_admin

    @router.get("/protected")
    async def protected(user: CurrentUser):
        ...

    @router.delete("/admin-only", dependencies=[Depends(require_admin)])
    async def admin_only():
        ...

Module-level guards::

    from app.modules.auth.api.deps import require_module
    from app.modules.auth.domain.entities.enums import Modulo, Permission

    # Read access to evaluacion_docente
    @router.get("/eval", dependencies=[Depends(require_module(Modulo.EVALUACION_DOCENTE))])
    async def list_evals():
        ...

    # Write access to control_docente
    dep = require_module(Modulo.CONTROL_DOCENTE, Permission.WRITE)

    @router.post("/ctrl", dependencies=[Depends(dep)])
    async def create_ctrl():
        ...
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.modules.auth.application.services.auth_service import AuthService
from app.modules.auth.application.services.authorization_service import AuthorizationService
from app.modules.auth.domain.entities.enums import Modulo, Permission, Role
from app.modules.auth.domain.entities.user import User
from app.modules.auth.infrastructure.repositories.user_repo import UserRepository
from app.shared.infrastructure.database.session import get_db

_bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
    db=Depends(get_db),
) -> User:
    """Extract and validate JWT from Authorization header, return the User."""
    repo = UserRepository(db)
    auth = AuthService(repo)
    return await auth.get_current_user(credentials.credentials)


# Typed annotation shortcut for route signatures.
CurrentUser = Annotated[User, Depends(get_current_user)]


# ── Role guards ──────────────────────────────────────────────────────


def _role_checker(minimum_role: Role):
    """Factory that returns a dependency enforcing *minimum_role*."""

    async def _check(user: CurrentUser) -> User:
        AuthorizationService.require_role(user, minimum_role)
        return user

    return _check


require_admin = _role_checker(Role.ADMIN)
require_coordinador = _role_checker(Role.COORDINADOR)
require_consultor = _role_checker(Role.CONSULTOR)


# ── Module guards ────────────────────────────────────────────────────


def require_module(modulo: Modulo, permission: Permission = Permission.READ):
    """Factory that returns a dependency enforcing module-level access.

    Example::

        @router.get("/", dependencies=[Depends(require_module(Modulo.EVALUACION_DOCENTE))])
    """

    async def _check(user: CurrentUser) -> User:
        AuthorizationService.require_module(user, modulo, permission)
        return user

    return _check
