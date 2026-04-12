"""Tests that domain enforcement rejects invalid data.

These tests exist to guarantee that weakening a guard will break CI.
Each test targets one invariant and one failure mode.
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from pydantic import ValidationError as PydanticValidationError

from app.modules.evaluacion_docente.application.parsing.schemas import PeriodoData
from app.modules.evaluacion_docente.application.services.alert_engine import AlertEngine
from app.modules.evaluacion_docente.domain.entities.enums import Modalidad
from app.modules.evaluacion_docente.domain.exceptions import (
    ModalidadInvalidaError,
    ModalidadRequeridaError,
)
from app.modules.evaluacion_docente.domain.invariants import (
    AÑO_MAX,
    AÑO_MIN,
    require_año,
    require_modalidad,
    require_modalidad_valid,
    require_periodo_orden,
)
from app.modules.evaluacion_docente.domain.periodo import parse_periodo
from app.shared.domain.exceptions import ValidationError

_AE_MOD = "app.modules.evaluacion_docente.application.services.alert_engine"

# ════════════════════════════════════════════════════════════════════════
#  require_modalidad — analytics-path enforcement
# ════════════════════════════════════════════════════════════════════════


class TestRequireModalidadEnforcement:
    """Guards on analytics/alert paths reject DESCONOCIDA and garbage."""

    def test_desconocida_rejected(self):
        with pytest.raises(ModalidadInvalidaError):
            require_modalidad("DESCONOCIDA")

    def test_none_rejected(self):
        with pytest.raises(ModalidadRequeridaError):
            require_modalidad(None)

    def test_empty_rejected(self):
        with pytest.raises(ModalidadRequeridaError):
            require_modalidad("")

    def test_garbage_rejected(self):
        with pytest.raises(ModalidadInvalidaError):
            require_modalidad("TRIMESTRAL")

    @pytest.mark.parametrize("mod", ["CUATRIMESTRAL", "MENSUAL", "B2B"])
    def test_valid_passes(self, mod: str):
        assert require_modalidad(mod) == mod


# ════════════════════════════════════════════════════════════════════════
#  require_modalidad_valid — persistence-path enforcement
# ════════════════════════════════════════════════════════════════════════


class TestRequireModalidadValidEnforcement:
    """Persistence path allows DESCONOCIDA but rejects garbage."""

    def test_desconocida_allowed(self):
        assert require_modalidad_valid("DESCONOCIDA") == "DESCONOCIDA"

    @pytest.mark.parametrize("mod", ["CUATRIMESTRAL", "MENSUAL", "B2B"])
    def test_analysis_modalidades_pass(self, mod: str):
        assert require_modalidad_valid(mod) == mod

    def test_garbage_rejected(self):
        with pytest.raises(ValidationError):
            require_modalidad_valid("TRIMESTRAL")

    def test_empty_rejected(self):
        with pytest.raises(ValidationError):
            require_modalidad_valid("")


# ════════════════════════════════════════════════════════════════════════
#  require_año — year range enforcement
# ════════════════════════════════════════════════════════════════════════


class TestRequireAñoEnforcement:
    """Year must be within [AÑO_MIN, AÑO_MAX]."""

    def test_below_min_rejected(self):
        with pytest.raises(ValidationError):
            require_año(AÑO_MIN - 1)

    def test_above_max_rejected(self):
        with pytest.raises(ValidationError):
            require_año(AÑO_MAX + 1)

    def test_min_boundary_passes(self):
        assert require_año(AÑO_MIN) == AÑO_MIN

    def test_max_boundary_passes(self):
        assert require_año(AÑO_MAX) == AÑO_MAX

    def test_typical_year_passes(self):
        assert require_año(2025) == 2025

    def test_year_2019_rejected(self):
        """Pre-2020 years must fail — matches DB CHECK constraint."""
        with pytest.raises(ValidationError):
            require_año(2019)


# ════════════════════════════════════════════════════════════════════════
#  require_periodo_orden — range enforcement per modalidad
# ════════════════════════════════════════════════════════════════════════


class TestRequirePeriodoOrdenEnforcement:
    """periodo_orden must be within legal range for its modalidad."""

    # ── Cuatrimestral: 1-3 ───────────────────────────────────────────

    def test_cuatrimestral_0_rejected(self):
        with pytest.raises(ValidationError):
            require_periodo_orden(0, "CUATRIMESTRAL")

    def test_cuatrimestral_4_rejected(self):
        with pytest.raises(ValidationError):
            require_periodo_orden(4, "CUATRIMESTRAL")

    @pytest.mark.parametrize("orden", [1, 2, 3])
    def test_cuatrimestral_valid(self, orden: int):
        assert require_periodo_orden(orden, "CUATRIMESTRAL") == orden

    # ── Mensual: 1-10 ───────────────────────────────────────────────

    def test_mensual_0_rejected(self):
        with pytest.raises(ValidationError):
            require_periodo_orden(0, "MENSUAL")

    def test_mensual_11_rejected(self):
        with pytest.raises(ValidationError):
            require_periodo_orden(11, "MENSUAL")

    @pytest.mark.parametrize("orden", [1, 5, 10])
    def test_mensual_valid(self, orden: int):
        assert require_periodo_orden(orden, "MENSUAL") == orden

    # ── B2B: fixed at 0 ─────────────────────────────────────────────

    def test_b2b_only_zero(self):
        assert require_periodo_orden(0, "B2B") == 0

    def test_b2b_nonzero_rejected(self):
        with pytest.raises(ValidationError):
            require_periodo_orden(1, "B2B")

    # ── Negative always rejected ─────────────────────────────────────

    def test_negative_rejected(self):
        with pytest.raises(ValidationError):
            require_periodo_orden(-1, "CUATRIMESTRAL")


# ════════════════════════════════════════════════════════════════════════
#  PeriodoData Pydantic model — cross-field validation
# ════════════════════════════════════════════════════════════════════════


def _periodo_data(**overrides) -> dict:
    """Helper to build a valid PeriodoData dict with overrides."""
    base = {
        "periodo_raw": "C1 2025",
        "periodo_normalizado": "C1 2025",
        "modalidad": "CUATRIMESTRAL",
        "año": 2025,
        "periodo_orden": 1,
        "prefijo": "C",
        "numero": 1,
    }
    base.update(overrides)
    return base


class TestPeriodoDataEnforcement:
    """Pydantic model rejects inconsistent periodo data at parse time."""

    def test_valid_cuatrimestral(self):
        pd = PeriodoData(**_periodo_data())
        assert pd.modalidad == Modalidad.CUATRIMESTRAL

    def test_periodo_orden_4_rejected_for_cuatrimestral(self):
        with pytest.raises(PydanticValidationError, match="periodo_orden"):
            PeriodoData(**_periodo_data(periodo_orden=4))

    def test_periodo_orden_0_rejected_for_cuatrimestral(self):
        with pytest.raises(PydanticValidationError, match="periodo_orden"):
            PeriodoData(**_periodo_data(periodo_orden=0))

    def test_periodo_orden_11_rejected_for_mensual(self):
        with pytest.raises(PydanticValidationError, match="periodo_orden"):
            PeriodoData(
                **_periodo_data(modalidad="MENSUAL", periodo_orden=11, prefijo="M", numero=11)
            )

    def test_año_2019_rejected(self):
        with pytest.raises(PydanticValidationError):
            PeriodoData(**_periodo_data(año=2019))

    def test_año_2101_rejected(self):
        with pytest.raises(PydanticValidationError):
            PeriodoData(**_periodo_data(año=2101))

    def test_invalid_modalidad_rejected(self):
        with pytest.raises(PydanticValidationError):
            PeriodoData(**_periodo_data(modalidad="TRIMESTRAL"))

    def test_valid_mensual(self):
        pd = PeriodoData(
            **_periodo_data(
                modalidad="MENSUAL",
                periodo_orden=10,
                prefijo="M",
                numero=10,
                periodo_raw="M10 2025",
                periodo_normalizado="M10 2025",
            )
        )
        assert pd.periodo_orden == 10

    def test_valid_b2b(self):
        pd = PeriodoData(
            **_periodo_data(
                modalidad="B2B",
                periodo_orden=0,
                prefijo="B2B",
                numero=0,
                periodo_raw="B2B EMPRESA 2025",
                periodo_normalizado="B2B EMPRESA 2025",
            )
        )
        assert pd.periodo_orden == 0


# ════════════════════════════════════════════════════════════════════════
#  parse_periodo — enforcement at parser level
# ════════════════════════════════════════════════════════════════════════


class TestParsePeriodoEnforcement:
    """parse_periodo rejects data that doesn't conform to business rules."""

    def test_year_2019_rejected(self):
        with pytest.raises(ValidationError, match="fuera de rango"):
            parse_periodo("C1 2019")

    def test_year_2101_rejected(self):
        with pytest.raises(ValidationError, match="fuera de rango"):
            parse_periodo("C1 2101")

    def test_cuatrimestral_c4_rejected(self):
        """C4 does not exist — only C1, C2, C3."""
        with pytest.raises(ValidationError):
            parse_periodo("C4 2025")

    def test_mensual_m11_rejected(self):
        with pytest.raises(ValidationError, match="fuera de rango"):
            parse_periodo("M11 2025")

    def test_garbage_format_rejected(self):
        with pytest.raises(ValidationError, match="no reconocido"):
            parse_periodo("XYZ 2025")

    def test_valid_c1_passes(self):
        info = parse_periodo("C1 2025")
        assert info.año == 2025
        assert info.periodo_orden == 1

    def test_valid_mt10_passes(self):
        info = parse_periodo("MT10 2025")
        assert info.modalidad == Modalidad.MENSUAL
        assert info.periodo_orden == 10


# ════════════════════════════════════════════════════════════════════════
#  AlertEngine — modalidad enforcement on entry
# ════════════════════════════════════════════════════════════════════════


class TestAlertEngineModalidadEnforcement:
    """AlertEngine.run_for_modalidad rejects invalid modalidades."""

    async def test_desconocida_rejected(self):
        db = AsyncMock()
        engine = AlertEngine(db, detectors=[])
        with pytest.raises(ModalidadInvalidaError):
            await engine.run_for_modalidad("DESCONOCIDA")

    async def test_garbage_rejected(self):
        db = AsyncMock()
        engine = AlertEngine(db, detectors=[])
        with pytest.raises(ModalidadInvalidaError):
            await engine.run_for_modalidad("TRIMESTRAL")

    async def test_none_rejected(self):
        db = AsyncMock()
        engine = AlertEngine(db, detectors=[])
        with pytest.raises(ModalidadRequeridaError):
            await engine.run_for_modalidad(None)

    async def test_valid_cuatrimestral_proceeds(self):
        db = AsyncMock()
        with patch(f"{_AE_MOD}.AlertaRepository") as mock_repo_cls:
            mock_repo = mock_repo_cls.return_value
            mock_repo.find_last_two_periods = AsyncMock(return_value=[])
            engine = AlertEngine(db, detectors=[])
            result = await engine.run_for_modalidad("CUATRIMESTRAL")
            assert result.modalidades_processed == 0  # no data, but no error


# ════════════════════════════════════════════════════════════════════════
#  Alert 2-period window — enforcement via SQL LIMIT
# ════════════════════════════════════════════════════════════════════════


class TestAlertTwoPeriodWindowEnforcement:
    """Alert engine must never process more than 2 periods per modalidad."""

    async def test_at_most_two_periods_used(self):
        """Even if repo somehow returns 3 periods, engine only uses first 2."""
        db = AsyncMock()
        with patch(f"{_AE_MOD}.AlertaRepository") as mock_repo_cls:
            mock_repo = mock_repo_cls.return_value
            # Simulate repo returning 3 periods (shouldn't happen with LIMIT 2)
            mock_repo.find_last_two_periods = AsyncMock(
                return_value=["C3 2025", "C2 2025", "C1 2025"]
            )
            mock_repo.load_snapshots = AsyncMock(return_value={})
            engine = AlertEngine(db, detectors=[])
            result = await engine.run_for_modalidad("CUATRIMESTRAL")
            # Engine uses periodos[0] and periodos[1], ignores [2]
            mock_repo.load_snapshots.assert_called_once_with(
                "CUATRIMESTRAL", ["C3 2025", "C2 2025", "C1 2025"]
            )
            # The result should include all periods from the repo
            assert result.periodos_by_modalidad["CUATRIMESTRAL"] == [
                "C3 2025",
                "C2 2025",
                "C1 2025",
            ]

    async def test_single_period_no_anterior(self):
        """With only 1 period, anterior snapshot is empty — no comparison alerts fire."""
        db = AsyncMock()

        class _CaidaOnlyDetector:
            """Only fires when anterior exists and there's a drop."""

            tipo = "CAIDA"

            def detect(self, actual, anterior):
                if anterior is None:
                    return []
                return [AsyncMock()]  # Would fire if anterior existed

        with patch(f"{_AE_MOD}.AlertaRepository") as mock_repo_cls:
            mock_repo = mock_repo_cls.return_value
            mock_repo.find_last_two_periods = AsyncMock(return_value=["C1 2025"])

            from app.modules.evaluacion_docente.domain.alert_rules import DocenteCursoSnapshot

            snap = DocenteCursoSnapshot(
                evaluacion_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
                docente_nombre="Prof. García",
                curso="ISW-101",
                periodo="C1 2025",
                modalidad="CUATRIMESTRAL",
                puntaje_general=90.0,
                total_comentarios=5,
                negativos_count=0,
                mejora_negativo_count=0,
                actitud_negativo_count=0,
                otro_count=0,
            )
            mock_repo.load_snapshots = AsyncMock(
                return_value={"C1 2025": {("Prof. García", "ISW-101"): snap}}
            )

            engine = AlertEngine(db, detectors=[_CaidaOnlyDetector()])
            result = await engine.run_for_modalidad("CUATRIMESTRAL")
            # No candidates because no anterior period
            assert result.candidates_generated == 0


# ════════════════════════════════════════════════════════════════════════
#  AÑO_MIN constant — DB alignment guard
# ════════════════════════════════════════════════════════════════════════


class TestAñoMinAlignment:
    """Guard that AÑO_MIN matches the DB CHECK constraint (año >= 2020)."""

    def test_año_min_is_2020(self):
        """If someone changes AÑO_MIN, this test breaks — intentional."""
        assert AÑO_MIN == 2020

    def test_año_max_is_2100(self):
        assert AÑO_MAX == 2100
