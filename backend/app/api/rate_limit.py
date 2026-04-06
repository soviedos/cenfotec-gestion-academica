"""Redis-backed sliding-window rate limiter for expensive endpoints.

Uses Redis INCR + EXPIRE for atomic counting across multiple Uvicorn
workers.  Falls back to an in-memory per-worker counter when Redis is
unreachable, ensuring rate limiting is always enforced.
"""

from __future__ import annotations

import ipaddress
import logging
import time
from collections import defaultdict
from threading import Lock

import redis.asyncio as aioredis
from fastapi import HTTPException, Request

from app.core.config import settings

logger = logging.getLogger(__name__)

_KEY_PREFIX = "ratelimit:"


class _InMemoryBucket:
    """Thread-safe in-memory sliding-window counter for a single key."""

    __slots__ = ("timestamps", "lock")

    def __init__(self) -> None:
        self.timestamps: list[float] = []
        self.lock = Lock()

    def check(self, window: int, max_requests: int) -> bool:
        """Return True if the request should be allowed."""
        now = time.monotonic()
        cutoff = now - window
        with self.lock:
            self.timestamps = [t for t in self.timestamps if t > cutoff]
            if len(self.timestamps) >= max_requests:
                return False
            self.timestamps.append(now)
            return True


class RateLimiter:
    """Sliding-window rate limiter backed by Redis, keyed by client IP.

    Falls back to in-memory limiting per worker when Redis is unavailable,
    preventing abuse even during Redis outages.
    """

    def __init__(self, max_requests: int = 10, window_seconds: int = 60) -> None:
        self.max_requests = max_requests
        self.window = window_seconds
        self._redis: aioredis.Redis | None = None
        self._redis_available: bool | None = None
        self._memory_buckets: defaultdict[str, _InMemoryBucket] = defaultdict(_InMemoryBucket)

    async def _get_redis(self) -> aioredis.Redis | None:
        if self._redis is not None:
            return self._redis
        try:
            self._redis = aioredis.from_url(
                settings.redis_url,
                decode_responses=True,
                socket_connect_timeout=2,
            )
            await self._redis.ping()
            self._redis_available = True
            return self._redis
        except Exception:
            logger.debug("Redis not reachable — using in-memory rate limiting")
            self._redis = None
            self._redis_available = False
            return None

    def _client_key(self, request: Request) -> str:
        """Extract client IP, validating X-Forwarded-For only from trusted proxies."""
        forwarded = request.headers.get("X-Forwarded-For")
        client_host = request.client.host if request.client else "unknown"

        # Only trust X-Forwarded-For from known reverse proxies (supports both
        # exact IPs and CIDR network ranges such as 10.0.0.0/8)
        _trusted_networks = [
            ipaddress.ip_network("127.0.0.1/32"),
            ipaddress.ip_network("::1/128"),
            ipaddress.ip_network("172.16.0.0/12"),
            ipaddress.ip_network("10.0.0.0/8"),
            ipaddress.ip_network("192.168.0.0/16"),
        ]
        if forwarded and client_host != "unknown":
            try:
                addr = ipaddress.ip_address(client_host)
                if any(addr in net for net in _trusted_networks):
                    return forwarded.split(",")[0].strip()
            except ValueError:
                pass
        return client_host

    def _check_memory(self, key: str) -> bool:
        """In-memory fallback rate check. Returns True if allowed."""
        return self._memory_buckets[key].check(self.window, self.max_requests)

    async def __call__(self, request: Request) -> None:
        client = self._client_key(request)
        r = await self._get_redis()

        if r is None:
            # In-memory fallback — still enforces limits per-worker
            if not self._check_memory(client):
                raise HTTPException(
                    status_code=429,
                    detail="Demasiadas solicitudes. Intente de nuevo en unos minutos.",
                    headers={"Retry-After": str(self.window)},
                )
            return

        key = f"{_KEY_PREFIX}{client}"
        try:
            current = await r.incr(key)
            if current == 1:
                await r.expire(key, self.window)
            if current > self.max_requests:
                raise HTTPException(
                    status_code=429,
                    detail="Demasiadas solicitudes. Intente de nuevo en unos minutos.",
                    headers={"Retry-After": str(self.window)},
                )
        except HTTPException:
            raise
        except Exception:
            # Redis error mid-operation — fall back to memory
            logger.warning("Rate limiter Redis error, falling back to in-memory")
            self._redis = None
            self._redis_available = False
            if not self._check_memory(client):
                raise HTTPException(
                    status_code=429,
                    detail="Demasiadas solicitudes. Intente de nuevo en unos minutos.",
                    headers={"Retry-After": str(self.window)},
                )

    async def reset(self) -> None:
        """Clear all rate-limit keys (useful for testing)."""
        self._memory_buckets.clear()
        r = await self._get_redis()
        if r is None:
            return
        try:
            cursor = 0
            while True:
                cursor, keys = await r.scan(cursor, match=f"{_KEY_PREFIX}*", count=200)
                if keys:
                    await r.delete(*keys)
                if cursor == 0:
                    break
        except Exception:
            pass

    async def close(self) -> None:
        """Close the Redis connection pool."""
        self._memory_buckets.clear()
        if self._redis is not None:
            await self._redis.aclose()
            self._redis = None


# Pre-configured limiter for the Gemini query endpoint
query_rate_limiter = RateLimiter(max_requests=10, window_seconds=60)
