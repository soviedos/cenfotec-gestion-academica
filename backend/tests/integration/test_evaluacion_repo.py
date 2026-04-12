"""Integration tests — EvaluacionRepository against a real database."""


import pytest

from app.modules.evaluacion_docente.infrastructure.repositories.documento import DocumentoRepository
from app.modules.evaluacion_docente.infrastructure.repositories.evaluacion import (
    EvaluacionRepository,
)
from tests.fixtures.factories import make_documento, make_evaluacion

pytestmark = pytest.mark.integration


class TestEvaluacionRepositoryCreate:
    async def test_create_linked_to_documento(self, db):
        doc_repo = DocumentoRepository(db)
        eval_repo = EvaluacionRepository(db)

        doc = make_documento()
        await doc_repo.create(doc)

        eval_ = make_evaluacion(documento_id=doc.id)
        created = await eval_repo.create(eval_)

        assert created.id == eval_.id
        assert created.documento_id == doc.id

    async def test_timestamps_set(self, db):
        doc_repo = DocumentoRepository(db)
        eval_repo = EvaluacionRepository(db)

        doc = make_documento()
        await doc_repo.create(doc)

        eval_ = make_evaluacion(documento_id=doc.id)
        created = await eval_repo.create(eval_)

        assert created.created_at is not None


class TestEvaluacionRepositoryListByDocumento:
    async def test_filters_by_documento(self, db):
        doc_repo = DocumentoRepository(db)
        eval_repo = EvaluacionRepository(db)

        doc1 = make_documento()
        doc2 = make_documento()
        await doc_repo.create(doc1)
        await doc_repo.create(doc2)

        await eval_repo.create(make_evaluacion(documento_id=doc1.id))
        await eval_repo.create(make_evaluacion(documento_id=doc1.id))
        await eval_repo.create(make_evaluacion(documento_id=doc2.id))

        items = await eval_repo.list_by_documento(doc1.id)
        count = await eval_repo.count_by_documento(doc1.id)

        assert len(items) == 2
        assert count == 2

    async def test_empty_when_no_evaluaciones(self, db):
        doc_repo = DocumentoRepository(db)
        eval_repo = EvaluacionRepository(db)

        doc = make_documento()
        await doc_repo.create(doc)

        items = await eval_repo.list_by_documento(doc.id)
        count = await eval_repo.count_by_documento(doc.id)

        assert items == []
        assert count == 0

    async def test_pagination(self, db):
        doc_repo = DocumentoRepository(db)
        eval_repo = EvaluacionRepository(db)

        doc = make_documento()
        await doc_repo.create(doc)
        for _ in range(5):
            await eval_repo.create(make_evaluacion(documento_id=doc.id))

        page1 = await eval_repo.list_by_documento(doc.id, offset=0, limit=2)
        page2 = await eval_repo.list_by_documento(doc.id, offset=2, limit=2)

        assert len(page1) == 2
        assert len(page2) == 2
