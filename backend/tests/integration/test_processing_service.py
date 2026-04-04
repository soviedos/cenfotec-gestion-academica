"""Integration tests for ProcessingService — upload → parse → persist pipeline.

The parser itself is covered by 94 unit tests.  Here we mock its output so
we can focus on the service's state-management and persistence logic.
"""

import json
import uuid
from unittest.mock import patch

import pytest

from app.application.parsing.errors import ParseError, ParseMetadata, ParseResult
from app.application.parsing.schemas import (
    CursoGrupo,
    DimensionMetrica,
    FuentePuntaje,
    HeaderData,
    ParsedEvaluacion,
    ResumenPorcentajes,
)
from app.application.services.processing_service import ProcessingService
from app.infrastructure.repositories.documento import DocumentoRepository
from app.infrastructure.repositories.evaluacion import EvaluacionRepository
from tests.fixtures.factories import make_documento

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

PARSER_PATH = "app.application.services.processing_service.parse_evaluacion"


def _make_successful_result() -> ParseResult:
    """Build a realistic successful ParseResult for mocking."""
    fp = FuentePuntaje(puntos_obtenidos=18.0, puntos_maximos=20.0, porcentaje=90.0)
    dim = DimensionMetrica(
        nombre="METODOLOGÍA",
        estudiante=fp,
        director=fp,
        autoevaluacion=fp,
        promedio_general_puntos=18.0,
        promedio_general_pct=90.0,
    )
    curso = CursoGrupo(
        escuela="ESC ING DEL SOFTWARE",
        codigo="INF-02",
        nombre="Fundamentos de Programación",
        estudiantes_respondieron=13,
        estudiantes_matriculados=15,
        grupo="SCV0",
        pct_estudiante=92.75,
        pct_director=100.0,
        pct_autoevaluacion=82.60,
        pct_promedio_general=91.78,
    )
    data = ParsedEvaluacion(
        header=HeaderData(
            profesor_nombre="JUAN PÉREZ MORA",
            profesor_codigo="P000099",
            periodo="C2 2025",
            recinto="TODOS",
        ),
        dimensiones=[dim],
        resumen_pct=ResumenPorcentajes(
            estudiante=92.0,
            director=100.0,
            autoevaluacion=79.60,
            promedio_general=90.53,
        ),
        cursos=[curso],
        total_respondieron=13,
        total_matriculados=15,
        secciones_comentarios=[],
    )
    return ParseResult(
        success=True,
        data=data,
        metadata=ParseMetadata(parser_version="1.0.0", pages_processed=2),
    )


def _make_failed_result() -> ParseResult:
    """Build a parser result that indicates failure."""
    return ParseResult(
        success=False,
        errors=[
            ParseError(
                stage="metricas",
                code="NO_DIMENSIONS_FOUND",
                message="No se encontró la tabla de dimensiones",
            ),
        ],
        metadata=ParseMetadata(parser_version="1.0.0", pages_processed=0),
    )


async def _setup_document(db, storage, estado="subido"):
    """Create a document in the DB and put a dummy file in storage."""
    doc = make_documento(estado=estado)
    repo = DocumentoRepository(db)
    created = await repo.create(doc)
    await storage.upload(doc.storage_path, b"%PDF-dummy", "application/pdf")
    return created


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestProcessingServiceSuccess:
    """Happy path — parser returns success, evaluation is persisted."""

    async def test_document_transitions_to_procesado(self, db, fake_storage):
        doc = await _setup_document(db, fake_storage)

        with patch(PARSER_PATH, return_value=_make_successful_result()):
            svc = ProcessingService(db, fake_storage)
            await svc.process_document(doc.id)

        await db.refresh(doc)
        assert doc.estado == "procesado"
        assert doc.error_detalle is None

    async def test_evaluacion_is_created(self, db, fake_storage):
        doc = await _setup_document(db, fake_storage)

        with patch(PARSER_PATH, return_value=_make_successful_result()):
            svc = ProcessingService(db, fake_storage)
            await svc.process_document(doc.id)

        eval_repo = EvaluacionRepository(db)
        evals = await eval_repo.list_by_documento(doc.id)
        assert len(evals) == 1

        ev = evals[0]
        assert ev.documento_id == doc.id
        assert ev.docente_nombre == "JUAN PÉREZ MORA"
        assert ev.periodo == "C2 2025"
        assert ev.estado == "completado"
        assert float(ev.puntaje_general) == pytest.approx(90.53)

    async def test_datos_completos_has_json(self, db, fake_storage):
        doc = await _setup_document(db, fake_storage)

        with patch(PARSER_PATH, return_value=_make_successful_result()):
            svc = ProcessingService(db, fake_storage)
            await svc.process_document(doc.id)

        eval_repo = EvaluacionRepository(db)
        evals = await eval_repo.list_by_documento(doc.id)
        data = json.loads(evals[0].datos_completos)
        assert "header" in data
        assert "dimensiones" in data
        assert data["header"]["profesor_nombre"] == "JUAN PÉREZ MORA"


@pytest.mark.asyncio
class TestProcessingServiceParserFailure:
    """Parser returns errors — document goes to error state."""

    async def test_parser_failure_sets_error_state(self, db, fake_storage):
        doc = await _setup_document(db, fake_storage)

        with patch(PARSER_PATH, return_value=_make_failed_result()):
            svc = ProcessingService(db, fake_storage)
            await svc.process_document(doc.id)

        await db.refresh(doc)
        assert doc.estado == "error"
        assert "NO_DIMENSIONS_FOUND" in doc.error_detalle

    async def test_parser_failure_creates_no_evaluacion(self, db, fake_storage):
        doc = await _setup_document(db, fake_storage)

        with patch(PARSER_PATH, return_value=_make_failed_result()):
            svc = ProcessingService(db, fake_storage)
            await svc.process_document(doc.id)

        eval_repo = EvaluacionRepository(db)
        evals = await eval_repo.list_by_documento(doc.id)
        assert len(evals) == 0


@pytest.mark.asyncio
class TestProcessingServiceEdgeCases:
    """Edge cases — missing document, wrong state, storage failure."""

    async def test_missing_document_is_noop(self, db, fake_storage):
        """Processing a non-existent ID should do nothing (no crash)."""
        svc = ProcessingService(db, fake_storage)
        await svc.process_document(uuid.uuid4())  # no exception

    async def test_already_procesado_is_skipped(self, db, fake_storage):
        doc = await _setup_document(db, fake_storage, estado="procesado")

        svc = ProcessingService(db, fake_storage)
        await svc.process_document(doc.id)

        await db.refresh(doc)
        assert doc.estado == "procesado"  # unchanged

    async def test_already_procesando_is_skipped(self, db, fake_storage):
        doc = await _setup_document(db, fake_storage, estado="procesando")

        svc = ProcessingService(db, fake_storage)
        await svc.process_document(doc.id)

        await db.refresh(doc)
        assert doc.estado == "procesando"  # unchanged

    async def test_storage_failure_sets_error(self, db, fake_storage):
        """If download fails, document goes to error state."""
        doc = await _setup_document(db, fake_storage)
        # Remove the file so download raises FileNotFoundError
        fake_storage.files.clear()

        svc = ProcessingService(db, fake_storage)
        await svc.process_document(doc.id)

        await db.refresh(doc)
        assert doc.estado == "error"
        assert doc.error_detalle is not None

    async def test_error_state_can_be_reprocessed(self, db, fake_storage):
        """Documents in 'error' state can be re-processed."""
        doc = await _setup_document(db, fake_storage, estado="error")

        with patch(PARSER_PATH, return_value=_make_successful_result()):
            svc = ProcessingService(db, fake_storage)
            await svc.process_document(doc.id)

        await db.refresh(doc)
        assert doc.estado == "procesado"
