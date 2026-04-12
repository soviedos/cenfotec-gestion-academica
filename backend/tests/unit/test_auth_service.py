"""Unit tests for AuthService — no I/O, pure JWT logic."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock
from uuid import uuid4

import jwt
import pytest

from app.modules.auth.application.services.auth_service import AuthService
from app.modules.auth.domain.entities.enums import Role
from app.modules.auth.domain.entities.user import User
from app.shared.core.config import settings
from app.shared.domain.exceptions import NotFoundError, ValidationError


def _make_user(**overrides) -> User:
    defaults = {
        "email": "test@cenfotec.ac.cr",
        "nombre": "Test User",
        "avatar_url": None,
        "google_sub": "google-123",
        "role": Role.CONSULTOR,
        "activo": True,
    }
    defaults.update(overrides)
    user = User(**defaults)
    if "id" not in overrides:
        user.id = uuid4()
    return user


class TestCreateAccessToken:
    def test_returns_valid_jwt(self):
        user = _make_user()
        repo = AsyncMock()
        svc = AuthService(repo)

        token = svc.create_access_token(user)
        payload = jwt.decode(
            token,
            settings.secret_key.get_secret_value(),
            algorithms=[settings.jwt_algorithm],
        )

        assert payload["sub"] == str(user.id)
        assert payload["email"] == user.email
        assert payload["role"] == user.role

    def test_token_has_expiration(self):
        user = _make_user()
        svc = AuthService(AsyncMock())

        token = svc.create_access_token(user)
        payload = jwt.decode(
            token,
            settings.secret_key.get_secret_value(),
            algorithms=[settings.jwt_algorithm],
        )

        assert "exp" in payload
        exp = datetime.fromtimestamp(payload["exp"], tz=UTC)
        assert exp > datetime.now(UTC)


class TestDecodeToken:
    def test_valid_token(self):
        user = _make_user()
        svc = AuthService(AsyncMock())
        token = svc.create_access_token(user)

        payload = AuthService.decode_token(token)

        assert payload["sub"] == str(user.id)

    def test_expired_token_raises(self):
        payload = {
            "sub": str(uuid4()),
            "email": "x@test.com",
            "role": "consultor",
            "iat": datetime.now(UTC) - timedelta(hours=10),
            "exp": datetime.now(UTC) - timedelta(hours=1),
        }
        token = jwt.encode(
            payload,
            settings.secret_key.get_secret_value(),
            algorithm=settings.jwt_algorithm,
        )

        with pytest.raises(ValidationError, match="expirado"):
            AuthService.decode_token(token)

    def test_tampered_token_raises(self):
        with pytest.raises(ValidationError, match="inválido"):
            AuthService.decode_token("not.a.valid.token")

    def test_wrong_secret_raises(self):
        payload = {
            "sub": str(uuid4()),
            "exp": datetime.now(UTC) + timedelta(hours=1),
        }
        token = jwt.encode(payload, "wrong-secret", algorithm="HS256")

        with pytest.raises(ValidationError, match="inválido"):
            AuthService.decode_token(token)


class TestGetCurrentUser:
    async def test_returns_user_for_valid_token(self):
        user = _make_user()
        repo = AsyncMock()
        repo.get_by_id.return_value = user
        svc = AuthService(repo)

        token = svc.create_access_token(user)
        result = await svc.get_current_user(token)

        assert result.id == user.id
        repo.get_by_id.assert_awaited_once_with(user.id)

    async def test_raises_if_user_not_found(self):
        user = _make_user()
        repo = AsyncMock()
        repo.get_by_id.return_value = None
        svc = AuthService(repo)

        token = svc.create_access_token(user)

        with pytest.raises(NotFoundError, match="Usuario"):
            await svc.get_current_user(token)

    async def test_raises_if_user_inactive(self):
        user = _make_user(activo=False)
        repo = AsyncMock()
        repo.get_by_id.return_value = user
        svc = AuthService(repo)

        token = svc.create_access_token(user)

        with pytest.raises(ValidationError, match="desactivada"):
            await svc.get_current_user(token)


class TestGetOrCreateFromGoogle:
    async def test_returns_existing_user(self):
        user = _make_user()
        repo = AsyncMock()
        repo.get_by_google_sub.return_value = user
        svc = AuthService(repo)

        result = await svc.get_or_create_from_google(
            google_sub="google-123",
            email="test@cenfotec.ac.cr",
            nombre="Test",
        )

        assert result is user
        repo.create.assert_not_awaited()

    async def test_creates_new_user_if_not_exists(self):
        repo = AsyncMock()
        repo.get_by_google_sub.return_value = None
        repo.create.side_effect = lambda u: u
        svc = AuthService(repo)

        result = await svc.get_or_create_from_google(
            google_sub="google-new",
            email="new@cenfotec.ac.cr",
            nombre="New User",
        )

        assert result.email == "new@cenfotec.ac.cr"
        assert result.role == Role.CONSULTOR
        repo.create.assert_awaited_once()
