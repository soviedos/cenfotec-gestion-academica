"""Period normalisation, validation, and ordering.

Implements business rules [BR-MOD-01]–[BR-MOD-05] and [BR-AN-40]–[BR-AN-42].

Usage
-----
>>> from app.modules.evaluacion_docente.domain.periodo import (
...     normalizar_periodo, validar_periodo, parse_periodo
... )
>>> normalizar_periodo("  c2   2025 ")
'C2 2025'
>>> validar_periodo("C2", 2025, Modalidad.CUATRIMESTRAL)
    PeriodoInfo(periodo_normalizado='C2 2025',
    modalidad=<Modalidad.CUATRIMESTRAL>, año=2025,
    periodo_orden=2, prefijo='C', numero=2)
>>> parse_periodo("MT10 2026")
    PeriodoInfo(periodo_normalizado='MT10 2026',
    modalidad=<Modalidad.MENSUAL>, año=2026,
    periodo_orden=10, prefijo='MT', numero=10)
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.modules.evaluacion_docente.domain.entities.enums import Modalidad
from app.modules.evaluacion_docente.domain.invariants import AÑO_MAX, AÑO_MIN
from app.shared.domain.exceptions import ValidationError

# ── Constants ────────────────────────────────────────────────────────────

# Year bounds imported from invariants — single source of truth.
# Must match DB CHECK constraint: año >= 2020.

# Compiled regexes — one per modalidad (anchored, case-insensitive)
_RE_CUATRIMESTRAL = re.compile(r"^C([1-3])$", re.IGNORECASE)
_RE_MENSUAL = re.compile(r"^(MT?)(\d{1,2})$", re.IGNORECASE)
_RE_B2B = re.compile(r"^B2B[\s\-].+", re.IGNORECASE)

# Full-string regex for periodo already containing year
_RE_FULL_CUATRIMESTRAL = re.compile(r"^C([1-3])\s+(\d{4})$", re.IGNORECASE)
_RE_FULL_MENSUAL = re.compile(r"^(MT?)(\d{1,2})\s+(\d{4})$", re.IGNORECASE)
_RE_FULL_B2B = re.compile(r"^B2B[\s\-].+", re.IGNORECASE)

# Valid ranges per prefix
_RANGOS: dict[str, tuple[int, int]] = {
    "C": (1, 3),
    "M": (1, 10),
    "MT": (1, 10),
}


# ── Result dataclass ────────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class PeriodoInfo:
    """Validated, normalised period information."""

    periodo_normalizado: str
    modalidad: Modalidad
    año: int
    periodo_orden: int
    prefijo: str
    numero: int


# ── Public API ───────────────────────────────────────────────────────────


def normalizar_periodo(raw: str) -> str:
    """Collapse whitespace, strip, and upper-case a raw periodo string.

    >>> normalizar_periodo("  c2   2025 ")
    'C2 2025'
    >>> normalizar_periodo("mt10  2026")
    'MT10 2026'
    >>> normalizar_periodo("b2b - empresa  2025-q1")
    'B2B - EMPRESA 2025-Q1'
    """
    return " ".join(raw.split()).upper()


def determinar_modalidad(periodo: str) -> Modalidad:
    """Infer *Modalidad* from a raw or normalised periodo string.

    Implements [BR-MOD-03].

    >>> determinar_modalidad("C2 2025")
    <Modalidad.CUATRIMESTRAL: 'CUATRIMESTRAL'>
    >>> determinar_modalidad("M10 2025")
    <Modalidad.MENSUAL: 'MENSUAL'>
    >>> determinar_modalidad("B2B-EMPRESA-2025-Q1")
    <Modalidad.B2B: 'B2B'>
    """
    normalizado = normalizar_periodo(periodo)

    # B2B — highest priority to prevent false positives
    if normalizado.startswith("B2B"):
        return Modalidad.B2B

    if _RE_FULL_CUATRIMESTRAL.match(normalizado):
        return Modalidad.CUATRIMESTRAL

    if _RE_FULL_MENSUAL.match(normalizado):
        m = _RE_FULL_MENSUAL.match(normalizado)
        assert m is not None
        prefijo = m.group(1).upper()
        numero = int(m.group(2))
        rango_min, rango_max = _RANGOS[prefijo]
        if rango_min <= numero <= rango_max:
            return Modalidad.MENSUAL

    return Modalidad.DESCONOCIDA


def parse_periodo(periodo: str) -> PeriodoInfo:
    """Parse a *full* periodo string (code + year) into structured data.

    Implements [BR-AN-41].

    Raises :class:`~app.domain.exceptions.ValidationError` if the string
    cannot be parsed or the values are out of range.

    >>> parse_periodo("C2 2025")
    PeriodoInfo(periodo_normalizado='C2 2025',
    modalidad=<Modalidad.CUATRIMESTRAL>, año=2025,
    periodo_orden=2, prefijo='C', numero=2)
    """
    normalizado = normalizar_periodo(periodo)

    # ── B2B ──────────────────────────────────────────────────────────
    if _RE_FULL_B2B.match(normalizado):
        # B2B periods have free-form format; order is 0 (manual override expected)
        return PeriodoInfo(
            periodo_normalizado=normalizado,
            modalidad=Modalidad.B2B,
            año=_extract_b2b_year(normalizado),
            periodo_orden=0,
            prefijo="B2B",
            numero=0,
        )

    # ── Cuatrimestral ────────────────────────────────────────────────
    m = _RE_FULL_CUATRIMESTRAL.match(normalizado)
    if m:
        numero = int(m.group(1))
        año = int(m.group(2))
        _validar_año(año)
        return PeriodoInfo(
            periodo_normalizado=normalizado,
            modalidad=Modalidad.CUATRIMESTRAL,
            año=año,
            periodo_orden=numero,
            prefijo="C",
            numero=numero,
        )

    # ── Mensual / MT ─────────────────────────────────────────────────
    m = _RE_FULL_MENSUAL.match(normalizado)
    if m:
        prefijo = m.group(1).upper()
        numero = int(m.group(2))
        año = int(m.group(3))
        _validar_año(año)
        rango_min, rango_max = _RANGOS[prefijo]
        if not (rango_min <= numero <= rango_max):
            raise ValidationError(
                f"Número de periodo {numero} fuera de rango [{rango_min}-{rango_max}] "
                f"para prefijo '{prefijo}'"
            )
        return PeriodoInfo(
            periodo_normalizado=normalizado,
            modalidad=Modalidad.MENSUAL,
            año=año,
            periodo_orden=numero,
            prefijo=prefijo,
            numero=numero,
        )

    raise ValidationError(f"Formato de periodo no reconocido: '{periodo}'")


def validar_periodo(
    codigo_periodo: str,
    año: int,
    modalidad: Modalidad,
) -> PeriodoInfo:
    """Validate that a period code is legal for the given modalidad and year.

    Parameters
    ----------
    codigo_periodo:
        Period code *without* year, e.g. ``"C2"``, ``"M10"``, ``"MT3"``.
        For B2B the full string including year is accepted.
    año:
        Academic year (e.g. 2025).
    modalidad:
        Expected :class:`Modalidad`.

    Returns
    -------
    PeriodoInfo
        Validated and normalised result.

    Raises
    ------
    ValidationError
        If the code/year/modalidad combination is invalid.

    >>> validar_periodo("C2", 2025, Modalidad.CUATRIMESTRAL)
    PeriodoInfo(periodo_normalizado='C2 2025',
    modalidad=<Modalidad.CUATRIMESTRAL>, año=2025,
    periodo_orden=2, prefijo='C', numero=2)
    """
    _validar_año(año)
    codigo_upper = codigo_periodo.strip().upper()

    if modalidad == Modalidad.DESCONOCIDA:
        raise ValidationError("No se puede validar un periodo con modalidad DESCONOCIDA")

    # ── B2B ──────────────────────────────────────────────────────────
    if modalidad == Modalidad.B2B:
        if not codigo_upper.startswith("B2B"):
            raise ValidationError(
                f"Periodo '{codigo_periodo}' no es válido para modalidad B2B "
                "(debe iniciar con 'B2B')"
            )
        normalizado = normalizar_periodo(codigo_periodo)
        return PeriodoInfo(
            periodo_normalizado=normalizado,
            modalidad=Modalidad.B2B,
            año=año,
            periodo_orden=0,
            prefijo="B2B",
            numero=0,
        )

    # ── Cuatrimestral ────────────────────────────────────────────────
    if modalidad == Modalidad.CUATRIMESTRAL:
        m = _RE_CUATRIMESTRAL.match(codigo_upper)
        if not m:
            raise ValidationError(
                f"Periodo '{codigo_periodo}' no es válido para modalidad CUATRIMESTRAL. "
                "Valores permitidos: C1, C2, C3"
            )
        numero = int(m.group(1))
        normalizado = f"C{numero} {año}"
        return PeriodoInfo(
            periodo_normalizado=normalizado,
            modalidad=Modalidad.CUATRIMESTRAL,
            año=año,
            periodo_orden=numero,
            prefijo="C",
            numero=numero,
        )

    # ── Mensual ──────────────────────────────────────────────────────
    if modalidad == Modalidad.MENSUAL:
        m = _RE_MENSUAL.match(codigo_upper)
        if not m:
            raise ValidationError(
                f"Periodo '{codigo_periodo}' no es válido para modalidad MENSUAL. "
                "Valores permitidos: M1-M10, MT1-MT10"
            )
        prefijo = m.group(1).upper()
        numero = int(m.group(2))
        rango_min, rango_max = _RANGOS[prefijo]
        if not (rango_min <= numero <= rango_max):
            raise ValidationError(
                f"Número de periodo {numero} fuera de rango [{rango_min}-{rango_max}] "
                f"para prefijo '{prefijo}'"
            )
        normalizado = f"{prefijo}{numero} {año}"
        return PeriodoInfo(
            periodo_normalizado=normalizado,
            modalidad=Modalidad.MENSUAL,
            año=año,
            periodo_orden=numero,
            prefijo=prefijo,
            numero=numero,
        )

    raise ValidationError(f"Modalidad no soportada: {modalidad}")


def periodo_sort_key(info: PeriodoInfo) -> tuple[int, str, int]:
    """Return a sort key for chronological ordering.

    Implements [BR-AN-40] and [BR-AN-42] — *within* the same modalidad,
    periods sort by (año ASC, prefijo ASC, numero ASC).  Cross-modalidad
    comparison is meaningful but the caller should filter by modalidad first.

    >>> sorted(
    ...     [parse_periodo("C3 2024"),
    ...      parse_periodo("C1 2025"),
    ...      parse_periodo("C1 2024")],
    ...     key=periodo_sort_key,
    ... )  # doctest: +SKIP
    [PeriodoInfo(...año=2024...numero=1...),
     PeriodoInfo(...año=2024...numero=3...),
     PeriodoInfo(...año=2025...numero=1...)]
    """
    return (info.año, info.prefijo, info.numero)


def _periodo_str_sort_key(periodo_str: str) -> tuple[int, str, int]:
    """Sort key from a raw periodo string.  Unparseable strings sort last."""
    try:
        info = parse_periodo(periodo_str)
        return periodo_sort_key(info)
    except (ValidationError, Exception):
        return (9999, periodo_str, 0)


def sort_periodos(rows: list[dict], *, key: str = "periodo") -> list[dict]:
    """Sort a list of dicts chronologically by their *key* field [BR-AN-40].

    This is the canonical way to sort analytics/dashboard results that
    contain a ``periodo`` string.  Unparseable periods are pushed to the end.

    >>> rows = [{"periodo": "C2 2025"}, {"periodo": "C1 2024"}, {"periodo": "C3 2024"}]
    >>> [r["periodo"] for r in sort_periodos(rows)]
    ['C1 2024', 'C3 2024', 'C2 2025']
    """
    return sorted(rows, key=lambda r: _periodo_str_sort_key(r[key]))


# ── Private helpers ──────────────────────────────────────────────────────


def _validar_año(año: int) -> None:
    if not (AÑO_MIN <= año <= AÑO_MAX):
        raise ValidationError(f"Año {año} fuera de rango válido [{AÑO_MIN}-{AÑO_MAX}]")


def _extract_b2b_year(normalizado: str) -> int:
    """Best-effort year extraction from a B2B period string."""
    m = re.search(r"\b(20\d{2})\b", normalizado)
    if m:
        return int(m.group(1))
    return 0
