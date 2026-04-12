"""Unit tests for domain exceptions — no I/O, pure logic."""

import pytest

from app.shared.domain.exceptions import DomainError, DuplicateError, NotFoundError, ValidationError


class TestDomainError:
    def test_default_message(self):
        err = DomainError()
        assert err.detail == "Error de dominio"

    def test_custom_message(self):
        err = DomainError("Algo salió mal")
        assert err.detail == "Algo salió mal"

    def test_is_exception(self):
        assert issubclass(DomainError, Exception)


class TestNotFoundError:
    def test_default_message(self):
        err = NotFoundError()
        assert err.detail == "Recurso no encontrado"

    def test_with_resource_name(self):
        err = NotFoundError("Documento")
        assert err.detail == "Documento no encontrado"

    def test_with_resource_id(self):
        err = NotFoundError("Documento", "abc-123")
        assert err.detail == "Documento no encontrado: abc-123"

    def test_inherits_domain_error(self):
        assert issubclass(NotFoundError, DomainError)


class TestDuplicateError:
    def test_default_message(self):
        err = DuplicateError()
        assert err.detail == "El recurso ya existe"

    def test_custom_message(self):
        err = DuplicateError("Hash duplicado")
        assert err.detail == "Hash duplicado"


class TestValidationError:
    def test_default_message(self):
        err = ValidationError()
        assert err.detail == "Error de validación"

    def test_all_errors_catchable_as_domain_error(self):
        """All domain exceptions should be catchable via the base class."""
        errors = [NotFoundError(), DuplicateError(), ValidationError()]
        for err in errors:
            with pytest.raises(DomainError):
                raise err

