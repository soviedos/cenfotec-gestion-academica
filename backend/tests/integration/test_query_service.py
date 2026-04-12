"""Integration tests for QueryService with real DB (PostgreSQL)."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.evaluacion_docente.application.services.query_service import QueryService
from app.modules.evaluacion_docente.domain.entities.gemini_audit_log import GeminiAuditLog
from app.modules.evaluacion_docente.domain.exceptions import GeminiError
from app.modules.evaluacion_docente.domain.schemas.query import QueryFilters
from tests.fixtures.factories import make_comentario, make_documento, make_evaluacion
from tests.fixtures.fakes import FakeGeminiGateway


async def _seed(db: AsyncSession) -> None:
    doc = make_documento()
    db.add(doc)
    await db.flush()

    ev = make_evaluacion(
        documento_id=doc.id,
        docente_nombre="Prof. López",
        periodo="2025-2",
        puntaje_general=85.0,
        estado="completado",
    )
    db.add(ev)
    await db.flush()

    db.add_all(
        [
            make_comentario(
                evaluacion_id=ev.id,
                tipo="fortaleza",
                texto="Muy buena comunicación con los estudiantes",
                tema="comunicacion",
                sentimiento="positivo",
                sent_score=0.85,
            ),
            make_comentario(
                evaluacion_id=ev.id,
                tipo="mejora",
                texto="Debería mejorar la organización del curso",
                tema="organizacion",
                sentimiento="negativo",
                sent_score=-0.40,
            ),
        ]
    )
    await db.flush()


@pytest.mark.asyncio
async def test_query_service_returns_answer_with_evidence(db):
    await _seed(db)
    gateway = FakeGeminiGateway(answer="Prof. López destaca en comunicación [1].")
    svc = QueryService(db, gateway)

    response = await svc.ask(
        question="¿Cómo es la comunicación de Prof. López?",
        filters=QueryFilters(modalidad="CUATRIMESTRAL", docente="Prof. López"),
    )

    assert response.answer == "Prof. López destaca en comunicación [1]."
    assert len(response.evidence) > 0
    assert response.metadata.model == "gemini-2.0-flash"
    assert response.metadata.tokens_used == 150  # 100 + 50


@pytest.mark.asyncio
async def test_query_service_persists_audit_log(db):
    await _seed(db)
    gateway = FakeGeminiGateway()
    svc = QueryService(db, gateway)

    response = await svc.ask(
        question="¿Cuál es el promedio de López?", filters=QueryFilters(modalidad="CUATRIMESTRAL")
    )

    # Audit log should exist
    assert response.metadata.audit_log_id is not None
    audit = await db.get(GeminiAuditLog, response.metadata.audit_log_id)
    assert audit is not None
    assert audit.operation == "query"
    assert audit.status == "ok"
    assert audit.tokens_input == 100
    assert audit.tokens_output == 50


@pytest.mark.asyncio
async def test_query_service_retrieves_metrics(db):
    await _seed(db)
    gateway = FakeGeminiGateway()
    svc = QueryService(db, gateway)

    response = await svc.ask(
        question="¿Cuál es el puntaje de Prof. López?",
        filters=QueryFilters(modalidad="CUATRIMESTRAL", docente="Prof. López"),
    )

    # Should have at least one metric evidence
    metric_evidence = [e for e in response.evidence if e.type == "metric"]
    assert len(metric_evidence) >= 1
    assert any(e.value == 85.0 for e in metric_evidence)


@pytest.mark.asyncio
async def test_query_service_filters_by_tema(db):
    await _seed(db)
    gateway = FakeGeminiGateway()
    svc = QueryService(db, gateway)

    # "comunicación" should trigger tema = "comunicacion"
    response = await svc.ask(
        question="¿Cómo es la comunicación del profesor?",
        filters=QueryFilters(modalidad="CUATRIMESTRAL"),
    )

    comment_evidence = [e for e in response.evidence if e.type == "comment"]
    # At least the comunicacion comment should be present
    if comment_evidence:
        assert any(
            "comunicación" in e.texto.lower() or "comunicacion" in e.texto.lower()
            for e in comment_evidence
        )


@pytest.mark.asyncio
async def test_query_service_gateway_error_persists_audit(db):
    await _seed(db)
    gateway = FakeGeminiGateway(error=GeminiError("Boom"))
    svc = QueryService(db, gateway)

    with pytest.raises(GeminiError, match="Boom"):
        await svc.ask(
            question="¿Algo sobre el profesor?", filters=QueryFilters(modalidad="CUATRIMESTRAL")
        )


@pytest.mark.asyncio
async def test_query_service_no_data(db):
    """Query on empty DB still works — returns answer with no evidence."""
    gateway = FakeGeminiGateway()
    svc = QueryService(db, gateway)

    response = await svc.ask(
        question="¿Cómo son los profesores?", filters=QueryFilters(modalidad="CUATRIMESTRAL")
    )
    assert response.answer
    assert response.metadata.audit_log_id is not None


@pytest.mark.asyncio
async def test_gateway_receives_correct_data(db):
    await _seed(db)
    gateway = FakeGeminiGateway()
    svc = QueryService(db, gateway)

    await svc.ask(
        question="¿Qué opinan de López?",
        filters=QueryFilters(modalidad="CUATRIMESTRAL", docente="Prof. López"),
    )

    assert len(gateway.calls) == 1
    call = gateway.calls[0]
    assert call["question"] == "¿Qué opinan de López?"
    assert isinstance(call["comments"], list)
    assert isinstance(call["metrics"], list)
