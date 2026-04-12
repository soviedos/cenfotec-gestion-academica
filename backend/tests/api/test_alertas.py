"""API tests for the /api/v1/alertas/ endpoints."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from tests.fixtures.factories import make_alerta, make_documento, make_evaluacion

# ── Seed helpers ─────────────────────────────────────────────────────────


async def _seed_evaluacion(db: AsyncSession):
    """Create a documento + evaluacion and return the evaluacion."""
    doc = make_documento()
    db.add(doc)
    await db.flush()

    ev = make_evaluacion(
        documento_id=doc.id,
        docente_nombre="Prof. García",
        periodo="C1 2025",
        modalidad="CUATRIMESTRAL",
        año=2025,
        periodo_orden=1,
        materia="ISW-101 Programación I",
        puntaje_general=55.0,
        estado="completado",
    )
    db.add(ev)
    await db.flush()
    return ev


async def _seed_alerts(db: AsyncSession, *, count: int = 3):
    """Seed N alerts linked to a real evaluacion."""
    ev = await _seed_evaluacion(db)
    alerts = []
    tipos = ["BAJO_DESEMPEÑO", "CAIDA", "SENTIMIENTO"]
    severidades = ["alta", "media", "baja"]

    for i in range(count):
        a = make_alerta(
            evaluacion_id=ev.id,
            docente_nombre="Prof. García",
            curso="ISW-101 Programación I",
            periodo="C1 2025",
            tipo_alerta=tipos[i % len(tipos)],
            modalidad="CUATRIMESTRAL",
            severidad=severidades[i % len(severidades)],
            valor_actual=55.0 + i,
            estado="activa",
        )
        db.add(a)
        alerts.append(a)
    await db.flush()
    return ev, alerts


# ═══════════════════════════════════════════════════════════════════════
# GET /api/v1/alertas
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_list_alerts_empty(client):
    resp = await client.get("/api/v1/alertas", params={"modalidad": "CUATRIMESTRAL"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0
    assert data["items"] == []
    assert data["page"] == 1
    assert data["page_size"] == 20
    assert data["total_pages"] == 1


@pytest.mark.asyncio
async def test_list_alerts_with_data(client, db):
    await _seed_alerts(db, count=3)
    resp = await client.get("/api/v1/alertas", params={"modalidad": "CUATRIMESTRAL"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 3
    assert len(data["items"]) == 3


@pytest.mark.asyncio
async def test_list_alerts_pagination(client, db):
    await _seed_alerts(db, count=3)
    resp = await client.get(
        "/api/v1/alertas", params={"page": 1, "page_size": 2, "modalidad": "CUATRIMESTRAL"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 3
    assert len(data["items"]) == 2
    assert data["page"] == 1
    assert data["total_pages"] == 2

    # Second page
    resp2 = await client.get(
        "/api/v1/alertas", params={"page": 2, "page_size": 2, "modalidad": "CUATRIMESTRAL"}
    )
    data2 = resp2.json()
    assert len(data2["items"]) == 1


@pytest.mark.asyncio
async def test_list_alerts_filter_modalidad(client, db):
    await _seed_alerts(db, count=3)
    resp = await client.get("/api/v1/alertas", params={"modalidad": "CUATRIMESTRAL"})
    assert resp.status_code == 200
    assert resp.json()["total"] == 3

    resp2 = await client.get("/api/v1/alertas", params={"modalidad": "MENSUAL"})
    assert resp2.json()["total"] == 0


@pytest.mark.asyncio
async def test_list_alerts_filter_severidad(client, db):
    await _seed_alerts(db, count=3)
    resp = await client.get(
        "/api/v1/alertas", params={"severidad": "alta", "modalidad": "CUATRIMESTRAL"}
    )
    assert resp.status_code == 200
    assert resp.json()["total"] == 1


@pytest.mark.asyncio
async def test_list_alerts_filter_docente(client, db):
    await _seed_alerts(db, count=3)
    resp = await client.get(
        "/api/v1/alertas", params={"docente": "García", "modalidad": "CUATRIMESTRAL"}
    )
    assert resp.status_code == 200
    assert resp.json()["total"] == 3

    resp2 = await client.get(
        "/api/v1/alertas", params={"docente": "NoExiste", "modalidad": "CUATRIMESTRAL"}
    )
    assert resp2.json()["total"] == 0


@pytest.mark.asyncio
async def test_list_alerts_filter_tipo(client, db):
    await _seed_alerts(db, count=3)
    resp = await client.get(
        "/api/v1/alertas", params={"tipo_alerta": "BAJO_DESEMPEÑO", "modalidad": "CUATRIMESTRAL"}
    )
    assert resp.status_code == 200
    assert resp.json()["total"] == 1


@pytest.mark.asyncio
async def test_list_alerts_filter_estado(client, db):
    await _seed_alerts(db, count=3)
    resp = await client.get(
        "/api/v1/alertas", params={"estado": "activa", "modalidad": "CUATRIMESTRAL"}
    )
    assert resp.status_code == 200
    assert resp.json()["total"] == 3

    resp2 = await client.get(
        "/api/v1/alertas", params={"estado": "resuelta", "modalidad": "CUATRIMESTRAL"}
    )
    assert resp2.json()["total"] == 0


@pytest.mark.asyncio
async def test_list_alerts_response_fields(client, db):
    await _seed_alerts(db, count=1)
    resp = await client.get("/api/v1/alertas", params={"modalidad": "CUATRIMESTRAL"})
    item = resp.json()["items"][0]
    required_fields = {
        "id",
        "docente_nombre",
        "curso",
        "periodo",
        "modalidad",
        "tipo_alerta",
        "metrica_afectada",
        "valor_actual",
        "valor_anterior",
        "descripcion",
        "severidad",
        "estado",
        "created_at",
        "updated_at",
    }
    assert required_fields.issubset(item.keys())


# ═══════════════════════════════════════════════════════════════════════
# GET /api/v1/alertas/summary
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_summary_empty(client):
    resp = await client.get("/api/v1/alertas/summary", params={"modalidad": "CUATRIMESTRAL"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_activas"] == 0
    assert data["docentes_afectados"] == 0


@pytest.mark.asyncio
async def test_summary_with_data(client, db):
    await _seed_alerts(db, count=3)
    resp = await client.get("/api/v1/alertas/summary", params={"modalidad": "CUATRIMESTRAL"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_activas"] == 3
    assert data["docentes_afectados"] == 1
    assert "alta" in data["por_severidad"]
    assert "CUATRIMESTRAL" in data["por_modalidad"]
    assert len(data["por_tipo"]) >= 1


# ═══════════════════════════════════════════════════════════════════════
# POST /api/v1/alertas/rebuild
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_rebuild_empty_db(client):
    resp = await client.post("/api/v1/alertas/rebuild")
    assert resp.status_code == 200
    data = resp.json()
    assert data["candidates_generated"] == 0
    assert data["created_or_updated"] == 0
    assert data["modalidades_processed"] == 0


@pytest.mark.requires_postgres
@pytest.mark.asyncio
async def test_rebuild_generates_alerts(client, db):
    # Seed a low-scoring evaluacion → should trigger BAJO_DESEMPEÑO alert
    await _seed_evaluacion(db)
    resp = await client.post("/api/v1/alertas/rebuild")
    assert resp.status_code == 200
    data = resp.json()
    assert data["candidates_generated"] >= 1
    assert data["created_or_updated"] >= 1
    assert "CUATRIMESTRAL" in data["periodos_by_modalidad"]


@pytest.mark.requires_postgres
@pytest.mark.asyncio
async def test_rebuild_then_list(client, db):
    await _seed_evaluacion(db)
    await client.post("/api/v1/alertas/rebuild")

    resp = await client.get("/api/v1/alertas", params={"modalidad": "CUATRIMESTRAL"})
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


# ═══════════════════════════════════════════════════════════════════════
# PATCH /api/v1/alertas/{id}/estado
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_update_estado_success(client, db):
    _, alerts = await _seed_alerts(db, count=1)
    alerta_id = str(alerts[0].id)
    resp = await client.patch(f"/api/v1/alertas/{alerta_id}/estado", params={"estado": "revisada"})
    assert resp.status_code == 200
    assert resp.json()["estado"] == "revisada"


@pytest.mark.asyncio
async def test_update_estado_not_found(client):
    fake_id = str(uuid.uuid4())
    resp = await client.patch(f"/api/v1/alertas/{fake_id}/estado", params={"estado": "revisada"})
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_estado_invalid_state(client, db):
    _, alerts = await _seed_alerts(db, count=1)
    alerta_id = str(alerts[0].id)
    resp = await client.patch(f"/api/v1/alertas/{alerta_id}/estado", params={"estado": "invalido"})
    assert resp.status_code == 422
