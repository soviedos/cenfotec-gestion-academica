"""Integration tests for QualitativeRepository."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.repositories.qualitative_repo import QualitativeRepository
from tests.fixtures.factories import make_comentario, make_documento, make_evaluacion


async def _seed(db: AsyncSession) -> dict:
    """Seed comments for 2 docentes, 2 temas, 2 sentimientos."""
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
    eval2 = make_evaluacion(
        documento_id=doc.id,
        docente_nombre="Prof. López",
        periodo="2025-2",
        puntaje_general=85.0,
        estado="completado",
    )
    db.add_all([eval1, eval2])
    await db.flush()

    comments = [
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
            tipo="fortaleza",
            texto="Excelente dominio del tema",
            tema="dominio_tema",
            sentimiento="positivo",
            sent_score=0.90,
        ),
        make_comentario(
            evaluacion_id=eval1.id,
            tipo="mejora",
            texto="No es puntual con las clases",
            tema="puntualidad",
            sentimiento="negativo",
            sent_score=-0.60,
        ),
        make_comentario(
            evaluacion_id=eval2.id,
            tipo="fortaleza",
            texto="Muy buena metodología de enseñanza",
            tema="metodologia",
            sentimiento="positivo",
            sent_score=0.70,
        ),
        make_comentario(
            evaluacion_id=eval2.id,
            tipo="observacion",
            texto="Algo genérico sin contexto",
            tema="otro",
            sentimiento="neutro",
            sent_score=0.0,
        ),
    ]
    db.add_all(comments)
    await db.flush()

    return {
        "eval1_id": eval1.id,
        "eval2_id": eval2.id,
        "total_comments": len(comments),
    }


@pytest.mark.asyncio
async def test_resumen_empty(db):
    repo = QualitativeRepository(db)
    result = await repo.resumen()
    assert result["total_comentarios"] == 0
    assert result["sentimiento_promedio"] is None


@pytest.mark.asyncio
async def test_resumen_with_data(db):
    seed = await _seed(db)
    repo = QualitativeRepository(db)
    result = await repo.resumen()

    assert result["total_comentarios"] == seed["total_comments"]
    assert len(result["por_tipo"]) > 0
    assert len(result["por_sentimiento"]) > 0
    assert len(result["temas_top"]) > 0
    assert result["sentimiento_promedio"] is not None


@pytest.mark.asyncio
async def test_resumen_filtered_by_docente(db):
    await _seed(db)
    repo = QualitativeRepository(db)
    result = await repo.resumen(docente="Prof. García")

    assert result["total_comentarios"] == 3


@pytest.mark.asyncio
async def test_resumen_filtered_by_periodo(db):
    await _seed(db)
    repo = QualitativeRepository(db)
    result = await repo.resumen(periodo="2025-2")

    assert result["total_comentarios"] == 2


@pytest.mark.asyncio
async def test_listar_comentarios_all(db):
    seed = await _seed(db)
    repo = QualitativeRepository(db)
    items = await repo.listar_comentarios()

    assert len(items) == seed["total_comments"]


@pytest.mark.asyncio
async def test_listar_comentarios_filtered(db):
    await _seed(db)
    repo = QualitativeRepository(db)

    items = await repo.listar_comentarios(tipo="fortaleza")
    assert len(items) == 3

    items = await repo.listar_comentarios(tema="comunicacion")
    assert len(items) == 1

    items = await repo.listar_comentarios(sentimiento="negativo")
    assert len(items) == 1


@pytest.mark.asyncio
async def test_listar_comentarios_pagination(db):
    await _seed(db)
    repo = QualitativeRepository(db)

    page1 = await repo.listar_comentarios(limit=2, offset=0)
    page2 = await repo.listar_comentarios(limit=2, offset=2)
    assert len(page1) == 2
    assert len(page2) == 2


@pytest.mark.asyncio
async def test_contar_comentarios(db):
    seed = await _seed(db)
    repo = QualitativeRepository(db)

    total = await repo.contar_comentarios()
    assert total == seed["total_comments"]

    filtered = await repo.contar_comentarios(tipo="mejora")
    assert filtered == 1


@pytest.mark.asyncio
async def test_distribucion_temas(db):
    await _seed(db)
    repo = QualitativeRepository(db)
    temas = await repo.distribucion_temas()

    assert len(temas) > 0
    temas_dict = {t["tema"]: t for t in temas}
    assert "comunicacion" in temas_dict
    assert temas_dict["comunicacion"]["count"] == 1
    # porcentajes should sum to ~100
    total_pct = sum(t["porcentaje"] for t in temas)
    assert 99.0 <= total_pct <= 101.0


@pytest.mark.asyncio
async def test_distribucion_temas_empty(db):
    repo = QualitativeRepository(db)
    result = await repo.distribucion_temas()
    assert result == []


@pytest.mark.asyncio
async def test_distribucion_sentimiento(db):
    await _seed(db)
    repo = QualitativeRepository(db)
    sents = await repo.distribucion_sentimiento()

    assert len(sents) > 0
    sents_dict = {s["sentimiento"]: s for s in sents}
    assert "positivo" in sents_dict
    assert sents_dict["positivo"]["count"] == 3


@pytest.mark.asyncio
async def test_distribucion_sentimiento_filtered(db):
    await _seed(db)
    repo = QualitativeRepository(db)
    sents = await repo.distribucion_sentimiento(tipo="fortaleza")

    # All 3 fortalezas are positivo
    assert len(sents) == 1
    assert sents[0]["sentimiento"] == "positivo"


@pytest.mark.asyncio
async def test_nube_palabras(db):
    await _seed(db)
    repo = QualitativeRepository(db)
    words = await repo.nube_palabras()

    assert len(words) > 0
    texts = [w["text"] for w in words]
    # "explica" should appear (from "Explica de forma clara")
    assert any("explic" in t for t in texts) or any("clara" in t for t in texts)


@pytest.mark.asyncio
async def test_nube_palabras_empty(db):
    repo = QualitativeRepository(db)
    words = await repo.nube_palabras()
    assert words == []
    assert words == []
    assert words == []
    assert words == []
