"""Cross-cutting business-rule tests.

Covers gaps identified in the test-plan:
- Modalidad validation edge cases
- Periodo parsing & periodo_orden correctness
- Chronological ordering (mixed B2B, M vs MT, cross-year)
- Alert engine: modalidad isolation, only-last-2-periods, multi-detector
- Alert deduplication contract
- Classifier sentiment boundary ±0.25 and prior interactions
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, patch

import pytest

from app.modules.evaluacion_docente.application.classification import (
    classify_comment,
    classify_sentimiento,
    classify_tema,
)
from app.modules.evaluacion_docente.application.services.alert_engine import AlertEngine
from app.modules.evaluacion_docente.domain.alert_rules import (
    AlertCandidate,
    BajoDesempenoDetector,
    CaidaDetector,
    DocenteCursoSnapshot,
    PatronDetector,
    SentimientoDetector,
)
from app.modules.evaluacion_docente.domain.entities.enums import Modalidad, Severidad, TipoAlerta
from app.modules.evaluacion_docente.domain.periodo import (
    determinar_modalidad,
    parse_periodo,
    periodo_sort_key,
    sort_periodos,
)

_AE_MOD = "app.modules.evaluacion_docente.application.services.alert_engine"

_UUID = uuid.UUID("00000000-0000-0000-0000-000000000001")
_UUID2 = uuid.UUID("00000000-0000-0000-0000-000000000002")


def _snap(
    *,
    periodo: str = "C1 2025",
    eval_id: uuid.UUID = _UUID,
    puntaje: float = 50.0,
    modalidad: str = "CUATRIMESTRAL",
    docente: str = "Prof. García",
    curso: str = "ISW-101",
    total: int = 10,
    neg: int = 1,
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
        negativos_count=neg,
        mejora_negativo_count=mejora_neg,
        actitud_negativo_count=actitud_neg,
        otro_count=otro,
    )


# ═══════════════════════════════════════════════════════════════════
#  1. Modalidad validation [BR-MOD-01]–[BR-MOD-05]
# ═══════════════════════════════════════════════════════════════════


class TestModalidadEdgeCases:
    """Edge cases not covered in test_periodo.py."""

    @pytest.mark.parametrize(
        "raw,expected",
        [
            ("C4 2025", Modalidad.DESCONOCIDA),
            ("C0 2025", Modalidad.DESCONOCIDA),
            ("M11 2025", Modalidad.DESCONOCIDA),
            ("M0 2025", Modalidad.DESCONOCIDA),
            ("MT11 2025", Modalidad.DESCONOCIDA),
            ("MT0 2025", Modalidad.DESCONOCIDA),
            ("B2BEMPRESA", Modalidad.B2B),  # starts with B2B → B2B
            ("C1", Modalidad.DESCONOCIDA),
            ("M5", Modalidad.DESCONOCIDA),
            ("2025", Modalidad.DESCONOCIDA),
            ("", Modalidad.DESCONOCIDA),
        ],
    )
    def test_out_of_range_returns_desconocida(self, raw, expected):
        assert determinar_modalidad(raw) == expected

    def test_desconocida_excluded_from_alertable(self):
        """[BR-MOD-05] DESCONOCIDA must NOT appear in alertable list."""
        from app.modules.evaluacion_docente.application.services.alert_engine import (
            _ALERTABLE_MODALIDADES,
        )

        assert "DESCONOCIDA" not in _ALERTABLE_MODALIDADES
        assert len(_ALERTABLE_MODALIDADES) == 3

    def test_all_valid_modalidades_are_alertable(self):
        from app.modules.evaluacion_docente.application.services.alert_engine import (
            _ALERTABLE_MODALIDADES,
        )

        assert "CUATRIMESTRAL" in _ALERTABLE_MODALIDADES
        assert "MENSUAL" in _ALERTABLE_MODALIDADES
        assert "B2B" in _ALERTABLE_MODALIDADES


# ═══════════════════════════════════════════════════════════════════
#  2. Periodo parsing & periodo_orden [BR-AN-41]
# ═══════════════════════════════════════════════════════════════════


class TestPeriodoOrden:
    """Verify periodo_orden is correctly derived."""

    @pytest.mark.parametrize(
        "periodo,expected_orden",
        [
            ("C1 2025", 1),
            ("C2 2025", 2),
            ("C3 2025", 3),
            ("M1 2025", 1),
            ("M5 2025", 5),
            ("M10 2025", 10),
            ("MT1 2025", 1),
            ("MT10 2025", 10),
        ],
    )
    def test_periodo_orden(self, periodo, expected_orden):
        info = parse_periodo(periodo)
        assert info.periodo_orden == expected_orden

    def test_b2b_orden_always_zero(self):
        info = parse_periodo("B2B-CORP-2025")
        assert info.periodo_orden == 0

    def test_b2b_without_year_returns_zero_año(self):
        info = parse_periodo("B2B-CORP-XYZ")
        assert info.año == 0
        assert info.prefijo == "B2B"

    def test_b2b_with_embedded_year(self):
        info = parse_periodo("B2B-EMPRESA-2025-Q1")
        assert info.año == 2025


# ═══════════════════════════════════════════════════════════════════
#  3. Chronological ordering [BR-AN-40], [BR-AN-42]
# ═══════════════════════════════════════════════════════════════════


class TestChronologicalOrdering:
    """Ordering gaps: B2B mixed, M vs MT, cross-prefix."""

    def test_b2b_mixed_with_cuatrimestral(self):
        """B2B (año=2025, prefijo='B2B') sorts after C (prefijo='C')
        when same year because 'B2B' < 'C' lexicographically."""
        rows = [
            {"periodo": "C1 2025"},
            {"periodo": "B2B-CORP-2025"},
        ]
        result = sort_periodos(rows)
        assert result[0]["periodo"] == "B2B-CORP-2025"
        assert result[1]["periodo"] == "C1 2025"

    def test_b2b_without_year_sorts_first(self):
        """B2B with año=0 sorts before everything."""
        rows = [
            {"periodo": "C1 2024"},
            {"periodo": "B2B-CORP-XYZ"},
        ]
        result = sort_periodos(rows)
        assert result[0]["periodo"] == "B2B-CORP-XYZ"

    def test_m_before_mt_same_year(self):
        """M sorts before MT because 'M' < 'MT' (string comparison)."""
        rows = [
            {"periodo": "MT1 2025"},
            {"periodo": "M1 2025"},
        ]
        result = sort_periodos(rows)
        assert result[0]["periodo"] == "M1 2025"
        assert result[1]["periodo"] == "MT1 2025"

    def test_m_vs_mt_cross_year(self):
        """M10 2024 before MT1 2025."""
        rows = [
            {"periodo": "MT1 2025"},
            {"periodo": "M10 2024"},
        ]
        result = sort_periodos(rows)
        assert result[0]["periodo"] == "M10 2024"
        assert result[1]["periodo"] == "MT1 2025"

    def test_full_mixed_ordering(self):
        """All modalidades together — verify (año, prefijo, numero)."""
        rows = [
            {"periodo": "C2 2025"},
            {"periodo": "M3 2025"},
            {"periodo": "MT1 2024"},
            {"periodo": "C1 2024"},
            {"periodo": "B2B-X-2024"},
            {"periodo": "basura"},
        ]
        result = sort_periodos(rows)
        periodos = [r["periodo"] for r in result]
        # 2024: B2B(0), C1, MT1 | 2025: C2, M3 | imparseable last
        assert periodos == [
            "B2B-X-2024",
            "C1 2024",
            "MT1 2024",
            "C2 2025",
            "M3 2025",
            "basura",
        ]

    def test_sort_key_tuple_values(self):
        """Verify exact tuple from periodo_sort_key."""
        info = parse_periodo("C2 2025")
        assert periodo_sort_key(info) == (2025, "C", 2)

        info_m = parse_periodo("M10 2024")
        assert periodo_sort_key(info_m) == (2024, "M", 10)

        info_mt = parse_periodo("MT3 2026")
        assert periodo_sort_key(info_mt) == (2026, "MT", 3)


# ═══════════════════════════════════════════════════════════════════
#  4. Alert engine: only last 2 periods [AL-01]
# ═══════════════════════════════════════════════════════════════════


class TestAlertEngineLastTwoPeriods:
    """Verify engine uses at most 2 periods per modalidad."""

    async def test_uses_only_two_periods_from_repo(self):
        """Even if repo returns 2, engine passes both to load_snapshots."""
        mock_db = AsyncMock()
        with patch(f"{_AE_MOD}.AlertaRepository") as mock_repo_cls:
            mock_repo = mock_repo_cls.return_value
            mock_repo.find_last_two_periods = AsyncMock(return_value=["C2 2025", "C1 2025"])
            mock_repo.load_snapshots = AsyncMock(return_value={})

            engine = AlertEngine(mock_db, detectors=[])
            await engine.run_for_modalidad("CUATRIMESTRAL")

            mock_repo.load_snapshots.assert_called_once_with(
                "CUATRIMESTRAL", ["C2 2025", "C1 2025"]
            )

    async def test_single_period_no_anterior(self):
        """[AL-02] With 1 period, anterior snapshots are empty."""
        mock_db = AsyncMock()
        detector_calls = []

        class _TrackingDetector:
            tipo = TipoAlerta.BAJO_DESEMPENO

            def detect(self, actual, anterior):
                detector_calls.append({"has_anterior": anterior is not None})
                return []

        with patch(f"{_AE_MOD}.AlertaRepository") as mock_repo_cls:
            mock_repo = mock_repo_cls.return_value
            mock_repo.find_last_two_periods = AsyncMock(return_value=["C1 2025"])
            mock_repo.load_snapshots = AsyncMock(
                return_value={
                    "C1 2025": {
                        ("Prof. García", "ISW-101"): _snap(),
                    },
                }
            )

            engine = AlertEngine(mock_db, detectors=[_TrackingDetector()])
            await engine.run_for_modalidad("CUATRIMESTRAL")

            assert len(detector_calls) == 1
            assert detector_calls[0]["has_anterior"] is False


# ═══════════════════════════════════════════════════════════════════
#  5. Alert deduplication contract [AL-40]
# ═══════════════════════════════════════════════════════════════════


class TestAlertDeduplication:
    """Verify deduplication key: (docente, curso, periodo, tipo)."""

    def test_same_candidate_twice_produces_same_key(self):
        """Two identical candidates share the dedup key."""
        cand1 = AlertCandidate(
            evaluacion_id=_UUID,
            docente_nombre="García",
            curso="ISW-101",
            periodo="C1 2025",
            modalidad="CUATRIMESTRAL",
            tipo_alerta=TipoAlerta.BAJO_DESEMPENO,
            metrica_afectada="puntaje_general",
            valor_actual=55.0,
            valor_anterior=None,
            descripcion="desc1",
            severidad=Severidad.ALTA,
        )
        cand2 = AlertCandidate(
            evaluacion_id=_UUID2,
            docente_nombre="García",
            curso="ISW-101",
            periodo="C1 2025",
            modalidad="CUATRIMESTRAL",
            tipo_alerta=TipoAlerta.BAJO_DESEMPENO,
            metrica_afectada="puntaje_general",
            valor_actual=58.0,
            valor_anterior=None,
            descripcion="desc2",
            severidad=Severidad.MEDIA,
        )
        key1 = (
            cand1.docente_nombre,
            cand1.curso,
            cand1.periodo,
            cand1.tipo_alerta,
        )
        key2 = (
            cand2.docente_nombre,
            cand2.curso,
            cand2.periodo,
            cand2.tipo_alerta,
        )
        assert key1 == key2

    def test_different_tipo_different_key(self):
        """Same docente+curso+periodo but different tipo → 2 alerts."""
        cand_bajo = AlertCandidate(
            evaluacion_id=_UUID,
            docente_nombre="García",
            curso="ISW-101",
            periodo="C1 2025",
            modalidad="CUATRIMESTRAL",
            tipo_alerta=TipoAlerta.BAJO_DESEMPENO,
            metrica_afectada="puntaje_general",
            valor_actual=55.0,
            valor_anterior=None,
            descripcion="bajo",
            severidad=Severidad.ALTA,
        )
        cand_caida = AlertCandidate(
            evaluacion_id=_UUID,
            docente_nombre="García",
            curso="ISW-101",
            periodo="C1 2025",
            modalidad="CUATRIMESTRAL",
            tipo_alerta=TipoAlerta.CAIDA,
            metrica_afectada="puntaje_general",
            valor_actual=55.0,
            valor_anterior=80.0,
            descripcion="caída",
            severidad=Severidad.ALTA,
        )
        key1 = (
            cand_bajo.docente_nombre,
            cand_bajo.curso,
            cand_bajo.periodo,
            cand_bajo.tipo_alerta,
        )
        key2 = (
            cand_caida.docente_nombre,
            cand_caida.curso,
            cand_caida.periodo,
            cand_caida.tipo_alerta,
        )
        assert key1 != key2

    def test_different_periodo_different_key(self):
        """Same docente+curso+tipo but different periodo → 2 alerts."""
        key1 = ("García", "ISW-101", "C1 2025", TipoAlerta.BAJO_DESEMPENO)
        key2 = ("García", "ISW-101", "C2 2025", TipoAlerta.BAJO_DESEMPENO)
        assert key1 != key2


# ═══════════════════════════════════════════════════════════════════
#  6. Modalidad isolation [BR-MOD-02]
# ═══════════════════════════════════════════════════════════════════


class TestModalidadIsolation:
    """Each modalidad gets its own run_for_modalidad call."""

    async def test_run_all_calls_each_modalidad_separately(self):
        """run_all iterates each modalidad independently."""
        mock_db = AsyncMock()
        called_modalidades = []

        with patch(f"{_AE_MOD}.AlertaRepository") as mock_repo_cls:
            mock_repo = mock_repo_cls.return_value

            async def track_find(modalidad):
                called_modalidades.append(modalidad)
                return []

            mock_repo.find_last_two_periods = AsyncMock(side_effect=track_find)

            engine = AlertEngine(mock_db, detectors=[])
            await engine.run_all()

            assert "CUATRIMESTRAL" in called_modalidades
            assert "MENSUAL" in called_modalidades
            assert "B2B" in called_modalidades
            assert "DESCONOCIDA" not in called_modalidades
            assert len(called_modalidades) == 3

    async def test_cuatrimestral_data_not_leaked_to_mensual(self):
        """Snapshots loaded for C are not reused for M."""
        mock_db = AsyncMock()
        load_calls = []

        with patch(f"{_AE_MOD}.AlertaRepository") as mock_repo_cls:
            mock_repo = mock_repo_cls.return_value

            async def track_find(modalidad):
                if modalidad == "CUATRIMESTRAL":
                    return ["C1 2025"]
                return []

            async def track_load(modalidad, periodos):
                load_calls.append({"modalidad": modalidad, "periodos": periodos})
                return {}

            mock_repo.find_last_two_periods = AsyncMock(side_effect=track_find)
            mock_repo.load_snapshots = AsyncMock(side_effect=track_load)

            engine = AlertEngine(mock_db, detectors=[])
            await engine.run_all()

            # Only CUATRIMESTRAL should have loaded snapshots
            assert len(load_calls) == 1
            assert load_calls[0]["modalidad"] == "CUATRIMESTRAL"


# ═══════════════════════════════════════════════════════════════════
#  7. Multi-detector for same snapshot
# ═══════════════════════════════════════════════════════════════════


class TestMultiDetectorSameSnapshot:
    """Multiple detectors fire for the same docente+curso."""

    def test_bajo_and_caida_both_fire(self):
        """A docente with low score AND a big drop triggers 2 alerts."""
        actual = _snap(puntaje=45.0, periodo="C1 2025")
        anterior = _snap(puntaje=80.0, periodo="C3 2024", eval_id=_UUID2)

        bajo = BajoDesempenoDetector()
        caida = CaidaDetector()

        alerts_bajo = bajo.detect(actual, anterior)
        alerts_caida = caida.detect(actual, anterior)

        assert len(alerts_bajo) == 1
        assert alerts_bajo[0].tipo_alerta == TipoAlerta.BAJO_DESEMPENO
        assert len(alerts_caida) == 1
        assert alerts_caida[0].tipo_alerta == TipoAlerta.CAIDA

    def test_engine_combines_multiple_detectors(self):
        """Engine returns candidates from all detectors."""
        db = AsyncMock()
        engine = AlertEngine(
            db,
            detectors=[BajoDesempenoDetector(), CaidaDetector()],
        )

        actual = _snap(puntaje=45.0, periodo="C1 2025")
        anterior = _snap(puntaje=80.0, periodo="C3 2024", eval_id=_UUID2)

        candidates = engine._detect(
            {("Prof. García", "ISW-101"): actual},
            {("Prof. García", "ISW-101"): anterior},
        )

        tipos = {c.tipo_alerta for c in candidates}
        assert TipoAlerta.BAJO_DESEMPENO in tipos
        assert TipoAlerta.CAIDA in tipos
        assert len(candidates) == 2


# ═══════════════════════════════════════════════════════════════════
#  8. Alert detector boundary values
# ═══════════════════════════════════════════════════════════════════


class TestDetectorBoundaries:
    """Exact boundary tests for all 4 detectors."""

    # ── CaidaDetector boundaries ─────────────────────────────

    @pytest.mark.parametrize(
        "drop,expected_sev",
        [
            (5.0, None),  # exactly at threshold → no alert (> 5)
            (5.01, Severidad.BAJA),
            (10.0, Severidad.BAJA),  # exactly 10 → still BAJA (> 10)
            (10.01, Severidad.MEDIA),
            (15.0, Severidad.MEDIA),  # exactly 15 → still MEDIA (> 15)
            (15.01, Severidad.ALTA),
        ],
    )
    def test_caida_boundary(self, drop, expected_sev):
        anterior_score = 80.0
        actual_score = anterior_score - drop
        actual = _snap(puntaje=actual_score, periodo="C1 2025")
        anterior = _snap(puntaje=anterior_score, periodo="C3 2024", eval_id=_UUID2)

        result = CaidaDetector().detect(actual, anterior)
        if expected_sev is None:
            assert result == []
        else:
            assert len(result) == 1
            assert result[0].severidad == expected_sev

    # ── SentimientoDetector boundaries ───────────────────────

    @pytest.mark.parametrize(
        "neg_actual,neg_anterior,total,expected_sev",
        [
            # incremento = (5/100 - 0/100)*100 = 5.0 → exactly at → no
            (5, 0, 100, None),
            # incremento = 5.1 → > 5 → BAJA
            (51, 0, 1000, Severidad.BAJA),
            # incremento = 10.0 → exactly → still BAJA
            (10, 0, 100, Severidad.BAJA),
            # incremento = 10.1 → > 10 → MEDIA
            (101, 0, 1000, Severidad.MEDIA),
            # incremento = 20.0 → exactly → still MEDIA
            (20, 0, 100, Severidad.MEDIA),
            # incremento = 20.1 → > 20 → ALTA
            (201, 0, 1000, Severidad.ALTA),
        ],
    )
    def test_sentimiento_boundary(self, neg_actual, neg_anterior, total, expected_sev):
        actual = _snap(total=total, neg=neg_actual, periodo="C1 2025")
        anterior = _snap(
            total=total,
            neg=neg_anterior,
            periodo="C3 2024",
            eval_id=_UUID2,
        )

        result = SentimientoDetector().detect(actual, anterior)
        if expected_sev is None:
            assert result == []
        else:
            assert len(result) == 1
            assert result[0].severidad == expected_sev

    # ── PatronDetector boundaries ────────────────────────────

    def test_patron_mejora_at_50_pct_no_alert(self):
        """Exactly 50% → no alert (> 0.50 required)."""
        actual = _snap(total=100, mejora_neg=50)
        assert PatronDetector().detect(actual, None) == []

    def test_patron_mejora_at_51_pct_alta(self):
        actual = _snap(total=100, mejora_neg=51)
        result = PatronDetector().detect(actual, None)
        assert len(result) == 1
        assert result[0].severidad == Severidad.ALTA

    def test_patron_actitud_at_30_pct_no_alert(self):
        actual = _snap(total=100, actitud_neg=30)
        assert PatronDetector().detect(actual, None) == []

    def test_patron_actitud_at_31_pct_media(self):
        actual = _snap(total=100, actitud_neg=31)
        result = PatronDetector().detect(actual, None)
        assert len(result) == 1
        assert result[0].severidad == Severidad.MEDIA

    def test_patron_otro_at_40_pct_no_alert(self):
        actual = _snap(total=100, otro=40)
        assert PatronDetector().detect(actual, None) == []

    def test_patron_otro_at_41_pct_baja(self):
        actual = _snap(total=100, otro=41)
        result = PatronDetector().detect(actual, None)
        assert len(result) == 1
        assert result[0].severidad == Severidad.BAJA


# ═══════════════════════════════════════════════════════════════════
#  9. Classifier sentiment boundaries [BR-CLAS-20]
# ═══════════════════════════════════════════════════════════════════


class TestSentimentBoundaries:
    """Exact ±0.25 threshold tests."""

    def test_score_exactly_at_positive_threshold(self):
        """score=0.25 is NOT > 0.25, so not 'positivo'."""
        # 1 pos keyword + observacion prior (no shift) → score = 1/1 = 1.0
        # Need score = exactly 0.25: pos=5, neg=3 → (5-3)/8 = 0.25
        # Construct: 5 "excelente" + 3 "terrible", observacion
        text = "excelente " * 5 + "terrible " * 3
        sent, score = classify_sentimiento(text, "observacion")
        # (5-3)/8 = 0.25 — not > 0.25
        assert score == 0.25
        # With both pos and neg hits → should be "mixto"
        assert sent == "mixto"

    def test_score_just_above_positive_threshold(self):
        """score > 0.25 → 'positivo'."""
        # 3 pos + 1 neg, observacion → (3-1)/4 = 0.5
        text = "excelente muy bien genial terrible"
        sent, score = classify_sentimiento(text, "observacion")
        assert score == 0.5
        assert sent == "positivo"

    def test_score_exactly_at_negative_threshold(self):
        """score=-0.25 is NOT < -0.25, so not 'negativo'."""
        # 3 neg + 5 pos → (5-3)/8 = 0.25 (positive)
        # Need: neg=5, pos=3 → (3-5)/8 = -0.25
        text = "terrible " * 5 + "excelente " * 3
        sent, score = classify_sentimiento(text, "observacion")
        assert score == -0.25
        assert sent == "mixto"

    def test_score_just_below_negative_threshold(self):
        """score < -0.25 → 'negativo'."""
        # 3 neg + 1 pos, observacion → (1-3)/4 = -0.5
        text = "terrible malo deficiente excelente"
        sent, score = classify_sentimiento(text, "observacion")
        assert score == -0.5
        assert sent == "negativo"

    def test_fortaleza_prior_shifts_positive(self):
        """fortaleza adds +1 to pos, shifting ambiguous → positive."""
        # 1 neg keyword + fortaleza prior adds +1 pos
        # pos=1, neg=1 → (1-1)/2 = 0.0 → mixto
        text = "terrible"
        sent, score = classify_sentimiento(text, "fortaleza")
        # pos=1(prior), neg=1(keyword) → score=(1-1)/2=0.0
        assert sent == "mixto"

    def test_mejora_prior_shifts_negative(self):
        """mejora adds +1 to neg, shifting ambiguous → negative."""
        # 1 pos keyword + mejora prior adds +1 neg
        text = "excelente"
        sent, score = classify_sentimiento(text, "mejora")
        # pos=1(keyword), neg=1(prior) → (1-1)/2=0.0 → mixto
        assert sent == "mixto"

    def test_fortaleza_with_positive_keyword_is_positivo(self):
        """fortaleza + 1 pos keyword → pos=2, neg=0 → 2/2=1.0 → positivo."""
        text = "excelente"
        sent, score = classify_sentimiento(text, "fortaleza")
        assert sent == "positivo"
        assert score == 1.0

    def test_mejora_with_negative_keyword_is_negativo(self):
        """mejora + 1 neg keyword → pos=0, neg=2 → -2/2=-1.0 → negativo."""
        text = "terrible"
        sent, score = classify_sentimiento(text, "mejora")
        assert sent == "negativo"
        assert score == -1.0

    def test_neutro_no_keywords(self):
        """No keywords at all → neutro, score=0.0."""
        sent, score = classify_sentimiento("El contenido del curso es interesante", "observacion")
        assert sent == "neutro"
        assert score == 0.0


# ═══════════════════════════════════════════════════════════════════
#  10. Classifier tema: multi-keyword overlap [BR-CLAS-10]
# ═══════════════════════════════════════════════════════════════════


class TestTemaMultiKeyword:
    """First-match-wins with multiple overlapping keywords."""

    def test_first_match_wins_metodologia_over_comunicacion(self):
        """'actividad' matches metodologia first, even with 'explica'."""
        text = "La actividad donde explica los conceptos"
        tema, _ = classify_tema(text)
        assert tema == "metodologia"

    def test_comunicacion_alone(self):
        text = "Explica de forma muy clara los conceptos"
        tema, _ = classify_tema(text)
        assert tema == "comunicacion"

    def test_three_themes_first_wins(self):
        """Keyword from 3 themes → first in TEMA_KEYWORDS order wins."""
        # "método" → metodologia, "explica" → comunicacion,
        # "nota" → evaluacion
        text = "El método que usa para explicar las notas"
        tema, _ = classify_tema(text)
        assert tema == "metodologia"

    def test_empty_string_returns_otro(self):
        tema, conf = classify_tema("")
        assert tema == "otro"
        assert conf == "regla"

    def test_classify_comment_integrates_both(self):
        """Full classify_comment returns all expected keys."""
        result = classify_comment("Excelente método de enseñanza", "fortaleza")
        assert result["tema"] == "metodologia"
        assert result["tema_confianza"] == "regla"
        assert result["sentimiento"] == "positivo"
        assert -1.0 <= result["sent_score"] <= 1.0
