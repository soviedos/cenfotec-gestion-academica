"""Courses extractor — course/group rows from the per-school tables.

Operates on pre-extracted table data from PyMuPDF ``page.find_tables()``.
Tables span page 2 (and possibly continuation pages) grouped by school.
"""

from __future__ import annotations

from app.modules.evaluacion_docente.application.parsing.constants import TOTAL_ESTUDIANTES_RE
from app.modules.evaluacion_docente.application.parsing.schemas import CursoGrupo

# ── Code-prefix → Escuela mapping ──────────────────────────────────────

_PREFIX_ESCUELA: dict[str, str] = {
    "SOFT": "Ingeniería del Software",
    "BISOFT": "Ingeniería del Software",
    "TSOFT": "Ingeniería del Software",
    "PSWE": "Ingeniería del Software",
    "INF": "Tecnologías de Información",
    "TINF": "Tecnologías de Información",
    "BITIC": "Tecnologías de Información",
    "SINF": "Sistemas de Información",
    "SINT": "Sistemas de Información",
    "DIWEB": "Diseño Web",
    "TWEB": "Diseño Web",
    "COMP": "Computación",
    "CIB": "Ciberseguridad",
    "FUN": "Fundamentos",
    "PIA": "Fundamentos",
}


def extract_courses(
    tables: list[list[list[str | None]]],
) -> tuple[list[CursoGrupo], int, int]:
    """Extract course rows from all tables that look like course tables.

    Returns ``(courses, total_respondieron, total_matriculados)``.
    """
    cursos: list[CursoGrupo] = []
    total_resp = 0
    total_mat = 0

    for table in tables:
        result = _try_parse_course_table(table)
        if result:
            cursos.extend(result)

    for c in cursos:
        total_resp += c.estudiantes_respondieron
        total_mat += c.estudiantes_matriculados

    return cursos, total_resp, total_mat


def _try_parse_course_table(rows: list[list[str | None]]) -> list[CursoGrupo] | None:
    """Attempt to interpret *rows* as a course table.

    A course table is identified by having a header row containing
    ``"Código"`` (or ``"Código asignatura"``) in the first cell.
    """
    if not rows:
        return None

    # Find header row
    header_idx = _find_header_row(rows)
    if header_idx is None:
        return None

    # Determine current school from text above the header
    escuela = _detect_school(rows, header_idx)

    cursos: list[CursoGrupo] = []
    for row in rows[header_idx + 1 :]:
        curso = _parse_course_row(row, escuela)
        if curso:
            cursos.append(curso)

    return cursos if cursos else None


def _find_header_row(rows: list[list[str | None]]) -> int | None:
    for i, row in enumerate(rows):
        first = _clean(row[0]) if row else ""
        if "Código" in first or "Codigo" in first:
            return i
    return None


def _detect_school(rows: list[list[str | None]], header_idx: int) -> str:
    """Look backwards from header for a row that's a school name.

    School names are typically single-cell rows like ``"ESC ING DEL SOFTWARE"``.
    Falls back to ``"DESCONOCIDA"`` — the caller may refine via code prefix.
    """
    for i in range(header_idx - 1, -1, -1):
        text = _clean(rows[i][0]) if rows[i] else ""
        if text and text.startswith("ESC "):
            return text
    return "DESCONOCIDA"


def _escuela_from_codigo(codigo: str) -> str | None:
    """Derive escuela from course code prefix (e.g. ``SOFT-09`` → ``Ingeniería del Software``)."""
    prefix = codigo.split("-")[0] if "-" in codigo else ""
    return _PREFIX_ESCUELA.get(prefix)


def _parse_course_row(row: list[str | None], escuela: str) -> CursoGrupo | None:
    """Parse a single course data row.

    Expected layout (7+ columns)::

        [código, nombre, total_est, grupo, est%, dir%, auto%, prom%]

    Subtotal/summary rows (no código) are skipped.
    """
    cells = [_clean(c) for c in row]
    if len(cells) < 7:
        return None

    codigo = cells[0]
    if not codigo or not _looks_like_course_code(codigo):
        return None

    nombre = cells[1].replace("\n", " ")
    resp, mat = parse_total_estudiantes(cells[2])
    if resp is None:
        return None

    grupo = cells[3]
    pct_est = _safe_float(cells[4])
    pct_dir = _safe_float(cells[5])
    pct_auto = _safe_float(cells[6])
    pct_prom = _safe_float(cells[7]) if len(cells) > 7 else None

    if pct_est is None or pct_dir is None or pct_auto is None:
        return None

    # Prefer escuela from code prefix over table-level detection
    resolved_escuela = _escuela_from_codigo(codigo) or escuela

    return CursoGrupo(
        escuela=resolved_escuela,
        codigo=codigo,
        nombre=nombre,
        estudiantes_respondieron=resp,
        estudiantes_matriculados=mat,
        grupo=grupo,
        pct_estudiante=pct_est,
        pct_director=pct_dir,
        pct_autoevaluacion=pct_auto,
        pct_promedio_general=pct_prom if pct_prom is not None else 0.0,
    )


# ── Public helpers ──────────────────────────────────────────────────────


def parse_total_estudiantes(value: str) -> tuple[int | None, int | None]:
    """Parse ``'13 / 15'`` into ``(13, 15)``."""
    m = TOTAL_ESTUDIANTES_RE.search(value)
    if not m:
        return None, None
    try:
        return int(m.group(1)), int(m.group(2))
    except ValueError:
        return None, None


def is_subtotal_row(row: list[str | None]) -> bool:
    """True if the row has no course code (first cell empty/None)."""
    first = _clean(row[0]) if row else ""
    return not first or not _looks_like_course_code(first)


# ── Internal helpers ────────────────────────────────────────────────────


def _looks_like_course_code(value: str) -> bool:
    """Course codes contain a hyphen: INF-02, SOFT-01, COMP-01."""
    return "-" in value and len(value) <= 20


def _safe_float(value: str | None) -> float | None:
    if not value:
        return None
    try:
        return float(value.strip())
    except ValueError:
        return None


def _clean(cell: str | None) -> str:
    if cell is None:
        return ""
    return cell.strip()
