"""API tests — /auth endpoints."""

import bcrypt
import pytest

from app.main import app
from app.modules.auth.api.deps import get_current_user
from app.modules.auth.domain.entities.enums import Modulo, Role
from app.modules.auth.domain.entities.user import User
from app.modules.auth.infrastructure.repositories.user_repo import UserRepository

pytestmark = pytest.mark.api


def _make_user(**overrides) -> User:
    from uuid import uuid4

    defaults = {
        "email": "me@cenfotec.ac.cr",
        "nombre": "Test User",
        "avatar_url": "https://example.com/avatar.png",
        "google_sub": "google-sub-123",
        "role": Role.CONSULTOR,
        "activo": True,
    }
    defaults.update(overrides)
    user = User(**defaults)
    if "id" not in overrides:
        user.id = uuid4()
    return user


class TestAuthMe:
    async def test_returns_user_profile(self, client):
        user = _make_user()

        async def _override():
            return user

        app.dependency_overrides[get_current_user] = _override
        try:
            response = await client.get("/api/v1/auth/me")
        finally:
            app.dependency_overrides.pop(get_current_user, None)

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == user.email
        assert data["nombre"] == user.nombre
        assert data["role"] == user.role
        assert data["activo"] is True
        # Consultor should see only evaluacion_docente with read
        assert "modulos" in data
        assert len(data["modulos"]) == 1
        assert data["modulos"][0]["modulo"] == "evaluacion_docente"
        assert data["modulos"][0]["permisos"] == ["read"]

    async def test_returns_401_without_token(self, client):
        # No override → HTTPBearer will reject the request
        app.dependency_overrides.pop(get_current_user, None)
        response = await client.get("/api/v1/auth/me")
        assert response.status_code in (401, 403)

    async def test_returns_admin_role(self, client):
        user = _make_user(role=Role.ADMIN)

        async def _override():
            return user

        app.dependency_overrides[get_current_user] = _override
        try:
            response = await client.get("/api/v1/auth/me")
        finally:
            app.dependency_overrides.pop(get_current_user, None)

        assert response.json()["role"] == "admin"

    async def test_admin_sees_all_modules(self, client):
        user = _make_user(role=Role.ADMIN)

        async def _override():
            return user

        app.dependency_overrides[get_current_user] = _override
        try:
            response = await client.get("/api/v1/auth/me")
        finally:
            app.dependency_overrides.pop(get_current_user, None)

        data = response.json()
        module_names = {m["modulo"] for m in data["modulos"]}
        assert module_names == {m.value for m in Modulo}
        # Each module should have admin, read, write
        for m in data["modulos"]:
            assert sorted(m["permisos"]) == ["admin", "read", "write"]


class TestDevToken:
    async def test_issues_token_in_dev(self, client, db):
        response = await client.post(
            "/api/v1/auth/dev-token",
            params={"email": "dev@cenfotec.ac.cr", "password": "secret123"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] > 0

    async def test_reuses_existing_user(self, client, db):
        # Create user first with a password
        repo = UserRepository(db)
        pw_hash = bcrypt.hashpw(b"mypassword", bcrypt.gensalt()).decode()
        user = User(
            email="existing@cenfotec.ac.cr",
            nombre="Existing",
            google_sub="dev-existing@cenfotec.ac.cr",
            role=Role.COORDINADOR,
            password_hash=pw_hash,
        )
        await repo.create(user)

        response = await client.post(
            "/api/v1/auth/dev-token",
            params={"email": "existing@cenfotec.ac.cr", "password": "mypassword"},
        )

        assert response.status_code == 200
        assert "access_token" in response.json()

    async def test_wrong_password_rejected(self, client, db):
        repo = UserRepository(db)
        pw_hash = bcrypt.hashpw(b"correct", bcrypt.gensalt()).decode()
        user = User(
            email="secure@cenfotec.ac.cr",
            nombre="Secure",
            google_sub="dev-secure@cenfotec.ac.cr",
            role=Role.ADMIN,
            password_hash=pw_hash,
        )
        await repo.create(user)

        response = await client.post(
            "/api/v1/auth/dev-token",
            params={"email": "secure@cenfotec.ac.cr", "password": "wrong"},
        )

        assert response.status_code == 422

    async def test_token_is_valid_for_me_endpoint(self, client, db):
        # Get a dev token (auto-creates user)
        resp = await client.post(
            "/api/v1/auth/dev-token",
            params={"email": "roundtrip@cenfotec.ac.cr", "password": "testpass"},
        )
        token = resp.json()["access_token"]

        # Remove any override so real auth runs
        app.dependency_overrides.pop(get_current_user, None)

        # Use it to call /me
        resp2 = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert resp2.status_code == 200
        assert resp2.json()["email"] == "roundtrip@cenfotec.ac.cr"
