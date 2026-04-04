"""API tests for qualitative analysis endpoints."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from tests.fixtures.factories import make_comentario, make_documento, make_evaluacion


async def _seed(db: AsyncSession) -> None:
    """Insert test comments for API tests."""
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

    db.add_all([
        make_comentario(
            evaluacion_id=eval1.id,
            tipo="fortaleza",
            texto="Explica de forma clara",
            tema="comunicacion",
            sentimiento="positivo",
            sent_score=0.80,
        ),
        make_comentario(
            evaluacion_id=eval1.id,
            tipo="mejora",
            texto="No es puntual",
            tema="puntualidad",
            sentimiento="negativo",
            sent_score=-0.50,
        ),
        make_comentario(
            evaluacion_id=eval1.id,
            tipo="observacion",
            texto="Clase normal sin novedades",
            tema="otro",
            sentimiento="neutro",
            sent_score=0.0,
        ),
    ])
    await db.flush()


# ── GET /resumen ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_resumen_empty(client):
    resp = await client.get("/api/v1/qualitative/resumen")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_comentarios"] == 0


@pytest.mark.asyncio
async def test_resumen_with_data(client, db):
    await _seed(db)
    resp = await client.get("/api/v1/qualitative/resumen")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_comentarios"] == 3
    assert len(data["por_tipo"]) > 0
    assert len(data["por_sentimiento"]) > 0
    assert len(data["temas_top"]) > 0


@pytest.mark.asyncio
async def test_resumen_filter_periodo(client, db):
    await _seed(db)
    resp = await client.get("/api/v1/qualitative/resumen?periodo=2025-1")
    assert resp.status_code == 200
    assert resp.json()["total_comentarios"] == 3

    resp2 = await client.get("/api/v1/qualitative/resumen?periodo=9999-9")
    assert resp2.status_code == 200
    assert resp2.json()["total_comentarios"] == 0


# ── GET /comentarios ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_comentarios_empty(client):
    resp = await client.get("/api/v1/qualitative/comentarios")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_comentarios_with_data(client, db):
    await _seed(db)
    resp = await client.get("/api/v1/qualitative/comentarios")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 3
    # Each comment has required fields
    item = data[0]
    assert "id" in item
    assert "tipo" in item
    assert "tema" in item
    assert "sentimiento" in item


@pytest.mark.asyncio
async def test_comentarios_filter_tipo(client, db):
    await _seed(db)
    resp = await client.get("/api/v1/qualitative/comentarios?tipo=fortaleza")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


@pytest.mark.asyncio
async def test_comentarios_pagination(client, db):
    await _seed(db)
    resp = await client.get("/api/v1/qualitative/comentarios?limit=2&offset=0")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


# ── GET /distribucion/temas ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_temas_empty(client):
    resp = await client.get("/api/v1/qualitative/distribucion/temas")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_temas_with_data(client, db):
    await _seed(db)
    resp = await client.get("/api/v1/qualitative/distribucion/temas")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 3
    temas = {d["tema"] for d in data}
    assert "comunicacion" in temas


# ── GET /distribucion/sentimiento ────────────────────────────────────────


@pytest.mark.asyncio
async def test_sentimiento_empty(client):
    resp = await client.get("/api/v1/qualitative/distribucion/sentimiento")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_sentimiento_with_data(client, db):
    await _seed(db)
    resp = await client.get("/api/v1/qualitative/distribucion/sentimiento")
    assert resp.status_code == 200
    data = resp.json()
    sentimientos = {d["sentimiento"] for d in data}
    assert "positivo" in sentimientos
    assert "negativo" in sentimientos


# ── GET /nube-palabras ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_nube_empty(client):
    resp = await client.get("/api/v1/qualitative/nube-palabras")
    assert resp.status_code == 200
    data = resp.json()
    assert data["tipo"] == "all"
    assert data["palabras"] == []


@pytest.mark.asyncio
async def test_nube_with_data(client, db):
    await _seed(db)
    resp = await client.get("/api/v1/qualitative/nube-palabras")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["palabras"]) > 0


@pytest.mark.asyncio
async def test_nube_filter_tipo(client, db):
    await _seed(db)
    resp = await client.get("/api/v1/qualitative/nube-palabras?tipo=fortaleza")
    assert resp.status_code == 200
    assert resp.json()["tipo"] == "fortaleza"
