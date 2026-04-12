"""Critical domain contract tests — business-rule invariants that must never break.

Each test class targets ONE domain guarantee.  If any of these fail,
a business-rule regression has been introduced.  Organised by:

1. Modalidad validation (invariants)
2. Periodo validation & parsing
3. period_order calculation (exhaustive, every valid input)
4. Chronological ordering by (año, period_order)
5. Alert engine: last-two-periods window
6. Alert engine: modalidad isolation
7. Alert engine: dedup key composition
8. Detector threshold boundaries (exact cut-off values)
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, patch

import pytest

from app.modules.evaluacion_docente.application.services.alert_engine import AlertEngine
from app.modules.evaluacion_docente.domain.alert_rules import (
    ALERT_THRESHOLD_HIGH,
    ALERT_THRESHOLD_LOW,
    ALERT_THRESHOLD_MEDIUM,
    DROP_THRESHOLD_HIGH,
    DROP_THRESHOLD_LOW,
    DROP_THRESHOLD_MEDIUM,
    PATTERN_ACTITUD_NEG,
    PATTERN_MEJORA_NEG,
    PATTERN_OTRO,
    SENT_THRESHOLD_HIGH,
    SENT_THRESHOLD_LOW,
    SENT_THRESHOLD_MEDIUM,
    AlertCandidate,
    BajoDesempenoDetector,
    CaidaDetector,
    DocenteCursoSnapshot,
    PatronDetector,
    SentimientoDetector,
)
from app.modules.evaluacion_docente.domain.entities.enums import Modalidad, Severidad, TipoAlerta
from app.modules.evaluacion_docente.domain.exceptions import (
    ModalidadInvalidaError,
    ModalidadRequeridaError,
)
from app.modules.evaluacion_docente.domain.invariants import (
    MODALIDADES_ANALISIS,
    require_modalidad,
    require_modalidad_valid,
    require_periodo_orden,
)
from app.modules.evaluacion_docente.domain.periodo import (
    determinar_modalidad,
    parse_periodo,
    periodo_sort_key,
    sort_periodos,
    validar_periodo,
)
from app.shared.domain.exceptions import ValidationError

_AE_MOD = "app.modules.evaluacion_docente.application.services.alert_engine"

_UUID = uuid.UUID("00000000-0000-0000-0000-000000000001")
_UUID2 = uuid.UUID("00000000-0000-0000-0000-000000000002")


def _snap(
    *,
    periodo: str = "C1 2025",
    eval_id: uuid.UUID = _UUID,
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


# ════════════════════════════════════════════════════════════════════════
#  1. Modalidad validation — completeness
# ════════════════════════════════════════════════════════════════════════


class TestModalidadValidation:
    """require_modalidad must normalise case, reject invalids,
    and match MODALIDADES_ANALISIS exactly."""

    @pytest.mark.parametrize(
        "raw, expected",
        [
            ("cuatrimestral", "CUATRIMESTRAL"),
            ("Cuatrimestral", "CUATRIMESTRAL"),
            ("CUATRIMESTRAL", "CUATRIMESTRAL"),
            ("mensual", "MENSUAL"),
            ("Mensual", "MENSUAL"),
            ("b2b", "B2B"),
            ("B2B", "B2B"),
            ("  CUATRIMESTRAL  ", "CUATRIMESTRAL"),
        ],
    )
    def test_case_insensitive_normalisation(self, raw: str, expected: str):
        assert require_modalidad(raw) == expected

    @pytest.mark.parametrize(
        "invalid",
        [
            "DESCONOCIDA",
            "TRIMESTRAL",
            "SEMESTRAL",
            "ANUAL",
            "cuatrimestral123",
            "  ",
            "B2B_EXTRA",
        ],
    )
    def test_rejects_non_analysis_values(self, invalid: str):
        with pytest.raises(ModalidadInvalidaError):
            require_modalidad(invalid)

    @pytest.mark.parametrize("empty", [None, ""])
    def test_rejects_empty(self, empty):
        with pytest.raises(ModalidadRequeridaError):
            require_modalidad(empty)

    def test_analisis_set_is_exactly_three(self):
        assert MODALIDADES_ANALISIS == {"CUATRIMESTRAL", "MENSUAL", "B2B"}

    def test_require_modalidad_valid_accepts_desconocida(self):
        assert require_modalidad_valid("DESCONOCIDA") == "DESCONOCIDA"

    def test_require_modalidad_valid_rejects_garbage(self):
        with pytest.raises(ValidationError):
            require_modalidad_valid("TRIMESTRAL")


# ════════════════════════════════════════════════════════════════════════
#  2. Periodo validation & parsing
# ════════════════════════════════════════════════════════════════════════


class TestPeriodoValidation:
    """parse_periodo and validar_periodo enforce all structural rules."""

    @pytest.mark.parametrize(
        "raw, expected_modalidad",
        [
            ("C1 2025", Modalidad.CUATRIMESTRAL),
            ("C2 2025", Modalidad.CUATRIMESTRAL),
            ("C3 2025", Modalidad.CUATRIMESTRAL),
            ("M1 2025", Modalidad.MENSUAL),
            ("M10 2025", Modalidad.MENSUAL),
            ("MT1 2025", Modalidad.MENSUAL),
            ("MT10 2025", Modalidad.MENSUAL),
            ("B2B-EMPRESA-2025", Modalidad.B2B),
        ],
    )
    def test_parse_valid_assigns_correct_modalidad(self, raw, expected_modalidad):
        info = parse_periodo(raw)
        assert info.modalidad == expected_modalidad

    @pytest.mark.parametrize(
        "invalid",
        [
            "C0 2025",
            "C4 2025",
            "M0 2025",
            "M11 2025",
            "MT0 2025",
            "MT11 2025",
            "X1 2025",
            "2025",
            "",
        ],
    )
    def test_parse_rejects_invalid_format(self, invalid):
        with pytest.raises(ValidationError):
            parse_periodo(invalid)

    def test_year_below_2020_rejected(self):
        with pytest.raises(ValidationError, match="fuera de rango"):
            parse_periodo("C1 2019")

    def test_year_above_2100_rejected(self):
        with pytest.raises(ValidationError, match="fuera de rango"):
            parse_periodo("C1 2101")

    def test_year_boundary_2020_accepted(self):
        assert parse_periodo("C1 2020").año == 2020

    def test_year_boundary_2100_accepted(self):
        assert parse_periodo("C1 2100").año == 2100

    def test_validar_rejects_cross_modalidad_code(self):
        """M1 code with CUATRIMESTRAL modalidad must raise."""
        with pytest.raises(ValidationError):
            validar_periodo("M1", 2025, Modalidad.CUATRIMESTRAL)

    def test_validar_rejects_desconocida_modalidad(self):
        with pytest.raises(ValidationError, match="DESCONOCIDA"):
            validar_periodo("C1", 2025, Modalidad.DESCONOCIDA)

    def test_parse_and_validar_produce_identical_output(self):
        parsed = parse_periodo("C2 2025")
        validated = validar_periodo("C2", 2025, Modalidad.CUATRIMESTRAL)
        assert parsed == validated


# ════════════════════════════════════════════════════════════════════════
#  3. period_order calculation — EXHAUSTIVE
# ════════════════════════════════════════════════════════════════════════


class TestPeriodOrderCalculation:
    """Every valid periodo string must produce the correct periodo_orden."""

    # ── Cuatrimestral: C1=1, C2=2, C3=3 ─────────────────────────────

    @pytest.mark.parametrize(
        "code, expected_orden",
        [
            ("C1", 1),
            ("C2", 2),
            ("C3", 3),
        ],
    )
    def test_cuatrimestral_periodo_orden(self, code, expected_orden):
        info = validar_periodo(code, 2025, Modalidad.CUATRIMESTRAL)
        assert info.periodo_orden == expected_orden

    # ── Mensual M: M1..M10 → orden 1..10 ────────────────────────────

    @pytest.mark.parametrize("n", range(1, 11))
    def test_mensual_m_periodo_orden(self, n):
        info = validar_periodo(f"M{n}", 2025, Modalidad.MENSUAL)
        assert info.periodo_orden == n

    # ── Mensual MT: MT1..MT10 → orden 1..10 ─────────────────────────

    @pytest.mark.parametrize("n", range(1, 11))
    def test_mensual_mt_periodo_orden(self, n):
        info = validar_periodo(f"MT{n}", 2025, Modalidad.MENSUAL)
        assert info.periodo_orden == n

    # ── B2B: always 0 ────────────────────────────────────────────────

    def test_b2b_periodo_orden_is_zero(self):
        info = validar_periodo("B2B-EMPRESA-2025", 2025, Modalidad.B2B)
        assert info.periodo_orden == 0

    # ── parse_periodo consistency ────────────────────────────────────

    @pytest.mark.parametrize(
        "raw, expected_orden",
        [
            ("C1 2025", 1),
            ("C2 2025", 2),
            ("C3 2025", 3),
            ("M1 2025", 1),
            ("M5 2025", 5),
            ("M10 2025", 10),
            ("MT1 2025", 1),
            ("MT5 2025", 5),
            ("MT10 2025", 10),
        ],
    )
    def test_parse_periodo_orden_matches_validar(self, raw, expected_orden):
        assert parse_periodo(raw).periodo_orden == expected_orden

    # ── require_periodo_orden enforcement ────────────────────────────

    @pytest.mark.parametrize(
        "orden, mod",
        [
            (0, "CUATRIMESTRAL"),
            (4, "CUATRIMESTRAL"),
            (0, "MENSUAL"),
            (11, "MENSUAL"),
            (1, "B2B"),
        ],
    )
    def test_require_rejects_out_of_range(self, orden, mod):
        with pytest.raises(ValidationError):
            require_periodo_orden(orden, mod)

    @pytest.mark.parametrize(
        "orden, mod",
        [
            (1, "CUATRIMESTRAL"),
            (3, "CUATRIMESTRAL"),
            (1, "MENSUAL"),
            (10, "MENSUAL"),
            (0, "B2B"),
        ],
    )
    def test_require_accepts_boundary_values(self, orden, mod):
        assert require_periodo_orden(orden, mod) == orden


# ════════════════════════════════════════════════════════════════════════
#  4. Chronological ordering by (año, prefijo, numero)
# ════════════════════════════════════════════════════════════════════════


class TestChronologicalOrdering:
    """Periods must sort by year first, then prefix, then number."""

    def test_same_year_cuatrimestral_ascending(self):
        periods = ["C3 2025", "C1 2025", "C2 2025"]
        infos = sorted([parse_periodo(p) for p in periods], key=periodo_sort_key)
        assert [i.periodo_normalizado for i in infos] == [
            "C1 2025",
            "C2 2025",
            "C3 2025",
        ]

    def test_cross_year_cuatrimestral(self):
        """C3 2024 < C1 2025 — year takes precedence."""
        periods = ["C1 2025", "C3 2024"]
        infos = sorted([parse_periodo(p) for p in periods], key=periodo_sort_key)
        assert infos[0].año == 2024
        assert infos[1].año == 2025

    def test_cross_year_mensual(self):
        """M10 2025 < M1 2026."""
        periods = ["M1 2026", "M10 2025"]
        infos = sorted([parse_periodo(p) for p in periods], key=periodo_sort_key)
        assert infos[0].periodo_normalizado == "M10 2025"
        assert infos[1].periodo_normalizado == "M1 2026"

    def test_mixed_years_full_sequence(self):
        """Full chronological sequence across multiple years."""
        periods = [
            "C1 2026",
            "C3 2024",
            "C2 2025",
            "C1 2024",
            "C1 2025",
            "C3 2025",
        ]
        infos = sorted([parse_periodo(p) for p in periods], key=periodo_sort_key)
        assert [i.periodo_normalizado for i in infos] == [
            "C1 2024",
            "C3 2024",
            "C1 2025",
            "C2 2025",
            "C3 2025",
            "C1 2026",
        ]

    def test_mensual_full_year_sequence(self):
        """M1..M10 within a year sorts correctly (numeric not lexicographic)."""
        periods = [f"M{n} 2025" for n in [10, 1, 5, 3, 9, 2, 7, 4, 8, 6]]
        infos = sorted([parse_periodo(p) for p in periods], key=periodo_sort_key)
        assert [i.numero for i in infos] == list(range(1, 11))

    def test_sort_periodos_with_dicts(self):
        """sort_periodos sorts list[dict] correctly."""
        rows = [
            {"periodo": "C2 2025", "value": 2},
            {"periodo": "C3 2024", "value": 1},
            {"periodo": "C1 2025", "value": 3},
        ]
        ordered = sort_periodos(rows)
        assert [r["periodo"] for r in ordered] == [
            "C3 2024",
            "C1 2025",
            "C2 2025",
        ]

    def test_sort_periodos_unparseable_sorts_last(self):
        """Unparseable values are pushed to the end."""
        rows = [
            {"periodo": "UNKNOWN"},
            {"periodo": "C1 2025"},
            {"periodo": "C3 2024"},
        ]
        ordered = sort_periodos(rows)
        assert ordered[-1]["periodo"] == "UNKNOWN"
        assert ordered[0]["periodo"] == "C3 2024"


# ════════════════════════════════════════════════════════════════════════
#  5. Alert engine: last-two-periods window
# ════════════════════════════════════════════════════════════════════════


class TestAlertLastTwoPeriodsWindow:
    """Alert engine must use at most 2 consecutive periods."""

    async def test_two_periods_both_used(self):
        """With 2 periods, engine uses index 0 as actual, index 1 as anterior."""
        mock_db = AsyncMock()
        with patch(f"{_AE_MOD}.AlertaRepository") as cls:
            repo = cls.return_value
            repo.find_last_two_periods = AsyncMock(return_value=["C2 2025", "C1 2025"])
            repo.load_snapshots = AsyncMock(
                return_value={
                    "C2 2025": {("D", "C"): _snap(periodo="C2 2025", puntaje=55.0)},
                    "C1 2025": {("D", "C"): _snap(periodo="C1 2025", puntaje=90.0, eval_id=_UUID2)},
                }
            )
            repo.upsert_batch = AsyncMock(return_value=2)

            engine = AlertEngine(mock_db, detectors=[BajoDesempenoDetector(), CaidaDetector()])
            result = await engine.run_for_modalidad("CUATRIMESTRAL")

            # bajo (55 < 60) + caída (90→55 = 35pt drop)
            assert result.candidates_generated == 2
            candidates = repo.upsert_batch.call_args[0][0]
            tipos = {c.tipo_alerta for c in candidates}
            assert TipoAlerta.BAJO_DESEMPENO in tipos
            assert TipoAlerta.CAIDA in tipos

    async def test_single_period_only_absolute_alerts(self):
        """With 1 period, only absolute detectors fire (no anterior)."""
        mock_db = AsyncMock()
        with patch(f"{_AE_MOD}.AlertaRepository") as cls:
            repo = cls.return_value
            repo.find_last_two_periods = AsyncMock(return_value=["C1 2025"])
            repo.load_snapshots = AsyncMock(
                return_value={
                    "C1 2025": {("D", "C"): _snap(periodo="C1 2025", puntaje=50.0)},
                }
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
            result = await engine.run_for_modalidad("CUATRIMESTRAL")

            assert result.candidates_generated == 1
            candidates = repo.upsert_batch.call_args[0][0]
            assert all(c.tipo_alerta == TipoAlerta.BAJO_DESEMPENO for c in candidates)

    async def test_zero_periods_no_processing(self):
        """No periods → no processing, no upsert."""
        mock_db = AsyncMock()
        with patch(f"{_AE_MOD}.AlertaRepository") as cls:
            repo = cls.return_value
            repo.find_last_two_periods = AsyncMock(return_value=[])

            engine = AlertEngine(mock_db, detectors=[BajoDesempenoDetector()])
            result = await engine.run_for_modalidad("CUATRIMESTRAL")

            assert result.modalidades_processed == 0
            assert result.candidates_generated == 0
            repo.load_snapshots.assert_not_called()
            repo.upsert_batch.assert_not_called()

    async def test_three_periods_engine_receives_all_but_uses_window(self):
        """Even if repo returns 3 periods, engine pairs idx 0 (actual) vs idx 1 (anterior)."""
        mock_db = AsyncMock()
        with patch(f"{_AE_MOD}.AlertaRepository") as cls:
            repo = cls.return_value
            repo.find_last_two_periods = AsyncMock(return_value=["C3 2025", "C2 2025", "C1 2025"])
            repo.load_snapshots = AsyncMock(
                return_value={
                    "C3 2025": {("D", "C"): _snap(periodo="C3 2025", puntaje=50.0)},
                    "C2 2025": {("D", "C"): _snap(periodo="C2 2025", puntaje=90.0, eval_id=_UUID2)},
                    "C1 2025": {
                        ("D", "C"): _snap(
                            periodo="C1 2025",
                            puntaje=95.0,
                            eval_id=uuid.UUID("00000000-0000-0000-0000-000000000003"),
                        )
                    },
                }
            )
            repo.upsert_batch = AsyncMock(return_value=2)

            engine = AlertEngine(mock_db, detectors=[CaidaDetector()])
            await engine.run_for_modalidad("CUATRIMESTRAL")

            # Caída compares C3 2025 (50) vs C2 2025 (90) = 40pt drop
            candidates = repo.upsert_batch.call_args[0][0]
            assert len(candidates) == 1
            assert candidates[0].periodo == "C3 2025"
            assert candidates[0].valor_anterior == 90.0  # from C2, not C1


# ════════════════════════════════════════════════════════════════════════
#  6. Alert engine: modalidad isolation
# ════════════════════════════════════════════════════════════════════════


class TestAlertModalidadIsolation:
    """Each modalidad must be processed independently — no data leaks."""

    async def test_run_all_processes_each_independently(self):
        """run_all calls run_for_modalidad once per alertable modalidad."""
        mock_db = AsyncMock()
        with patch(f"{_AE_MOD}.AlertaRepository") as cls:
            repo = cls.return_value
            calls: list[str] = []

            async def track(mod):
                calls.append(mod)
                return ["C1 2025"] if mod == "CUATRIMESTRAL" else []

            repo.find_last_two_periods = AsyncMock(side_effect=track)
            repo.load_snapshots = AsyncMock(
                return_value={
                    "C1 2025": {("D", "C"): _snap(puntaje=50.0)},
                }
            )
            repo.upsert_batch = AsyncMock(return_value=1)

            engine = AlertEngine(mock_db, detectors=[BajoDesempenoDetector()])
            await engine.run_all()

            assert set(calls) == {"B2B", "CUATRIMESTRAL", "MENSUAL"}

    def test_cross_modalidad_candidate_filtered(self):
        """Detector emitting wrong modalidad → filtered by _detect guard."""

        class _WrongMod:
            tipo = TipoAlerta.BAJO_DESEMPENO

            def detect(self, actual, anterior=None):
                return [
                    AlertCandidate(
                        evaluacion_id=actual.evaluacion_id,
                        docente_nombre=actual.docente_nombre,
                        curso=actual.curso,
                        periodo=actual.periodo,
                        modalidad="MENSUAL",  # wrong
                        tipo_alerta=self.tipo,
                        metrica_afectada="puntaje_general",
                        valor_actual=50.0,
                        valor_anterior=None,
                        descripcion="wrong",
                        severidad=Severidad.ALTA,
                    )
                ]

        db = AsyncMock()
        engine = AlertEngine(db, detectors=[_WrongMod()])
        snap = _snap(modalidad="CUATRIMESTRAL", puntaje=50.0)
        candidates = engine._detect(
            {("D", "C"): snap},
            {},
            expected_modalidad="CUATRIMESTRAL",
        )
        assert candidates == []

    def test_correct_modalidad_candidate_passes(self):
        """Detector emitting correct modalidad → passes guard."""
        db = AsyncMock()
        engine = AlertEngine(db, detectors=[BajoDesempenoDetector()])
        snap = _snap(modalidad="CUATRIMESTRAL", puntaje=50.0)
        candidates = engine._detect(
            {("D", "C"): snap},
            {},
            expected_modalidad="CUATRIMESTRAL",
        )
        assert len(candidates) == 1
        assert candidates[0].modalidad == "CUATRIMESTRAL"

    def test_same_docente_different_modalidades_are_independent(self):
        """Same docente in two modalidades → two independent alerts."""
        db = AsyncMock()
        engine = AlertEngine(db, detectors=[BajoDesempenoDetector()])

        cuatri = _snap(modalidad="CUATRIMESTRAL", periodo="C1 2025", puntaje=50.0)
        mensual = _snap(modalidad="MENSUAL", periodo="M1 2025", puntaje=50.0)

        c1 = engine._detect(
            {("Prof. García", "ISW-101"): cuatri},
            {},
            expected_modalidad="CUATRIMESTRAL",
        )
        c2 = engine._detect(
            {("Prof. García", "ISW-101"): mensual},
            {},
            expected_modalidad="MENSUAL",
        )
        assert len(c1) == 1 and c1[0].modalidad == "CUATRIMESTRAL"
        assert len(c2) == 1 and c2[0].modalidad == "MENSUAL"

    async def test_desconocida_rejected_by_engine(self):
        db = AsyncMock()
        engine = AlertEngine(db, detectors=[])
        with pytest.raises(ModalidadInvalidaError):
            await engine.run_for_modalidad("DESCONOCIDA")


# ════════════════════════════════════════════════════════════════════════
#  7. Alert dedup key composition
# ════════════════════════════════════════════════════════════════════════


class TestAlertDedupKeyComposition:
    """Dedup key = (docente, curso, periodo, tipo_alerta, modalidad).
    All 5 components matter; differing in any → not a duplicate."""

    def _run(self, engine, snap_actual, snap_anterior=None, expected_mod="CUATRIMESTRAL"):
        return engine._detect(
            snap_actual,
            snap_anterior or {},
            expected_modalidad=expected_mod,
        )

    def test_identical_key_deduped(self):
        """Two identical candidates → only 1 survives."""

        class _Double:
            tipo = TipoAlerta.BAJO_DESEMPENO

            def detect(self, actual, anterior=None):
                c = AlertCandidate(
                    evaluacion_id=actual.evaluacion_id,
                    docente_nombre=actual.docente_nombre,
                    curso=actual.curso,
                    periodo=actual.periodo,
                    modalidad=actual.modalidad,
                    tipo_alerta=self.tipo,
                    metrica_afectada="puntaje_general",
                    valor_actual=50.0,
                    valor_anterior=None,
                    descripcion="dup",
                    severidad=Severidad.ALTA,
                )
                return [c, c]

        db = AsyncMock()
        engine = AlertEngine(db, detectors=[_Double()])
        snap = _snap(puntaje=50.0)
        assert len(self._run(engine, {("D", "C"): snap})) == 1

    def test_different_tipo_alerta_not_deduped(self):
        """BAJO_DESEMPEÑO + CAIDA for same docente+curso+periodo → 2 alerts."""
        db = AsyncMock()
        engine = AlertEngine(db, detectors=[BajoDesempenoDetector(), CaidaDetector()])

        actual = _snap(puntaje=50.0, periodo="C1 2025")
        anterior = _snap(puntaje=90.0, periodo="C3 2024", eval_id=_UUID2)

        candidates = self._run(
            engine,
            {("D", "C"): actual},
            {("D", "C"): anterior},
        )
        tipos = {c.tipo_alerta for c in candidates}
        assert tipos == {TipoAlerta.BAJO_DESEMPENO, TipoAlerta.CAIDA}

    def test_different_curso_not_deduped(self):
        """Same docente, different cursos → separate alerts."""
        db = AsyncMock()
        engine = AlertEngine(db, detectors=[BajoDesempenoDetector()])

        snap_actual = {
            ("D", "ISW-101"): _snap(curso="ISW-101", puntaje=50.0),
            ("D", "ISW-202"): _snap(curso="ISW-202", puntaje=55.0),
        }
        candidates = self._run(engine, snap_actual)
        assert len(candidates) == 2
        assert {c.curso for c in candidates} == {"ISW-101", "ISW-202"}

    def test_different_periodo_not_deduped(self):
        """Same docente+curso but different periodos → not duplicates."""
        db = AsyncMock()
        engine = AlertEngine(db, detectors=[BajoDesempenoDetector()])

        snap1 = _snap(periodo="C1 2025", puntaje=50.0)
        snap2 = _snap(periodo="C2 2025", puntaje=55.0)

        c1 = self._run(engine, {("D", "C"): snap1})
        c2 = self._run(engine, {("D", "C"): snap2})
        assert len(c1) == 1 and c1[0].periodo == "C1 2025"
        assert len(c2) == 1 and c2[0].periodo == "C2 2025"

    def test_rerun_idempotent(self):
        """Running _detect twice with same data → identical output."""
        db = AsyncMock()
        engine = AlertEngine(db, detectors=[BajoDesempenoDetector(), CaidaDetector()])

        actual = _snap(puntaje=55.0, periodo="C1 2025")
        anterior = _snap(puntaje=90.0, periodo="C3 2024", eval_id=_UUID2)
        snaps_a = {("D", "C"): actual}
        snaps_p = {("D", "C"): anterior}

        run1 = self._run(engine, snaps_a, snaps_p)
        run2 = self._run(engine, snaps_a, snaps_p)

        assert len(run1) == len(run2)
        for c1, c2 in zip(run1, run2):
            assert (c1.docente_nombre, c1.curso, c1.periodo, c1.tipo_alerta, c1.modalidad) == (
                c2.docente_nombre,
                c2.curso,
                c2.periodo,
                c2.tipo_alerta,
                c2.modalidad,
            )


# ════════════════════════════════════════════════════════════════════════
#  8. Detector threshold boundaries
# ════════════════════════════════════════════════════════════════════════


class TestBajoDesempenoThresholds:
    """[AL-20] Exact boundary values for BajoDesempeño detector."""

    det = BajoDesempenoDetector()

    def _detect(self, puntaje):
        snap = _snap(puntaje=puntaje)
        return self.det.detect(snap, None)

    # ── Threshold values ─────────────────────────────────────────────

    def test_threshold_constants(self):
        assert ALERT_THRESHOLD_HIGH == 60.0
        assert ALERT_THRESHOLD_MEDIUM == 70.0
        assert ALERT_THRESHOLD_LOW == 80.0

    # ── Below HIGH → alta ────────────────────────────────────────────

    def test_below_high_is_alta(self):
        alerts = self._detect(59.99)
        assert len(alerts) == 1 and alerts[0].severidad == Severidad.ALTA

    def test_at_high_is_media(self):
        """Exactly 60.0 → NOT alta (< 60 is alta, >= 60 is next tier)."""
        alerts = self._detect(60.0)
        assert len(alerts) == 1 and alerts[0].severidad == Severidad.MEDIA

    # ── HIGH to MEDIUM → media ───────────────────────────────────────

    def test_between_high_and_medium_is_media(self):
        alerts = self._detect(65.0)
        assert len(alerts) == 1 and alerts[0].severidad == Severidad.MEDIA

    def test_at_medium_is_baja(self):
        """Exactly 70.0 → baja (not media)."""
        alerts = self._detect(70.0)
        assert len(alerts) == 1 and alerts[0].severidad == Severidad.BAJA

    # ── MEDIUM to LOW → baja ─────────────────────────────────────────

    def test_between_medium_and_low_is_baja(self):
        alerts = self._detect(75.0)
        assert len(alerts) == 1 and alerts[0].severidad == Severidad.BAJA

    def test_at_low_no_alert(self):
        """Exactly 80.0 → no alert (only < 80 triggers)."""
        assert self._detect(80.0) == []

    def test_above_low_no_alert(self):
        assert self._detect(90.0) == []

    def test_none_puntaje_no_alert(self):
        assert self._detect(None) == []


class TestCaidaThresholds:
    """[AL-21] Exact boundary values for Caída detector."""

    det = CaidaDetector()

    def _detect(self, actual_puntaje, anterior_puntaje):
        actual = _snap(puntaje=actual_puntaje, periodo="C1 2025")
        anterior = _snap(puntaje=anterior_puntaje, periodo="C3 2024", eval_id=_UUID2)
        return self.det.detect(actual, anterior)

    def test_threshold_constants(self):
        assert DROP_THRESHOLD_HIGH == 15.0
        assert DROP_THRESHOLD_MEDIUM == 10.0
        assert DROP_THRESHOLD_LOW == 5.0

    def test_no_drop_no_alert(self):
        """No drop (actual >= anterior) → no alert."""
        assert self._detect(90.0, 85.0) == []

    def test_equal_no_alert(self):
        assert self._detect(80.0, 80.0) == []

    def test_drop_below_low_no_alert(self):
        """Drop of exactly 5.0 → no alert (threshold is > 5, not >=)."""
        assert self._detect(85.0, 90.0) == []

    def test_drop_above_low_is_baja(self):
        """Drop of 5.01 → baja."""
        alerts = self._detect(84.99, 90.0)
        assert len(alerts) == 1 and alerts[0].severidad == Severidad.BAJA

    def test_drop_above_medium_is_media(self):
        """Drop of 10.01 → media."""
        alerts = self._detect(79.99, 90.0)
        assert len(alerts) == 1 and alerts[0].severidad == Severidad.MEDIA

    def test_drop_above_high_is_alta(self):
        """Drop of 15.01 → alta."""
        alerts = self._detect(74.99, 90.0)
        assert len(alerts) == 1 and alerts[0].severidad == Severidad.ALTA

    def test_drop_exactly_high_is_media(self):
        """Drop of exactly 15.0 → media (threshold is > 15, not >=)."""
        alerts = self._detect(75.0, 90.0)
        assert len(alerts) == 1 and alerts[0].severidad == Severidad.MEDIA

    def test_no_anterior_no_alert(self):
        actual = _snap(puntaje=50.0)
        assert self.det.detect(actual, None) == []


class TestSentimientoThresholds:
    """[AL-22] Exact boundary values for Sentimiento detector."""

    det = SentimientoDetector()

    def _detect(self, actual_neg_pct, anterior_neg_pct, total=100):
        actual_neg = int(actual_neg_pct)
        anterior_neg = int(anterior_neg_pct)
        actual = _snap(
            total=total,
            negativos=actual_neg,
            periodo="C1 2025",
        )
        anterior = _snap(
            total=total,
            negativos=anterior_neg,
            periodo="C3 2024",
            eval_id=_UUID2,
        )
        return self.det.detect(actual, anterior)

    def test_threshold_constants(self):
        assert SENT_THRESHOLD_HIGH == 20.0
        assert SENT_THRESHOLD_MEDIUM == 10.0
        assert SENT_THRESHOLD_LOW == 5.0

    def test_no_increase_no_alert(self):
        assert self._detect(10, 10) == []

    def test_decrease_no_alert(self):
        assert self._detect(5, 10) == []

    def test_increase_below_low_no_alert(self):
        """5% increment → no alert (> 5, not >=)."""
        assert self._detect(10, 5) == []

    def test_increase_above_low_is_baja(self):
        """6% increment → baja."""
        alerts = self._detect(11, 5)
        assert len(alerts) == 1 and alerts[0].severidad == Severidad.BAJA

    def test_increase_above_medium_is_media(self):
        """11% increment → media."""
        alerts = self._detect(16, 5)
        assert len(alerts) == 1 and alerts[0].severidad == Severidad.MEDIA

    def test_increase_above_high_is_alta(self):
        """21% increment → alta."""
        alerts = self._detect(26, 5)
        assert len(alerts) == 1 and alerts[0].severidad == Severidad.ALTA

    def test_zero_total_no_alert(self):
        actual = _snap(total=0, negativos=0)
        anterior = _snap(total=0, negativos=0, eval_id=_UUID2)
        assert self.det.detect(actual, anterior) == []


class TestPatronThresholds:
    """[AL-23] Exact boundary values for Patrón detector."""

    det = PatronDetector()

    def test_threshold_constants(self):
        assert PATTERN_MEJORA_NEG == 0.50
        assert PATTERN_ACTITUD_NEG == 0.30
        assert PATTERN_OTRO == 0.40

    def test_mejora_neg_above_50pct_is_alta(self):
        snap = _snap(total=100, mejora_neg=51)
        alerts = self.det.detect(snap, None)
        assert len(alerts) == 1 and alerts[0].severidad == Severidad.ALTA

    def test_mejora_neg_at_50pct_no_alert(self):
        """Exactly 50% → no alert (threshold is >, not >=)."""
        snap = _snap(total=100, mejora_neg=50)
        assert self.det.detect(snap, None) == []

    def test_actitud_neg_above_30pct_is_media(self):
        snap = _snap(total=100, actitud_neg=31, mejora_neg=0)
        alerts = self.det.detect(snap, None)
        assert len(alerts) == 1 and alerts[0].severidad == Severidad.MEDIA

    def test_actitud_neg_at_30pct_no_alert(self):
        snap = _snap(total=100, actitud_neg=30, mejora_neg=0)
        assert self.det.detect(snap, None) == []

    def test_otro_above_40pct_is_baja(self):
        snap = _snap(total=100, otro=41, mejora_neg=0, actitud_neg=0)
        alerts = self.det.detect(snap, None)
        assert len(alerts) == 1 and alerts[0].severidad == Severidad.BAJA

    def test_otro_at_40pct_no_alert(self):
        snap = _snap(total=100, otro=40, mejora_neg=0, actitud_neg=0)
        assert self.det.detect(snap, None) == []

    def test_mejora_neg_takes_priority_over_actitud(self):
        """When both ratios exceed thresholds, mejora_neg (alta) wins."""
        snap = _snap(total=100, mejora_neg=55, actitud_neg=35)
        alerts = self.det.detect(snap, None)
        assert len(alerts) == 1
        assert alerts[0].severidad == Severidad.ALTA
        assert "mejora" in alerts[0].descripcion.lower()

    def test_zero_total_no_alert(self):
        snap = _snap(total=0)
        assert self.det.detect(snap, None) == []


# ════════════════════════════════════════════════════════════════════════
#  9. determinar_modalidad ↔ parse_periodo consistency
# ════════════════════════════════════════════════════════════════════════


class TestModalidadInferenceConsistency:
    """determinar_modalidad must agree with parse_periodo."""

    @pytest.mark.parametrize(
        "raw",
        [
            "C1 2025",
            "C2 2024",
            "C3 2025",
            "M1 2025",
            "M5 2025",
            "M10 2025",
            "MT1 2025",
            "MT5 2025",
            "MT10 2025",
        ],
    )
    def test_determinar_matches_parse(self, raw):
        inferred = determinar_modalidad(raw)
        parsed = parse_periodo(raw)
        assert inferred == parsed.modalidad

    @pytest.mark.parametrize("raw", ["B2B-EMPRESA-2025", "B2B MICROSOFT 2026"])
    def test_b2b_matches(self, raw):
        assert determinar_modalidad(raw) == Modalidad.B2B
        assert parse_periodo(raw).modalidad == Modalidad.B2B

    @pytest.mark.parametrize("raw", ["C4 2025", "M11 2025", "X1 2025"])
    def test_desconocida_and_parse_raises(self, raw):
        assert determinar_modalidad(raw) == Modalidad.DESCONOCIDA
        with pytest.raises(ValidationError):
            parse_periodo(raw)
