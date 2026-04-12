"""Module permission matrix — code-defined RBAC policy.

Single source of truth that maps (role, module) → set of permissions.
ADMIN always gets full access to every module (enforced in code, not in the matrix).

To grant a new module to a role, add an entry here.
To add a new module, add it to ``Modulo`` and optionally add matrix entries.
"""

from __future__ import annotations

from app.modules.auth.domain.entities.enums import Modulo, Permission, Role

# ── Matrix: role → module → granted permissions ──────────────────────
# Omitted entries mean "no access". ADMIN overrides are handled in code.

MODULE_PERMISSIONS: dict[Role, dict[Modulo, frozenset[Permission]]] = {
    Role.COORDINADOR: {
        Modulo.EVALUACION_DOCENTE: frozenset({Permission.READ, Permission.WRITE}),
        Modulo.CONTROL_DOCENTE: frozenset({Permission.READ, Permission.WRITE}),
        Modulo.CONVALIDACIONES: frozenset({Permission.READ}),
        Modulo.PLANIFICACION_CUATRIMESTRAL: frozenset({Permission.READ, Permission.WRITE}),
        Modulo.PLANIFICACION_MENSUAL: frozenset({Permission.READ, Permission.WRITE}),
        Modulo.PLANIFICACION_B2B: frozenset({Permission.READ, Permission.WRITE}),
    },
    Role.CONSULTOR: {
        Modulo.EVALUACION_DOCENTE: frozenset({Permission.READ}),
    },
}

# Full permission set (used for ADMIN override).
_ALL_PERMISSIONS = frozenset({Permission.READ, Permission.WRITE, Permission.ADMIN})


def get_module_permissions(role: str, modulo: Modulo) -> frozenset[Permission]:
    """Return the granted permissions for *role* in *modulo*.

    ADMIN always receives all permissions for every module.
    """
    if role == Role.ADMIN:
        return _ALL_PERMISSIONS
    return MODULE_PERMISSIONS.get(Role(role), {}).get(modulo, frozenset())


def get_accessible_modules(role: str) -> list[dict]:
    """Return a list of ``{"modulo": ..., "permisos": [...]}`` for *role*.

    Used by ``GET /auth/me`` so the frontend knows which nav items to show.
    """
    if role == Role.ADMIN:
        return [{"modulo": m.value, "permisos": sorted(_ALL_PERMISSIONS)} for m in Modulo]

    role_map = MODULE_PERMISSIONS.get(Role(role), {})
    return [
        {"modulo": m.value, "permisos": sorted(perms)} for m, perms in role_map.items() if perms
    ]
