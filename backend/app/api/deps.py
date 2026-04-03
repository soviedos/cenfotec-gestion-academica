"""FastAPI dependency injection functions.

Centralizes all shared dependencies (DB sessions, services, etc.)
to keep route handlers thin and testable.
"""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.session import get_db

# Typed annotation for route-handler signatures:
#   async def my_route(db: DbSession): ...
DbSession = Annotated[AsyncSession, Depends(get_db)]
