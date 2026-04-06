"""Tests for the RateLimiter — including concurrency safety.

These tests mock out Redis so they exercise the in-memory fallback path,
which is the correct behaviour for unit tests that run without infrastructure.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.api.rate_limit import RateLimiter


def _fake_request(ip: str = "127.0.0.1") -> MagicMock:
    """Build a minimal fake Request with the given client IP."""
    request = MagicMock()
    request.headers = {}
    request.client = MagicMock()
    request.client.host = ip
    return request


def _no_redis():
    """Patch ``_get_redis`` to return None so tests use the in-memory path."""
    return patch.object(
        RateLimiter, "_get_redis", new_callable=lambda: lambda self: AsyncMock(return_value=None)()
    )


@pytest.mark.asyncio
class TestRateLimiterBasic:
    async def test_allows_requests_under_limit(self):
        limiter = RateLimiter(max_requests=3, window_seconds=60)
        req = _fake_request()

        with _no_redis():
            for _ in range(3):
                await limiter(req)  # should not raise

    async def test_blocks_after_exceeding_limit(self):
        limiter = RateLimiter(max_requests=2, window_seconds=60)
        req = _fake_request()

        with _no_redis():
            await limiter(req)
            await limiter(req)

            with pytest.raises(HTTPException) as exc_info:
                await limiter(req)
            assert exc_info.value.status_code == 429

    async def test_different_ips_are_independent(self):
        limiter = RateLimiter(max_requests=1, window_seconds=60)

        with _no_redis():
            await limiter(_fake_request("10.0.0.1"))
            await limiter(_fake_request("10.0.0.2"))  # different IP — should pass

            with pytest.raises(HTTPException):
                await limiter(_fake_request("10.0.0.1"))  # same IP — blocked

    async def test_reset_clears_state(self):
        limiter = RateLimiter(max_requests=1, window_seconds=60)
        req = _fake_request()

        with _no_redis():
            await limiter(req)
            await limiter.reset()
            await limiter(req)  # should pass after reset

    async def test_forwarded_for_header_used(self):
        limiter = RateLimiter(max_requests=1, window_seconds=60)
        req = MagicMock()
        req.headers = {"X-Forwarded-For": "203.0.113.5, 10.0.0.1"}
        req.client = MagicMock()
        req.client.host = "127.0.0.1"

        with _no_redis():
            await limiter(req)
            with pytest.raises(HTTPException):
                await limiter(req)  # blocked by forwarded IP


@pytest.mark.asyncio
class TestRateLimiterConcurrency:
    """Verify the in-memory Lock prevents race conditions."""

    async def test_concurrent_requests_respect_limit(self):
        """Fire N concurrent requests — exactly max_requests should succeed."""
        max_req = 5
        limiter = RateLimiter(max_requests=max_req, window_seconds=60)
        req = _fake_request()

        results: list[bool] = []

        async def attempt():
            try:
                await limiter(req)
                results.append(True)
            except HTTPException:
                results.append(False)

        with _no_redis():
            await asyncio.gather(*(attempt() for _ in range(20)))

        assert results.count(True) == max_req
        assert results.count(False) == 15
