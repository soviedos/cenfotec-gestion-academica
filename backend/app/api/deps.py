"""FastAPI dependency injection functions.

Centralizes all shared dependencies (DB sessions, services, etc.)
to keep route handlers thin and testable.
"""

from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.domain.exceptions import GeminiUnavailableError
from app.infrastructure.database.session import get_db
from app.infrastructure.external.gemini_gateway import GeminiGateway
from app.infrastructure.storage.file_storage import FileStorage, MinioFileStorage

# Typed annotation for route-handler signatures:
#   async def my_route(db: DbSession): ...
DbSession = Annotated[AsyncSession, Depends(get_db)]


def get_file_storage() -> FileStorage:
    """Provide a file storage backend (MinIO in production)."""
    return MinioFileStorage()


FileStorageDep = Annotated[FileStorage, Depends(get_file_storage)]


@lru_cache(maxsize=1)
def _create_gemini_gateway() -> GeminiGateway:
    """Singleton factory — reuses the SDK client across requests."""
    return GeminiGateway(api_key=settings.gemini_api_key.get_secret_value())


def get_gemini_gateway() -> GeminiGateway:
    """Provide a GeminiGateway instance. Raises domain error if not configured."""
    if not settings.gemini_api_key.get_secret_value():
        raise GeminiUnavailableError(detail="GEMINI_API_KEY no configurada")
    return _create_gemini_gateway()


GeminiDep = Annotated[GeminiGateway, Depends(get_gemini_gateway)]
