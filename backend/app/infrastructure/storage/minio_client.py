"""MinIO S3-compatible storage client."""

from minio import Minio

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def get_minio_client() -> Minio:
    """Create a MinIO client from settings."""
    return Minio(
        endpoint=settings.minio_endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        secure=settings.minio_secure,
    )


def ensure_bucket_exists(client: Minio, bucket_name: str | None = None) -> None:
    """Create the bucket if it doesn't exist."""
    name = bucket_name or settings.minio_bucket
    if not client.bucket_exists(name):
        client.make_bucket(name)
        logger.info("Bucket '%s' created", name)
