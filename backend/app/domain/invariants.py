"""Domain invariants — enforcement helpers for business rules.

These functions raise domain exceptions when an invariant is violated.
Call them at system boundaries (API endpoints, service methods) to
guarantee the system cannot operate incorrectly.
"""

from __future__ import annotations

from app.core.logging import get_logger
from app.domain.entities.enums import Modalidad
from app.domain.exceptions import ModalidadInvalidaError, ModalidadRequeridaError

logger = get_logger(__name__)

# Modalidades that may appear in analytics / alerts / rankings [BR-MOD-05].
MODALIDADES_ANALISIS: frozenset[str] = frozenset(
    {Modalidad.CUATRIMESTRAL, Modalidad.MENSUAL, Modalidad.B2B}
)


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
