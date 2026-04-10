"""Domain exceptions — business rule violations.

Raise these from services; the API layer catches and maps to HTTP responses.
"""


class DomainError(Exception):
    """Base class for all domain errors."""

    def __init__(self, detail: str = "Error de dominio"):
        self.detail = detail
        super().__init__(detail)


class NotFoundError(DomainError):
    """Resource does not exist."""

    def __init__(self, resource: str = "Recurso", resource_id: str = ""):
        detail = f"{resource} no encontrado" + (f": {resource_id}" if resource_id else "")
        super().__init__(detail)


class DuplicateError(DomainError):
    """Resource already exists (e.g. duplicate hash)."""

    def __init__(self, detail: str = "El recurso ya existe"):
        super().__init__(detail)


class ValidationError(DomainError):
    """Business-rule validation failure."""

    def __init__(self, detail: str = "Error de validación"):
        super().__init__(detail)


class ModalidadRequeridaError(ValidationError):
    """Analytics / alert endpoints require a modalidad filter [BR-MOD-02].

    Raised when a caller omits the mandatory ``modalidad`` parameter on
    operations that *must* be scoped to a single modality.
    """

    def __init__(self) -> None:
        super().__init__("El parámetro 'modalidad' es obligatorio para esta consulta [BR-MOD-02]")


class ModalidadInvalidaError(ValidationError):
    """The supplied modalidad value is not a valid modality [BR-MOD-01].

    Valid analysis modalities: CUATRIMESTRAL, MENSUAL, B2B.
    DESCONOCIDA is stored but excluded from analytics per [BR-MOD-05].
    """

    _VALID = ("CUATRIMESTRAL", "MENSUAL", "B2B")

    def __init__(self, valor: str) -> None:
        super().__init__(
            f"Modalidad inválida: '{valor}'. "
            f"Valores permitidos: {', '.join(self._VALID)} [BR-MOD-01]"
        )


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
