"""FastAPI dependency injection functions.

Centralizes all shared dependencies (DB sessions, services, etc.)
to keep route handlers thin and testable.
"""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.session import get_db
from app.infrastructure.storage.file_storage import FileStorage, MinioFileStorage

# Typed annotation for route-handler signatures:
#   async def my_route(db: DbSession): ...
DbSession = Annotated[AsyncSession, Depends(get_db)]


def get_file_storage() -> FileStorage:
    """Provide a file storage backend (MinIO in production)."""
    return MinioFileStorage()


FileStorageDep = Annotated[FileStorage, Depends(get_file_storage)]
