"""Domain invariants — enforcement helpers for business rules.

These functions raise domain exceptions when an invariant is violated.
Call them at system boundaries (API endpoints, service methods) to
guarantee the system cannot operate incorrectly.
"""

from __future__ import annotations

from app.core.logging import get_logger
from app.domain.entities.enums import Modalidad
from app.domain.exceptions import ModalidadInvalidaError, ModalidadRequeridaError, ValidationError

logger = get_logger(__name__)

# Modalidades that may appear in analytics / alerts / rankings [BR-MOD-05].
MODALIDADES_ANALISIS: frozenset[str] = frozenset(
    {Modalidad.CUATRIMESTRAL, Modalidad.MENSUAL, Modalidad.B2B}
)

# ── Año constraints (must match DB CHECK: año >= 2020) ──────────────────

AÑO_MIN = 2020
AÑO_MAX = 2100

# ── periodo_orden ranges per modalidad ──────────────────────────────────

_PERIODO_ORDEN_RANGOS: dict[str, tuple[int, int]] = {
    Modalidad.CUATRIMESTRAL: (1, 3),
    Modalidad.MENSUAL: (1, 10),
    Modalidad.B2B: (0, 0),
}


def require_modalidad(valor: str | None) -> str:
    """Validate that *valor* is a non-null, analysis-eligible modalidad.

    Returns the validated (upper-cased) value so callers can use it
    directly::

        mod = require_modalidad(raw_param)   # raises or returns str

    Raises
    ------
    ModalidadRequeridaError
        When *valor* is ``None`` or empty.
    ModalidadInvalidaError
        When *valor* is not one of the three analysis modalities.

    References: [BR-MOD-02], [BR-MOD-05], [BR-AN-01].
    """
    if not valor:
        logger.warning("modalidad_missing | caller omitted required modalidad param")
        raise ModalidadRequeridaError()

    normalised = valor.strip().upper()

    if normalised not in MODALIDADES_ANALISIS:
        logger.warning("modalidad_invalida | valor=%s", valor)
        raise ModalidadInvalidaError(valor)

    return normalised


def require_modalidad_valid(valor: str) -> str:
    """Validate that *valor* is any valid Modalidad member (including DESCONOCIDA).

    Use this for persistence paths where DESCONOCIDA is allowed.
    Use ``require_modalidad()`` for analytics paths.
    """
    normalised = valor.strip().upper()
    valid = {m.value for m in Modalidad}
    if normalised not in valid:
        raise ValidationError(
            f"Modalidad '{valor}' no es un valor válido. "
            f"Valores permitidos: {', '.join(sorted(valid))}"
        )
    return normalised


def require_año(año: int) -> int:
    """Validate year is within allowed range [BR-MOD-04].

    Must match DB CHECK constraint ``año >= 2020`` and upper bound.
    """
    if not (AÑO_MIN <= año <= AÑO_MAX):
        raise ValidationError(f"Año {año} fuera de rango válido [{AÑO_MIN}-{AÑO_MAX}]")
    return año


def require_periodo_orden(periodo_orden: int, modalidad: str) -> int:
    """Validate periodo_orden is within the legal range for *modalidad*.

    Ranges:
    - CUATRIMESTRAL: 1-3
    - MENSUAL: 1-10
    - B2B: 0 (fixed)
    - DESCONOCIDA: any non-negative (no strict enforcement)
    """
    if periodo_orden < 0:
        raise ValidationError(f"periodo_orden no puede ser negativo: {periodo_orden}")

    rango = _PERIODO_ORDEN_RANGOS.get(modalidad)
    if rango is not None:
        rango_min, rango_max = rango
        if not (rango_min <= periodo_orden <= rango_max):
            raise ValidationError(
                f"periodo_orden {periodo_orden} fuera de rango [{rango_min}-{rango_max}] "
                f"para modalidad '{modalidad}'"
            )
    return periodo_orden
    return periodo_orden
