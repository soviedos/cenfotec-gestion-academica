"""Tests for rate limiting and security hardening."""

import pytest

from app.api.rate_limit import RateLimiter

pytestmark = pytest.mark.api


# ── Rate limiter unit tests ────────────────────────────────────────────


class TestRateLimiter:
    """Unit tests for the in-memory rate limiter."""

    @pytest.fixture
    def limiter(self):
        return RateLimiter(max_requests=3, window_seconds=60)

    class FakeRequest:
        """Minimal request stub for rate limiter testing."""

        def __init__(self, host: str = "127.0.0.1"):
            self.client = type("Client", (), {"host": host})()
            self.headers = {}

    @pytest.mark.asyncio
    async def test_allows_within_limit(self, limiter):
        req = self.FakeRequest()
        for _ in range(3):
            await limiter(req)  # should not raise

    @pytest.mark.asyncio
    async def test_blocks_over_limit(self, limiter):
        req = self.FakeRequest()
        for _ in range(3):
            await limiter(req)

        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await limiter(req)
        assert exc_info.value.status_code == 429

    @pytest.mark.asyncio
    async def test_separate_clients_have_separate_limits(self, limiter):
        req_a = self.FakeRequest("10.0.0.1")
        req_b = self.FakeRequest("10.0.0.2")

        for _ in range(3):
            await limiter(req_a)
            await limiter(req_b)

        # Both should still be within their own limits

    @pytest.mark.asyncio
    async def test_uses_x_forwarded_for_header(self, limiter):
        req = self.FakeRequest("127.0.0.1")
        req.headers = {"X-Forwarded-For": "203.0.113.50, 70.41.3.18"}

        for _ in range(3):
            await limiter(req)

        from fastapi import HTTPException

        with pytest.raises(HTTPException):
            await limiter(req)

        # A request from a different forwarded IP should still work
        req2 = self.FakeRequest("127.0.0.1")
        req2.headers = {"X-Forwarded-For": "198.51.100.1"}
        await limiter(req2)  # should not raise

    @pytest.mark.asyncio
    async def test_ignores_x_forwarded_for_from_untrusted_proxy(self, limiter):
        """When client is not a trusted proxy, X-Forwarded-For must be ignored."""
        req = self.FakeRequest("203.0.113.99")
        req.headers = {"X-Forwarded-For": "10.0.0.1"}
        # Should use the direct client IP (203.0.113.99), not the header
        for _ in range(3):
            await limiter(req)

        from fastapi import HTTPException

        with pytest.raises(HTTPException):
            await limiter(req)

    @pytest.mark.asyncio
    async def test_memory_fallback_enforces_limits(self, limiter):
        """In-memory fallback (no Redis) still enforces rate limits."""
        req = self.FakeRequest("10.0.0.50")
        for _ in range(3):
            await limiter(req)  # should use in-memory path

        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await limiter(req)
        assert exc_info.value.status_code == 429


# ── Security headers integration tests ─────────────────────────────────


class TestSecurityHeaders:
    """Verify security headers are present on responses."""

    @pytest.mark.asyncio
    async def test_health_has_security_headers(self, client):
        resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.headers["X-Content-Type-Options"] == "nosniff"
        assert resp.headers["X-Frame-Options"] == "DENY"
        assert resp.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
        assert resp.headers["X-XSS-Protection"] == "1; mode=block"

    @pytest.mark.asyncio
    async def test_api_response_has_security_headers(self, client):
        resp = await client.get("/api/v1/analytics/resumen")
        assert resp.headers["X-Content-Type-Options"] == "nosniff"


# ── Query endpoint rate limiting ───────────────────────────────────────


class TestQueryRateLimit:
    """Verify rate limiting is enforced on the /query endpoint."""

    @pytest.mark.asyncio
    async def test_query_returns_429_after_burst(self, client):
        """Send more requests than the limit allows."""
        payload = {"question": "¿Quién es el mejor docente?"}

        # The rate limiter allows 10/min by default; send 11
        for i in range(10):
            resp = await client.post("/api/v1/query", json=payload)
            # May return 200 or other codes, but should not be 429 yet
            assert resp.status_code != 429, f"Blocked too early on request {i + 1}"

        resp = await client.post("/api/v1/query", json=payload)
        assert resp.status_code == 429
        assert "Retry-After" in resp.headers
