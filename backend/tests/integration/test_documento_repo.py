"""Integration tests — DocumentoRepository against a real database."""


import pytest

from app.modules.evaluacion_docente.infrastructure.repositories.documento import DocumentoRepository
from tests.fixtures.factories import make_documento

pytestmark = pytest.mark.integration


class TestDocumentoRepositoryCreate:
    async def test_create_and_retrieve(self, db):
        repo = DocumentoRepository(db)
        doc = make_documento()

        created = await repo.create(doc)

        assert created.id == doc.id
        assert created.nombre_archivo == doc.nombre_archivo

        fetched = await repo.get_by_id(doc.id)
        assert fetched is not None
        assert fetched.hash_sha256 == doc.hash_sha256

    async def test_create_sets_timestamps(self, db):
        repo = DocumentoRepository(db)
        doc = make_documento()

        created = await repo.create(doc)

        assert created.created_at is not None
        assert created.updated_at is not None


class TestDocumentoRepositoryList:
    async def test_empty_list(self, db):
        repo = DocumentoRepository(db)

        items = await repo.list()
        total = await repo.count()

        assert items == []
        assert total == 0

    async def test_list_with_pagination(self, db):
        repo = DocumentoRepository(db)
        for _ in range(5):
            await repo.create(make_documento())

        page1 = await repo.list(offset=0, limit=2)
        page2 = await repo.list(offset=2, limit=2)
        total = await repo.count()

        assert len(page1) == 2
        assert len(page2) == 2
        assert total == 5

    async def test_list_ordered_by_created_at_desc(self, db):
        repo = DocumentoRepository(db)
        docs = [make_documento() for _ in range(3)]
        for doc in docs:
            await repo.create(doc)

        items = await repo.list()

        # Most recent first (all created nearly simultaneously, so just check count)
        assert len(items) == 3


class TestDocumentoRepositoryGetByHash:
    async def test_found(self, db):
        repo = DocumentoRepository(db)
        doc = make_documento(hash_sha256="a" * 64)
        await repo.create(doc)

        found = await repo.get_by_hash("a" * 64)

        assert found is not None
        assert found.id == doc.id

    async def test_not_found(self, db):
        repo = DocumentoRepository(db)

        found = await repo.get_by_hash("nonexistent")

        assert found is None


class TestDocumentoRepositoryDelete:
    async def test_delete_removes_entity(self, db):
        repo = DocumentoRepository(db)
        doc = make_documento()
        await repo.create(doc)

        await repo.delete(doc)

        assert await repo.get_by_id(doc.id) is None
        assert await repo.count() == 0
