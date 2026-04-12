"""Authorization service — role-based access control (RBAC).

Provides helpers to enforce that the current user holds the required role
and has access to specific platform modules.
"""

from __future__ import annotations

from app.modules.auth.domain.entities.enums import Modulo, Permission, Role
from app.modules.auth.domain.entities.user import User
from app.modules.auth.domain.permissions import get_accessible_modules, get_module_permissions
from app.shared.domain.exceptions import ValidationError

# Role hierarchy: higher roles include all permissions of lower roles.
_ROLE_LEVEL: dict[str, int] = {
    Role.CONSULTOR: 0,
    Role.COORDINADOR: 1,
    Role.ADMIN: 2,
}


class AuthorizationService:
    """Checks permissions for the authenticated user."""

    # ── Role-level checks ────────────────────────────────────────────

    @staticmethod
    def require_role(user: User, minimum_role: Role) -> None:
        """Raise ``ValidationError`` if *user* lacks *minimum_role* or higher."""
        user_level = _ROLE_LEVEL.get(user.role, -1)
        required_level = _ROLE_LEVEL.get(minimum_role, 0)
        if user_level < required_level:
            raise ValidationError(
                f"Permiso insuficiente: se requiere rol '{minimum_role}' o superior"
            )

    @staticmethod
    def has_role(user: User, minimum_role: Role) -> bool:
        """Return True if *user* holds *minimum_role* or higher."""
        user_level = _ROLE_LEVEL.get(user.role, -1)
        required_level = _ROLE_LEVEL.get(minimum_role, 0)
        return user_level >= required_level

    # ── Module-level checks ──────────────────────────────────────────

    @staticmethod
    def require_module(
        user: User, modulo: Modulo, permission: Permission = Permission.READ
    ) -> None:
        """Raise ``ValidationError`` if *user* lacks *permission* for *modulo*."""
        granted = get_module_permissions(user.role, modulo)
        if permission not in granted:
            raise ValidationError(
                f"Sin acceso al módulo '{modulo}' (requiere permiso '{permission}')"
            )

    @staticmethod
    def has_module_permission(
        user: User, modulo: Modulo, permission: Permission = Permission.READ
    ) -> bool:
        """Return True if *user* has *permission* for *modulo*."""
        return permission in get_module_permissions(user.role, modulo)

    @staticmethod
    def list_modules(user: User) -> list[dict]:
        """Return accessible modules with their permissions for *user*."""
        return get_accessible_modules(user.role)
