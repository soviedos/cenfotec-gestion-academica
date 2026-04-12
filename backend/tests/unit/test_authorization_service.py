"""Unit tests for AuthorizationService — no I/O, pure RBAC logic."""

import pytest

from app.modules.auth.application.services.authorization_service import AuthorizationService
from app.modules.auth.domain.entities.enums import Role
from app.modules.auth.domain.entities.user import User
from app.shared.domain.exceptions import ValidationError


def _make_user(role: str) -> User:
    return User(
        email="test@test.com",
        nombre="Test",
        google_sub=f"sub-{role}",
        role=role,
    )


class TestRequireRole:
    def test_admin_passes_admin_check(self):
        AuthorizationService.require_role(_make_user(Role.ADMIN), Role.ADMIN)

    def test_admin_passes_coordinador_check(self):
        AuthorizationService.require_role(_make_user(Role.ADMIN), Role.COORDINADOR)

    def test_admin_passes_consultor_check(self):
        AuthorizationService.require_role(_make_user(Role.ADMIN), Role.CONSULTOR)

    def test_coordinador_passes_coordinador_check(self):
        AuthorizationService.require_role(_make_user(Role.COORDINADOR), Role.COORDINADOR)

    def test_coordinador_passes_consultor_check(self):
        AuthorizationService.require_role(_make_user(Role.COORDINADOR), Role.CONSULTOR)

    def test_coordinador_fails_admin_check(self):
        with pytest.raises(ValidationError, match="Permiso insuficiente"):
            AuthorizationService.require_role(_make_user(Role.COORDINADOR), Role.ADMIN)

    def test_consultor_fails_admin_check(self):
        with pytest.raises(ValidationError, match="Permiso insuficiente"):
            AuthorizationService.require_role(_make_user(Role.CONSULTOR), Role.ADMIN)

    def test_consultor_fails_coordinador_check(self):
        with pytest.raises(ValidationError, match="Permiso insuficiente"):
            AuthorizationService.require_role(_make_user(Role.CONSULTOR), Role.COORDINADOR)

    def test_consultor_passes_consultor_check(self):
        AuthorizationService.require_role(_make_user(Role.CONSULTOR), Role.CONSULTOR)


class TestHasRole:
    def test_admin_has_all_roles(self):
        user = _make_user(Role.ADMIN)
        assert AuthorizationService.has_role(user, Role.ADMIN)
        assert AuthorizationService.has_role(user, Role.COORDINADOR)
        assert AuthorizationService.has_role(user, Role.CONSULTOR)

    def test_consultor_only_has_consultor(self):
        user = _make_user(Role.CONSULTOR)
        assert AuthorizationService.has_role(user, Role.CONSULTOR)
        assert not AuthorizationService.has_role(user, Role.COORDINADOR)
        assert not AuthorizationService.has_role(user, Role.ADMIN)

    def test_unknown_role_is_denied(self):
        user = _make_user("unknown")
        assert not AuthorizationService.has_role(user, Role.CONSULTOR)
