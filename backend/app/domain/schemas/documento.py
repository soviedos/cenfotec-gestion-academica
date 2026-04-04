"""Documento DTOs."""

import uuid
from typing import Literal

from pydantic import Field

from app.domain.schemas.common import BaseSchema, PaginatedItems, TimestampSchema

DocumentoEstado = Literal["subido", "procesando", "procesado", "error"]
DocumentoSortField = Literal[
    "created_at", "updated_at", "nombre_archivo", "estado", "tamano_bytes"
]


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


class DocumentoFilterParams(BaseSchema):
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
    sort_by: DocumentoSortField = "created_at"
    sort_order: Literal["asc", "desc"] = "desc"
    estado: DocumentoEstado | None = None
    docente: str | None = None
    periodo: str | None = None
    nombre_archivo: str | None = None
