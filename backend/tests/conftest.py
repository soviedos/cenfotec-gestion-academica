"""Root conftest — shared fixtures for all test layers.

Fixture scopes:
    - ``engine`` / ``tables``: session-scoped — schema created once per test run.
    - ``db``: function-scoped — each test gets a fresh transaction that is
      rolled back automatically (zero leftover data).
    - ``client``: function-scoped — ASGI test client with DB override.

Notes:
    Uses ``testcontainers`` to spin up a real PostgreSQL container so that
    tests exercise the same dialect, UUID type, JSON operators, and
    constraints as production.  The container is started once per session
    and torn down automatically.
"""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from testcontainers.postgres import PostgresContainer

from app.api.deps import get_file_storage, get_gemini_gateway
from app.api.rate_limit import query_rate_limiter
from app.core.cache import analytics_cache
from app.domain.entities.base import Base
from app.infrastructure.database.session import get_db
from app.main import app
from tests.fixtures.fakes import FakeFileStorage, FakeGeminiGateway

# ---------------------------------------------------------------------------
# PostgreSQL container (session-scoped — one container per test run)
# ---------------------------------------------------------------------------

_PG_IMAGE = "pgvector/pgvector:pg16"


@pytest.fixture(scope="session")
def postgres_container():
    """Start a disposable PostgreSQL container for the entire test session."""
    with PostgresContainer(
        image=_PG_IMAGE,
        username="test_user",
        password="test_pass",
        dbname="test_evaluaciones",
    ) as pg:
        yield pg


@pytest.fixture(scope="session")
def engine(postgres_container):
    """Create a single async engine connected to the test container."""
    # testcontainers gives us a psycopg2 URL; convert to asyncpg
    sync_url = postgres_container.get_connection_url()
    async_url = sync_url.replace("psycopg2", "asyncpg", 1)
    return create_async_engine(async_url, echo=False)


@pytest.fixture(scope="session", autouse=True)
async def tables(engine):
    """Create all tables once before the first test; drop after the last."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


# ---------------------------------------------------------------------------
# DB session (function-scoped — each test is wrapped in a rolled-back txn)
# ---------------------------------------------------------------------------
@pytest.fixture
async def db(engine):
    """Yield a transactional session that rolls back after each test.

    This guarantees full test isolation without needing to truncate tables.
    """
    async with engine.connect() as conn:
        txn = await conn.begin()
        session = AsyncSession(bind=conn, expire_on_commit=False)
        try:
            yield session
        finally:
            await session.close()
            await txn.rollback()


# ---------------------------------------------------------------------------
# Clear analytics cache between tests
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
async def _clear_analytics_cache():
    """Ensure each test starts with a fresh analytics cache."""
    await analytics_cache.invalidate()
    await query_rate_limiter.reset()
    yield
    await analytics_cache.invalidate()
    await query_rate_limiter.reset()


# ---------------------------------------------------------------------------
# Fake file storage (function-scoped)
# ---------------------------------------------------------------------------
@pytest.fixture
def fake_storage():
    """Provide an in-memory file storage that captures uploads."""
    return FakeFileStorage()


# ---------------------------------------------------------------------------
# Fake Gemini gateway (function-scoped)
# ---------------------------------------------------------------------------
@pytest.fixture
def fake_gemini():
    """Provide a fake Gemini gateway that returns canned responses."""
    return FakeGeminiGateway()


# ---------------------------------------------------------------------------
# ASGI test client (function-scoped)
# ---------------------------------------------------------------------------
@pytest.fixture
async def client(db, fake_storage, fake_gemini):
    """HTTP test client with DB, storage, and Gemini dependencies overridden."""

    async def _override():
        yield db

    app.dependency_overrides[get_db] = _override
    app.dependency_overrides[get_file_storage] = lambda: fake_storage
    app.dependency_overrides[get_gemini_gateway] = lambda: fake_gemini
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
