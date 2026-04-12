"""Unit tests for domain exceptions — Gemini error hierarchy."""

from app.modules.evaluacion_docente.domain.exceptions import (
    GeminiError,
    GeminiRateLimitError,
    GeminiTimeoutError,
    GeminiUnavailableError,
)
from app.shared.domain.exceptions import DomainError


class TestGeminiExceptions:
    def test_gemini_error_is_domain_error(self):
        assert issubclass(GeminiError, DomainError)

    def test_gemini_timeout_is_gemini_error(self):
        assert issubclass(GeminiTimeoutError, GeminiError)

    def test_gemini_rate_limit_is_gemini_error(self):
        assert issubclass(GeminiRateLimitError, GeminiError)

    def test_gemini_unavailable_is_gemini_error(self):
        assert issubclass(GeminiUnavailableError, GeminiError)

    def test_gemini_error_default_message(self):
        exc = GeminiError()
        assert exc.detail == "Error en servicio Gemini"

    def test_gemini_timeout_default_message(self):
        exc = GeminiTimeoutError()
        assert "tiempo" in exc.detail.lower() or "agotado" in exc.detail.lower()

    def test_gemini_unavailable_custom_message(self):
        exc = GeminiUnavailableError("API key missing")
        assert exc.detail == "API key missing"
