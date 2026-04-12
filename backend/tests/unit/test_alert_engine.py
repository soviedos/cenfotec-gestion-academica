"""Unit tests for AlertEngine orchestration logic.

Uses a fake repository to isolate the engine from the database.
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, patch

import pytest

from app.modules.evaluacion_docente.application.services.alert_engine import AlertEngine
from app.modules.evaluacion_docente.domain.alert_rules import AlertCandidate, DocenteCursoSnapshot
from app.modules.evaluacion_docente.domain.entities.enums import Severidad, TipoAlerta

_AE_MOD = "app.modules.evaluacion_docente.application.services.alert_engine"

_UUID1 = uuid.UUID("00000000-0000-0000-0000-000000000001")
_UUID2 = uuid.UUID("00000000-0000-0000-0000-000000000002")


def _snap(
    *,
    periodo: str = "C1 2025",
    eval_id: uuid.UUID = _UUID1,
    puntaje: float = 50.0,
    docente: str = "Prof. García",
    curso: str = "ISW-101",
) -> DocenteCursoSnapshot:
    return DocenteCursoSnapshot(
        evaluacion_id=eval_id,
        docente_nombre=docente,
        curso=curso,
        periodo=periodo,
        modalidad="CUATRIMESTRAL",
        puntaje_general=puntaje,
        total_comentarios=10,
        negativos_count=1,
        mejora_negativo_count=0,
        actitud_negativo_count=0,
        otro_count=0,
    )


class _StubDetector:
    """Detector that always returns one alert."""

    tipo = TipoAlerta.BAJO_DESEMPENO

    def detect(
        self,
        actual: DocenteCursoSnapshot,
        anterior: DocenteCursoSnapshot | None,
    ) -> list[AlertCandidate]:
        return [
            AlertCandidate(
                evaluacion_id=actual.evaluacion_id,
                docente_nombre=actual.docente_nombre,
                curso=actual.curso,
                periodo=actual.periodo,
                modalidad=actual.modalidad,
                tipo_alerta=self.tipo,
                metrica_afectada="puntaje_general",
                valor_actual=actual.puntaje_general or 0,
                valor_anterior=None,
                descripcion="stub alert",
                severidad=Severidad.ALTA,
            )
        ]


class _NeverDetector:
    """Detector that never fires."""

    tipo = TipoAlerta.PATRON

    def detect(
        self,
        actual: DocenteCursoSnapshot,
        anterior: DocenteCursoSnapshot | None,
    ) -> list[AlertCandidate]:
        return []


class TestAlertEngineDetect:
    """Tests for the ``_detect`` method (no I/O)."""

    def test_runs_all_detectors(self):
        db = AsyncMock()
        engine = AlertEngine(db, detectors=[_StubDetector(), _StubDetector()])
        snap_actual = {("Prof. García", "ISW-101"): _snap()}
        candidates = engine._detect(snap_actual, {})
        # 2 detectors with identical dedup key → in-memory dedup keeps 1
        assert len(candidates) == 1

    def test_no_candidates_when_empty_snapshots(self):
        db = AsyncMock()
        engine = AlertEngine(db, detectors=[_StubDetector()])
        assert engine._detect({}, {}) == []

    def test_anterior_passed_to_detectors(self):
        db = AsyncMock()

        class _TrackerDetector:
            tipo = TipoAlerta.CAIDA

            def __init__(self):
                self.calls: list[tuple] = []

            def detect(self, actual, anterior):
                self.calls.append((actual, anterior))
                return []

        tracker = _TrackerDetector()
        engine = AlertEngine(db, detectors=[tracker])

        actual = _snap(periodo="C1 2025")
        anterior = _snap(periodo="C3 2024", eval_id=_UUID2)

        engine._detect(
            {("Prof. García", "ISW-101"): actual},
            {("Prof. García", "ISW-101"): anterior},
        )

        assert len(tracker.calls) == 1
        assert tracker.calls[0][1] is anterior

    def test_anterior_none_when_not_found(self):
        db = AsyncMock()

        class _TrackerDetector:
            tipo = TipoAlerta.CAIDA

            def __init__(self):
                self.received_anterior = "NOT_SET"

            def detect(self, actual, anterior):
                self.received_anterior = anterior
                return []

        tracker = _TrackerDetector()
        engine = AlertEngine(db, detectors=[tracker])

        engine._detect(
            {("Prof. García", "ISW-101"): _snap()},
            {},  # No anterior data
        )
        assert tracker.received_anterior is None

    def test_multiple_docente_cursos(self):
        db = AsyncMock()
        engine = AlertEngine(db, detectors=[_StubDetector()])
        snap_actual = {
            ("Prof. García", "ISW-101"): _snap(docente="Prof. García", curso="ISW-101"),
            ("Prof. López", "ISW-202"): _snap(docente="Prof. López", curso="ISW-202"),
        }
        candidates = engine._detect(snap_actual, {})
        assert len(candidates) == 2


class TestAlertEngineRunForModalidad:
    """Tests for ``run_for_modalidad`` using mocked repo."""

    @pytest.fixture
    def mock_db(self):
        return AsyncMock()

    async def test_no_periodos_skips(self, mock_db):
        with patch(f"{_AE_MOD}.AlertaRepository") as mock_repo_cls:
            mock_repo = mock_repo_cls.return_value
            mock_repo.find_last_two_periods = AsyncMock(return_value=[])

            engine = AlertEngine(mock_db, detectors=[_StubDetector()])
            result = await engine.run_for_modalidad("CUATRIMESTRAL")

            assert result.modalidades_processed == 0
            assert result.candidates_generated == 0

    async def test_single_period_runs_absolute_only(self, mock_db):
        with patch(f"{_AE_MOD}.AlertaRepository") as mock_repo_cls:
            mock_repo = mock_repo_cls.return_value
            mock_repo.find_last_two_periods = AsyncMock(return_value=["C1 2025"])
            mock_repo.load_snapshots = AsyncMock(
                return_value={
                    "C1 2025": {("Prof. García", "ISW-101"): _snap(puntaje=50.0)},
                }
            )
            mock_repo.upsert_batch = AsyncMock(return_value=1)

            engine = AlertEngine(mock_db, detectors=[_StubDetector()])
            result = await engine.run_for_modalidad("CUATRIMESTRAL")

            assert result.modalidades_processed == 1
            assert result.candidates_generated == 1
            assert result.created_or_updated == 1

    async def test_two_periods_loads_both(self, mock_db):
        with patch(f"{_AE_MOD}.AlertaRepository") as mock_repo_cls:
            mock_repo = mock_repo_cls.return_value
            mock_repo.find_last_two_periods = AsyncMock(return_value=["C1 2025", "C3 2024"])
            mock_repo.load_snapshots = AsyncMock(
                return_value={
                    "C1 2025": {("Prof. García", "ISW-101"): _snap(periodo="C1 2025")},
                    "C3 2024": {
                        ("Prof. García", "ISW-101"): _snap(periodo="C3 2024", eval_id=_UUID2)
                    },
                }
            )
            mock_repo.upsert_batch = AsyncMock(return_value=1)

            engine = AlertEngine(mock_db, detectors=[_StubDetector()])
            result = await engine.run_for_modalidad("CUATRIMESTRAL")

            assert result.periodos_by_modalidad["CUATRIMESTRAL"] == [
                "C1 2025",
                "C3 2024",
            ]

    async def test_no_candidates_skips_upsert(self, mock_db):
        with patch(f"{_AE_MOD}.AlertaRepository") as mock_repo_cls:
            mock_repo = mock_repo_cls.return_value
            mock_repo.find_last_two_periods = AsyncMock(return_value=["C1 2025"])
            mock_repo.load_snapshots = AsyncMock(
                return_value={
                    "C1 2025": {("Prof. García", "ISW-101"): _snap(puntaje=90.0)},
                }
            )

            engine = AlertEngine(mock_db, detectors=[_NeverDetector()])
            result = await engine.run_for_modalidad("CUATRIMESTRAL")

            assert result.candidates_generated == 0
            assert result.created_or_updated == 0
            mock_repo.upsert_batch.assert_not_called()


class TestAlertEngineRunAll:
    """Tests for ``run_all`` aggregation across modalidades."""

    async def test_aggregates_results(self):
        mock_db = AsyncMock()
        with patch(f"{_AE_MOD}.AlertaRepository") as mock_repo_cls:
            mock_repo = mock_repo_cls.return_value
            # CUATRIMESTRAL has data, MENSUAL and B2B don't
            mock_repo.find_last_two_periods = AsyncMock(
                side_effect=lambda m: ["C1 2025"] if m == "CUATRIMESTRAL" else []
            )
            mock_repo.load_snapshots = AsyncMock(
                return_value={
                    "C1 2025": {("Prof. García", "ISW-101"): _snap(puntaje=50.0)},
                }
            )
            mock_repo.upsert_batch = AsyncMock(return_value=1)

            engine = AlertEngine(mock_db, detectors=[_StubDetector()])
            result = await engine.run_all()

            assert result.modalidades_processed == 1
            assert result.candidates_generated == 1
            assert "CUATRIMESTRAL" in result.periodos_by_modalidad


class TestAlertEngineRegisterDetector:
    def test_register_adds_detector(self):
        db = AsyncMock()
        engine = AlertEngine(db, detectors=[])
        assert len(engine._detectors) == 0

        engine.register_detector(_StubDetector())
        assert len(engine._detectors) == 1
