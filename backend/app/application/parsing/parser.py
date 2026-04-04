"""PDF Parser orchestrator — the main entry point.

Usage::

    from app.application.parsing import parse_evaluacion

    result = parse_evaluacion(pdf_bytes)
    if result.success:
        data = result.data  # ParsedEvaluacion
    else:
        for err in result.errors:
            print(err.stage, err.code, err.message)
"""

from __future__ import annotations

import time

import fitz  # PyMuPDF

from app.application.parsing.constants import PARSER_VERSION
from app.application.parsing.errors import ParseError, ParseMetadata, ParseResult, ParseWarning
from app.application.parsing.extractors.comments import extract_comments
from app.application.parsing.extractors.courses import extract_courses
from app.application.parsing.extractors.header import extract_header
from app.application.parsing.extractors.metrics import extract_metrics
from app.application.parsing.schemas import ParsedEvaluacion


def parse_evaluacion(pdf_bytes: bytes) -> ParseResult:
    """Parse a CENFOTEC teacher-evaluation PDF into structured data.

    This function **never raises** — it always returns a ``ParseResult``
    with either ``success=True`` and populated ``data``, or ``success=False``
    with a list of errors describing what went wrong.
    """
    start = time.monotonic()
    errors: list[ParseError] = []
    warnings: list[ParseWarning] = []

    # ── E1: Open document ───────────────────────────────────────────
    doc = _open_document(pdf_bytes, errors)
    if doc is None:
        return _fail(errors, warnings, start)

    num_pages = len(doc)
    pages_text = [doc[i].get_text("text") for i in range(num_pages)]
    total_tables = 0

    # Validate text content
    if not any(t.strip() for t in pages_text):
        errors.append(
            ParseError(
                stage="open",
                code="NO_TEXT_CONTENT",
                message="El PDF no contiene texto extraíble (posiblemente escaneado)",
            )
        )
        doc.close()
        return _fail(errors, warnings, start, pages_processed=num_pages)

    # ── E2: Header extraction ───────────────────────────────────────
    header = extract_header(pages_text[0])
    if header is None:
        errors.append(
            ParseError(
                stage="header",
                code="MISSING_HEADER_FIELDS",
                message="No se pudo extraer profesor, periodo o recinto de la página 1",
                context={"page": 1, "text_preview": pages_text[0][:200]},
            )
        )
        doc.close()
        return _fail(errors, warnings, start, pages_processed=num_pages)

    # ── E3: Metrics (page 1 tables) ────────────────────────────────
    page1_tables = _extract_tables(doc[0])
    total_tables += len(page1_tables)

    dimensiones, resumen_pct = extract_metrics(page1_tables)
    if not dimensiones:
        errors.append(
            ParseError(
                stage="metricas",
                code="NO_DIMENSIONS_FOUND",
                message="No se encontró la tabla de dimensiones en la página 1",
                context={"tables_found_page1": len(page1_tables)},
            )
        )
        doc.close()
        return _fail(errors, warnings, start, pages_processed=num_pages)

    if resumen_pct is None:
        warnings.append(
            ParseWarning(
                code="MISSING_SUMMARY_ROW",
                message="No se encontró la fila de resumen de porcentajes",
            )
        )
        # Build a fallback from dimension averages
        from app.application.parsing.schemas import ResumenPorcentajes

        resumen_pct = ResumenPorcentajes(
            estudiante=_avg([d.estudiante.porcentaje for d in dimensiones]),
            director=_avg([d.director.porcentaje for d in dimensiones]),
            autoevaluacion=_avg([d.autoevaluacion.porcentaje for d in dimensiones]),
            promedio_general=_avg([d.promedio_general_pct for d in dimensiones]),
        )

    # ── E4: Courses (page 2+ tables) ───────────────────────────────
    all_tables_post_p1: list[list[list[str | None]]] = []
    for i in range(1, num_pages):
        tbls = _extract_tables(doc[i])
        total_tables += len(tbls)
        all_tables_post_p1.extend(tbls)

    cursos, total_resp, total_mat = extract_courses(all_tables_post_p1)
    if not cursos:
        errors.append(
            ParseError(
                stage="cursos",
                code="NO_COURSES_FOUND",
                message="No se encontraron tablas de cursos/grupos",
                context={"tables_found_total": total_tables},
            )
        )
        doc.close()
        return _fail(errors, warnings, start, pages_processed=num_pages)

    # ── E5: Qualitative comments ───────────────────────────────────
    tables_by_page: dict[int, list[list[list[str | None]]]] = {}
    for i in range(num_pages):
        tables_by_page[i] = _extract_tables(doc[i])
        total_tables += len(tables_by_page[i])

    secciones = extract_comments(pages_text, tables_by_page)
    comment_sections_count = len(secciones)

    if not secciones:
        warnings.append(
            ParseWarning(
                code="NO_COMMENT_SECTIONS",
                message="No se encontraron secciones de comentarios cualitativos",
            )
        )

    # ── E6: Validate and build result ──────────────────────────────
    for curso in cursos:
        if curso.estudiantes_respondieron > curso.estudiantes_matriculados:
            warnings.append(
                ParseWarning(
                    code="RESPONDED_GT_ENROLLED",
                    message=(
                        f"Curso {curso.codigo}: respondieron ({curso.estudiantes_respondieron}) "
                        f"> matriculados ({curso.estudiantes_matriculados})"
                    ),
                    context={"curso": curso.codigo},
                )
            )

    parsed = ParsedEvaluacion(
        header=header,
        dimensiones=dimensiones,
        resumen_pct=resumen_pct,
        cursos=cursos,
        total_respondieron=total_resp,
        total_matriculados=total_mat,
        secciones_comentarios=secciones,
    )

    elapsed_ms = (time.monotonic() - start) * 1000

    # Detect declared total pages from footer
    total_declared = _detect_total_pages(pages_text)

    doc.close()

    return ParseResult(
        success=True,
        data=parsed,
        errors=[],
        warnings=warnings,
        metadata=ParseMetadata(
            parser_version=PARSER_VERSION,
            pages_processed=len(pages_text),
            total_pages_declared=total_declared,
            tables_found=total_tables,
            comment_sections_found=comment_sections_count,
            processing_time_ms=round(elapsed_ms, 2),
        ),
    )


# ── Internal helpers ────────────────────────────────────────────────────


def _open_document(pdf_bytes: bytes, errors: list[ParseError]) -> fitz.Document | None:
    """Open raw bytes as a PyMuPDF document, appending errors on failure."""
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as exc:
        errors.append(
            ParseError(
                stage="open",
                code="CORRUPT_PDF",
                message=f"No se pudo abrir el PDF: {exc}",
            )
        )
        return None

    if len(doc) == 0:
        errors.append(
            ParseError(stage="open", code="EMPTY_PDF", message="El PDF tiene 0 páginas")
        )
        doc.close()
        return None

    return doc


def _extract_tables(page: fitz.Page) -> list[list[list[str | None]]]:
    """Extract all tables from a page as lists of rows of cells."""
    try:
        finder = page.find_tables()
        return [t.extract() for t in finder.tables]
    except Exception:
        return []


def _detect_total_pages(pages_text: list[str]) -> int | None:
    """Try to read 'X de Y' from the last page footer."""
    from app.application.parsing.constants import FOOTER_PAGE_RE

    for text in reversed(pages_text):
        m = FOOTER_PAGE_RE.search(text)
        if m:
            try:
                return int(m.group(2))
            except ValueError:
                pass
    return None


def _avg(values: list[float]) -> float:
    return round(sum(values) / len(values), 2) if values else 0.0


def _fail(
    errors: list[ParseError],
    warnings: list[ParseWarning],
    start: float,
    pages_processed: int = 0,
) -> ParseResult:
    elapsed_ms = (time.monotonic() - start) * 1000
    return ParseResult(
        success=False,
        data=None,
        errors=errors,
        warnings=warnings,
        metadata=ParseMetadata(
            parser_version=PARSER_VERSION,
            pages_processed=pages_processed,
            processing_time_ms=round(elapsed_ms, 2),
        ),
    )
