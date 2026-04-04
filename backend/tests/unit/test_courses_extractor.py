"""Unit tests for courses extraction from table data."""

import pytest

from app.application.parsing.extractors.courses import (
    extract_courses,
    is_subtotal_row,
    parse_total_estudiantes,
)

# ── Helpers ─────────────────────────────────────────────────────────────

COURSE_HEADER = [
    "Código\nasignatura", "Nombre asignatura", "Total\nestudiantes",
    "Grupo", "Estudiante", "Director", "Autoevaluación\n(docente)", "Promedio\ngeneral",
]


def _make_course_table(escuela: str = "ESC ING DEL SOFTWARE"):
    return [
        [escuela, None, None, None, None, None, None, None],
        COURSE_HEADER,
        ["INF-02", "Fundamentos de\nProgramación", "13 / 15", "SCV0",
         "92.75", "100.00", "82.60", "91.78"],
        ["INF-03", "Fundamentos de\nBases de Datos", "17 / 19", "SCV1",
         "94.94", "100.00", "81.20", "92.05"],
        # Subtotal row
        [None, None, "54 / 62", None, "93.99", "100.00", "81.95", "91.98"],
    ]


# ── Tests ───────────────────────────────────────────────────────────────


class TestParseTotalEstudiantes:
    def test_normal(self):
        assert parse_total_estudiantes("13 / 15") == (13, 15)

    def test_large_numbers(self):
        assert parse_total_estudiantes("72 / 81") == (72, 81)

    def test_no_match(self):
        assert parse_total_estudiantes("not a fraction") == (None, None)

    def test_empty_string(self):
        assert parse_total_estudiantes("") == (None, None)

    def test_single_digit(self):
        assert parse_total_estudiantes("5 / 8") == (5, 8)


class TestIsSubtotalRow:
    def test_subtotal_row(self):
        row = [None, None, "54 / 62", None, "93.99", "100.00", "81.95", "91.98"]
        assert is_subtotal_row(row) is True

    def test_course_row(self):
        row = ["INF-02", "Fundamentos", "13 / 15", "SCV0", "92.75", "100.00", "82.60", "91.78"]
        assert is_subtotal_row(row) is False

    def test_empty_row(self):
        assert is_subtotal_row([]) is True

    def test_non_code_text(self):
        row = ["Promedios\ngenerales", None, "72 / 81"]
        assert is_subtotal_row(row) is True  # no hyphen, not a course code


class TestExtractCourses:
    def test_basic_course_table(self):
        table = _make_course_table()
        cursos, total_resp, total_mat = extract_courses([table])

        assert len(cursos) == 2
        assert cursos[0].codigo == "INF-02"
        assert cursos[0].nombre == "Fundamentos de\nProgramación"
        assert cursos[0].estudiantes_respondieron == 13
        assert cursos[0].estudiantes_matriculados == 15
        assert cursos[0].grupo == "SCV0"
        assert cursos[0].pct_estudiante == pytest.approx(92.75)
        assert cursos[0].escuela == "ESC ING DEL SOFTWARE"

    def test_totals_computed(self):
        table = _make_course_table()
        _, total_resp, total_mat = extract_courses([table])
        assert total_resp == 30  # 13 + 17
        assert total_mat == 34   # 15 + 19

    def test_multiple_school_tables(self):
        t1 = _make_course_table("ESC ING DEL SOFTWARE")
        t2 = [
            ["ESC SIST DE INFORMACIÓN", None, None, None, None, None, None, None],
            COURSE_HEADER,
            ["COMP-01", "Procesos\nEmpresariales", "18 / 19", "NCV2",
             "93.50", "100.00", "81.40", "91.63"],
        ]
        cursos, _, _ = extract_courses([t1, t2])
        assert len(cursos) == 3
        escuelas = {c.escuela for c in cursos}
        assert "ESC ING DEL SOFTWARE" in escuelas
        assert "ESC SIST DE INFORMACIÓN" in escuelas

    def test_subtotal_rows_skipped(self):
        table = _make_course_table()
        cursos, _, _ = extract_courses([table])
        codes = [c.codigo for c in cursos]
        assert all("-" in code for code in codes)

    def test_empty_tables(self):
        cursos, total_resp, total_mat = extract_courses([])
        assert cursos == []
        assert total_resp == 0
        assert total_mat == 0

    def test_unrelated_table_skipped(self):
        unrelated = [["A", "B"], ["C", "D"]]
        cursos, _, _ = extract_courses([unrelated])
        assert cursos == []

    def test_school_detected_from_preceding_row(self):
        table = [
            ["ESC TESTING", None, None, None, None, None, None, None],
            COURSE_HEADER,
            ["TST-01", "Test Course", "5 / 10", "G1", "90.00", "100.00", "80.00", "90.00"],
        ]
        cursos, _, _ = extract_courses([table])
        assert cursos[0].escuela == "ESC TESTING"
