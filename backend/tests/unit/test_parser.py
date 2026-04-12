"""Integration tests for the full parser pipeline.

These tests use real (but minimal) PDF bytes created with PyMuPDF
to exercise the complete parse_evaluacion() flow without relying
on golden-file fixtures.
"""

import fitz  # PyMuPDF

from app.modules.evaluacion_docente.application.parsing.parser import parse_evaluacion

# ── Helper: build a minimal evaluation PDF ──────────────────────────────


def _build_minimal_pdf() -> bytes:
    """Create a 2-page PDF that mimics the CENFOTEC evaluation structure.

    Page 1: header + metrics table
    Page 2: course table + comments table
    """
    doc = fitz.open()

    # ── Page 1: header text + metrics table ──────────────────────────
    page1 = doc.new_page(width=595, height=842)

    header_text = (
        "Universidad Cenfotec\n"
        "Evaluación docente: C2 2025\n"
        "Recinto: TODOS, ESC ING DEL SOFTWARE\n"
        "Resultados evaluaciones docentes\n"
        "Profesor: JUAN PÉREZ MORA (P000099)\n"
    )
    page1.insert_text((50, 50), header_text, fontsize=10)

    # Insert metrics table as a real PDF table (using a simple grid)
    _insert_table(page1, y_start=160, rows=[
        ["Dimensiones", "Estudiante", "", "Director", "",
         "Autoevaluación\n(docente)", "", "Promedio\ngeneral", ""],
        ["", "Puntos", "%", "Puntos", "%", "Puntos", "%", "Puntos", "%"],
        ["METODOLOGÍA", "18.00 / 20.00", "90.00", "10.00 / 10.00", "100.00",
         "16.00 / 20.00", "80.00", "14.67", "90.00"],
        ["Dominio", "19.00 / 20.00", "95.00", "20.00 / 20.00", "100.00",
         "17.00 / 20.00", "85.00", "18.67", "93.33"],
        ["CUMPLIMIENTO", "18.00 / 20.00", "90.00", "40.00 / 40.00", "100.00",
         "22.00 / 25.00", "88.00", "26.67", "92.67"],
        ["ESTRATEGIA", "19.00 / 20.00", "95.00", "10.00 / 10.00", "100.00",
         "17.00 / 20.00", "85.00", "15.33", "93.33"],
        ["GENERAL", "18.00 / 20.00", "90.00", "20.00 / 20.00", "100.00",
         "9.00 / 15.00", "60.00", "15.67", "83.33"],
        ["", "92.00", "", "100.00", "", "79.60", "", "", "90.53"],
    ])

    footer1 = "1 de 2"
    page1.insert_text((500, 830), footer1, fontsize=8)

    # ── Page 2: course table + comments ──────────────────────────────
    page2 = doc.new_page(width=595, height=842)

    _insert_table(page2, y_start=50, rows=[
        ["ESC ING DEL SOFTWARE", "", "", "", "", "", "", ""],
        ["Código\nasignatura", "Nombre asignatura", "Total\nestudiantes",
         "Grupo", "Estudiante", "Director", "Autoevaluación\n(docente)",
         "Promedio\ngeneral"],
        ["INF-02", "Fundamentos de Programación", "13 / 15", "SCV0",
         "92.75", "100.00", "82.60", "91.78"],
    ])

    # Comment section (use text + table)
    comment_anchor = "Evaluación Estudiante Profesor -- Fundamentos de Programación"
    page2.insert_text((50, 350), comment_anchor, fontsize=9)

    _insert_table(page2, y_start=370, rows=[
        ["Fortalezas", "Mejoras", "Observaciones"],
        ["Excelente profesor", "Entrega tardía", "Todo bien"],
        ["Buen dominio", ".", "N/A"],
    ])

    footer2 = "2 de 2"
    page2.insert_text((500, 830), footer2, fontsize=8)

    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def _insert_table(page: fitz.Page, y_start: float, rows: list[list[str]]) -> None:
    """Insert rows as text lines on the page for table extraction.

    NOTE: PyMuPDF's find_tables() works best with actual table structures.
    For unit testing we create text-based grids.  Real PDFs will have proper
    table structures.  Here we just place text so the extractors can work
    on the text-based fallback.
    """
    y = y_start
    for row in rows:
        x = 50
        for cell in row:
            if cell:
                # Truncate long text
                display = cell[:30] if len(cell) > 30 else cell
                page.insert_text((x, y), display, fontsize=7)
            x += 60
        y += 14


# ── Tests ───────────────────────────────────────────────────────────────


class TestParseEvaluacionWithCorruptPdf:
    def test_corrupt_bytes(self):
        result = parse_evaluacion(b"this is not a PDF")
        assert result.success is False
        assert any(e.code == "CORRUPT_PDF" for e in result.errors)

    def test_empty_bytes(self):
        result = parse_evaluacion(b"")
        assert result.success is False
        assert any(e.code == "CORRUPT_PDF" for e in result.errors)


class TestParseEvaluacionWithEmptyPdf:
    def test_pdf_without_text(self):
        """A valid PDF with a blank page has no text."""
        doc = fitz.open()
        doc.new_page()
        pdf_bytes = doc.tobytes()
        doc.close()

        result = parse_evaluacion(pdf_bytes)
        assert result.success is False
        assert any(e.code == "NO_TEXT_CONTENT" for e in result.errors)


class TestParseEvaluacionWithMissingHeader:
    def test_no_header_fields(self):
        """A PDF with text but no recognizable header."""
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((50, 50), "This is not an evaluation document.")
        pdf_bytes = doc.tobytes()
        doc.close()

        result = parse_evaluacion(pdf_bytes)
        assert result.success is False
        assert any(e.code == "MISSING_HEADER_FIELDS" for e in result.errors)


class TestParseEvaluacionMetadata:
    def test_metadata_on_failure(self):
        result = parse_evaluacion(b"not a pdf")
        assert result.metadata.parser_version == "1.0.0"
        assert result.metadata.processing_time_ms >= 0

    def test_metadata_on_empty_pdf(self):
        doc = fitz.open()
        doc.new_page()
        result = parse_evaluacion(doc.tobytes())
        doc.close()
        assert result.metadata.pages_processed == 1
