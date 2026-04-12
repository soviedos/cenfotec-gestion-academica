"""Unit tests for the TTL cache."""

import asyncio

import pytest

from app.shared.core.cache import TTLCache

pytestmark = pytest.mark.unit


class TestTTLCache:
    @pytest.fixture
    def cache(self):
        return TTLCache(default_ttl=1)

    @pytest.mark.asyncio
    async def test_set_and_get(self, cache: TTLCache):
        await cache.set("k1", {"value": 42})
        assert await cache.get("k1") == {"value": 42}

    @pytest.mark.asyncio
    async def test_returns_none_for_missing_key(self, cache: TTLCache):
        assert await cache.get("nonexistent") is None

    @pytest.mark.asyncio
    async def test_expires_after_ttl(self, cache: TTLCache):
        await cache.set("k1", "short-lived", ttl=0)  # instant expiry
        await asyncio.sleep(0.01)
        assert await cache.get("k1") is None

    @pytest.mark.asyncio
    async def test_invalidate_by_prefix(self, cache: TTLCache):
        await cache.set("analytics:resumen:2025", "data1")
        await cache.set("analytics:docentes:2025", "data2")
        await cache.set("other:key", "data3")

        await cache.invalidate("analytics:")

        assert await cache.get("analytics:resumen:2025") is None
        assert await cache.get("analytics:docentes:2025") is None
        assert await cache.get("other:key") == "data3"

    @pytest.mark.asyncio
    async def test_invalidate_all(self, cache: TTLCache):
        await cache.set("a", 1)
        await cache.set("b", 2)
        await cache.invalidate()
        assert await cache.get("a") is None
        assert await cache.get("b") is None
