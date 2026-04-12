"""Integration tests for AnalyticsRepository — aggregate queries."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.repositories.analytics_repo import AnalyticsRepository
from tests.fixtures.factories import make_dimension, make_documento, make_evaluacion

# ── Helpers ─────────────────────────────────────────────────────────────


async def _seed_evaluaciones(db: AsyncSession) -> dict:
    """Seed the DB with two docentes across two periods and return references."""
    doc1 = make_documento()
    doc2 = make_documento()
    doc3 = make_documento()
    db.add_all([doc1, doc2, doc3])
    await db.flush()

    eval1 = make_evaluacion(
        documento_id=doc1.id,
        docente_nombre="Prof. García",
        periodo="2025-1",
        año=2025,
        periodo_orden=1,
        puntaje_general=85.0,
        estado="completado",
    )
    eval2 = make_evaluacion(
        documento_id=doc2.id,
        docente_nombre="Prof. López",
        periodo="2025-1",
        año=2025,
        periodo_orden=1,
        puntaje_general=90.0,
        estado="completado",
    )
    eval3 = make_evaluacion(
        documento_id=doc3.id,
        docente_nombre="Prof. García",
        periodo="2025-2",
        año=2025,
        periodo_orden=2,
        puntaje_general=88.0,
        estado="completado",
    )
    db.add_all([eval1, eval2, eval3])
    await db.flush()

    # Dimensions for eval1
    db.add(make_dimension(evaluacion_id=eval1.id, nombre="Metodología", pct_promedio=80.0))
    db.add(make_dimension(evaluacion_id=eval1.id, nombre="Dominio", pct_promedio=85.0))
    # Dimensions for eval2
    db.add(make_dimension(evaluacion_id=eval2.id, nombre="Metodología", pct_promedio=92.0))
    db.add(make_dimension(evaluacion_id=eval2.id, nombre="Dominio", pct_promedio=88.0))
    # Dimensions for eval3
    db.add(make_dimension(evaluacion_id=eval3.id, nombre="Metodología", pct_promedio=86.0))
    db.add(make_dimension(evaluacion_id=eval3.id, nombre="Dominio", pct_promedio=90.0))
    await db.flush()

    return {
        "eval1": eval1,
        "eval2": eval2,
        "eval3": eval3,
        "doc1": doc1,
        "doc2": doc2,
        "doc3": doc3,
    }


# ── Tests ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_resumen_global_empty(db):
    repo = AnalyticsRepository(db)
    result = await repo.resumen_global()
    assert result["total_evaluaciones"] == 0
    assert result["promedio_global"] == 0.0


@pytest.mark.asyncio
async def test_resumen_global_with_data(db):
    await _seed_evaluaciones(db)
    repo = AnalyticsRepository(db)
    result = await repo.resumen_global()
    assert result["total_evaluaciones"] == 3
    assert result["total_docentes"] == 2
    assert result["total_periodos"] == 2
    # (85 + 90 + 88) / 3 = 87.67
    assert result["promedio_global"] == pytest.approx(87.67, abs=0.01)


@pytest.mark.asyncio
async def test_resumen_global_filter_by_periodo(db):
    await _seed_evaluaciones(db)
    repo = AnalyticsRepository(db)
    result = await repo.resumen_global(periodo="2025-1")
    assert result["total_evaluaciones"] == 2
    assert result["total_docentes"] == 2
    assert result["total_periodos"] == 1


@pytest.mark.asyncio
async def test_promedios_por_docente(db):
    await _seed_evaluaciones(db)
    repo = AnalyticsRepository(db)
    rows = await repo.promedios_por_docente()
    assert len(rows) == 2
    # López (90) first, then García (86.5)
    assert rows[0]["docente_nombre"] == "Prof. López"
    assert rows[0]["promedio"] == 90.0
    assert rows[1]["docente_nombre"] == "Prof. García"
    assert rows[1]["promedio"] == pytest.approx(86.5, abs=0.01)
    assert rows[1]["evaluaciones_count"] == 2


@pytest.mark.asyncio
async def test_promedios_por_docente_filter_periodo(db):
    await _seed_evaluaciones(db)
    repo = AnalyticsRepository(db)
    rows = await repo.promedios_por_docente(periodo="2025-2")
    assert len(rows) == 1
    assert rows[0]["docente_nombre"] == "Prof. García"


@pytest.mark.asyncio
async def test_promedios_por_dimension(db):
    await _seed_evaluaciones(db)
    repo = AnalyticsRepository(db)
    rows = await repo.promedios_por_dimension()
    assert len(rows) == 2
    dims = {r["dimension"]: r for r in rows}
    assert "Dominio" in dims
    assert "Metodología" in dims
    # Dominio: (85 + 88 + 90) / 3 = 87.67
    assert dims["Dominio"]["pct_promedio"] == pytest.approx(87.67, abs=0.01)


@pytest.mark.asyncio
async def test_promedios_por_dimension_filter_docente(db):
    await _seed_evaluaciones(db)
    repo = AnalyticsRepository(db)
    rows = await repo.promedios_por_dimension(docente="Prof. López")
    assert len(rows) == 2
    dims = {r["dimension"]: r for r in rows}
    assert dims["Metodología"]["pct_promedio"] == 92.0


@pytest.mark.asyncio
async def test_evolucion_periodos(db):
    await _seed_evaluaciones(db)
    repo = AnalyticsRepository(db)
    rows = await repo.evolucion_periodos()
    assert len(rows) == 2
    assert rows[0]["periodo"] == "2025-1"
    assert rows[1]["periodo"] == "2025-2"
    # 2025-1: (85+90)/2 = 87.5
    assert rows[0]["promedio"] == pytest.approx(87.5, abs=0.01)
    assert rows[0]["año"] == 2025
    assert rows[0]["periodo_orden"] == 1
    assert rows[1]["año"] == 2025
    assert rows[1]["periodo_orden"] == 2


@pytest.mark.asyncio
async def test_evolucion_filter_docente(db):
    await _seed_evaluaciones(db)
    repo = AnalyticsRepository(db)
    rows = await repo.evolucion_periodos(docente="Prof. García")
    assert len(rows) == 2
    assert rows[0]["evaluaciones_count"] == 1
    assert rows[1]["evaluaciones_count"] == 1


@pytest.mark.asyncio
async def test_ranking_docentes(db):
    await _seed_evaluaciones(db)
    repo = AnalyticsRepository(db)
    rows = await repo.ranking_docentes(limit=5)
    assert len(rows) == 2
    assert rows[0]["posicion"] == 1
    assert rows[0]["docente_nombre"] == "Prof. López"
    assert rows[1]["posicion"] == 2
    assert rows[1]["docente_nombre"] == "Prof. García"


@pytest.mark.asyncio
async def test_ranking_respects_limit(db):
    await _seed_evaluaciones(db)
    repo = AnalyticsRepository(db)
    rows = await repo.ranking_docentes(limit=1)
    assert len(rows) == 1


@pytest.mark.asyncio
async def test_ignores_non_completado(db):
    """Evaluaciones not in estado='completado' are excluded from analytics."""
    doc = make_documento()
    db.add(doc)
    await db.flush()
    eval_ = make_evaluacion(
        documento_id=doc.id,
        estado="pendiente",
        puntaje_general=99.0,
    )
    db.add(eval_)
    await db.flush()

    repo = AnalyticsRepository(db)
    result = await repo.resumen_global()
    assert result["total_evaluaciones"] == 0
