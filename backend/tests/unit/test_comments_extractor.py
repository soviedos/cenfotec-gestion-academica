"""Unit tests for comments extraction."""


from app.modules.evaluacion_docente.application.parsing.extractors.comments import (
    clean_comment,
    extract_comments,
    parse_section_header,
)

# ── Helpers ─────────────────────────────────────────────────────────────


def _comment_table(rows: list[list[str]]) -> list[list[str | None]]:
    """Build a comment table with the standard header + data rows."""
    return [["Fortalezas", "Mejoras", "Observaciones"], *rows]


# ── Tests: clean_comment ────────────────────────────────────────────────


class TestCleanComment:
    def test_normal_text(self):
        assert clean_comment("Excelente profesor") == "Excelente profesor"

    def test_empty_string(self):
        assert clean_comment("") is None

    def test_none(self):
        assert clean_comment(None) is None

    def test_single_dot(self):
        assert clean_comment(".") is None

    def test_na_variations(self):
        assert clean_comment("N/A") is None
        assert clean_comment("Na") is None
        assert clean_comment("n/a") is None
        assert clean_comment("NA") is None

    def test_apostrophe(self):
        assert clean_comment("'") is None

    def test_dash(self):
        assert clean_comment("-") is None

    def test_no_keyword(self):
        assert clean_comment("no") is None

    def test_ninguna(self):
        assert clean_comment("Ninguna") is None
        assert clean_comment("ninguno") is None

    def test_whitespace_only(self):
        assert clean_comment("   ") is None

    def test_whitespace_around_noise(self):
        assert clean_comment("  N/A  ") is None

    def test_preserves_real_text(self):
        assert clean_comment("  Explica muy bien  ") == "Explica muy bien"

    def test_sin_comentarios(self):
        assert clean_comment("Sin comentarios.") is None


# ── Tests: parse_section_header ─────────────────────────────────────────


class TestParseSectionHeader:
    def test_estudiante_section(self):
        line = "Evaluación Estudiante Profesor -- Fundamentos de Bases de Datos"
        result = parse_section_header(line)
        assert result == ("Estudiante", "Fundamentos de Bases de Datos")

    def test_director_section(self):
        line = "Evaluación Director Profesor -- ESC ING DEL SOFTWARE"
        result = parse_section_header(line)
        assert result == ("Director", "ESC ING DEL SOFTWARE")

    def test_without_accent(self):
        line = "Evaluacion Estudiante Profesor -- Programación"
        result = parse_section_header(line)
        assert result == ("Estudiante", "Programación")

    def test_no_match(self):
        assert parse_section_header("Resultados evaluaciones docentes") is None

    def test_empty_string(self):
        assert parse_section_header("") is None


# ── Tests: extract_comments ─────────────────────────────────────────────


class TestExtractComments:
    def test_single_section(self):
        text = (
            "Resultado cualitativos\n"
            "Evaluación Estudiante Profesor -- Fundamentos de Bases de Datos\n"
            "Fortalezas Mejoras Observaciones\n"
        )
        table = _comment_table([
            ["Excelente profesor", "Entrega tardía de notas", "Todo bien"],
            ["Buen dominio del tema", ".", "N/A"],
        ])
        sections = extract_comments([text], {0: [table]})

        assert len(sections) == 1
        sec = sections[0]
        assert sec.tipo_evaluacion == "Estudiante"
        assert sec.asignatura == "Fundamentos de Bases de Datos"
        assert len(sec.comentarios) == 2

    def test_noise_rows_filtered(self):
        text = "Evaluación Estudiante Profesor -- Test\n"
        table = _comment_table([
            [".", "N/A", "'"],
            [".", "-", "Na"],
        ])
        sections = extract_comments([text], {0: [table]})
        assert len(sections) == 0  # all rows are noise

    def test_partial_noise_preserved(self):
        text = "Evaluación Estudiante Profesor -- Test\n"
        table = _comment_table([
            ["Buen profesor", ".", "N/A"],
        ])
        sections = extract_comments([text], {0: [table]})
        assert len(sections) == 1
        c = sections[0].comentarios[0]
        assert c.fortaleza == "Buen profesor"
        assert c.mejora is None
        assert c.observacion is None

    def test_multiple_sections_same_page(self):
        text = (
            "Evaluación Estudiante Profesor -- Bases de Datos\n"
            "stuff\n"
            "Evaluación Estudiante Profesor -- Programación\n"
        )
        t1 = _comment_table([["F1", "M1", "O1"]])
        t2 = _comment_table([["F2", "M2", "O2"]])
        sections = extract_comments([text], {0: [t1, t2]})
        assert len(sections) == 2

    def test_sections_merged_across_pages(self):
        text_p1 = "Evaluación Estudiante Profesor -- Bases de Datos\n"
        text_p2 = "Evaluación Estudiante Profesor -- Bases de Datos\n"
        t1 = _comment_table([["F1", "M1", "O1"]])
        t2 = _comment_table([["F2", "M2", "O2"]])
        sections = extract_comments([text_p1, text_p2], {0: [t1], 1: [t2]})
        assert len(sections) == 1
        assert len(sections[0].comentarios) == 2

    def test_no_sections_found(self):
        sections = extract_comments(["no anchors here"], {0: []})
        assert sections == []

    def test_director_section(self):
        text = "Evaluación Director Profesor -- ESC ING DEL SOFTWARE\n"
        table = _comment_table([["Fortaleza dir", "Mejora dir", "Obs dir"]])
        sections = extract_comments([text], {0: [table]})
        assert len(sections) == 1
        assert sections[0].tipo_evaluacion == "Director"
