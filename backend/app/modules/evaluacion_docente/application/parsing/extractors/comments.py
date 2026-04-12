"""Comments extractor — qualitative feedback grouped by section.

Handles both *Estudiante* and *Director* evaluation sections.  Each section
is identified by the anchor line::

    Evaluación Estudiante Profesor -- Fundamentos de Bases de Datos

and followed by a table with columns ``Fortalezas | Mejoras | Observaciones``.
"""

from __future__ import annotations

from app.modules.evaluacion_docente.application.parsing.constants import (
    COMMENT_HEADER_MARKERS,
    COMMENT_SECTION_RE,
    NOISE_VALUES,
)
from app.modules.evaluacion_docente.application.parsing.schemas import (
    Comentario,
    SeccionComentarios,
)


def extract_comments(
    pages_text: list[str],
    tables_by_page: dict[int, list[list[list[str | None]]]],
) -> list[SeccionComentarios]:
    """Extract all qualitative-comment sections from the entire document.

    Parameters
    ----------
    pages_text:
        Raw text for each page (index = page number - 1).
    tables_by_page:
        Tables extracted per page via ``page.find_tables()``.
        Key is 0-based page index.

    Returns a list of comment sections, potentially empty.
    """
    sections: list[SeccionComentarios] = []

    for page_idx, text in enumerate(pages_text):
        page_sections = _find_sections_in_text(text)
        page_tables = tables_by_page.get(page_idx, [])

        comment_tables = _pick_comment_tables(page_tables)

        if page_sections and comment_tables:
            # Classic path: pair detected anchors with detected tables
            for tipo, asignatura in page_sections:
                if comment_tables:
                    table = comment_tables.pop(0)
                    comentarios = _parse_comment_table(table)
                else:
                    comentarios = []

                if comentarios:
                    sections.append(
                        SeccionComentarios(
                            tipo_evaluacion=tipo,
                            asignatura=asignatura,
                            comentarios=comentarios,
                        )
                    )
        elif comment_tables:
            # Wrapped layout: section header is embedded inside the table
            for table in comment_tables:
                header_info = _extract_section_from_table(table)
                comentarios = _parse_comment_table(table)
                if header_info and comentarios:
                    sections.append(
                        SeccionComentarios(
                            tipo_evaluacion=header_info[0],
                            asignatura=header_info[1],
                            comentarios=comentarios,
                        )
                    )

    return _merge_sections(sections)


# ── Section detection ───────────────────────────────────────────────────


def _find_sections_in_text(text: str) -> list[tuple[str, str]]:
    """Find all ``Evaluación X Profesor -- Asignatura`` anchors in page text."""
    results: list[tuple[str, str]] = []
    for m in COMMENT_SECTION_RE.finditer(text):
        tipo = m.group(1).capitalize()  # Normalize to "Estudiante" / "Director"
        asignatura = m.group(2).strip()
        results.append((tipo, asignatura))
    return results


def _extract_section_from_table(rows: list[list[str | None]]) -> tuple[str, str] | None:
    """Try to extract the section header from within the first rows of a table.

    Handles wrapped tables where the section header (e.g.
    ``Evaluación Estudiante Profesor -- Asignatura``) is embedded in one
    of the early rows of the table itself.
    """
    for row in rows[:4]:
        for cell in row:
            if cell is None:
                continue
            result = parse_section_header(cell)
            if result:
                return result
    return None


# ── Table filtering ─────────────────────────────────────────────────────


def _pick_comment_tables(tables: list[list[list[str | None]]]) -> list[list[list[str | None]]]:
    """Filter tables that look like comment tables (have Fortalezas/Mejoras header)."""
    result: list[list[list[str | None]]] = []
    for table in tables:
        if _is_comment_table(table):
            result.append(table)
    return result


def _is_comment_table(rows: list[list[str | None]]) -> bool:
    """Check if any of the first rows contains the comment column headers.

    Handles two layouts:
    - Classic: row 0 = [Fortalezas, Mejoras, Observaciones]
    - Wrapped: row 0 = 'Resultado cualitativos', row 1 = section header,
              row 2 = [Fortalezas, Mejoras, Observaciones]
    """
    if not rows:
        return False
    # Check the first few rows (up to 4) for the header markers
    for row in rows[:4]:
        header_cells = {_clean(c) for c in row}
        if header_cells & COMMENT_HEADER_MARKERS:
            return True
    return False


# ── Row parsing ─────────────────────────────────────────────────────────


def _find_header_row_index(rows: list[list[str | None]]) -> int:
    """Find the index of the Fortalezas/Mejoras/Observaciones header row."""
    for i, row in enumerate(rows[:4]):
        header_cells = {_clean(c) for c in row}
        if header_cells & COMMENT_HEADER_MARKERS:
            return i
    return 0  # fallback to first row


def _parse_comment_table(rows: list[list[str | None]]) -> list[Comentario]:
    """Parse a 3-column comment table, skipping everything up to and including the header."""
    header_idx = _find_header_row_index(rows)
    comentarios: list[Comentario] = []
    for row in rows[header_idx + 1:]:
        cells = [_clean(c) for c in row]
        # Ensure at least 3 columns
        while len(cells) < 3:
            cells.append("")

        fortaleza = clean_comment(cells[0])
        mejora = clean_comment(cells[1])
        observacion = clean_comment(cells[2])

        # Skip rows where all three are empty/noise
        if fortaleza is None and mejora is None and observacion is None:
            continue

        comentarios.append(
            Comentario(fortaleza=fortaleza, mejora=mejora, observacion=observacion)
        )
    return comentarios


# ── Merge split sections ────────────────────────────────────────────────


def _merge_sections(sections: list[SeccionComentarios]) -> list[SeccionComentarios]:
    """Merge sections with the same (tipo, asignatura) split across pages."""
    merged: dict[tuple[str, str], SeccionComentarios] = {}
    for sec in sections:
        key = (sec.tipo_evaluacion, sec.asignatura)
        if key in merged:
            merged[key].comentarios.extend(sec.comentarios)
        else:
            merged[key] = SeccionComentarios(
                tipo_evaluacion=sec.tipo_evaluacion,
                asignatura=sec.asignatura,
                comentarios=list(sec.comentarios),
            )
    return list(merged.values())


# ── Public helpers ──────────────────────────────────────────────────────


def clean_comment(value: str | None) -> str | None:
    """Normalize a comment cell.  Returns ``None`` for noise/empty values."""
    if value is None:
        return None
    stripped = value.strip()
    if not stripped:
        return None
    if stripped.lower() in NOISE_VALUES:
        return None
    return stripped


def parse_section_header(line: str) -> tuple[str, str] | None:
    """Parse a comment section header line.

    Returns ``(tipo_evaluacion, asignatura)`` or ``None``.
    """
    m = COMMENT_SECTION_RE.search(line)
    if not m:
        return None
    return m.group(1).capitalize(), m.group(2).strip()


# ── Internal helpers ────────────────────────────────────────────────────


def _clean(cell: str | None) -> str:
    if cell is None:
        return ""
    return cell.strip()
