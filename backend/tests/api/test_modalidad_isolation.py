"""BR-MOD-02 compliance tests — modalidad isolation across all endpoints.

Every analytics, qualitative, and evaluaciones endpoint must **require**
``modalidad`` so that data from different modalities (CUATRIMESTRAL,
MENSUAL, etc.) is never mixed.  See also ``test_modalidad_enforcement.py``
for 422-rejection tests.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from tests.fixtures.factories import (
    make_comentario,
    make_dimension,
    make_documento,
    make_evaluacion,
)


async def _seed_two_modalidades(db: AsyncSession) -> None:
    """Create two evaluations of different modalidad with distinct data."""
    doc1 = make_documento()
    doc2 = make_documento()
    db.add_all([doc1, doc2])
    await db.flush()

    eval_cuat = make_evaluacion(
        documento_id=doc1.id,
        docente_nombre="Prof. García",
        periodo="2025-1",
        modalidad="CUATRIMESTRAL",
        puntaje_general=80.0,
        estado="completado",
    )
    eval_mens = make_evaluacion(
        documento_id=doc2.id,
        docente_nombre="Prof. López",
        periodo="2025-1",
        modalidad="MENSUAL",
        puntaje_general=95.0,
        estado="completado",
    )
    db.add_all([eval_cuat, eval_mens])
    await db.flush()

    db.add(make_dimension(evaluacion_id=eval_cuat.id, nombre="Metodología", pct_promedio=75.0))
    db.add(make_dimension(evaluacion_id=eval_mens.id, nombre="Metodología", pct_promedio=98.0))

    db.add(
        make_comentario(
            evaluacion_id=eval_cuat.id,
            tipo="fortaleza",
            texto="Buena explicación cuatrimestral",
            tema="comunicacion",
            sentimiento="positivo",
            sent_score=0.8,
        )
    )
    db.add(
        make_comentario(
            evaluacion_id=eval_mens.id,
            tipo="mejora",
            texto="Mejorar puntualidad mensual",
            tema="puntualidad",
            sentimiento="negativo",
            sent_score=-0.5,
        )
    )
    await db.flush()


# ── Analytics: resumen ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_analytics_resumen_filters_by_modalidad(client, db):
    await _seed_two_modalidades(db)
    resp = await client.get("/api/v1/analytics/resumen", params={"modalidad": "CUATRIMESTRAL"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_evaluaciones"] == 1
    assert data["total_docentes"] == 1
    assert data["promedio_global"] == 80.0


# ── Analytics: docentes ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_analytics_docentes_filters_by_modalidad(client, db):
    await _seed_two_modalidades(db)
    resp = await client.get("/api/v1/analytics/docentes", params={"modalidad": "MENSUAL"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["docente_nombre"] == "Prof. López"


# ── Analytics: dimensiones ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_analytics_dimensiones_filters_by_modalidad(client, db):
    await _seed_two_modalidades(db)
    resp = await client.get("/api/v1/analytics/dimensiones", params={"modalidad": "CUATRIMESTRAL"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["pct_promedio"] == 75.0


# ── Analytics: evolucion ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_analytics_evolucion_filters_by_modalidad(client, db):
    await _seed_two_modalidades(db)
    resp = await client.get("/api/v1/analytics/evolucion", params={"modalidad": "MENSUAL"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["promedio"] == 95.0


# ── Analytics: ranking ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_analytics_ranking_filters_by_modalidad(client, db):
    await _seed_two_modalidades(db)
    resp = await client.get("/api/v1/analytics/ranking", params={"modalidad": "CUATRIMESTRAL"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["docente_nombre"] == "Prof. García"


# ── Qualitative: resumen ───────────────────────────────────────────────


@pytest.mark.asyncio
async def test_qualitative_resumen_filters_by_modalidad(client, db):
    await _seed_two_modalidades(db)
    resp = await client.get("/api/v1/qualitative/resumen", params={"modalidad": "CUATRIMESTRAL"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_comentarios"] == 1


# ── Qualitative: comentarios ───────────────────────────────────────────


@pytest.mark.asyncio
async def test_qualitative_comentarios_filters_by_modalidad(client, db):
    await _seed_two_modalidades(db)
    resp = await client.get("/api/v1/qualitative/comentarios", params={"modalidad": "MENSUAL"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert "mensual" in data[0]["texto"].lower()


# ── Qualitative: distribución temas ────────────────────────────────────


@pytest.mark.asyncio
async def test_qualitative_distribucion_temas_filters_by_modalidad(client, db):
    await _seed_two_modalidades(db)
    resp = await client.get(
        "/api/v1/qualitative/distribucion/temas", params={"modalidad": "CUATRIMESTRAL"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["tema"] == "comunicacion"


# ── Qualitative: distribución sentimiento ──────────────────────────────


@pytest.mark.asyncio
async def test_qualitative_distribucion_sentimiento_filters_by_modalidad(client, db):
    await _seed_two_modalidades(db)
    resp = await client.get(
        "/api/v1/qualitative/distribucion/sentimiento", params={"modalidad": "MENSUAL"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["sentimiento"] == "negativo"


# ── Evaluaciones ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_evaluaciones_filters_by_modalidad(client, db):
    await _seed_two_modalidades(db)
    resp = await client.get("/api/v1/evaluaciones/", params={"modalidad": "CUATRIMESTRAL"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["docente_nombre"] == "Prof. García"


@pytest.mark.asyncio
async def test_evaluaciones_filters_by_estado(client, db):
    await _seed_two_modalidades(db)
    resp = await client.get("/api/v1/evaluaciones/", params={"estado": "completado"})
    assert resp.status_code == 200
    assert resp.json()["total"] == 2


@pytest.mark.asyncio
async def test_evaluaciones_filters_by_docente(client, db):
    await _seed_two_modalidades(db)
    resp = await client.get("/api/v1/evaluaciones/", params={"docente": "Prof. López"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["modalidad"] == "MENSUAL"
