"""Auth domain enums — roles and permission scopes."""

from enum import StrEnum


class Role(StrEnum):
    """Application roles (RBAC).

    ADMIN       — full access (user management, config, all data)
    COORDINADOR — read/write evaluaciones for assigned escuelas
    CONSULTOR   — read-only access to analytics and reports
    """

    ADMIN = "admin"
    COORDINADOR = "coordinador"
    CONSULTOR = "consultor"
