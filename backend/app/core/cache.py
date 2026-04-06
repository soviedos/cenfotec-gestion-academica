"""Redis-backed TTL cache for async functions.

Uses the shared Redis instance so the cache is consistent across
multiple Uvicorn workers.  When Redis is unreachable the cache is
silently disabled (get returns None, set is a no-op), so callers
always work — just without caching.
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any

import redis.asyncio as aioredis

from app.core.config import settings

logger = logging.getLogger(__name__)

_KEY_PREFIX = "cache:"


class TTLCache:
    """Redis-backed TTL cache with in-memory fallback."""

    def __init__(self, default_ttl: int = 300) -> None:
        self._default_ttl = default_ttl
        self._redis: aioredis.Redis | None = None
        self._local: dict[str, tuple[float, Any]] = {}

    async def _get_redis(self) -> aioredis.Redis | None:
        """Lazy-connect to Redis; return None if unavailable."""
        if self._redis is not None:
            return self._redis
        try:
            self._redis = aioredis.from_url(
                settings.redis_url,
                decode_responses=True,
                socket_connect_timeout=2,
            )
            await self._redis.ping()
            return self._redis
        except Exception:
            logger.debug("Redis not reachable — using in-memory fallback")
            self._redis = None
            return None

    async def get(self, key: str) -> Any | None:
        r = await self._get_redis()
        if r is None:
            entry = self._local.get(key)
            if entry is None:
                return None
            expiry, value = entry
            if expiry and time.monotonic() > expiry:
                del self._local[key]
                return None
            return value
        try:
            raw = await r.get(f"{_KEY_PREFIX}{key}")
            if raw is None:
                return None
            return json.loads(raw)
        except Exception:
            logger.debug("Cache get error for key %s", key)
            return None

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        effective_ttl = ttl if ttl is not None else self._default_ttl
        r = await self._get_redis()
        if r is None:
            expiry = time.monotonic() + effective_ttl if effective_ttl else 0.0
            self._local[key] = (expiry, value)
            return
        try:
            await r.set(
                f"{_KEY_PREFIX}{key}",
                json.dumps(value, default=str),
                ex=effective_ttl,
            )
        except Exception:
            logger.debug("Cache set error for key %s", key)

    async def invalidate(self, prefix: str = "") -> None:
        """Remove all entries whose key starts with *prefix* (or all cache keys)."""
        r = await self._get_redis()
        if r is None:
            if not prefix:
                self._local.clear()
            else:
                to_delete = [k for k in self._local if k.startswith(prefix)]
                for k in to_delete:
                    del self._local[k]
            return
        try:
            pattern = f"{_KEY_PREFIX}{prefix}*"
            cursor = 0
            while True:
                cursor, keys = await r.scan(cursor, match=pattern, count=200)
                if keys:
                    await r.delete(*keys)
                if cursor == 0:
                    break
        except Exception:
            logger.debug("Cache invalidate error for prefix %s", prefix)

    async def close(self) -> None:
        """Close the Redis connection pool."""
        if self._redis is not None:
            await self._redis.aclose()
            self._redis = None


# Singleton cache shared across requests (multi-worker safe via Redis)
analytics_cache = TTLCache(default_ttl=300)  # 5 min
