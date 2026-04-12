"""Auth domain enums — roles, modules, and permission scopes."""

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


class Modulo(StrEnum):
    """Platform modules — each maps to a bounded context."""

    EVALUACION_DOCENTE = "evaluacion_docente"
    CONTROL_DOCENTE = "control_docente"
    CONVALIDACIONES = "convalidaciones"
    PLANIFICACION_CUATRIMESTRAL = "planificacion_cuatrimestral"
    PLANIFICACION_MENSUAL = "planificacion_mensual"
    PLANIFICACION_B2B = "planificacion_b2b"


class Permission(StrEnum):
    """Actions that can be performed within a module."""

    READ = "read"
    WRITE = "write"
    ADMIN = "admin"
