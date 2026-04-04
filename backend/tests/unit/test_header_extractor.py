"""Unit tests for header extraction."""


from app.application.parsing.extractors.header import extract_header


class TestExtractHeader:
    """Full header extraction from page text."""

    def test_complete_header(self):
        text = (
            "Universidad Cenfotec\n"
            "Evaluación docente: C2 2025\n"
            "Recinto: TODOS, ESC ING DEL SOFTWARE\n"
            "Resultados evaluaciones docentes\n"
            "Profesor: ALVARO CORDERO PEÑA (P000001249)\n"
        )
        h = extract_header(text)
        assert h is not None
        assert h.profesor_nombre == "ALVARO CORDERO PEÑA"
        assert h.profesor_codigo == "P000001249"
        assert h.periodo == "C2 2025"
        assert h.recinto == "TODOS, ESC ING DEL SOFTWARE"

    def test_profesor_without_code(self):
        text = (
            "Evaluación docente: C1 2026\n"
            "Recinto: SEDE CENTRAL\n"
            "Profesor: MARÍA GARCÍA LÓPEZ\n"
        )
        h = extract_header(text)
        assert h is not None
        assert h.profesor_nombre == "MARÍA GARCÍA LÓPEZ"
        assert h.profesor_codigo is None

    def test_missing_profesor_returns_none(self):
        text = (
            "Evaluación docente: C2 2025\n"
            "Recinto: TODOS\n"
        )
        assert extract_header(text) is None

    def test_missing_periodo_returns_none(self):
        text = (
            "Recinto: TODOS\n"
            "Profesor: JUAN PÉREZ (P000)\n"
        )
        assert extract_header(text) is None

    def test_missing_recinto_returns_none(self):
        text = (
            "Evaluación docente: C3 2024\n"
            "Profesor: ANA MORA (P123)\n"
        )
        assert extract_header(text) is None

    def test_evaluacion_with_accent(self):
        text = (
            "Evaluacion docente: C2 2025\n"
            "Recinto: SEDE\n"
            "Profesor: TEST (P1)\n"
        )
        h = extract_header(text)
        assert h is not None
        assert h.periodo == "C2 2025"

    def test_whitespace_trimming(self):
        text = (
            "Evaluación docente:   C2 2025  \n"
            "Recinto:   TODOS, ESC ING DEL SOFTWARE  \n"
            "Profesor:   ALVARO CORDERO PEÑA   (P000001249)  \n"
        )
        h = extract_header(text)
        assert h is not None
        assert h.profesor_nombre == "ALVARO CORDERO PEÑA"
        assert h.periodo == "C2 2025"


class TestExtractHeaderEdgeCases:
    def test_empty_text(self):
        assert extract_header("") is None

    def test_unrelated_text(self):
        assert extract_header("This is not an evaluation PDF at all.") is None

    def test_partial_match_profesor_only(self):
        text = "Profesor: SOLO NOMBRE (X1)\n"
        assert extract_header(text) is None  # missing periodo and recinto
