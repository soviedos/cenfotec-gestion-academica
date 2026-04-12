"""Unit tests for Pydantic schemas — serialization and validation."""

import uuid
from datetime import UTC, datetime

from app.modules.evaluacion_docente.domain.schemas.documento import DocumentoCreate, DocumentoRead
from app.shared.domain.schemas.common import ErrorResponse, HealthResponse, PaginatedItems


class TestDocumentoCreate:
    def test_valid_creation(self):
        schema = DocumentoCreate(
            nombre_archivo="reporte.pdf",
            hash_sha256="a" * 64,
            storage_path="evaluaciones/reporte.pdf",
            tamano_bytes=2048,
        )
        assert schema.nombre_archivo == "reporte.pdf"
        assert schema.tamano_bytes == 2048

    def test_optional_tamano(self):
        schema = DocumentoCreate(
            nombre_archivo="reporte.pdf",
            hash_sha256="b" * 64,
            storage_path="evaluaciones/reporte.pdf",
        )
        assert schema.tamano_bytes is None


class TestDocumentoRead:
    def test_from_dict(self):
        now = datetime.now(tz=UTC)
        data = {
            "id": uuid.uuid4(),
            "nombre_archivo": "test.pdf",
            "hash_sha256": "c" * 64,
            "storage_path": "evaluaciones/test.pdf",
            "estado": "subido",
            "tamano_bytes": 512,
            "error_detalle": None,
            "created_at": now,
            "updated_at": now,
        }
        schema = DocumentoRead.model_validate(data)
        assert schema.estado == "subido"
        assert schema.id == data["id"]


class TestPaginatedItems:
    def test_generic_serialization(self):
        paginated = PaginatedItems[str](
            items=["a", "b"],
            total=10,
            page=1,
            page_size=2,
        )
        assert len(paginated.items) == 2
        assert paginated.total == 10

    def test_empty_page(self):
        paginated = PaginatedItems[str](
            items=[],
            total=0,
            page=1,
            page_size=20,
        )
        assert paginated.items == []
        assert paginated.total == 0


class TestHealthResponse:
    def test_serialization(self):
        resp = HealthResponse(status="ok", version="0.1.0", environment="test")
        assert resp.status == "ok"


class TestErrorResponse:
    def test_with_code(self):
        resp = ErrorResponse(detail="Not found", code="NOT_FOUND")
        assert resp.code == "NOT_FOUND"

    def test_without_code(self):
        resp = ErrorResponse(detail="Something failed")
        assert resp.code is None
