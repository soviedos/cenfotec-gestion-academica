"""Edge-case tests for the alert engine — year boundaries, incomplete
periods, cross-modalidad isolation, snapshot aggregation, and dedup.

Covers business rules [AL-01], [AL-10], [AL-40], [BR-MOD-02].
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, patch

from app.modules.evaluacion_docente.application.services.alert_engine import (
    _ALERTABLE_MODALIDADES,
    AlertEngine,
)
from app.modules.evaluacion_docente.domain.alert_rules import (
    AlertCandidate,
    BajoDesempenoDetector,
    CaidaDetector,
    DocenteCursoSnapshot,
    SentimientoDetector,
)
from app.modules.evaluacion_docente.domain.entities.enums import Modalidad, Severidad, TipoAlerta

_AE_MOD = "app.modules.evaluacion_docente.application.services.alert_engine"

_UUID1 = uuid.UUID("00000000-0000-0000-0000-000000000001")
_UUID2 = uuid.UUID("00000000-0000-0000-0000-000000000002")
_UUID3 = uuid.UUID("00000000-0000-0000-0000-000000000003")


# ── Helpers ──────────────────────────────────────────────────────────────


def _snap(
    *,
    periodo: str = "C1 2025",
    eval_id: uuid.UUID = _UUID1,
    puntaje: float | None = 50.0,
    docente: str = "Prof. García",
    curso: str = "ISW-101",
    modalidad: str = "CUATRIMESTRAL",
    total: int = 10,
    negativos: int = 1,
    mejora_neg: int = 0,
    actitud_neg: int = 0,
    otro: int = 0,
) -> DocenteCursoSnapshot:
    return DocenteCursoSnapshot(
        evaluacion_id=eval_id,
        docente_nombre=docente,
        curso=curso,
        periodo=periodo,
        modalidad=modalidad,
        puntaje_general=puntaje,
        total_comentarios=total,
        negativos_count=negativos,
        mejora_negativo_count=mejora_neg,
        actitud_negativo_count=actitud_neg,
        otro_count=otro,
    )


class _StubDetector:
    """Detector that always emits one BAJO_DESEMPEÑO alert."""

    tipo = TipoAlerta.BAJO_DESEMPENO

    def detect(self, actual: DocenteCursoSnapshot, anterior=None) -> list[AlertCandidate]:
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
                valor_anterior=anterior.puntaje_general if anterior else None,
                descripcion="stub alert",
                severidad=Severidad.ALTA,
            )
        ]


class _DuplicatingDetector:
    """Detector that returns TWO identical candidates for the same key."""

    tipo = TipoAlerta.BAJO_DESEMPENO

    def detect(self, actual: DocenteCursoSnapshot, anterior=None) -> list[AlertCandidate]:
        c = AlertCandidate(
            evaluacion_id=actual.evaluacion_id,
            docente_nombre=actual.docente_nombre,
            curso=actual.curso,
            periodo=actual.periodo,
            modalidad=actual.modalidad,
            tipo_alerta=self.tipo,
            metrica_afectada="puntaje_general",
            valor_actual=actual.puntaje_general or 0,
            valor_anterior=None,
            descripcion="duplicate candidate",
            severidad=Severidad.ALTA,
        )
        return [c, c]


# ═══════════════════════════════════════════════════════════════════════
# Year-boundary scenarios [AL-01]
# ═══════════════════════════════════════════════════════════════════════


class TestYearBoundary:
    """Ensure alerts work across year boundaries (e.g. C3 2024 → C1 2025)."""

    def test_detect_across_year_boundary(self):
        """CaídaDetector fires when comparing C1 2025 vs C3 2024."""
        db = AsyncMock()
        engine = AlertEngine(db, detectors=[CaidaDetector()])

        actual = _snap(periodo="C1 2025", puntaje=60.0)
        anterior = _snap(periodo="C3 2024", puntaje=90.0, eval_id=_UUID2)

        candidates = engine._detect(
            {("Prof. García", "ISW-101"): actual},
            {("Prof. García", "ISW-101"): anterior},
        )
        assert len(candidates) == 1
        assert candidates[0].severidad == Severidad.ALTA
        assert "C3 2024" in candidates[0].descripcion

    async def test_run_for_modalidad_year_boundary(self):
        """Engine loads C1 2025 + C3 2024 and produces comparative alerts."""
        mock_db = AsyncMock()
        with patch(f"{_AE_MOD}.AlertaRepository") as cls:
            repo = cls.return_value
            repo.find_last_two_periods = AsyncMock(return_value=["C1 2025", "C3 2024"])
            repo.load_snapshots = AsyncMock(
                return_value={
                    "C1 2025": {
                        ("Prof. García", "ISW-101"): _snap(periodo="C1 2025", puntaje=55.0)
                    },
                    "C3 2024": {
                        ("Prof. García", "ISW-101"): _snap(
                            periodo="C3 2024", puntaje=85.0, eval_id=_UUID2
                        )
                    },
                }
            )
            repo.upsert_batch = AsyncMock(return_value=2)

            engine = AlertEngine(mock_db, detectors=[BajoDesempenoDetector(), CaidaDetector()])
            result = await engine.run_for_modalidad("CUATRIMESTRAL")

            assert result.periodos_by_modalidad["CUATRIMESTRAL"] == ["C1 2025", "C3 2024"]
            assert result.candidates_generated >= 2  # bajo + caida

    def test_mensual_year_boundary(self):
        """M1 2026 vs M10 2025 — should detect drop across year."""
        db = AsyncMock()
        engine = AlertEngine(db, detectors=[CaidaDetector()])

        actual = _snap(periodo="M1 2026", puntaje=65.0, modalidad="MENSUAL")
        anterior = _snap(periodo="M10 2025", puntaje=90.0, eval_id=_UUID2, modalidad="MENSUAL")

        candidates = engine._detect(
            {("Prof. García", "ISW-101"): actual},
            {("Prof. García", "ISW-101"): anterior},
        )
        assert len(candidates) == 1
        assert candidates[0].modalidad == "MENSUAL"


# ═══════════════════════════════════════════════════════════════════════
# Incomplete period scenarios [AL-02]
# ═══════════════════════════════════════════════════════════════════════


class TestIncompletePeriods:
    """When only 1 period exists, only absolute detectors fire."""

    async def test_single_period_no_comparative_alerts(self):
        """With one period, Caída and Sentimiento must produce zero alerts."""
        mock_db = AsyncMock()
        with patch(f"{_AE_MOD}.AlertaRepository") as cls:
            repo = cls.return_value
            repo.find_last_two_periods = AsyncMock(return_value=["C1 2025"])
            repo.load_snapshots = AsyncMock(
                return_value={
                    "C1 2025": {("Prof. García", "ISW-101"): _snap(puntaje=50.0)},
                }
            )
            repo.upsert_batch = AsyncMock(return_value=1)

            engine = AlertEngine(
                mock_db,
                detectors=[BajoDesempenoDetector(), CaidaDetector(), SentimientoDetector()],
            )
            result = await engine.run_for_modalidad("CUATRIMESTRAL")

            # Only BajoDesempeño fires (puntaje=50 < 60 → alta)
            assert result.candidates_generated == 1
            upserted = repo.upsert_batch.call_args[0][0]
            assert upserted[0].tipo_alerta == TipoAlerta.BAJO_DESEMPENO

    def test_caida_requires_anterior(self):
        """CaídaDetector returns empty when anterior is None."""
        db = AsyncMock()
        engine = AlertEngine(db, detectors=[CaidaDetector()])
        actual = _snap(puntaje=50.0)
        assert engine._detect({("P", "C"): actual}, {}) == []

    def test_sentimiento_requires_anterior(self):
        """SentimientoDetector returns empty when anterior is None."""
        db = AsyncMock()
        engine = AlertEngine(db, detectors=[SentimientoDetector()])
        actual = _snap(puntaje=50.0, total=10, negativos=8)
        assert engine._detect({("P", "C"): actual}, {}) == []

    async def test_zero_periods_returns_empty_result(self):
        """No periods at all → skip entirely, zero everything."""
        mock_db = AsyncMock()
        with patch(f"{_AE_MOD}.AlertaRepository") as cls:
            repo = cls.return_value
            repo.find_last_two_periods = AsyncMock(return_value=[])

            engine = AlertEngine(mock_db, detectors=[_StubDetector()])
            result = await engine.run_for_modalidad("CUATRIMESTRAL")

            assert result.modalidades_processed == 0
            assert result.candidates_generated == 0
            assert result.created_or_updated == 0


# ═══════════════════════════════════════════════════════════════════════
# Cross-modalidad isolation [BR-MOD-02]
# ═══════════════════════════════════════════════════════════════════════


class TestModalidadIsolation:
    """Ensure engine never mixes data across modalidades."""

    def test_alertable_modalidades_excludes_desconocida(self):
        """DESCONOCIDA must never appear in alertable modalidades."""
        assert Modalidad.DESCONOCIDA.value not in _ALERTABLE_MODALIDADES

    def test_three_alertable_modalidades(self):
        """Only CUATRIMESTRAL, MENSUAL, B2B."""
        assert set(_ALERTABLE_MODALIDADES) == {
            Modalidad.CUATRIMESTRAL.value,
            Modalidad.MENSUAL.value,
            Modalidad.B2B.value,
        }

    async def test_run_all_processes_each_modalidad_independently(self):
        """run_all() calls run_for_modalidad() once per alertable modalidad."""
        mock_db = AsyncMock()
        with patch(f"{_AE_MOD}.AlertaRepository") as cls:
            repo = cls.return_value
            periodos_by_mod = {
                "CUATRIMESTRAL": ["C1 2025"],
                "MENSUAL": ["M1 2025"],
                "B2B": [],
            }
            repo.find_last_two_periods = AsyncMock(side_effect=lambda m: periodos_by_mod.get(m, []))
            repo.load_snapshots = AsyncMock(
                side_effect=lambda m, p: {
                    p[0]: {
                        ("Prof. García", "ISW-101"): _snap(puntaje=50.0, modalidad=m, periodo=p[0])
                    }
                }
            )
            repo.upsert_batch = AsyncMock(return_value=1)

            engine = AlertEngine(mock_db, detectors=[_StubDetector()])
            result = await engine.run_all()

            # CUATRIMESTRAL + MENSUAL processed; B2B skipped (no periodos)
            assert result.modalidades_processed == 2
            assert "CUATRIMESTRAL" in result.periodos_by_modalidad
            assert "MENSUAL" in result.periodos_by_modalidad
            assert "B2B" not in result.periodos_by_modalidad

    def test_candidates_preserve_modalidad(self):
        """Each candidate carries the modalidad of its source snapshot."""
        db = AsyncMock()
        engine = AlertEngine(db, detectors=[_StubDetector()])

        cuatri = _snap(docente="Prof. A", modalidad="CUATRIMESTRAL", periodo="C1 2025")
        mensual = _snap(docente="Prof. B", modalidad="MENSUAL", periodo="M1 2025")

        # Process cuatrimestral snapshots
        c1 = engine._detect({("Prof. A", "ISW-101"): cuatri}, {})
        assert all(c.modalidad == "CUATRIMESTRAL" for c in c1)

        # Process mensual snapshots
        c2 = engine._detect({("Prof. B", "ISW-101"): mensual}, {})
        assert all(c.modalidad == "MENSUAL" for c in c2)


# ═══════════════════════════════════════════════════════════════════════
# In-memory deduplication [AL-40]
# ═══════════════════════════════════════════════════════════════════════


class TestInMemoryDedup:
    """Verify the engine deduplicates candidates before DB upsert."""

    def test_duplicate_detector_produces_single_candidate(self):
        """A detector returning 2 identical candidates yields only 1."""
        db = AsyncMock()
        engine = AlertEngine(db, detectors=[_DuplicatingDetector()])

        snap = _snap(puntaje=50.0)
        candidates = engine._detect({("Prof. García", "ISW-101"): snap}, {})
        assert len(candidates) == 1

    def test_different_tipos_not_deduped(self):
        """Candidates with different tipo_alerta are NOT deduped."""
        db = AsyncMock()

        class _CaidaStub:
            tipo = TipoAlerta.CAIDA

            def detect(self, actual, anterior):
                if anterior is None:
                    return []
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
                        valor_anterior=anterior.puntaje_general if anterior else None,
                        descripcion="caida stub",
                        severidad=Severidad.MEDIA,
                    )
                ]

        engine = AlertEngine(db, detectors=[_StubDetector(), _CaidaStub()])

        actual = _snap(puntaje=50.0, periodo="C1 2025")
        anterior = _snap(puntaje=90.0, periodo="C3 2024", eval_id=_UUID2)

        candidates = engine._detect(
            {("Prof. García", "ISW-101"): actual},
            {("Prof. García", "ISW-101"): anterior},
        )
        # BAJO_DESEMPEÑO + CAIDA = 2 different tipos → both kept
        tipos = {c.tipo_alerta for c in candidates}
        assert tipos == {TipoAlerta.BAJO_DESEMPENO, TipoAlerta.CAIDA}

    def test_different_modalidades_not_deduped(self):
        """Same docente+curso+periodo but different modalidad → both kept."""
        db = AsyncMock()
        engine = AlertEngine(db, detectors=[_StubDetector()])

        cuatri = _snap(modalidad="CUATRIMESTRAL", periodo="C1 2025")
        mensual = _snap(
            modalidad="MENSUAL", periodo="M1 2025", docente="Prof. García", curso="ISW-101"
        )

        # These have different periods so different dedup keys
        c1 = engine._detect({("Prof. García", "ISW-101"): cuatri}, {})
        c2 = engine._detect({("Prof. García", "ISW-101"): mensual}, {})

        assert len(c1) == 1
        assert len(c2) == 1
        assert c1[0].modalidad != c2[0].modalidad

    def test_same_key_different_severidad_keeps_first(self):
        """When duplicate key appears, the first candidate wins."""
        db = AsyncMock()

        class _DoubleDetector:
            tipo = TipoAlerta.BAJO_DESEMPENO

            def detect(self, actual, anterior):
                return [
                    AlertCandidate(
                        evaluacion_id=actual.evaluacion_id,
                        docente_nombre=actual.docente_nombre,
                        curso=actual.curso,
                        periodo=actual.periodo,
                        modalidad=actual.modalidad,
                        tipo_alerta=self.tipo,
                        metrica_afectada="puntaje_general",
                        valor_actual=50.0,
                        valor_anterior=None,
                        descripcion="first",
                        severidad=Severidad.ALTA,
                    ),
                    AlertCandidate(
                        evaluacion_id=actual.evaluacion_id,
                        docente_nombre=actual.docente_nombre,
                        curso=actual.curso,
                        periodo=actual.periodo,
                        modalidad=actual.modalidad,
                        tipo_alerta=self.tipo,
                        metrica_afectada="puntaje_general",
                        valor_actual=55.0,
                        valor_anterior=None,
                        descripcion="second — should be dropped",
                        severidad=Severidad.BAJA,
                    ),
                ]

        engine = AlertEngine(db, detectors=[_DoubleDetector()])
        candidates = engine._detect({("Prof. García", "ISW-101"): _snap()}, {})
        assert len(candidates) == 1
        assert candidates[0].descripcion == "first"
        assert candidates[0].severidad == Severidad.ALTA


# ═══════════════════════════════════════════════════════════════════════
# Alert content completeness [AL-30]
# ═══════════════════════════════════════════════════════════════════════


class TestAlertContentCompleteness:
    """Every AlertCandidate must include all required fields."""

    def _assert_complete(self, candidate: AlertCandidate) -> None:
        assert candidate.docente_nombre
        assert candidate.curso
        assert candidate.periodo
        assert candidate.modalidad
        assert candidate.tipo_alerta is not None
        assert candidate.metrica_afectada
        assert candidate.valor_actual is not None
        assert candidate.descripcion
        assert candidate.severidad is not None

    def test_bajo_desempeno_complete(self):
        actual = _snap(puntaje=50.0)
        alerts = BajoDesempenoDetector().detect(actual, None)
        for a in alerts:
            self._assert_complete(a)

    def test_caida_complete(self):
        actual = _snap(puntaje=50.0, periodo="C1 2025")
        anterior = _snap(puntaje=90.0, periodo="C3 2024", eval_id=_UUID2)
        alerts = CaidaDetector().detect(actual, anterior)
        for a in alerts:
            self._assert_complete(a)
            assert a.valor_anterior is not None  # caída requires comparative value

    def test_sentimiento_complete(self):
        actual = _snap(total=100, negativos=30, periodo="C1 2025")
        anterior = _snap(total=100, negativos=5, periodo="C3 2024", eval_id=_UUID2)
        alerts = SentimientoDetector().detect(actual, anterior)
        for a in alerts:
            self._assert_complete(a)
            assert a.valor_anterior is not None  # sentimiento requires comparative value

    def test_patron_complete(self):
        from app.modules.evaluacion_docente.domain.alert_rules import PatronDetector

        actual = _snap(total=100, mejora_neg=60)
        alerts = PatronDetector().detect(actual, None)
        for a in alerts:
            self._assert_complete(a)
            # Patrón never has valor_anterior
            assert a.valor_anterior is None


# ═══════════════════════════════════════════════════════════════════════
# Docente+curso appearing only in anterior — no alerts [AL-01]
# ═══════════════════════════════════════════════════════════════════════


class TestDocenteOnlyInAnterior:
    """A docente+curso that existed in the previous period but NOT in the
    current one should NOT generate alerts (alerts scope to periodo actual)."""

    def test_no_actual_snapshot_no_alert(self):
        db = AsyncMock()
        engine = AlertEngine(db, detectors=[_StubDetector(), CaidaDetector()])

        # Prof. García only in anterior, not in actual
        anterior = _snap(periodo="C3 2024", puntaje=90.0, eval_id=_UUID2)
        candidates = engine._detect(
            {},  # No actual data
            {("Prof. García", "ISW-101"): anterior},
        )
        assert candidates == []


# ═══════════════════════════════════════════════════════════════════════
# Multiple docentes and courses in a single run
# ═══════════════════════════════════════════════════════════════════════


class TestMultipleDocentesCursos:
    """Ensure all docente+curso pairs are processed independently."""

    def test_multiple_pairs_generate_independent_alerts(self):
        db = AsyncMock()
        engine = AlertEngine(db, detectors=[BajoDesempenoDetector()])

        snap_actual = {
            ("Prof. García", "ISW-101"): _snap(
                docente="Prof. García", curso="ISW-101", puntaje=50.0
            ),
            ("Prof. López", "ISW-202"): _snap(docente="Prof. López", curso="ISW-202", puntaje=65.0),
            ("Prof. Martínez", "ISW-303"): _snap(
                docente="Prof. Martínez", curso="ISW-303", puntaje=90.0
            ),
        }
        candidates = engine._detect(snap_actual, {})

        # García (50 < 60 → alta), López (65 < 70 → media), Martínez (90 ≥ 80 → none)
        assert len(candidates) == 2
        docentes = {c.docente_nombre for c in candidates}
        assert docentes == {"Prof. García", "Prof. López"}

    def test_anterior_matched_by_key(self):
        """Each docente+curso pair matches its own anterior, not others'."""
        db = AsyncMock()
        engine = AlertEngine(db, detectors=[CaidaDetector()])

        snap_actual = {
            ("Prof. García", "ISW-101"): _snap(
                docente="Prof. García", curso="ISW-101", puntaje=50.0, periodo="C1 2025"
            ),
            ("Prof. López", "ISW-202"): _snap(
                docente="Prof. López", curso="ISW-202", puntaje=85.0, periodo="C1 2025"
            ),
        }
        snap_anterior = {
            ("Prof. García", "ISW-101"): _snap(
                docente="Prof. García",
                curso="ISW-101",
                puntaje=90.0,
                periodo="C3 2024",
                eval_id=_UUID2,
            ),
            # Prof. López has NO anterior
        }

        candidates = engine._detect(snap_actual, snap_anterior)
        # Only García has a drop (90 → 50 = 40pt drop → alta)
        assert len(candidates) == 1
        assert candidates[0].docente_nombre == "Prof. García"


# ═══════════════════════════════════════════════════════════════════════
# SIN CURSO edge case
# ═══════════════════════════════════════════════════════════════════════


class TestSinCurso:
    """Evaluaciones with NULL materia should be handled as 'SIN CURSO'."""

    def test_sin_curso_generates_alerts(self):
        db = AsyncMock()
        engine = AlertEngine(db, detectors=[BajoDesempenoDetector()])

        snap = _snap(curso="SIN CURSO", puntaje=50.0)
        candidates = engine._detect({("Prof. García", "SIN CURSO"): snap}, {})
        assert len(candidates) == 1
        assert candidates[0].curso == "SIN CURSO"


# ═══════════════════════════════════════════════════════════════════════
# Year-change scenarios — strict [AL-01]
# ═══════════════════════════════════════════════════════════════════════


class TestYearChangeStrict:
    """Verify year boundaries are handled correctly for each modalidad."""

    def test_cuatrimestral_c3_previous_year_to_c1_current(self):
        """Caída detector must fire when comparing C1 2025 vs C3 2024."""
        db = AsyncMock()
        engine = AlertEngine(db, detectors=[CaidaDetector()])

        actual = _snap(periodo="C1 2025", puntaje=60.0, modalidad="CUATRIMESTRAL")
        anterior = _snap(
            periodo="C3 2024",
            puntaje=90.0,
            eval_id=_UUID2,
            modalidad="CUATRIMESTRAL",
        )

        candidates = engine._detect(
            {("Prof. García", "ISW-101"): actual},
            {("Prof. García", "ISW-101"): anterior},
            expected_modalidad="CUATRIMESTRAL",
        )
        assert len(candidates) == 1
        assert candidates[0].tipo_alerta == TipoAlerta.CAIDA
        assert candidates[0].valor_anterior == 90.0
        assert candidates[0].valor_actual == 60.0
        assert candidates[0].modalidad == "CUATRIMESTRAL"

    def test_mensual_m10_previous_year_to_m1_current(self):
        """Caída detector must fire when comparing M1 2026 vs M10 2025."""
        db = AsyncMock()
        engine = AlertEngine(db, detectors=[CaidaDetector()])

        actual = _snap(periodo="M1 2026", puntaje=65.0, modalidad="MENSUAL")
        anterior = _snap(
            periodo="M10 2025",
            puntaje=90.0,
            eval_id=_UUID2,
            modalidad="MENSUAL",
        )

        candidates = engine._detect(
            {("Prof. García", "ISW-101"): actual},
            {("Prof. García", "ISW-101"): anterior},
            expected_modalidad="MENSUAL",
        )
        assert len(candidates) == 1
        assert candidates[0].modalidad == "MENSUAL"
        assert "M10 2025" in candidates[0].descripcion

    async def test_engine_loads_cross_year_periods(self):
        """run_for_modalidad correctly pairs C1 2025 (actual) with C3 2024 (anterior)."""
        mock_db = AsyncMock()
        with patch(f"{_AE_MOD}.AlertaRepository") as cls:
            repo = cls.return_value
            repo.find_last_two_periods = AsyncMock(return_value=["C1 2025", "C3 2024"])
            repo.load_snapshots = AsyncMock(
                return_value={
                    "C1 2025": {
                        ("Prof. García", "ISW-101"): _snap(periodo="C1 2025", puntaje=55.0)
                    },
                    "C3 2024": {
                        ("Prof. García", "ISW-101"): _snap(
                            periodo="C3 2024", puntaje=90.0, eval_id=_UUID2
                        )
                    },
                },
            )
            repo.upsert_batch = AsyncMock(return_value=2)

            engine = AlertEngine(mock_db, detectors=[BajoDesempenoDetector(), CaidaDetector()])
            result = await engine.run_for_modalidad("CUATRIMESTRAL")

            assert result.periodos_by_modalidad["CUATRIMESTRAL"] == [
                "C1 2025",
                "C3 2024",
            ]
            # bajo (55 < 60 → alta) + caída (90 → 55 = 35 drop → alta)
            assert result.candidates_generated == 2

    def test_sentimiento_across_year_boundary(self):
        """Sentimiento detector fires across year boundary."""
        db = AsyncMock()
        engine = AlertEngine(db, detectors=[SentimientoDetector()])

        actual = _snap(
            periodo="C1 2025",
            total=100,
            negativos=30,
            modalidad="CUATRIMESTRAL",
        )
        anterior = _snap(
            periodo="C3 2024",
            total=100,
            negativos=5,
            eval_id=_UUID2,
            modalidad="CUATRIMESTRAL",
        )

        candidates = engine._detect(
            {("Prof. García", "ISW-101"): actual},
            {("Prof. García", "ISW-101"): anterior},
            expected_modalidad="CUATRIMESTRAL",
        )
        assert len(candidates) == 1
        assert candidates[0].tipo_alerta == TipoAlerta.SENTIMIENTO
        assert candidates[0].modalidad == "CUATRIMESTRAL"


# ═══════════════════════════════════════════════════════════════════════
# Missing periods — strict [AL-02]
# ═══════════════════════════════════════════════════════════════════════


class TestMissingPeriodsStrict:
    """When some periods are missing, engine must behave safely."""

    async def test_gap_uses_last_two_available(self):
        """If C2 2025 is missing, engine uses C3 2025 + C1 2025 (the two most recent)."""
        mock_db = AsyncMock()
        with patch(f"{_AE_MOD}.AlertaRepository") as cls:
            repo = cls.return_value
            # Simulating C3 2025 and C1 2025 exist, C2 2025 is missing
            repo.find_last_two_periods = AsyncMock(return_value=["C3 2025", "C1 2025"])
            repo.load_snapshots = AsyncMock(
                return_value={
                    "C3 2025": {
                        ("Prof. García", "ISW-101"): _snap(periodo="C3 2025", puntaje=50.0)
                    },
                    "C1 2025": {
                        ("Prof. García", "ISW-101"): _snap(
                            periodo="C1 2025", puntaje=90.0, eval_id=_UUID2
                        )
                    },
                },
            )
            repo.upsert_batch = AsyncMock(return_value=2)

            engine = AlertEngine(mock_db, detectors=[BajoDesempenoDetector(), CaidaDetector()])
            result = await engine.run_for_modalidad("CUATRIMESTRAL")

            assert result.periodos_by_modalidad["CUATRIMESTRAL"] == [
                "C3 2025",
                "C1 2025",
            ]
            # bajo (50 < 60) + caída (90 → 50 = 40pt drop)
            assert result.candidates_generated == 2

    async def test_only_one_period_no_comparative(self):
        """Single period: only absolute detectors fire, no comparative alerts."""
        mock_db = AsyncMock()
        with patch(f"{_AE_MOD}.AlertaRepository") as cls:
            repo = cls.return_value
            repo.find_last_two_periods = AsyncMock(return_value=["M5 2025"])
            repo.load_snapshots = AsyncMock(
                return_value={
                    "M5 2025": {
                        ("Prof. García", "ISW-101"): _snap(
                            periodo="M5 2025",
                            puntaje=50.0,
                            modalidad="MENSUAL",
                            total=100,
                            negativos=80,
                        )
                    },
                },
            )
            repo.upsert_batch = AsyncMock(return_value=1)

            engine = AlertEngine(
                mock_db,
                detectors=[
                    BajoDesempenoDetector(),
                    CaidaDetector(),
                    SentimientoDetector(),
                ],
            )
            result = await engine.run_for_modalidad("MENSUAL")

            # Only BajoDesempeño fires; Caída and Sentimiento need anterior
            assert result.candidates_generated == 1
            upserted = repo.upsert_batch.call_args[0][0]
            assert all(c.tipo_alerta == TipoAlerta.BAJO_DESEMPENO for c in upserted)

    async def test_zero_periods_no_alerts(self):
        """No completed evaluations → zero alerts, zero processing."""
        mock_db = AsyncMock()
        with patch(f"{_AE_MOD}.AlertaRepository") as cls:
            repo = cls.return_value
            repo.find_last_two_periods = AsyncMock(return_value=[])

            engine = AlertEngine(mock_db, detectors=[_StubDetector()])
            result = await engine.run_for_modalidad("B2B")

            assert result.modalidades_processed == 0
            assert result.candidates_generated == 0
            assert result.created_or_updated == 0
            repo.load_snapshots.assert_not_called()

    def test_docente_only_in_anterior_no_alert(self):
        """Docente disappearing from current period must NOT trigger alerts."""
        db = AsyncMock()
        engine = AlertEngine(db, detectors=[BajoDesempenoDetector(), CaidaDetector()])
        anterior = _snap(periodo="C3 2024", puntaje=50.0, eval_id=_UUID2)
        candidates = engine._detect(
            {},
            {("Prof. García", "ISW-101"): anterior},
            expected_modalidad="CUATRIMESTRAL",
        )
        assert candidates == []


# ═══════════════════════════════════════════════════════════════════════
# Modalidad mixing prevention — strict [BR-MOD-02]
# ═══════════════════════════════════════════════════════════════════════


class TestModalidadMixingStrict:
    """Verify the engine never mixes data across modalidades."""

    def test_detect_filters_wrong_modalidad_candidate(self):
        """_detect with expected_modalidad rejects mismatched candidates."""
        db = AsyncMock()

        class _WrongModalidadDetector:
            """Detector that emits a candidate with MENSUAL modalidad."""

            tipo = TipoAlerta.BAJO_DESEMPENO

            def detect(self, actual, anterior=None):
                return [
                    AlertCandidate(
                        evaluacion_id=actual.evaluacion_id,
                        docente_nombre=actual.docente_nombre,
                        curso=actual.curso,
                        periodo=actual.periodo,
                        modalidad="MENSUAL",  # WRONG — source is CUATRIMESTRAL
                        tipo_alerta=self.tipo,
                        metrica_afectada="puntaje_general",
                        valor_actual=50.0,
                        valor_anterior=None,
                        descripcion="bad modalidad",
                        severidad=Severidad.ALTA,
                    )
                ]

        engine = AlertEngine(db, detectors=[_WrongModalidadDetector()])
        snap = _snap(modalidad="CUATRIMESTRAL", puntaje=50.0)

        candidates = engine._detect(
            {("Prof. García", "ISW-101"): snap},
            {},
            expected_modalidad="CUATRIMESTRAL",
        )
        # Must be filtered out — wrong modalidad
        assert candidates == []

    def test_detect_without_expected_modalidad_keeps_all(self):
        """Without expected_modalidad (legacy), no filtering occurs."""
        db = AsyncMock()
        engine = AlertEngine(db, detectors=[_StubDetector()])

        snap = _snap(modalidad="CUATRIMESTRAL", puntaje=50.0)
        candidates = engine._detect(
            {("Prof. García", "ISW-101"): snap},
            {},
        )
        assert len(candidates) == 1

    async def test_run_all_isolates_modalidades(self):
        """run_all processes each modalidad independently — no data leaks."""
        mock_db = AsyncMock()
        with patch(f"{_AE_MOD}.AlertaRepository") as cls:
            repo = cls.return_value

            snapshot_calls: list[tuple[str, list[str]]] = []

            async def track_snapshots(mod, periodos):
                snapshot_calls.append((mod, list(periodos)))
                return {
                    periodos[0]: {
                        ("Prof.", "C"): _snap(puntaje=50.0, modalidad=mod, periodo=periodos[0])
                    }
                }

            repo.find_last_two_periods = AsyncMock(
                side_effect=lambda m: {
                    "B2B": [],
                    "CUATRIMESTRAL": ["C1 2025"],
                    "MENSUAL": ["M1 2025"],
                }.get(m, [])
            )
            repo.load_snapshots = AsyncMock(side_effect=track_snapshots)
            repo.upsert_batch = AsyncMock(return_value=1)

            engine = AlertEngine(mock_db, detectors=[_StubDetector()])
            await engine.run_all()

            # Verify each load_snapshots call was scoped to its modalidad
            assert len(snapshot_calls) == 2
            modalidades_called = {m for m, _ in snapshot_calls}
            assert modalidades_called == {"CUATRIMESTRAL", "MENSUAL"}

            # Verify upsert_batch candidates carry correct modalidades
            for call in repo.upsert_batch.call_args_list:
                candidates = call[0][0]
                for c in candidates:
                    assert c.modalidad in {"CUATRIMESTRAL", "MENSUAL"}

    def test_same_docente_two_modalidades_independent(self):
        """Same docente in CUATRIMESTRAL and MENSUAL → independent alerts."""
        db = AsyncMock()
        engine = AlertEngine(db, detectors=[BajoDesempenoDetector()])

        # Run for CUATRIMESTRAL
        cuatri = _snap(
            docente="Prof. García",
            curso="ISW-101",
            puntaje=50.0,
            modalidad="CUATRIMESTRAL",
            periodo="C1 2025",
        )
        c1 = engine._detect(
            {("Prof. García", "ISW-101"): cuatri},
            {},
            expected_modalidad="CUATRIMESTRAL",
        )

        # Run for MENSUAL
        mensual = _snap(
            docente="Prof. García",
            curso="ISW-101",
            puntaje=50.0,
            modalidad="MENSUAL",
            periodo="M1 2025",
        )
        c2 = engine._detect(
            {("Prof. García", "ISW-101"): mensual},
            {},
            expected_modalidad="MENSUAL",
        )

        assert len(c1) == 1
        assert len(c2) == 1
        assert c1[0].modalidad == "CUATRIMESTRAL"
        assert c2[0].modalidad == "MENSUAL"
        # Different dedup keys (periodo differs + modalidad differs)
        assert c1[0].periodo != c2[0].periodo


# ═══════════════════════════════════════════════════════════════════════
# Alert duplication prevention — strict [AL-40]
# ═══════════════════════════════════════════════════════════════════════


class TestDuplicationPreventionStrict:
    """Verify no duplicate alerts are created, even in edge cases."""

    def test_rerun_produces_identical_candidates(self):
        """Running _detect twice with same data yields same result."""
        db = AsyncMock()
        engine = AlertEngine(
            db,
            detectors=[BajoDesempenoDetector(), CaidaDetector()],
        )

        actual = _snap(periodo="C1 2025", puntaje=55.0)
        anterior = _snap(periodo="C3 2024", puntaje=90.0, eval_id=_UUID2)
        snap_a = {("Prof. García", "ISW-101"): actual}
        snap_p = {("Prof. García", "ISW-101"): anterior}

        run1 = engine._detect(snap_a, snap_p, expected_modalidad="CUATRIMESTRAL")
        run2 = engine._detect(snap_a, snap_p, expected_modalidad="CUATRIMESTRAL")

        assert len(run1) == len(run2)
        for c1, c2 in zip(run1, run2):
            assert c1.docente_nombre == c2.docente_nombre
            assert c1.curso == c2.curso
            assert c1.periodo == c2.periodo
            assert c1.tipo_alerta == c2.tipo_alerta
            assert c1.modalidad == c2.modalidad
            assert c1.severidad == c2.severidad

    def test_multiple_detectors_same_type_dedup(self):
        """Two detectors returning same tipo_alerta → only first candidate kept."""
        db = AsyncMock()
        engine = AlertEngine(db, detectors=[_StubDetector(), _StubDetector()])

        snap = _snap(puntaje=50.0)
        candidates = engine._detect(
            {("Prof. García", "ISW-101"): snap},
            {},
            expected_modalidad="CUATRIMESTRAL",
        )
        assert len(candidates) == 1

    def test_different_cursos_same_docente_not_deduped(self):
        """Same docente, different cursos → separate alerts (not duplicates)."""
        db = AsyncMock()
        engine = AlertEngine(db, detectors=[BajoDesempenoDetector()])

        snap_actual = {
            ("Prof. García", "ISW-101"): _snap(
                docente="Prof. García", curso="ISW-101", puntaje=50.0
            ),
            ("Prof. García", "ISW-202"): _snap(
                docente="Prof. García", curso="ISW-202", puntaje=55.0
            ),
        }
        candidates = engine._detect(snap_actual, {}, expected_modalidad="CUATRIMESTRAL")
        # Both courses below threshold → separate alerts
        assert len(candidates) == 2
        cursos = {c.curso for c in candidates}
        assert cursos == {"ISW-101", "ISW-202"}

    def test_different_tipos_same_docente_curso_not_deduped(self):
        """Bajo + Caída for same docente+curso → 2 alerts (different tipo_alerta)."""
        db = AsyncMock()
        engine = AlertEngine(db, detectors=[BajoDesempenoDetector(), CaidaDetector()])

        actual = _snap(docente="Prof. García", curso="ISW-101", puntaje=50.0, periodo="C1 2025")
        anterior = _snap(
            docente="Prof. García",
            curso="ISW-101",
            puntaje=90.0,
            periodo="C3 2024",
            eval_id=_UUID2,
        )

        candidates = engine._detect(
            {("Prof. García", "ISW-101"): actual},
            {("Prof. García", "ISW-101"): anterior},
            expected_modalidad="CUATRIMESTRAL",
        )
        tipos = {c.tipo_alerta for c in candidates}
        assert tipos == {TipoAlerta.BAJO_DESEMPENO, TipoAlerta.CAIDA}

    def test_duplicating_detector_filtered_by_dedup(self):
        """Detector returning 2 identical candidates → only 1 passes dedup."""
        db = AsyncMock()
        engine = AlertEngine(db, detectors=[_DuplicatingDetector()])

        snap = _snap(puntaje=50.0)
        candidates = engine._detect(
            {("Prof. García", "ISW-101"): snap},
            {},
            expected_modalidad="CUATRIMESTRAL",
        )
        assert len(candidates) == 1
