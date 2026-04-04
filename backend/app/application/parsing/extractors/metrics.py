"""Metrics extractor — dimension scores from the summary table.

Operates on pre-extracted table data (``list[list[str | None]]``) produced
by ``page.find_tables()`` from PyMuPDF.
"""

from __future__ import annotations

from app.application.parsing.constants import KNOWN_DIMENSIONS, PUNTOS_RE
from app.application.parsing.schemas import DimensionMetrica, FuentePuntaje, ResumenPorcentajes


def extract_metrics(
    tables: list[list[list[str | None]]],
) -> tuple[list[DimensionMetrica], ResumenPorcentajes | None]:
    """Find the dimensions table and extract all rows.

    Parameters
    ----------
    tables:
        All tables extracted from page 1 via ``page.find_tables()``.
        Each table is a list of rows, each row a list of cell strings.

    Returns a tuple of (dimensions, summary).  Either may be empty/None
    if the table is not found.
    """
    for table in tables:
        dims, summary = _try_parse_metrics_table(table)
        if dims:
            return dims, summary
    return [], None


def _try_parse_metrics_table(
    rows: list[list[str | None]],
) -> tuple[list[DimensionMetrica], ResumenPorcentajes | None]:
    """Attempt to interpret *rows* as the dimensions summary table."""
    dimensiones: list[DimensionMetrica] = []
    summary: ResumenPorcentajes | None = None

    for row in rows:
        cells = [_clean(c) for c in row]
        if not cells or not cells[0]:
            # Could be the summary row — all numbers, first cell empty
            summary = _try_parse_summary_row(cells)
            continue

        if cells[0] in KNOWN_DIMENSIONS:
            dim = _parse_dimension_row(cells)
            if dim:
                dimensiones.append(dim)

    return dimensiones, summary


def _parse_dimension_row(cells: list[str]) -> DimensionMetrica | None:
    """Parse one dimension row into a ``DimensionMetrica``.

    Expected cell layout (9 columns)::

        [name, est_pts, est_%, dir_pts, dir_%, auto_pts, auto_%, prom_pts, prom_%]
    """
    if len(cells) < 9:
        return None

    nombre = cells[0]
    est = _parse_fuente(cells[1], cells[2])
    director = _parse_fuente(cells[3], cells[4])
    auto = _parse_fuente(cells[5], cells[6])
    prom_pts = _safe_float(cells[7])
    prom_pct = _safe_float(cells[8])

    if not est or not director or not auto or prom_pts is None or prom_pct is None:
        return None

    return DimensionMetrica(
        nombre=nombre,
        estudiante=est,
        director=director,
        autoevaluacion=auto,
        promedio_general_puntos=prom_pts,
        promedio_general_pct=prom_pct,
    )


def _parse_fuente(puntos_cell: str, pct_cell: str) -> FuentePuntaje | None:
    """Parse a points-fraction cell (``'18.61 / 20.00'``) and a percentage cell."""
    pts = parse_puntos(puntos_cell)
    pct = _safe_float(pct_cell)
    if pts is None or pct is None:
        return None
    return FuentePuntaje(puntos_obtenidos=pts[0], puntos_maximos=pts[1], porcentaje=pct)


def _try_parse_summary_row(cells: list[str]) -> ResumenPorcentajes | None:
    """Parse the bottom summary row (no dimension name, just 4 percentages).

    The row looks like: ['', '93.99', '', '100.00', '', '81.95', '', '', '91.98']
    We pick the non-empty numeric cells.
    """
    nums = [_safe_float(c) for c in cells if c]
    nums = [n for n in nums if n is not None]
    if len(nums) >= 4:
        return ResumenPorcentajes(
            estudiante=nums[0],
            director=nums[1],
            autoevaluacion=nums[2],
            promedio_general=nums[3],
        )
    return None


# ── Public helpers (also used in tests) ─────────────────────────────────


def parse_puntos(value: str) -> tuple[float, float] | None:
    """Parse ``'18.61 / 20.00'`` into ``(18.61, 20.0)``."""
    m = PUNTOS_RE.search(value)
    if not m:
        return None
    try:
        return float(m.group(1)), float(m.group(2))
    except ValueError:
        return None


# ── Internal helpers ────────────────────────────────────────────────────


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
