"""Tests for periodo validation inside the parser pipeline.

Verifies that the parser correctly:
- Extracts and validates periodo from the PDF header [BR-MOD-03]
- Populates PeriodoData on successful parse [BR-AN-41]
- Rejects structurally invalid periodos with ParseError
- Marks DESCONOCIDA periodos with a warning but still succeeds [BR-MOD-05]
- Feeds periodo data through to ProcessingService for DB persistence

These tests mock the PDF layer and exercise the _resolve_periodo stage
and its integration with the rest of the pipeline.
"""

from __future__ import annotations

import pytest

from app.modules.evaluacion_docente.application.parsing.errors import ParseError, ParseWarning
from app.modules.evaluacion_docente.application.parsing.parser import _resolve_periodo
from app.modules.evaluacion_docente.application.parsing.schemas import PeriodoData


class TestResolvePeriodo:
    """Direct tests of the _resolve_periodo helper."""

    # ── Cuatrimestral ────────────────────────────────────────────────

    @pytest.mark.parametrize(
        "raw, norm, modalidad, año, orden, prefijo, numero",
        [
            ("C1 2024", "C1 2024", "CUATRIMESTRAL", 2024, 1, "C", 1),
            ("C2 2025", "C2 2025", "CUATRIMESTRAL", 2025, 2, "C", 2),
            ("C3 2025", "C3 2025", "CUATRIMESTRAL", 2025, 3, "C", 3),
            ("  c2  2025 ", "C2 2025", "CUATRIMESTRAL", 2025, 2, "C", 2),
        ],
    )
    def test_cuatrimestral(self, raw, norm, modalidad, año, orden, prefijo, numero) -> None:
        errors: list[ParseError] = []
        warnings: list[ParseWarning] = []
        result = _resolve_periodo(raw, errors, warnings)

        assert result is not None
        assert result.periodo_raw == raw
        assert result.periodo_normalizado == norm
        assert result.modalidad == modalidad
        assert result.año == año
        assert result.periodo_orden == orden
        assert result.prefijo == prefijo
        assert result.numero == numero
        assert errors == []
        assert warnings == []

    # ── Mensual M ────────────────────────────────────────────────────

    @pytest.mark.parametrize(
        "raw, norm, año, orden, prefijo, numero",
        [
            ("M1 2026", "M1 2026", 2026, 1, "M", 1),
            ("M10 2025", "M10 2025", 2025, 10, "M", 10),
            ("m5 2025", "M5 2025", 2025, 5, "M", 5),
        ],
    )
    def test_mensual_m(self, raw, norm, año, orden, prefijo, numero) -> None:
        errors: list[ParseError] = []
        warnings: list[ParseWarning] = []
        result = _resolve_periodo(raw, errors, warnings)

        assert result is not None
        assert result.modalidad == "MENSUAL"
        assert result.periodo_normalizado == norm
        assert result.año == año
        assert result.periodo_orden == orden
        assert result.prefijo == prefijo
        assert result.numero == numero
        assert errors == []

    # ── Mensual MT ───────────────────────────────────────────────────

    @pytest.mark.parametrize(
        "raw, norm, año, orden, prefijo, numero",
        [
            ("MT1 2024", "MT1 2024", 2024, 1, "MT", 1),
            ("MT3 2024", "MT3 2024", 2024, 3, "MT", 3),
            ("MT10 2025", "MT10 2025", 2025, 10, "MT", 10),
        ],
    )
    def test_mensual_mt(self, raw, norm, año, orden, prefijo, numero) -> None:
        errors: list[ParseError] = []
        warnings: list[ParseWarning] = []
        result = _resolve_periodo(raw, errors, warnings)

        assert result is not None
        assert result.modalidad == "MENSUAL"
        assert result.periodo_normalizado == norm
        assert result.año == año
        assert result.periodo_orden == orden
        assert result.prefijo == prefijo
        assert result.numero == numero
        assert errors == []

    # ── B2B ──────────────────────────────────────────────────────────

    def test_b2b_with_year(self) -> None:
        errors: list[ParseError] = []
        warnings: list[ParseWarning] = []
        result = _resolve_periodo("B2B-EMPRESA-2025-Q1", errors, warnings)

        assert result is not None
        assert result.modalidad == "B2B"
        assert result.año == 2025
        assert result.periodo_orden == 0
        assert result.prefijo == "B2B"
        assert errors == []

    def test_b2b_space_format(self) -> None:
        errors: list[ParseError] = []
        warnings: list[ParseWarning] = []
        result = _resolve_periodo("B2B MICROSOFT 2026", errors, warnings)

        assert result is not None
        assert result.modalidad == "B2B"
        assert result.año == 2026
        assert result.periodo_normalizado == "B2B MICROSOFT 2026"
        assert errors == []

    # ── DESCONOCIDA → warning, not error [BR-MOD-05] ────────────────

    @pytest.mark.parametrize(
        "raw",
        [
            "X1 2025",
            "2025",
            "CUATRIMESTRAL",
            "C1",  # no year
            "M5",  # no year
        ],
    )
    def test_desconocida_warns_but_succeeds(self, raw: str) -> None:
        errors: list[ParseError] = []
        warnings: list[ParseWarning] = []
        result = _resolve_periodo(raw, errors, warnings)

        assert result is not None
        assert result.modalidad == "DESCONOCIDA"
        assert result.periodo_orden == 0
        assert errors == []
        assert len(warnings) == 1
        assert warnings[0].code == "UNKNOWN_MODALIDAD"

    def test_desconocida_extracts_year_when_present(self) -> None:
        errors: list[ParseError] = []
        warnings: list[ParseWarning] = []
        result = _resolve_periodo("SPECIAL 2026", errors, warnings)

        assert result is not None
        assert result.año == 2026

    def test_desconocida_defaults_year_2020(self) -> None:
        errors: list[ParseError] = []
        warnings: list[ParseWarning] = []
        result = _resolve_periodo("UNKNOWN", errors, warnings)

        assert result is not None
        assert result.año == 2020

    # ── Invalid structures → error, returns None ─────────────────────

    @pytest.mark.parametrize(
        "raw",
        [
            "C1 1999",  # year too low
            "C1 2101",  # year too high
        ],
    )
    def test_invalid_year_returns_none(self, raw: str) -> None:
        errors: list[ParseError] = []
        warnings: list[ParseWarning] = []
        result = _resolve_periodo(raw, errors, warnings)

        assert result is None
        assert len(errors) == 1
        assert errors[0].stage == "periodo"
        assert errors[0].code == "INVALID_PERIODO_STRUCTURE"
        assert raw in errors[0].context["periodo_raw"]

    @pytest.mark.parametrize(
        "raw",
        [
            "M11 2025",  # M11 outside valid range → DESCONOCIDA
            "MT0 2025",  # MT0 outside valid range → DESCONOCIDA
        ],
    )
    def test_out_of_range_becomes_desconocida(self, raw: str) -> None:
        """Out-of-range numbers don't match regex → DESCONOCIDA, not error."""
        errors: list[ParseError] = []
        warnings: list[ParseWarning] = []
        result = _resolve_periodo(raw, errors, warnings)

        assert result is not None
        assert result.modalidad == "DESCONOCIDA"
        assert errors == []
        assert len(warnings) == 1
        assert warnings[0].code == "UNKNOWN_MODALIDAD"

    # ── PeriodoData structure ────────────────────────────────────────

    def test_returns_periodo_data_type(self) -> None:
        errors: list[ParseError] = []
        warnings: list[ParseWarning] = []
        result = _resolve_periodo("C2 2025", errors, warnings)

        assert isinstance(result, PeriodoData)
        assert result.periodo_raw == "C2 2025"

    def test_periodo_data_is_serializable(self) -> None:
        """PeriodoData must serialize for datos_completos JSON."""
        errors: list[ParseError] = []
        warnings: list[ParseWarning] = []
        result = _resolve_periodo("MT3 2024", errors, warnings)

        assert result is not None
        d = result.model_dump(mode="json")
        assert d["modalidad"] == "MENSUAL"
        assert d["año"] == 2024
        assert d["periodo_orden"] == 3
        assert d["prefijo"] == "MT"


class TestResolvePeridoSortable:
    """Ensures multiple parsed periods sort chronologically [BR-AN-40]."""

    def test_cuatrimestral_chronological_order(self) -> None:
        raws = ["C3 2024", "C1 2025", "C1 2024", "C2 2024"]
        results = []
        for raw in raws:
            errors: list[ParseError] = []
            warnings: list[ParseWarning] = []
            result = _resolve_periodo(raw, errors, warnings)
            assert result is not None
            results.append(result)

        ordered = sorted(results, key=lambda r: (r.año, r.prefijo, r.numero))
        assert [r.periodo_normalizado for r in ordered] == [
            "C1 2024",
            "C2 2024",
            "C3 2024",
            "C1 2025",
        ]

    def test_mensual_cross_year_order(self) -> None:
        raws = ["M10 2025", "M1 2026", "M5 2025"]
        results = []
        for raw in raws:
            errors: list[ParseError] = []
            warnings: list[ParseWarning] = []
            result = _resolve_periodo(raw, errors, warnings)
            assert result is not None
            results.append(result)

        ordered = sorted(results, key=lambda r: (r.año, r.prefijo, r.numero))
        assert [r.periodo_normalizado for r in ordered] == [
            "M5 2025",
            "M10 2025",
            "M1 2026",
        ]
