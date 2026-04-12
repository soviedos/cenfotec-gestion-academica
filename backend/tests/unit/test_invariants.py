"""Unit tests for domain invariants enforcement helpers."""

import pytest

from app.modules.evaluacion_docente.domain.exceptions import (
    ModalidadInvalidaError,
    ModalidadRequeridaError,
)
from app.modules.evaluacion_docente.domain.invariants import require_modalidad


class TestRequireModalidad:
    def test_valid_cuatrimestral(self):
        assert require_modalidad("CUATRIMESTRAL") == "CUATRIMESTRAL"

    def test_valid_mensual(self):
        assert require_modalidad("MENSUAL") == "MENSUAL"

    def test_valid_b2b(self):
        assert require_modalidad("B2B") == "B2B"

    def test_case_insensitive(self):
        assert require_modalidad("cuatrimestral") == "CUATRIMESTRAL"
        assert require_modalidad("Mensual") == "MENSUAL"
        assert require_modalidad("b2b") == "B2B"

    def test_none_raises(self):
        with pytest.raises(ModalidadRequeridaError):
            require_modalidad(None)

    def test_empty_string_raises(self):
        with pytest.raises(ModalidadRequeridaError):
            require_modalidad("")

    def test_whitespace_raises(self):
        with pytest.raises(ModalidadInvalidaError):
            require_modalidad("   ")

    def test_desconocida_rejected(self):
        with pytest.raises(ModalidadInvalidaError):
            require_modalidad("DESCONOCIDA")

    def test_arbitrary_string_rejected(self):
        with pytest.raises(ModalidadInvalidaError):
            require_modalidad("FOO_BAR")
