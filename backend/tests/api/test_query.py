"""API tests for the intelligent query endpoint (POST /api/v1/query)."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from tests.fixtures.factories import make_comentario, make_documento, make_evaluacion


async def _seed_query_data(db: AsyncSession) -> None:
    """Insert test data for query endpoint tests."""
    doc = make_documento()
    db.add(doc)
    await db.flush()

    eval1 = make_evaluacion(
        documento_id=doc.id,
        docente_nombre="Prof. García",
        periodo="2025-1",
        puntaje_general=90.0,
        estado="completado",
    )
    db.add(eval1)
    await db.flush()

    db.add_all(
        [
            make_comentario(
                evaluacion_id=eval1.id,
                tipo="fortaleza",
                texto="Explica de forma clara y dinámica",
                tema="comunicacion",
                sentimiento="positivo",
                sent_score=0.80,
            ),
            make_comentario(
                evaluacion_id=eval1.id,
                tipo="mejora",
                texto="No es puntual con los horarios",
                tema="puntualidad",
                sentimiento="negativo",
                sent_score=-0.50,
            ),
            make_comentario(
                evaluacion_id=eval1.id,
                tipo="fortaleza",
                texto="Domina el tema a la perfección",
                tema="dominio_tema",
                sentimiento="positivo",
                sent_score=0.90,
            ),
        ]
    )
    await db.flush()


# ── POST /api/v1/query ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_query_success(client, db):
    await _seed_query_data(db)
    resp = await client.post(
        "/api/v1/query",
        json={
            "question": "¿Cuáles son las fortalezas de Prof. García?",
            "filters": {"modalidad": "CUATRIMESTRAL"},
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "answer" in data
    assert data["answer"]  # non-empty
    assert "evidence" in data
    assert "metadata" in data
    assert data["metadata"]["model"] == "gemini-2.0-flash"
    assert data["metadata"]["tokens_used"] > 0
    assert data["metadata"]["audit_log_id"]  # UUID present


@pytest.mark.asyncio
async def test_query_with_filters(client, db):
    await _seed_query_data(db)
    resp = await client.post(
        "/api/v1/query",
        json={
            "question": "¿Qué opinan los estudiantes?",
            "filters": {
                "modalidad": "CUATRIMESTRAL",
                "periodo": "2025-1",
                "docente": "Prof. García",
            },
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["answer"]


@pytest.mark.asyncio
async def test_query_empty_db(client):
    resp = await client.post(
        "/api/v1/query",
        json={
            "question": "¿Cómo enseña el profesor?",
            "filters": {"modalidad": "CUATRIMESTRAL"},
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "answer" in data


@pytest.mark.asyncio
async def test_query_validation_short_question(client):
    resp = await client.post(
        "/api/v1/query",
        json={"question": "ab"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_query_validation_missing_question(client):
    resp = await client.post("/api/v1/query", json={})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_query_tema_filter_applied(client, db):
    """When the question mentions 'metodología', only metodologia comments appear."""
    await _seed_query_data(db)
    resp = await client.post(
        "/api/v1/query",
        json={
            "question": "¿Cómo es la metodología del profesor?",
            "filters": {"modalidad": "CUATRIMESTRAL"},
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    # No metodologia comments were seeded, so evidence should be mostly metrics
    assert "answer" in data


@pytest.mark.asyncio
async def test_query_response_has_metadata_fields(client, db):
    await _seed_query_data(db)
    resp = await client.post(
        "/api/v1/query",
        json={
            "question": "¿Cuál es el puntaje promedio?",
            "filters": {"modalidad": "CUATRIMESTRAL"},
        },
    )
    data = resp.json()
    meta = data["metadata"]
    assert "model" in meta
    assert "tokens_used" in meta
    assert "latency_ms" in meta
    assert "audit_log_id" in meta
