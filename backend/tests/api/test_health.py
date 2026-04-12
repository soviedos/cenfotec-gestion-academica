"""API tests — /health endpoint."""

import pytest

pytestmark = pytest.mark.api


class TestHealthEndpoint:
    async def test_returns_ok(self, client):
        response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["database"] == "connected"

    async def test_contains_version_and_environment(self, client):
        response = await client.get("/health")

        data = response.json()
        assert "version" in data
        assert "environment" in data

    async def test_version_matches_settings(self, client):
        from app.shared.core.config import settings

        response = await client.get("/health")

        data = response.json()
        assert data["version"] == settings.app_version
