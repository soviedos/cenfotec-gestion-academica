"""API tests — /api/v1/evaluaciones endpoints."""

import pytest

from app.modules.evaluacion_docente.infrastructure.repositories.documento import DocumentoRepository
from app.modules.evaluacion_docente.infrastructure.repositories.evaluacion import (
    EvaluacionRepository,
)
from tests.fixtures.factories import make_documento, make_evaluacion

pytestmark = pytest.mark.api


class TestListEvaluaciones:
    async def test_empty_list(self, client):
        response = await client.get("/api/v1/evaluaciones/")

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    async def test_with_data(self, client, db):
        doc_repo = DocumentoRepository(db)
        eval_repo = EvaluacionRepository(db)

        doc = make_documento()
        await doc_repo.create(doc)
        await eval_repo.create(make_evaluacion(documento_id=doc.id))

        response = await client.get("/api/v1/evaluaciones/")

        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1

    async def test_item_shape(self, client, db):
        doc_repo = DocumentoRepository(db)
        eval_repo = EvaluacionRepository(db)

        doc = make_documento()
        await doc_repo.create(doc)
        await eval_repo.create(
            make_evaluacion(documento_id=doc.id, docente_nombre="Prof. López")
        )

        response = await client.get("/api/v1/evaluaciones/")

        item = response.json()["items"][0]
        assert item["docente_nombre"] == "Prof. López"
        assert "id" in item
        assert "periodo" in item
        assert "estado" in item
        assert "created_at" in item
