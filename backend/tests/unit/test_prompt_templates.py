"""Unit tests for prompt_templates module."""

from app.modules.evaluacion_docente.infrastructure.external.prompt_templates import (
    format_evidence_block,
)


class TestFormatEvidenceBlock:
    def test_empty_evidence(self):
        result = format_evidence_block([], [])
        assert result == "(Sin evidencia disponible)"

    def test_metrics_only(self):
        metrics = [
            {"label": "Puntaje promedio", "value": 92.5, "periodo": "2025-1", "docente": None},
        ]
        result = format_evidence_block([], metrics)
        assert "[1] MÉTRICA" in result
        assert "Puntaje promedio: 92.5" in result
        assert "período: 2025-1" in result

    def test_comments_only(self):
        comments = [
            {
                "texto": "Explica muy bien",
                "tipo": "fortaleza",
                "docente": "Prof. García",
                "asignatura": "Cálculo",
                "periodo": "2025-1",
                "fuente": "estudiante",
            },
        ]
        result = format_evidence_block(comments, [])
        assert "[1] COMENTARIO" in result
        assert "Explica muy bien" in result
        assert "Prof. García" in result

    def test_mixed_evidence_numbering(self):
        metrics = [{"label": "Promedio", "value": 88.0}]
        comments = [
            {
                "texto": "Buen profesor",
                "tipo": "fortaleza",
                "docente": "Prof. López",
                "asignatura": "Física",
                "periodo": "2025-2",
                "fuente": "estudiante",
            },
        ]
        result = format_evidence_block(comments, metrics)
        # Metrics come first: [1], comments after: [2]
        assert "[1] MÉTRICA" in result
        assert "[2] COMENTARIO" in result
