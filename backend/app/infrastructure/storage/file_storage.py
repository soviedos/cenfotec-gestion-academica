"""File storage abstraction — async interface with MinIO implementation."""

import asyncio
import io

from minio import Minio

from app.core.config import settings
from app.infrastructure.storage.minio_client import get_minio_client


class FileStorage:
    """Base interface for file storage operations."""

    async def upload(self, path: str, data: bytes, content_type: str) -> str:
        raise NotImplementedError

    async def delete(self, path: str) -> None:
        raise NotImplementedError


class MinioFileStorage(FileStorage):
    """MinIO-backed file storage — wraps sync client in async threads."""

    def __init__(self, client: Minio | None = None, bucket: str | None = None) -> None:
        self.client = client or get_minio_client()
        self.bucket = bucket or settings.minio_bucket

    async def upload(self, path: str, data: bytes, content_type: str) -> str:
        await asyncio.to_thread(
            self.client.put_object,
            self.bucket,
            path,
            io.BytesIO(data),
            len(data),
            content_type,
        )
        return path

    async def delete(self, path: str) -> None:
        await asyncio.to_thread(self.client.remove_object, self.bucket, path)
