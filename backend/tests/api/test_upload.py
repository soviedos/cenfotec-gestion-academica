"""API tests — POST /api/v1/documentos/upload endpoint."""

import pytest

pytestmark = pytest.mark.api

PDF_CONTENT = b"%PDF-1.4 fake content for testing purposes"


def _pdf_file(content: bytes = PDF_CONTENT, filename: str = "evaluacion.pdf"):
    """Build a multipart file tuple for httpx."""
    return {"file": (filename, content, "application/pdf")}


class TestUploadDocumento:
    async def test_upload_success(self, client, fake_storage):
        response = await client.post("/api/v1/documentos/upload", files=_pdf_file())

        assert response.status_code == 201
        data = response.json()
        assert data["nombre_archivo"] == "evaluacion.pdf"
        assert data["estado"] == "subido"
        assert data["tamano_bytes"] == len(PDF_CONTENT)
        assert "id" in data
        assert "hash_sha256" in data
        assert "created_at" in data
        assert "updated_at" in data
        assert len(fake_storage.files) == 1

    async def test_upload_duplicate_returns_409(self, client):
        files = _pdf_file()
        first = await client.post("/api/v1/documentos/upload", files=files)
        assert first.status_code == 201

        second = await client.post("/api/v1/documentos/upload", files=files)
        assert second.status_code == 409
        assert "ya fue cargado" in second.json()["detail"]

    async def test_upload_invalid_extension(self, client):
        files = {"file": ("notas.txt", PDF_CONTENT, "application/pdf")}

        response = await client.post("/api/v1/documentos/upload", files=files)

        assert response.status_code == 400
        assert "PDF" in response.json()["detail"]

    async def test_upload_invalid_content_type(self, client):
        files = {"file": ("doc.pdf", PDF_CONTENT, "text/plain")}

        response = await client.post("/api/v1/documentos/upload", files=files)

        assert response.status_code == 400
        assert "Tipo de contenido" in response.json()["detail"]

    async def test_upload_invalid_magic_bytes(self, client):
        files = {"file": ("doc.pdf", b"NOT-A-PDF content here", "application/pdf")}

        response = await client.post("/api/v1/documentos/upload", files=files)

        assert response.status_code == 400
        assert "PDF valido" in response.json()["detail"]

    async def test_upload_empty_file(self, client):
        files = {"file": ("empty.pdf", b"", "application/pdf")}

        response = await client.post("/api/v1/documentos/upload", files=files)

        assert response.status_code == 400
        assert "vacio" in response.json()["detail"]

    async def test_upload_shows_in_list(self, client):
        await client.post("/api/v1/documentos/upload", files=_pdf_file())

        response = await client.get("/api/v1/documentos/")

        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["nombre_archivo"] == "evaluacion.pdf"
        assert data["items"][0]["estado"] == "subido"
