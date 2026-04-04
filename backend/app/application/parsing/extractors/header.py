"""Header extractor — professor name, code, period, campus.

Works on raw text (``page.get_text()``) from the first page.
"""

from __future__ import annotations

from app.application.parsing.constants import (PERIODO_RE, PROFESOR_RE,
                                               RECINTO_RE)
from app.application.parsing.schemas import HeaderData


def extract_header(text: str) -> HeaderData | None:
    """Extract header fields from page-1 raw text.

    Returns ``None`` if any *required* field (profesor, periodo, recinto)
    cannot be found — callers should treat this as a fatal parse error.
    """
    profesor_nombre, profesor_codigo = _extract_profesor(text)
    periodo = _extract_periodo(text)
    recinto = _extract_recinto(text)

    if not profesor_nombre or not periodo or not recinto:
        return None

    return HeaderData(
        profesor_nombre=profesor_nombre,
        profesor_codigo=profesor_codigo,
        periodo=periodo,
        recinto=recinto,
    )


# ── helpers ─────────────────────────────────────────────────────────────


def _extract_profesor(text: str) -> tuple[str | None, str | None]:
    m = PROFESOR_RE.search(text)
    if not m:
        return None, None
    nombre = m.group(1).strip()
    codigo = m.group(2) if m.group(2) else None
    return nombre, codigo


def _extract_periodo(text: str) -> str | None:
    m = PERIODO_RE.search(text)
    return m.group(1).strip() if m else None


def _extract_recinto(text: str) -> str | None:
    m = RECINTO_RE.search(text)
    return m.group(1).strip() if m else None
