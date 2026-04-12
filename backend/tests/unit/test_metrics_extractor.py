"""Unit tests for metrics extraction from table data."""

import pytest

from app.modules.evaluacion_docente.application.parsing.extractors.metrics import (
    extract_metrics,
    parse_puntos,
)

# ── Helpers ─────────────────────────────────────────────────────────────

HEADER_ROW = [
    "Dimensiones", "Estudiante", "", "Director", "",
    "Autoevaluación\n(docente)", "", "Promedio\ngeneral", "",
]
SUBHEADER_ROW = ["", "Puntos", "%", "Puntos", "%", "Puntos", "%", "Puntos", "%"]

METODOLOGIA_ROW = [
    "METODOLOGÍA", "18.61 / 20.00", "93.05", "10.00 / 10.00", "100.00",
    "16.00 / 20.00", "80.00", "14.87", "91.02",
]
DOMINIO_ROW = [
    "Dominio", "19.57 / 20.00", "97.86", "20.00 / 20.00", "100.00",
    "17.95 / 20.00", "89.75", "19.17", "95.87",
]
CUMPLIMIENTO_ROW = [
    "CUMPLIMIENTO", "18.60 / 20.00", "92.98", "40.00 / 40.00", "100.00",
    "22.00 / 25.00", "88.00", "26.87", "93.66",
]
ESTRATEGIA_ROW = [
    "ESTRATEGIA", "18.94 / 20.00", "94.69", "10.00 / 10.00", "100.00",
    "17.00 / 20.00", "85.00", "15.31", "93.23",
]
GENERAL_ROW = [
    "GENERAL", "18.27 / 20.00", "91.36", "20.00 / 20.00", "100.00",
    "9.00 / 15.00", "60.00", "15.76", "83.79",
]
SUMMARY_ROW = ["", "93.99", "", "100.00", "", "81.95", "", "", "91.98"]


def _make_metrics_table():
    return [
        HEADER_ROW,
        SUBHEADER_ROW,
        METODOLOGIA_ROW,
        DOMINIO_ROW,
        CUMPLIMIENTO_ROW,
        ESTRATEGIA_ROW,
        GENERAL_ROW,
        SUMMARY_ROW,
    ]


# ── Tests ───────────────────────────────────────────────────────────────


class TestParsePuntos:
    def test_normal_fraction(self):
        assert parse_puntos("18.61 / 20.00") == (18.61, 20.0)

    def test_integer_fraction(self):
        assert parse_puntos("40.00 / 40.00") == (40.0, 40.0)

    def test_small_fraction(self):
        assert parse_puntos("9.00 / 15.00") == (9.0, 15.0)

    def test_no_match(self):
        assert parse_puntos("not a fraction") is None

    def test_empty_string(self):
        assert parse_puntos("") is None


class TestExtractMetrics:
    def test_full_table(self):
        table = _make_metrics_table()
        dims, summary = extract_metrics([table])

        assert len(dims) == 5
        assert dims[0].nombre == "METODOLOGÍA"
        assert dims[0].estudiante.puntos_obtenidos == pytest.approx(18.61)
        assert dims[0].estudiante.puntos_maximos == pytest.approx(20.0)
        assert dims[0].estudiante.porcentaje == pytest.approx(93.05)
        assert dims[0].promedio_general_pct == pytest.approx(91.02)

    def test_summary_row(self):
        table = _make_metrics_table()
        _, summary = extract_metrics([table])

        assert summary is not None
        assert summary.estudiante == pytest.approx(93.99)
        assert summary.director == pytest.approx(100.0)
        assert summary.autoevaluacion == pytest.approx(81.95)
        assert summary.promedio_general == pytest.approx(91.98)

    def test_all_dimensions_present(self):
        table = _make_metrics_table()
        dims, _ = extract_metrics([table])
        names = {d.nombre for d in dims}
        assert names == {"METODOLOGÍA", "Dominio", "CUMPLIMIENTO", "ESTRATEGIA", "GENERAL"}

    def test_dominio_row(self):
        table = _make_metrics_table()
        dims, _ = extract_metrics([table])
        dominio = next(d for d in dims if d.nombre == "Dominio")
        assert dominio.director.porcentaje == pytest.approx(100.0)
        assert dominio.autoevaluacion.porcentaje == pytest.approx(89.75)

    def test_general_low_autoeval(self):
        table = _make_metrics_table()
        dims, _ = extract_metrics([table])
        general = next(d for d in dims if d.nombre == "GENERAL")
        assert general.autoevaluacion.porcentaje == pytest.approx(60.0)

    def test_empty_tables(self):
        dims, summary = extract_metrics([])
        assert dims == []
        assert summary is None

    def test_unrelated_table_skipped(self):
        unrelated = [["Código", "Nombre", "Total"], ["INF-02", "Prog", "13 / 15"]]
        dims, _ = extract_metrics([unrelated])
        assert dims == []

    def test_multiple_tables_finds_correct_one(self):
        unrelated = [["foo", "bar"], ["baz", "qux"]]
        metrics = _make_metrics_table()
        dims, _ = extract_metrics([unrelated, metrics])
        assert len(dims) == 5

    def test_row_with_too_few_cells_skipped(self):
        table = [
            HEADER_ROW,
            ["METODOLOGÍA", "18.61 / 20.00"],  # only 2 cells
        ]
        dims, _ = extract_metrics([table])
        assert dims == []
