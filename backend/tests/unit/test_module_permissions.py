"""Unit tests for module permission matrix and access control."""

import pytest

from app.modules.auth.application.services.authorization_service import AuthorizationService
from app.modules.auth.domain.entities.enums import Modulo, Permission, Role
from app.modules.auth.domain.entities.user import User
from app.modules.auth.domain.permissions import get_accessible_modules, get_module_permissions
from app.shared.domain.exceptions import ValidationError


def _make_user(role: str) -> User:
    return User(
        email="test@test.com",
        nombre="Test",
        google_sub=f"sub-{role}",
        role=role,
    )


# ── get_module_permissions ───────────────────────────────────────────


class TestGetModulePermissions:
    def test_admin_gets_all_permissions_for_any_module(self):
        for modulo in Modulo:
            perms = get_module_permissions(Role.ADMIN, modulo)
            assert Permission.READ in perms
            assert Permission.WRITE in perms
            assert Permission.ADMIN in perms

    def test_coordinador_can_read_write_evaluacion_docente(self):
        perms = get_module_permissions(Role.COORDINADOR, Modulo.EVALUACION_DOCENTE)
        assert Permission.READ in perms
        assert Permission.WRITE in perms
        assert Permission.ADMIN not in perms

    def test_coordinador_can_read_write_planificacion_modules(self):
        for mod in (
            Modulo.PLANIFICACION_CUATRIMESTRAL,
            Modulo.PLANIFICACION_MENSUAL,
            Modulo.PLANIFICACION_B2B,
        ):
            perms = get_module_permissions(Role.COORDINADOR, mod)
            assert Permission.READ in perms
            assert Permission.WRITE in perms

    def test_coordinador_read_only_convalidaciones(self):
        perms = get_module_permissions(Role.COORDINADOR, Modulo.CONVALIDACIONES)
        assert Permission.READ in perms
        assert Permission.WRITE not in perms

    def test_consultor_can_read_evaluacion_docente(self):
        perms = get_module_permissions(Role.CONSULTOR, Modulo.EVALUACION_DOCENTE)
        assert Permission.READ in perms
        assert Permission.WRITE not in perms

    def test_consultor_has_no_access_to_control_docente(self):
        perms = get_module_permissions(Role.CONSULTOR, Modulo.CONTROL_DOCENTE)
        assert len(perms) == 0

    def test_consultor_has_no_access_to_planificacion(self):
        for mod in (
            Modulo.PLANIFICACION_CUATRIMESTRAL,
            Modulo.PLANIFICACION_MENSUAL,
            Modulo.PLANIFICACION_B2B,
        ):
            perms = get_module_permissions(Role.CONSULTOR, mod)
            assert len(perms) == 0


# ── get_accessible_modules ───────────────────────────────────────────


class TestGetAccessibleModules:
    def test_admin_sees_all_modules(self):
        modules = get_accessible_modules(Role.ADMIN)
        module_names = {m["modulo"] for m in modules}
        assert module_names == {m.value for m in Modulo}

    def test_admin_modules_have_all_permissions(self):
        modules = get_accessible_modules(Role.ADMIN)
        for m in modules:
            assert "read" in m["permisos"]
            assert "write" in m["permisos"]
            assert "admin" in m["permisos"]

    def test_coordinador_sees_six_modules(self):
        modules = get_accessible_modules(Role.COORDINADOR)
        assert len(modules) == 6

    def test_consultor_sees_one_module(self):
        modules = get_accessible_modules(Role.CONSULTOR)
        assert len(modules) == 1
        assert modules[0]["modulo"] == "evaluacion_docente"
        assert modules[0]["permisos"] == ["read"]

    def test_modules_list_is_sorted_permissions(self):
        modules = get_accessible_modules(Role.ADMIN)
        for m in modules:
            assert m["permisos"] == sorted(m["permisos"])


# ── AuthorizationService.require_module ──────────────────────────────


class TestRequireModule:
    def test_admin_passes_any_module(self):
        user = _make_user(Role.ADMIN)
        for modulo in Modulo:
            AuthorizationService.require_module(user, modulo, Permission.ADMIN)

    def test_coordinador_passes_read_evaluacion(self):
        user = _make_user(Role.COORDINADOR)
        AuthorizationService.require_module(user, Modulo.EVALUACION_DOCENTE, Permission.READ)

    def test_coordinador_passes_write_evaluacion(self):
        user = _make_user(Role.COORDINADOR)
        AuthorizationService.require_module(user, Modulo.EVALUACION_DOCENTE, Permission.WRITE)

    def test_coordinador_fails_admin_evaluacion(self):
        user = _make_user(Role.COORDINADOR)
        with pytest.raises(ValidationError, match="Sin acceso"):
            AuthorizationService.require_module(user, Modulo.EVALUACION_DOCENTE, Permission.ADMIN)

    def test_consultor_passes_read_evaluacion(self):
        user = _make_user(Role.CONSULTOR)
        AuthorizationService.require_module(user, Modulo.EVALUACION_DOCENTE, Permission.READ)

    def test_consultor_fails_write_evaluacion(self):
        user = _make_user(Role.CONSULTOR)
        with pytest.raises(ValidationError, match="Sin acceso"):
            AuthorizationService.require_module(user, Modulo.EVALUACION_DOCENTE, Permission.WRITE)

    def test_consultor_fails_control_docente(self):
        user = _make_user(Role.CONSULTOR)
        with pytest.raises(ValidationError, match="Sin acceso"):
            AuthorizationService.require_module(user, Modulo.CONTROL_DOCENTE)


# ── AuthorizationService.has_module_permission ───────────────────────


class TestHasModulePermission:
    def test_admin_has_all(self):
        user = _make_user(Role.ADMIN)
        assert AuthorizationService.has_module_permission(
            user, Modulo.CONVALIDACIONES, Permission.ADMIN
        )

    def test_consultor_has_read_eval(self):
        user = _make_user(Role.CONSULTOR)
        assert AuthorizationService.has_module_permission(
            user, Modulo.EVALUACION_DOCENTE, Permission.READ
        )

    def test_consultor_no_write_eval(self):
        user = _make_user(Role.CONSULTOR)
        assert not AuthorizationService.has_module_permission(
            user, Modulo.EVALUACION_DOCENTE, Permission.WRITE
        )

    def test_consultor_no_access_planificacion(self):
        user = _make_user(Role.CONSULTOR)
        assert not AuthorizationService.has_module_permission(user, Modulo.PLANIFICACION_B2B)


# ── AuthorizationService.list_modules ────────────────────────────────


class TestListModules:
    def test_returns_correct_shape(self):
        user = _make_user(Role.CONSULTOR)
        modules = AuthorizationService.list_modules(user)
        assert isinstance(modules, list)
        assert all("modulo" in m and "permisos" in m for m in modules)

    def test_admin_gets_all(self):
        user = _make_user(Role.ADMIN)
        modules = AuthorizationService.list_modules(user)
        assert len(modules) == len(Modulo)
