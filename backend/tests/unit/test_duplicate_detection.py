"""Unit tests for DuplicateDetectionService.

Uses AsyncMock for the DB session and repository to isolate
the service from infrastructure.
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

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
from app.modules.evaluacion_docente.domain.entities.documento import Documento
from app.modules.evaluacion_docente.domain.fingerprint import compute_content_fingerprint

_UUID_NEW = uuid.UUID("00000000-0000-0000-0000-000000000001")
_UUID_EXISTING = uuid.UUID("00000000-0000-0000-0000-000000000002")


# ═══════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════


def _make_parsed(**overrides) -> ParsedEvaluacion:
    """Minimal ParsedEvaluacion with sensible defaults."""
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


def _make_doc(
    doc_id: uuid.UUID = _UUID_NEW,
    fingerprint: str | None = None,
) -> MagicMock:
    """Create a mock Documento with the minimum needed attributes."""
    doc = MagicMock(spec=Documento)
    doc.id = doc_id
    doc.content_fingerprint = fingerprint
    doc.estado = "procesado"
    return doc


# ═══════════════════════════════════════════════════════════════════════
# Tests
# ═══════════════════════════════════════════════════════════════════════


class TestCheckAndFlag:
    """Tests for the main check_and_flag entry point."""

    @pytest.fixture
    def db(self):
        session = AsyncMock()
        session.flush = AsyncMock()
        return session

    @pytest.fixture
    def service(self, db):
        return DuplicateDetectionService(db)

    async def test_no_candidates_returns_zero(self, service):
        """When no candidates match, returns 0 and no findings are created."""
        parsed = _make_parsed()
        doc = _make_doc()

        with patch.object(
            service.dup_repo, "find_candidates", new_callable=AsyncMock, return_value=[]
        ):
            result = await service.check_and_flag(doc, parsed)

        assert result == 0
        assert doc.content_fingerprint is not None  # fingerprint was still stored

    async def test_exact_match_creates_finding(self, service):
        """When a candidate has the same fingerprint, a finding is created."""
        parsed = _make_parsed()
        doc = _make_doc()

        # Compute the fingerprint the new doc would get
        fp = compute_content_fingerprint(parsed)

        # Create a candidate with the same fingerprint
        candidate = _make_doc(doc_id=_UUID_EXISTING, fingerprint=fp.fingerprint)

        with (
            patch.object(
                service.dup_repo,
                "find_candidates",
                new_callable=AsyncMock,
                return_value=[candidate],
            ),
            patch.object(
                service.dup_repo,
                "exists_pair",
                new_callable=AsyncMock,
                return_value=False,
            ),
            patch.object(
                service.dup_repo,
                "create_finding",
                new_callable=AsyncMock,
            ) as mock_create,
        ):
            result = await service.check_and_flag(doc, parsed)

        assert result == 1
        mock_create.assert_called_once()
        call_kwargs = mock_create.call_args.kwargs
        assert call_kwargs["documento_id"] == _UUID_NEW
        assert call_kwargs["documento_coincidente_id"] == _UUID_EXISTING
        assert call_kwargs["score"] == 1.0
        assert call_kwargs["fingerprint"] == fp.fingerprint

    async def test_different_fingerprint_no_finding(self, service):
        """When candidate fingerprint differs, no finding is created."""
        parsed = _make_parsed()
        doc = _make_doc()

        candidate = _make_doc(
            doc_id=_UUID_EXISTING,
            fingerprint="a" * 64,  # definitely different
        )

        with (
            patch.object(
                service.dup_repo,
                "find_candidates",
                new_callable=AsyncMock,
                return_value=[candidate],
            ),
            patch.object(
                service.dup_repo,
                "create_finding",
                new_callable=AsyncMock,
            ) as mock_create,
        ):
            result = await service.check_and_flag(doc, parsed)

        assert result == 0
        mock_create.assert_not_called()

    async def test_existing_pair_not_duplicated(self, service):
        """When a finding already exists for the pair, skip it."""
        parsed = _make_parsed()
        doc = _make_doc()
        fp = compute_content_fingerprint(parsed)
        candidate = _make_doc(doc_id=_UUID_EXISTING, fingerprint=fp.fingerprint)

        with (
            patch.object(
                service.dup_repo,
                "find_candidates",
                new_callable=AsyncMock,
                return_value=[candidate],
            ),
            patch.object(
                service.dup_repo,
                "exists_pair",
                new_callable=AsyncMock,
                return_value=True,  # already exists
            ),
            patch.object(
                service.dup_repo,
                "create_finding",
                new_callable=AsyncMock,
            ) as mock_create,
        ):
            result = await service.check_and_flag(doc, parsed)

        assert result == 0
        mock_create.assert_not_called()

    async def test_candidate_without_fingerprint_skipped(self, service):
        """Candidates that have not been fingerprinted yet are skipped."""
        parsed = _make_parsed()
        doc = _make_doc()

        candidate = _make_doc(doc_id=_UUID_EXISTING, fingerprint=None)

        with patch.object(
            service.dup_repo,
            "find_candidates",
            new_callable=AsyncMock,
            return_value=[candidate],
        ):
            result = await service.check_and_flag(doc, parsed)

        assert result == 0

    async def test_multiple_candidates_multiple_matches(self, service):
        """When multiple candidates match, multiple findings are created."""
        parsed = _make_parsed()
        doc = _make_doc()
        fp = compute_content_fingerprint(parsed)

        uuid3 = uuid.UUID("00000000-0000-0000-0000-000000000003")
        candidate_1 = _make_doc(doc_id=_UUID_EXISTING, fingerprint=fp.fingerprint)
        candidate_2 = _make_doc(doc_id=uuid3, fingerprint=fp.fingerprint)

        with (
            patch.object(
                service.dup_repo,
                "find_candidates",
                new_callable=AsyncMock,
                return_value=[candidate_1, candidate_2],
            ),
            patch.object(
                service.dup_repo,
                "exists_pair",
                new_callable=AsyncMock,
                return_value=False,
            ),
            patch.object(
                service.dup_repo,
                "create_finding",
                new_callable=AsyncMock,
            ) as mock_create,
        ):
            result = await service.check_and_flag(doc, parsed)

        assert result == 2
        assert mock_create.call_count == 2

    async def test_exception_swallowed(self, service):
        """Internal errors are caught — check_and_flag never raises."""
        parsed = _make_parsed()
        doc = _make_doc()

        with patch.object(
            service.dup_repo,
            "find_candidates",
            new_callable=AsyncMock,
            side_effect=RuntimeError("boom"),
        ):
            # flush in _detect will raise before find_candidates,
            # but let's test the outer try/except
            result = await service.check_and_flag(doc, parsed)

        assert result == 0

    async def test_stores_fingerprint_on_document(self, service):
        """The service always stores the fingerprint on the document."""
        parsed = _make_parsed()
        doc = _make_doc()

        with patch.object(
            service.dup_repo,
            "find_candidates",
            new_callable=AsyncMock,
            return_value=[],
        ):
            await service.check_and_flag(doc, parsed)

        fp = compute_content_fingerprint(parsed)
        assert doc.content_fingerprint == fp.fingerprint

    async def test_criterios_stored_as_evidence(self, service):
        """The finding's criterios dict matches the fingerprint output."""
        parsed = _make_parsed()
        doc = _make_doc()
        fp = compute_content_fingerprint(parsed)

        candidate = _make_doc(doc_id=_UUID_EXISTING, fingerprint=fp.fingerprint)

        with (
            patch.object(
                service.dup_repo,
                "find_candidates",
                new_callable=AsyncMock,
                return_value=[candidate],
            ),
            patch.object(
                service.dup_repo,
                "exists_pair",
                new_callable=AsyncMock,
                return_value=False,
            ),
            patch.object(
                service.dup_repo,
                "create_finding",
                new_callable=AsyncMock,
            ) as mock_create,
        ):
            await service.check_and_flag(doc, parsed)

        call_kwargs = mock_create.call_args.kwargs
        assert call_kwargs["criterios"] == fp.criterios
        assert "docente_nombre" in call_kwargs["criterios"]
        assert "modalidad" in call_kwargs["criterios"]

    async def test_sets_posible_duplicado_on_match(self, service):
        """When a finding is created, posible_duplicado is set to True."""
        parsed = _make_parsed()
        doc = _make_doc()
        doc.posible_duplicado = False
        fp = compute_content_fingerprint(parsed)
        candidate = _make_doc(doc_id=_UUID_EXISTING, fingerprint=fp.fingerprint)

        with (
            patch.object(
                service.dup_repo,
                "find_candidates",
                new_callable=AsyncMock,
                return_value=[candidate],
            ),
            patch.object(
                service.dup_repo,
                "exists_pair",
                new_callable=AsyncMock,
                return_value=False,
            ),
            patch.object(
                service.dup_repo,
                "create_finding",
                new_callable=AsyncMock,
            ),
        ):
            result = await service.check_and_flag(doc, parsed)

        assert result == 1
        assert doc.posible_duplicado is True

    async def test_no_flag_when_no_matches(self, service):
        """When no matches are found, posible_duplicado stays False."""
        parsed = _make_parsed()
        doc = _make_doc()
        doc.posible_duplicado = False

        with patch.object(
            service.dup_repo,
            "find_candidates",
            new_callable=AsyncMock,
            return_value=[],
        ):
            result = await service.check_and_flag(doc, parsed)

        assert result == 0
        assert doc.posible_duplicado is False
