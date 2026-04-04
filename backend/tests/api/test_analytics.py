"""API tests for the /api/v1/analytics/ endpoints."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from tests.fixtures.factories import make_dimension, make_documento, make_evaluacion


async def _seed(db: AsyncSession) -> None:
    """Insert a small analytics dataset through the session."""
    doc1 = make_documento()
    doc2 = make_documento()
    db.add_all([doc1, doc2])
    await db.flush()

    eval1 = make_evaluacion(
        documento_id=doc1.id, docente_nombre="Prof. García",
        periodo="2025-1", puntaje_general=82.0, estado="completado",
    )
    eval2 = make_evaluacion(
        documento_id=doc2.id, docente_nombre="Prof. López",
        periodo="2025-1", puntaje_general=91.0, estado="completado",
    )
    db.add_all([eval1, eval2])
    await db.flush()

    db.add(make_dimension(evaluacion_id=eval1.id, nombre="Metodología", pct_promedio=80.0))
    db.add(make_dimension(evaluacion_id=eval2.id, nombre="Metodología", pct_promedio=95.0))
    await db.flush()


# ── GET /api/v1/analytics/resumen ───────────────────────────────────────

@pytest.mark.asyncio
async def test_resumen_empty(client):
    resp = await client.get("/api/v1/analytics/resumen")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_evaluaciones"] == 0
    assert data["promedio_global"] == 0.0


@pytest.mark.asyncio
async def test_resumen_with_data(client, db):
    await _seed(db)
    resp = await client.get("/api/v1/analytics/resumen")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_evaluaciones"] == 2
    assert data["total_docentes"] == 2


@pytest.mark.asyncio
async def test_resumen_filter_periodo(client, db):
    await _seed(db)
    resp = await client.get("/api/v1/analytics/resumen", params={"periodo": "2099-1"})
    assert resp.status_code == 200
    assert resp.json()["total_evaluaciones"] == 0


# ── GET /api/v1/analytics/docentes ──────────────────────────────────────

@pytest.mark.asyncio
async def test_docentes_with_data(client, db):
    await _seed(db)
    resp = await client.get("/api/v1/analytics/docentes")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    assert data[0]["docente_nombre"] == "Prof. López"


@pytest.mark.asyncio
async def test_docentes_respects_limit(client, db):
    await _seed(db)
    resp = await client.get("/api/v1/analytics/docentes", params={"limit": 1})
    assert resp.status_code == 200
    assert len(resp.json()) == 1


# ── GET /api/v1/analytics/dimensiones ──────────────────────────────────

@pytest.mark.asyncio
async def test_dimensiones_with_data(client, db):
    await _seed(db)
    resp = await client.get("/api/v1/analytics/dimensiones")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["dimension"] == "Metodología"


@pytest.mark.asyncio
async def test_dimensiones_filter_docente(client, db):
    await _seed(db)
    resp = await client.get(
        "/api/v1/analytics/dimensiones", params={"docente": "Prof. García"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["pct_promedio"] == 80.0


# ── GET /api/v1/analytics/evolucion ────────────────────────────────────

@pytest.mark.asyncio
async def test_evolucion_with_data(client, db):
    await _seed(db)
    resp = await client.get("/api/v1/analytics/evolucion")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["periodo"] == "2025-1"


# ── GET /api/v1/analytics/ranking ──────────────────────────────────────

@pytest.mark.asyncio
async def test_ranking_with_data(client, db):
    await _seed(db)
    resp = await client.get("/api/v1/analytics/ranking")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    assert data[0]["posicion"] == 1
    assert data[0]["docente_nombre"] == "Prof. López"


@pytest.mark.asyncio
async def test_ranking_respects_limit(client, db):
    await _seed(db)
    resp = await client.get("/api/v1/analytics/ranking", params={"limit": 1})
    assert resp.status_code == 200
    assert len(resp.json()) == 1
