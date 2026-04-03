"""FastAPI dependency injection functions.

Centralizes all shared dependencies (DB sessions, services, etc.)
to keep route handlers thin and testable.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import async_session_factory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session, auto-closed after request."""
    async with async_session_factory() as session:
        yield session
