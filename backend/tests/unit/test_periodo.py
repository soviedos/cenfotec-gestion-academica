"""Tests for app.domain.periodo — period normalisation, validation & ordering.

Covers business rules [BR-MOD-01]–[BR-MOD-05] and [BR-AN-40]–[BR-AN-42].
"""

from __future__ import annotations

import pytest

from app.domain.entities.enums import Modalidad
from app.domain.exceptions import ValidationError
from app.domain.periodo import (
    PeriodoInfo,
    _periodo_str_sort_key,
    determinar_modalidad,
    normalizar_periodo,
    parse_periodo,
    periodo_sort_key,
    sort_periodos,
    validar_periodo,
)

# ════════════════════════════════════════════════════════════════════════
#  normalizar_periodo
# ════════════════════════════════════════════════════════════════════════


class TestNormalizarPeriodo:
    """[BR-MOD-03] Whitespace + case normalisation."""

    @pytest.mark.parametrize(
        "raw, expected",
        [
            ("C1 2025", "C1 2025"),
            ("  c2   2025 ", "C2 2025"),
            ("c3  2024", "C3 2024"),
            ("m1 2026", "M1 2026"),
            ("mt10  2025", "MT10 2025"),
            ("  mt3   2024  ", "MT3 2024"),
            ("b2b - empresa  2025-q1", "B2B - EMPRESA 2025-Q1"),
            ("B2B MICROSOFT 2026", "B2B MICROSOFT 2026"),
        ],
    )
    def test_normalises_correctly(self, raw: str, expected: str) -> None:
        assert normalizar_periodo(raw) == expected

    def test_empty_string(self) -> None:
        assert normalizar_periodo("") == ""

    def test_only_whitespace(self) -> None:
        assert normalizar_periodo("   ") == ""


# ════════════════════════════════════════════════════════════════════════
#  determinar_modalidad
# ════════════════════════════════════════════════════════════════════════


class TestDeterminarModalidad:
    """[BR-MOD-03] Infer modalidad from raw periodo string."""

    # ── Cuatrimestral ────────────────────────────────────────────────

    @pytest.mark.parametrize("periodo", ["C1 2024", "C2 2025", "C3 2025", "c1 2026", "  c3  2024 "])
    def test_cuatrimestral(self, periodo: str) -> None:
        assert determinar_modalidad(periodo) == Modalidad.CUATRIMESTRAL

    # ── Mensual M ────────────────────────────────────────────────────

    @pytest.mark.parametrize(
        "periodo",
        ["M1 2026", "M5 2025", "M10 2025", "m1 2025", "  m10  2025 "],
    )
    def test_mensual_m(self, periodo: str) -> None:
        assert determinar_modalidad(periodo) == Modalidad.MENSUAL

    # ── Mensual MT ───────────────────────────────────────────────────

    @pytest.mark.parametrize(
        "periodo",
        ["MT1 2024", "MT3 2024", "MT10 2025", "mt5 2025", "  mt1  2024 "],
    )
    def test_mensual_mt(self, periodo: str) -> None:
        assert determinar_modalidad(periodo) == Modalidad.MENSUAL

    # ── B2B ──────────────────────────────────────────────────────────

    @pytest.mark.parametrize(
        "periodo",
        [
            "B2B-EMPRESA-2025-Q1",
            "B2B MICROSOFT 2026",
            "b2b - test 2025",
            "B2B-xyz",
        ],
    )
    def test_b2b(self, periodo: str) -> None:
        assert determinar_modalidad(periodo) == Modalidad.B2B

    # ── Desconocida ──────────────────────────────────────────────────

    @pytest.mark.parametrize(
        "periodo",
        [
            "X1 2025",
            "C4 2025",  # C4 doesn't exist
            "M0 2025",  # M0 doesn't exist
            "M11 2025",  # M11 doesn't exist
            "MT0 2025",  # MT0 doesn't exist
            "MT11 2025",  # MT11 doesn't exist
            "2025",
            "",
            "CUATRIMESTRAL",
            "C1",  # Missing year
            "M5",  # Missing year
        ],
    )
    def test_desconocida(self, periodo: str) -> None:
        assert determinar_modalidad(periodo) == Modalidad.DESCONOCIDA

    def test_b2b_priority_over_others(self) -> None:
        """B2B prefix takes priority even if the rest looks like C or M."""
        assert determinar_modalidad("B2B C1 2025") == Modalidad.B2B


# ════════════════════════════════════════════════════════════════════════
#  parse_periodo
# ════════════════════════════════════════════════════════════════════════


class TestParsePeriodo:
    """[BR-AN-41] Parse full periodo string into structured data."""

    # ── Cuatrimestral valid ──────────────────────────────────────────

    @pytest.mark.parametrize(
        "raw, año, numero, prefijo",
        [
            ("C1 2024", 2024, 1, "C"),
            ("C2 2025", 2025, 2, "C"),
            ("C3 2025", 2025, 3, "C"),
            ("  c2  2025 ", 2025, 2, "C"),
        ],
    )
    def test_cuatrimestral(self, raw: str, año: int, numero: int, prefijo: str) -> None:
        info = parse_periodo(raw)
        assert info.modalidad == Modalidad.CUATRIMESTRAL
        assert info.año == año
        assert info.numero == numero
        assert info.periodo_orden == numero
        assert info.prefijo == prefijo
        assert info.periodo_normalizado == f"C{numero} {año}"

    # ── Mensual valid ────────────────────────────────────────────────

    @pytest.mark.parametrize(
        "raw, año, numero, prefijo",
        [
            ("M1 2026", 2026, 1, "M"),
            ("M10 2025", 2025, 10, "M"),
            ("m5 2025", 2025, 5, "M"),
        ],
    )
    def test_mensual_m(self, raw: str, año: int, numero: int, prefijo: str) -> None:
        info = parse_periodo(raw)
        assert info.modalidad == Modalidad.MENSUAL
        assert info.año == año
        assert info.numero == numero
        assert info.periodo_orden == numero
        assert info.prefijo == prefijo

    @pytest.mark.parametrize(
        "raw, año, numero, prefijo",
        [
            ("MT1 2024", 2024, 1, "MT"),
            ("MT3 2024", 2024, 3, "MT"),
            ("MT10 2025", 2025, 10, "MT"),
            ("  mt5  2025 ", 2025, 5, "MT"),
        ],
    )
    def test_mensual_mt(self, raw: str, año: int, numero: int, prefijo: str) -> None:
        info = parse_periodo(raw)
        assert info.modalidad == Modalidad.MENSUAL
        assert info.año == año
        assert info.numero == numero
        assert info.periodo_orden == numero
        assert info.prefijo == prefijo

    # ── B2B valid ────────────────────────────────────────────────────

    def test_b2b_with_year(self) -> None:
        info = parse_periodo("B2B-EMPRESA-2025-Q1")
        assert info.modalidad == Modalidad.B2B
        assert info.año == 2025
        assert info.periodo_orden == 0
        assert info.prefijo == "B2B"

    def test_b2b_space_separator(self) -> None:
        info = parse_periodo("B2B MICROSOFT 2026")
        assert info.modalidad == Modalidad.B2B
        assert info.año == 2026
        assert info.periodo_normalizado == "B2B MICROSOFT 2026"

    def test_b2b_no_year(self) -> None:
        info = parse_periodo("B2B-xyz-abc")
        assert info.modalidad == Modalidad.B2B
        assert info.año == 0  # no year found

    # ── Invalid formats ──────────────────────────────────────────────

    @pytest.mark.parametrize(
        "raw",
        [
            "C4 2025",
            "M0 2025",
            "M11 2025",
            "MT0 2025",
            "MT11 2025",
            "X1 2025",
            "2025",
            "C1",
            "",
            "garbage",
        ],
    )
    def test_invalid_raises(self, raw: str) -> None:
        with pytest.raises(ValidationError):
            parse_periodo(raw)

    # ── Year range ───────────────────────────────────────────────────

    def test_year_too_low(self) -> None:
        with pytest.raises(ValidationError, match="fuera de rango"):
            parse_periodo("C1 1999")

    def test_year_too_high(self) -> None:
        with pytest.raises(ValidationError, match="fuera de rango"):
            parse_periodo("C1 2101")

    # ── Frozen dataclass ─────────────────────────────────────────────

    def test_result_is_immutable(self) -> None:
        info = parse_periodo("C1 2025")
        with pytest.raises(AttributeError):
            info.año = 2026  # type: ignore[misc]


# ════════════════════════════════════════════════════════════════════════
#  validar_periodo
# ════════════════════════════════════════════════════════════════════════


class TestValidarPeriodo:
    """Validate code + year + modalidad triple."""

    # ── Cuatrimestral ────────────────────────────────────────────────

    @pytest.mark.parametrize("codigo", ["C1", "C2", "C3", "c1", " c2 "])
    def test_cuatrimestral_valid(self, codigo: str) -> None:
        info = validar_periodo(codigo, 2025, Modalidad.CUATRIMESTRAL)
        assert info.modalidad == Modalidad.CUATRIMESTRAL
        assert info.año == 2025

    def test_cuatrimestral_c4_invalid(self) -> None:
        with pytest.raises(ValidationError, match="CUATRIMESTRAL"):
            validar_periodo("C4", 2025, Modalidad.CUATRIMESTRAL)

    def test_cuatrimestral_m1_invalid(self) -> None:
        with pytest.raises(ValidationError, match="CUATRIMESTRAL"):
            validar_periodo("M1", 2025, Modalidad.CUATRIMESTRAL)

    # ── Mensual M ────────────────────────────────────────────────────

    @pytest.mark.parametrize("codigo", ["M1", "M5", "M10", "m1", " m10 "])
    def test_mensual_m_valid(self, codigo: str) -> None:
        info = validar_periodo(codigo, 2025, Modalidad.MENSUAL)
        assert info.modalidad == Modalidad.MENSUAL
        assert info.prefijo == "M"

    def test_mensual_m0_invalid(self) -> None:
        with pytest.raises(ValidationError, match="fuera de rango"):
            validar_periodo("M0", 2025, Modalidad.MENSUAL)

    def test_mensual_m11_invalid(self) -> None:
        with pytest.raises(ValidationError, match="fuera de rango"):
            validar_periodo("M11", 2025, Modalidad.MENSUAL)

    # ── Mensual MT ───────────────────────────────────────────────────

    @pytest.mark.parametrize("codigo", ["MT1", "MT5", "MT10", "mt3", " mt10 "])
    def test_mensual_mt_valid(self, codigo: str) -> None:
        info = validar_periodo(codigo, 2025, Modalidad.MENSUAL)
        assert info.modalidad == Modalidad.MENSUAL
        assert info.prefijo == "MT"

    def test_mensual_mt0_invalid(self) -> None:
        with pytest.raises(ValidationError, match="fuera de rango"):
            validar_periodo("MT0", 2025, Modalidad.MENSUAL)

    def test_mensual_mt11_invalid(self) -> None:
        with pytest.raises(ValidationError, match="fuera de rango"):
            validar_periodo("MT11", 2025, Modalidad.MENSUAL)

    # ── B2B ──────────────────────────────────────────────────────────

    def test_b2b_valid(self) -> None:
        info = validar_periodo("B2B-EMPRESA-2025-Q1", 2025, Modalidad.B2B)
        assert info.modalidad == Modalidad.B2B
        assert info.periodo_orden == 0

    def test_b2b_rejects_non_b2b_prefix(self) -> None:
        with pytest.raises(ValidationError, match="B2B"):
            validar_periodo("C1", 2025, Modalidad.B2B)

    # ── Cross-modalidad mismatch ─────────────────────────────────────

    def test_m_code_for_cuatrimestral_fails(self) -> None:
        with pytest.raises(ValidationError):
            validar_periodo("M1", 2025, Modalidad.CUATRIMESTRAL)

    def test_c_code_for_mensual_fails(self) -> None:
        with pytest.raises(ValidationError):
            validar_periodo("C1", 2025, Modalidad.MENSUAL)

    # ── DESCONOCIDA ──────────────────────────────────────────────────

    def test_desconocida_modalidad_rejects(self) -> None:
        with pytest.raises(ValidationError, match="DESCONOCIDA"):
            validar_periodo("C1", 2025, Modalidad.DESCONOCIDA)

    # ── Year validation ──────────────────────────────────────────────

    def test_year_too_low(self) -> None:
        with pytest.raises(ValidationError, match="fuera de rango"):
            validar_periodo("C1", 1999, Modalidad.CUATRIMESTRAL)

    def test_year_too_high(self) -> None:
        with pytest.raises(ValidationError, match="fuera de rango"):
            validar_periodo("C1", 2101, Modalidad.CUATRIMESTRAL)

    # ── Return type ──────────────────────────────────────────────────

    def test_returns_periodo_info(self) -> None:
        info = validar_periodo("C2", 2025, Modalidad.CUATRIMESTRAL)
        assert isinstance(info, PeriodoInfo)
        assert info.periodo_normalizado == "C2 2025"
        assert info.periodo_orden == 2
        assert info.prefijo == "C"
        assert info.numero == 2


# ════════════════════════════════════════════════════════════════════════
#  periodo_sort_key  [BR-AN-40, BR-AN-42]
# ════════════════════════════════════════════════════════════════════════


class TestPeriodoSortKey:
    """Chronological ordering of periods."""

    def test_cuatrimestral_order_within_year(self) -> None:
        periods = [parse_periodo(p) for p in ["C3 2024", "C1 2024", "C2 2024"]]
        ordered = sorted(periods, key=periodo_sort_key)
        assert [p.periodo_normalizado for p in ordered] == [
            "C1 2024",
            "C2 2024",
            "C3 2024",
        ]

    def test_cuatrimestral_cross_year(self) -> None:
        """[BR-AN-42] continuity between years."""
        periods = [parse_periodo(p) for p in ["C1 2025", "C3 2024", "C2 2025", "C1 2024"]]
        ordered = sorted(periods, key=periodo_sort_key)
        assert [p.periodo_normalizado for p in ordered] == [
            "C1 2024",
            "C3 2024",
            "C1 2025",
            "C2 2025",
        ]

    def test_mensual_order_within_year(self) -> None:
        periods = [parse_periodo(p) for p in ["M10 2025", "M1 2025", "M5 2025"]]
        ordered = sorted(periods, key=periodo_sort_key)
        assert [p.periodo_normalizado for p in ordered] == [
            "M1 2025",
            "M5 2025",
            "M10 2025",
        ]

    def test_mensual_cross_year(self) -> None:
        periods = [parse_periodo(p) for p in ["M1 2026", "M10 2025", "M5 2025"]]
        ordered = sorted(periods, key=periodo_sort_key)
        assert [p.periodo_normalizado for p in ordered] == [
            "M5 2025",
            "M10 2025",
            "M1 2026",
        ]

    def test_mt_order(self) -> None:
        periods = [parse_periodo(p) for p in ["MT10 2025", "MT1 2025", "MT3 2025"]]
        ordered = sorted(periods, key=periodo_sort_key)
        assert [p.periodo_normalizado for p in ordered] == [
            "MT1 2025",
            "MT3 2025",
            "MT10 2025",
        ]

    def test_m_and_mt_sort_separately_by_prefix(self) -> None:
        """M and MT are both MENSUAL but sort in separate prefix groups."""
        periods = [parse_periodo(p) for p in ["MT1 2025", "M2 2025", "M1 2025", "MT2 2025"]]
        ordered = sorted(periods, key=periodo_sort_key)
        names = [p.periodo_normalizado for p in ordered]
        # M < MT lexicographically → M first
        assert names == ["M1 2025", "M2 2025", "MT1 2025", "MT2 2025"]


# ════════════════════════════════════════════════════════════════════════
#  Edge cases & integration
# ════════════════════════════════════════════════════════════════════════


class TestEdgeCases:
    """Boundary and integration-style tests."""

    def test_parse_and_validate_agree(self) -> None:
        """parse_periodo and validar_periodo should produce identical info."""
        parsed = parse_periodo("C2 2025")
        validated = validar_periodo("C2", 2025, Modalidad.CUATRIMESTRAL)
        assert parsed == validated

    def test_determinar_then_parse_roundtrip(self) -> None:
        raw = "MT3 2024"
        modalidad = determinar_modalidad(raw)
        assert modalidad == Modalidad.MENSUAL
        info = parse_periodo(raw)
        assert info.modalidad == modalidad

    def test_normalise_idempotent(self) -> None:
        raw = "  c2   2025 "
        once = normalizar_periodo(raw)
        twice = normalizar_periodo(once)
        assert once == twice

    @pytest.mark.parametrize("año", [2020, 2100])
    def test_year_boundary_valid(self, año: int) -> None:
        info = parse_periodo(f"C1 {año}")
        assert info.año == año

    @pytest.mark.parametrize("año", [2019, 2101])
    def test_year_boundary_invalid(self, año: int) -> None:
        with pytest.raises(ValidationError):
            parse_periodo(f"C1 {año}")


# ════════════════════════════════════════════════════════════════════════
#  _periodo_str_sort_key
# ════════════════════════════════════════════════════════════════════════


class TestPeriodoStrSortKey:
    """Tests for the raw-string sort-key helper."""

    def test_valid_cuatrimestral(self) -> None:
        assert _periodo_str_sort_key("C2 2025") == (2025, "C", 2)

    def test_valid_mensual(self) -> None:
        assert _periodo_str_sort_key("M10 2024") == (2024, "M", 10)

    def test_valid_mt(self) -> None:
        assert _periodo_str_sort_key("MT3 2026") == (2026, "MT", 3)

    def test_unparseable_returns_fallback(self) -> None:
        key = _periodo_str_sort_key("garbage")
        assert key == (9999, "garbage", 0)

    def test_empty_string_returns_fallback(self) -> None:
        key = _periodo_str_sort_key("")
        assert key[0] == 9999


# ════════════════════════════════════════════════════════════════════════
#  sort_periodos
# ════════════════════════════════════════════════════════════════════════


class TestSortPeriodos:
    """[BR-AN-40] Chronological ordering of dict rows by periodo."""

    def test_cuatrimestral_within_year(self) -> None:
        rows = [
            {"periodo": "C3 2024", "v": 3},
            {"periodo": "C1 2024", "v": 1},
            {"periodo": "C2 2024", "v": 2},
        ]
        result = sort_periodos(rows)
        assert [r["periodo"] for r in result] == ["C1 2024", "C2 2024", "C3 2024"]

    def test_cross_year_ordering(self) -> None:
        """[BR-AN-42] C3 2024 before C1 2025."""
        rows = [
            {"periodo": "C1 2025"},
            {"periodo": "C3 2024"},
            {"periodo": "C2 2025"},
            {"periodo": "C1 2024"},
        ]
        result = sort_periodos(rows)
        assert [r["periodo"] for r in result] == [
            "C1 2024",
            "C3 2024",
            "C1 2025",
            "C2 2025",
        ]

    def test_mensual_ordering(self) -> None:
        rows = [
            {"periodo": "M10 2024"},
            {"periodo": "M1 2024"},
            {"periodo": "M5 2024"},
        ]
        result = sort_periodos(rows)
        assert [r["periodo"] for r in result] == ["M1 2024", "M5 2024", "M10 2024"]

    def test_mt_ordering(self) -> None:
        rows = [
            {"periodo": "MT3 2024"},
            {"periodo": "MT1 2024"},
        ]
        result = sort_periodos(rows)
        assert [r["periodo"] for r in result] == ["MT1 2024", "MT3 2024"]

    def test_empty_list(self) -> None:
        assert sort_periodos([]) == []

    def test_single_element(self) -> None:
        rows = [{"periodo": "C1 2025"}]
        assert sort_periodos(rows) == rows

    def test_unparseable_sorts_last(self) -> None:
        rows = [
            {"periodo": "garbage"},
            {"periodo": "C1 2024"},
            {"periodo": "C2 2024"},
        ]
        result = sort_periodos(rows)
        assert [r["periodo"] for r in result] == ["C1 2024", "C2 2024", "garbage"]

    def test_custom_key(self) -> None:
        rows = [
            {"period": "C3 2024", "x": 1},
            {"period": "C1 2024", "x": 2},
        ]
        result = sort_periodos(rows, key="period")
        assert [r["period"] for r in result] == ["C1 2024", "C3 2024"]

    def test_does_not_mutate_original(self) -> None:
        rows = [{"periodo": "C2 2024"}, {"periodo": "C1 2024"}]
        original_order = [r["periodo"] for r in rows]
        sort_periodos(rows)
        assert [r["periodo"] for r in rows] == original_order

    def test_preserves_extra_fields(self) -> None:
        rows = [
            {"periodo": "C2 2024", "promedio": 85.5},
            {"periodo": "C1 2024", "promedio": 90.0},
        ]
        result = sort_periodos(rows)
        assert result[0] == {"periodo": "C1 2024", "promedio": 90.0}
        assert result[1] == {"periodo": "C2 2024", "promedio": 85.5}
