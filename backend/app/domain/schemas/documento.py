"""Documento DTOs."""

import uuid
from typing import Literal

from app.domain.schemas.common import BaseSchema, PaginatedItems, TimestampSchema

DocumentoEstado = Literal["subido", "procesando", "procesado", "error"]


class DocumentoCreate(BaseSchema):
    nombre_archivo: str
    hash_sha256: str
    storage_path: str
    tamano_bytes: int | None = None


class DocumentoRead(TimestampSchema):
    id: uuid.UUID
    nombre_archivo: str
    hash_sha256: str
    storage_path: str
    estado: DocumentoEstado
    tamano_bytes: int | None
    error_detalle: str | None


class DocumentoUploadResponse(TimestampSchema):
    id: uuid.UUID
    nombre_archivo: str
    hash_sha256: str
    estado: DocumentoEstado
    tamano_bytes: int | None


class DocumentoList(PaginatedItems[DocumentoRead]):
    pass
    pass
    pass
    pass
