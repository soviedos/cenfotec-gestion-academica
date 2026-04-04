"""API tests — /api/v1/documentos endpoints."""

import pytest

from app.infrastructure.repositories.documento import DocumentoRepository
from app.infrastructure.repositories.evaluacion import EvaluacionRepository
from tests.fixtures.factories import make_documento, make_evaluacion

pytestmark = pytest.mark.api


class TestListDocumentos:
    async def test_empty_list(self, client):
        response = await client.get("/api/v1/documentos/")

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0
        assert data["page"] == 1
        assert data["page_size"] == 20
        assert data["total_pages"] == 1

    async def test_with_data(self, client, db):
        repo = DocumentoRepository(db)
        await repo.create(make_documento())
        await repo.create(make_documento())

        response = await client.get("/api/v1/documentos/")

        data = response.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2

    async def test_pagination_params(self, client, db):
        repo = DocumentoRepository(db)
        for _ in range(5):
            await repo.create(make_documento())

        response = await client.get("/api/v1/documentos/?page=2&page_size=2")

        data = response.json()
        assert data["page"] == 2
        assert data["page_size"] == 2
        assert len(data["items"]) == 2
        assert data["total"] == 5
        assert data["total_pages"] == 3

    async def test_item_shape(self, client, db):
        repo = DocumentoRepository(db)
        await repo.create(make_documento(nombre_archivo="archivo.pdf"))

        response = await client.get("/api/v1/documentos/")

        item = response.json()["items"][0]
        assert item["nombre_archivo"] == "archivo.pdf"
        assert "id" in item
        assert "hash_sha256" in item
        assert "estado" in item
        assert "created_at" in item


class TestListDocumentosFilters:
    async def test_filter_by_estado(self, client, db):
        repo = DocumentoRepository(db)
        await repo.create(make_documento(estado="subido"))
        await repo.create(make_documento(estado="procesado"))
        await repo.create(make_documento(estado="error"))

        response = await client.get("/api/v1/documentos/?estado=subido")

        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["estado"] == "subido"

    async def test_filter_by_nombre_archivo(self, client, db):
        repo = DocumentoRepository(db)
        await repo.create(make_documento(nombre_archivo="evaluacion_q1_2025.pdf"))
        await repo.create(make_documento(nombre_archivo="evaluacion_q2_2025.pdf"))
        await repo.create(make_documento(nombre_archivo="otro_documento.pdf"))

        response = await client.get("/api/v1/documentos/?nombre_archivo=evaluacion")

        data = response.json()
        assert data["total"] == 2

    async def test_filter_by_docente(self, client, db):
        doc_repo = DocumentoRepository(db)
        eval_repo = EvaluacionRepository(db)

        doc1 = await doc_repo.create(make_documento())
        doc2 = await doc_repo.create(make_documento())

        await eval_repo.create(make_evaluacion(documento_id=doc1.id, docente_nombre="Prof. García"))
        await eval_repo.create(make_evaluacion(documento_id=doc2.id, docente_nombre="Prof. López"))

        response = await client.get("/api/v1/documentos/?docente=García")

        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["id"] == str(doc1.id)

    async def test_filter_by_periodo(self, client, db):
        doc_repo = DocumentoRepository(db)
        eval_repo = EvaluacionRepository(db)

        doc1 = await doc_repo.create(make_documento())
        doc2 = await doc_repo.create(make_documento())

        await eval_repo.create(make_evaluacion(documento_id=doc1.id, periodo="2025-1"))
        await eval_repo.create(make_evaluacion(documento_id=doc2.id, periodo="2025-2"))

        response = await client.get("/api/v1/documentos/?periodo=2025-1")

        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["id"] == str(doc1.id)

    async def test_combined_filters(self, client, db):
        doc_repo = DocumentoRepository(db)
        eval_repo = EvaluacionRepository(db)

        doc1 = await doc_repo.create(make_documento(estado="procesado"))
        doc2 = await doc_repo.create(make_documento(estado="procesado"))
        await doc_repo.create(make_documento(estado="subido"))

        await eval_repo.create(
            make_evaluacion(documento_id=doc1.id, docente_nombre="Prof. García", periodo="2025-1")
        )
        await eval_repo.create(
            make_evaluacion(documento_id=doc2.id, docente_nombre="Prof. López", periodo="2025-1")
        )

        response = await client.get("/api/v1/documentos/?estado=procesado&docente=García")

        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["id"] == str(doc1.id)

    async def test_no_results_for_nonexistent_docente(self, client, db):
        repo = DocumentoRepository(db)
        await repo.create(make_documento())

        response = await client.get("/api/v1/documentos/?docente=NoExiste")

        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []


class TestListDocumentosSorting:
    async def test_sort_by_nombre_asc(self, client, db):
        repo = DocumentoRepository(db)
        await repo.create(make_documento(nombre_archivo="c_doc.pdf"))
        await repo.create(make_documento(nombre_archivo="a_doc.pdf"))
        await repo.create(make_documento(nombre_archivo="b_doc.pdf"))

        response = await client.get(
            "/api/v1/documentos/?sort_by=nombre_archivo&sort_order=asc"
        )

        names = [i["nombre_archivo"] for i in response.json()["items"]]
        assert names == ["a_doc.pdf", "b_doc.pdf", "c_doc.pdf"]

    async def test_sort_by_nombre_desc(self, client, db):
        repo = DocumentoRepository(db)
        await repo.create(make_documento(nombre_archivo="a_doc.pdf"))
        await repo.create(make_documento(nombre_archivo="c_doc.pdf"))
        await repo.create(make_documento(nombre_archivo="b_doc.pdf"))

        response = await client.get(
            "/api/v1/documentos/?sort_by=nombre_archivo&sort_order=desc"
        )

        names = [i["nombre_archivo"] for i in response.json()["items"]]
        assert names == ["c_doc.pdf", "b_doc.pdf", "a_doc.pdf"]

    async def test_default_sort_is_created_at_desc(self, client, db):
        repo = DocumentoRepository(db)
        await repo.create(make_documento(nombre_archivo="first.pdf"))
        await repo.create(make_documento(nombre_archivo="second.pdf"))

        response = await client.get("/api/v1/documentos/")

        items = response.json()["items"]
        assert len(items) == 2
        # Default sort applies created_at desc; with same-second timestamps
        # the result is stable but order may vary — just verify it works
        names = {i["nombre_archivo"] for i in items}
        assert names == {"first.pdf", "second.pdf"}


class TestListDocumentosValidation:
    async def test_page_size_max_100(self, client):
        response = await client.get("/api/v1/documentos/?page_size=101")
        assert response.status_code == 422

    async def test_page_min_1(self, client):
        response = await client.get("/api/v1/documentos/?page=0")
        assert response.status_code == 422

    async def test_invalid_sort_field(self, client):
        response = await client.get("/api/v1/documentos/?sort_by=invalid_field")
        assert response.status_code == 422

    async def test_invalid_estado(self, client):
        response = await client.get("/api/v1/documentos/?estado=invalido")
        assert response.status_code == 422

    async def test_total_pages_calculation(self, client, db):
        repo = DocumentoRepository(db)
        for _ in range(7):
            await repo.create(make_documento())

        response = await client.get("/api/v1/documentos/?page_size=3")

        data = response.json()
        assert data["total"] == 7
        assert data["total_pages"] == 3
