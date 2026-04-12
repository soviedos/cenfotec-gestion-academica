"""Unit tests for QueryService._detect_tema and GeminiCallResult schema."""

import pytest

from app.modules.evaluacion_docente.application.services.query_service import QueryService
from app.modules.evaluacion_docente.domain.schemas.query import (
    GeminiCallResult,
    QueryFilters,
    QueryRequest,
)


class TestDetectTema:
    def test_metodologia(self):
        assert QueryService._detect_tema("¿Cómo es la metodología del profesor?") == "metodologia"

    def test_comunicacion(self):
        assert QueryService._detect_tema("¿El profesor explica bien?") == "comunicacion"

    def test_puntualidad(self):
        assert QueryService._detect_tema("¿Es puntual el docente?") == "puntualidad"

    def test_evaluacion(self):
        assert QueryService._detect_tema("¿Cómo son las evaluaciones?") == "evaluacion"

    def test_dominio(self):
        assert QueryService._detect_tema("¿Tiene dominio de la materia?") == "dominio_tema"

    def test_no_match(self):
        assert QueryService._detect_tema("¿Cuántos profesores hay en la lista?") is None

    def test_case_insensitive(self):
        assert QueryService._detect_tema("METODOLOGÍA del curso") == "metodologia"


class TestQuerySchemas:
    def test_query_request_requires_filters(self):
        with pytest.raises(Exception):
            QueryRequest(question="¿Cómo enseña García?")

    def test_query_request_requires_modalidad_in_filters(self):
        with pytest.raises(Exception):
            QueryRequest(
                question="¿Cómo enseña García?",
                filters=QueryFilters(periodo="2025-1"),
            )

    def test_query_request_with_filters(self):
        req = QueryRequest(
            question="¿Qué opinan los estudiantes?",
            filters=QueryFilters(
                modalidad="CUATRIMESTRAL", periodo="2025-1", docente="Prof. García"
            ),
        )
        assert req.filters.periodo == "2025-1"
        assert req.filters.docente == "Prof. García"
        assert req.filters.modalidad == "CUATRIMESTRAL"

    def test_query_request_min_length(self):
        with pytest.raises(Exception):
            QueryRequest(question="ab")

    def test_gemini_call_result(self):
        result = GeminiCallResult(
            text="Respuesta de prueba",
            model_name="gemini-2.0-flash",
            tokens_input=100,
            tokens_output=50,
            latency_ms=200,
        )
        assert result.text == "Respuesta de prueba"
        assert result.tokens_input == 100
