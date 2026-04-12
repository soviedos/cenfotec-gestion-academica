"""Integration tests — DuplicadoRepository + DuplicateDetectionService.

Uses the real PostgreSQL testcontainer and transactional rollback
per test (from root conftest.py).
"""

from __future__ import annotations

import uuid

import pytest

from app.modules.evaluacion_docente.application.parsing.schemas import (
    CursoGrupo,
    DimensionMetrica,
    FuentePuntaje,
    HeaderData,
    ParsedEvaluacion,
    PeriodoData,
    ResumenPorcentajes,
)
from app.modules.evaluacion_docente.application.services.duplicate_detection_service import (
    DuplicateDetectionService,
)
from app.modules.evaluacion_docente.domain.fingerprint import compute_content_fingerprint
from app.modules.evaluacion_docente.infrastructure.repositories.documento import DocumentoRepository
from app.modules.evaluacion_docente.infrastructure.repositories.duplicado_repo import (
    DuplicadoRepository,
)
from app.modules.evaluacion_docente.infrastructure.repositories.evaluacion import (
    EvaluacionRepository,
)
from tests.fixtures.factories import make_documento, make_evaluacion

pytestmark = pytest.mark.integration


# ═══════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════


def _make_parsed(**overrides) -> ParsedEvaluacion:
    defaults = {
        "header": HeaderData(
            profesor_nombre="Juan Carlos Pérez",
            periodo="C1 2025",
            recinto="San José",
        ),
        "periodo_data": PeriodoData(
            periodo_raw="C1 2025",
            periodo_normalizado="C1 2025",
            modalidad="CUATRIMESTRAL",
            año=2025,
            periodo_orden=1,
            prefijo="C",
            numero=1,
        ),
        "dimensiones": [
            DimensionMetrica(
                nombre="METODOLOGÍA",
                estudiante=FuentePuntaje(puntos_obtenidos=18, puntos_maximos=20, porcentaje=90.0),
                director=FuentePuntaje(puntos_obtenidos=10, puntos_maximos=10, porcentaje=100.0),
                autoevaluacion=FuentePuntaje(
                    puntos_obtenidos=16, puntos_maximos=20, porcentaje=80.0
                ),
                promedio_general_puntos=14.0,
                promedio_general_pct=90.0,
            ),
        ],
        "resumen_pct": ResumenPorcentajes(
            estudiante=85.0,
            director=95.0,
            autoevaluacion=75.0,
            promedio_general=85.0,
        ),
        "cursos": [
            CursoGrupo(
                escuela="TI",
                codigo="MAT201",
                nombre="Cálculo II",
                estudiantes_respondieron=15,
                estudiantes_matriculados=20,
                grupo="01",
                pct_estudiante=85.0,
                pct_director=90.0,
                pct_autoevaluacion=80.0,
                pct_promedio_general=85.0,
            ),
        ],
        "total_respondieron": 15,
        "total_matriculados": 20,
        "secciones_comentarios": [],
    }
    defaults.update(overrides)
    return ParsedEvaluacion(**defaults)


async def _setup_existing_doc(db, *, parsed: ParsedEvaluacion | None = None) -> tuple:
    """Create and persist a document + evaluacion with fingerprint.

    Returns (documento, evaluacion, fingerprint_result).
    """
    parsed = parsed or _make_parsed()
    fp = compute_content_fingerprint(parsed)

    doc_repo = DocumentoRepository(db)
    eval_repo = EvaluacionRepository(db)

    doc = make_documento(estado="procesado", content_fingerprint=fp.fingerprint)
    doc = await doc_repo.create(doc)

    evaluacion = make_evaluacion(
        documento_id=doc.id,
        docente_nombre=parsed.header.profesor_nombre,
        periodo=parsed.periodo_data.periodo_normalizado,
        modalidad=parsed.periodo_data.modalidad,
        año=parsed.periodo_data.año,
        periodo_orden=parsed.periodo_data.periodo_orden,
        estado="completado",
    )
    await eval_repo.create(evaluacion)

    return doc, evaluacion, fp


# ═══════════════════════════════════════════════════════════════════════
# Repository tests
# ═══════════════════════════════════════════════════════════════════════


class TestDuplicadoRepositoryFindCandidates:
    """Test the cheap candidate query."""

    async def test_finds_same_modalidad_year_docente(self, db):
        """A doc with same modalidad, year, and docente is a candidate."""
        parsed = _make_parsed()
        existing_doc, _, _ = await _setup_existing_doc(db, parsed=parsed)

        dup_repo = DuplicadoRepository(db)
        candidates = await dup_repo.find_candidates(
            modalidad="CUATRIMESTRAL",
            año=2025,
            docente_nombre="Juan Carlos Pérez",
            periodo="C1 2025",
            exclude_documento_id=uuid.uuid4(),  # different doc
        )

        assert len(candidates) == 1
        assert candidates[0].id == existing_doc.id

    async def test_excludes_self(self, db):
        """The document being checked is excluded from candidates."""
        parsed = _make_parsed()
        existing_doc, _, _ = await _setup_existing_doc(db, parsed=parsed)

        dup_repo = DuplicadoRepository(db)
        candidates = await dup_repo.find_candidates(
            modalidad="CUATRIMESTRAL",
            año=2025,
            docente_nombre="Juan Carlos Pérez",
            periodo="C1 2025",
            exclude_documento_id=existing_doc.id,  # same doc → excluded
        )

        assert candidates == []

    async def test_different_modalidad_not_a_candidate(self, db):
        """A doc with different modalidad is not a candidate."""
        await _setup_existing_doc(db, parsed=_make_parsed())

        dup_repo = DuplicadoRepository(db)
        candidates = await dup_repo.find_candidates(
            modalidad="MENSUAL",  # different
            año=2025,
            docente_nombre="Juan Carlos Pérez",
            periodo="C1 2025",
            exclude_documento_id=uuid.uuid4(),
        )

        assert candidates == []

    async def test_different_year_not_a_candidate(self, db):
        """A doc with different year is not a candidate."""
        await _setup_existing_doc(db, parsed=_make_parsed())

        dup_repo = DuplicadoRepository(db)
        candidates = await dup_repo.find_candidates(
            modalidad="CUATRIMESTRAL",
            año=2024,  # different
            docente_nombre="Juan Carlos Pérez",
            periodo="C1 2025",
            exclude_documento_id=uuid.uuid4(),
        )

        assert candidates == []

    async def test_matches_by_periodo_only(self, db):
        """Candidate found when only periodo matches (docente differs)."""
        await _setup_existing_doc(db, parsed=_make_parsed())

        dup_repo = DuplicadoRepository(db)
        candidates = await dup_repo.find_candidates(
            modalidad="CUATRIMESTRAL",
            año=2025,
            docente_nombre="Otro Docente",  # different docente
            periodo="C1 2025",  # same periodo
            exclude_documento_id=uuid.uuid4(),
        )

        assert len(candidates) == 1

    async def test_no_fingerprint_excluded(self, db):
        """A processed doc without fingerprint is excluded."""
        doc_repo = DocumentoRepository(db)
        eval_repo = EvaluacionRepository(db)

        doc = make_documento(estado="procesado", content_fingerprint=None)
        doc = await doc_repo.create(doc)
        await eval_repo.create(
            make_evaluacion(
                documento_id=doc.id,
                modalidad="CUATRIMESTRAL",
                año=2025,
                docente_nombre="Juan Carlos Pérez",
                periodo="C1 2025",
                periodo_orden=1,
                estado="completado",
            )
        )

        dup_repo = DuplicadoRepository(db)
        candidates = await dup_repo.find_candidates(
            modalidad="CUATRIMESTRAL",
            año=2025,
            docente_nombre="Juan Carlos Pérez",
            periodo="C1 2025",
            exclude_documento_id=uuid.uuid4(),
        )

        assert candidates == []


class TestDuplicadoRepositoryExistsPair:
    async def test_no_pair(self, db):
        dup_repo = DuplicadoRepository(db)
        result = await dup_repo.exists_pair(uuid.uuid4(), uuid.uuid4())
        assert result is False

    async def test_pair_exists_forward(self, db):
        doc_a, _, fp = await _setup_existing_doc(db)
        doc_b, _, _ = await _setup_existing_doc(db)

        dup_repo = DuplicadoRepository(db)
        await dup_repo.create_finding(
            documento_id=doc_a.id,
            documento_coincidente_id=doc_b.id,
            fingerprint=fp.fingerprint,
            score=1.0,
            criterios=fp.criterios,
        )

        assert await dup_repo.exists_pair(doc_a.id, doc_b.id) is True

    async def test_pair_exists_reversed(self, db):
        """exists_pair checks both orderings."""
        doc_a, _, fp = await _setup_existing_doc(db)
        doc_b, _, _ = await _setup_existing_doc(db)

        dup_repo = DuplicadoRepository(db)
        await dup_repo.create_finding(
            documento_id=doc_a.id,
            documento_coincidente_id=doc_b.id,
            fingerprint=fp.fingerprint,
            score=1.0,
            criterios=fp.criterios,
        )

        # Check reversed order
        assert await dup_repo.exists_pair(doc_b.id, doc_a.id) is True


# ═══════════════════════════════════════════════════════════════════════
# Service integration tests
# ═══════════════════════════════════════════════════════════════════════


class TestDuplicateDetectionServiceIntegration:
    """End-to-end tests with real DB."""

    async def test_detects_exact_duplicate(self, db):
        """Full flow: existing doc + identical new doc → finding created."""
        parsed = _make_parsed()
        existing_doc, _, _ = await _setup_existing_doc(db, parsed=parsed)

        # Create the "new" document
        doc_repo = DocumentoRepository(db)
        new_doc = make_documento(estado="procesado")
        new_doc = await doc_repo.create(new_doc)

        # Create evaluacion for the new doc (needed for candidate query)
        eval_repo = EvaluacionRepository(db)
        await eval_repo.create(
            make_evaluacion(
                documento_id=new_doc.id,
                docente_nombre=parsed.header.profesor_nombre,
                periodo=parsed.periodo_data.periodo_normalizado,
                modalidad=parsed.periodo_data.modalidad,
                año=parsed.periodo_data.año,
                periodo_orden=parsed.periodo_data.periodo_orden,
                estado="completado",
            )
        )

        service = DuplicateDetectionService(db)
        result = await service.check_and_flag(new_doc, parsed)

        assert result == 1
        assert new_doc.content_fingerprint is not None

        # Verify finding was persisted
        dup_repo = DuplicadoRepository(db)
        assert await dup_repo.exists_pair(new_doc.id, existing_doc.id) is True

    async def test_no_duplicate_when_different_content(self, db):
        """Different parsed content → no finding."""
        parsed_existing = _make_parsed()
        await _setup_existing_doc(db, parsed=parsed_existing)

        parsed_new = _make_parsed(
            header=HeaderData(
                profesor_nombre="María López",
                periodo="C2 2025",
                recinto="Heredia",
            ),
            periodo_data=PeriodoData(
                periodo_raw="C2 2025",
                periodo_normalizado="C2 2025",
                modalidad="CUATRIMESTRAL",
                año=2025,
                periodo_orden=2,
                prefijo="C",
                numero=2,
            ),
        )

        doc_repo = DocumentoRepository(db)
        new_doc = make_documento(estado="procesado")
        new_doc = await doc_repo.create(new_doc)

        service = DuplicateDetectionService(db)
        result = await service.check_and_flag(new_doc, parsed_new)

        assert result == 0
        # Fingerprint is still stored even when no match
        assert new_doc.content_fingerprint is not None

    async def test_idempotent_no_double_findings(self, db):
        """Running detection twice on same doc doesn't create duplicate findings."""
        parsed = _make_parsed()
        existing_doc, _, _ = await _setup_existing_doc(db, parsed=parsed)

        doc_repo = DocumentoRepository(db)
        new_doc = make_documento(estado="procesado")
        new_doc = await doc_repo.create(new_doc)

        eval_repo = EvaluacionRepository(db)
        await eval_repo.create(
            make_evaluacion(
                documento_id=new_doc.id,
                docente_nombre=parsed.header.profesor_nombre,
                periodo=parsed.periodo_data.periodo_normalizado,
                modalidad=parsed.periodo_data.modalidad,
                año=parsed.periodo_data.año,
                periodo_orden=parsed.periodo_data.periodo_orden,
                estado="completado",
            )
        )

        service = DuplicateDetectionService(db)

        first_run = await service.check_and_flag(new_doc, parsed)
        second_run = await service.check_and_flag(new_doc, parsed)

        assert first_run == 1
        assert second_run == 0  # already exists, not duplicated
