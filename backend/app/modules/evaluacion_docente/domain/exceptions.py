"""Module-specific exceptions for evaluación docente.

These extend the shared-kernel base errors with domain concepts
that only make sense within this bounded context.
"""

from app.shared.domain.exceptions import DomainError, ValidationError

# ── Modalidad ────────────────────────────────────────────────────────


class ModalidadRequeridaError(ValidationError):
    """Analytics / alert endpoints require a modalidad filter [BR-MOD-02]."""

    def __init__(self) -> None:
        super().__init__("El parámetro 'modalidad' es obligatorio para esta consulta [BR-MOD-02]")


class ModalidadInvalidaError(ValidationError):
    """The supplied modalidad value is not valid [BR-MOD-01]."""

    def __init__(self, valor: str) -> None:
        from app.modules.evaluacion_docente.domain.invariants import MODALIDADES_ANALISIS

        super().__init__(
            f"Modalidad inválida: '{valor}'. "
            f"Valores permitidos: {', '.join(sorted(MODALIDADES_ANALISIS))} [BR-MOD-01]"
        )


# ── Gemini ───────────────────────────────────────────────────────────


class GeminiError(DomainError):
    """Base error for Gemini API interactions."""

    def __init__(self, detail: str = "Error en servicio Gemini"):
        super().__init__(detail)


class GeminiTimeoutError(GeminiError):
    """Gemini API call exceeded the configured timeout."""

    def __init__(self, detail: str = "Tiempo de espera agotado en Gemini"):
        super().__init__(detail)


class GeminiRateLimitError(GeminiError):
    """Gemini API rate limit exceeded."""

    def __init__(self, detail: str = "Límite de solicitudes de Gemini excedido"):
        super().__init__(detail)


class GeminiUnavailableError(GeminiError):
    """Gemini API key not configured or service unreachable."""

    def __init__(self, detail: str = "Servicio Gemini no disponible"):
        super().__init__(detail)
