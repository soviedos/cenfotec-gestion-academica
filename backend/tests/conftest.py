"""Root conftest — shared fixtures for all test layers.

Fixture scopes:
    - ``engine`` / ``tables``: session-scoped — schema created once per test run.
    - ``db``: function-scoped — each test gets a fresh transaction that is
      rolled back automatically (zero leftover data).
    - ``client``: function-scoped — ASGI test client with DB override.

Notes:
    ``StaticPool`` is used so that every SQLAlchemy connection reuses the same
    underlying SQLite connection.  Without it, ``sqlite+aiosqlite:///:memory:``
    would create a brand-new (empty) database for each connection, meaning
    tables created in the ``tables`` fixture would be invisible to ``db``
    sessions opened afterwards.
"""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import StaticPool

from app.api.deps import get_file_storage
from app.domain.entities.base import Base
from app.infrastructure.database.session import get_db
from app.main import app
from tests.fixtures.fakes import FakeFileStorage

# ---------------------------------------------------------------------------
# Engine (session-scoped — one in-memory DB for the whole test run)
# ---------------------------------------------------------------------------
# StaticPool forces every create_engine() call to reuse the same underlying
# connection, so tables created in `tables` are visible in every `db` session.
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def engine():
    """Create a single async engine shared across the entire test session."""
    return create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )


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
# Fake file storage (function-scoped)
# ---------------------------------------------------------------------------
@pytest.fixture
def fake_storage():
    """Provide an in-memory file storage that captures uploads."""
    return FakeFileStorage()


# ---------------------------------------------------------------------------
# ASGI test client (function-scoped)
# ---------------------------------------------------------------------------
@pytest.fixture
async def client(db, fake_storage):
    """HTTP test client with DB and storage dependencies overridden."""

    async def _override():
        yield db

    app.dependency_overrides[get_db] = _override
    app.dependency_overrides[get_file_storage] = lambda: fake_storage
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
    app.dependency_overrides.clear()
