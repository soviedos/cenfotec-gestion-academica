import pytest


@pytest.mark.asyncio
async def test_health_check(client):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "environment" in data


@pytest.mark.asyncio
async def test_list_evaluaciones(client):
    response = await client.get("/api/v1/evaluaciones/")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_list_documentos(client):
    response = await client.get("/api/v1/documentos/")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert data["total"] == 0
