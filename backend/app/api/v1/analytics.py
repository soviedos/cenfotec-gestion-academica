"""Analytics / BI dashboard endpoints."""

from fastapi import APIRouter, Query

from app.api.deps import DbSession
from app.application.services.analytics_service import AnalyticsService
from app.domain.schemas.analytics import (
    DimensionPromedio,
    DocentePromedio,
    PeriodoMetrica,
    RankingDocente,
    ResumenGeneral,
)

router = APIRouter()


@router.get("/resumen", response_model=ResumenGeneral)
async def resumen_general(
    db: DbSession,
    periodo: str | None = Query(None, description="Filtrar por período"),
):
    """Tarjetas resumen del dashboard: promedio global, totales."""
    svc = AnalyticsService(db)
    return await svc.resumen(periodo=periodo)


@router.get("/docentes", response_model=list[DocentePromedio])
async def promedios_por_docente(
    db: DbSession,
    periodo: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """Promedio ponderado por docente."""
    svc = AnalyticsService(db)
    return await svc.promedios_docentes(periodo=periodo, limit=limit, offset=offset)


@router.get("/dimensiones", response_model=list[DimensionPromedio])
async def promedios_por_dimension(
    db: DbSession,
    periodo: str | None = Query(None),
    docente: str | None = Query(None),
):
    """Promedios por dimensión (para gráfico radar)."""
    svc = AnalyticsService(db)
    return await svc.dimensiones(periodo=periodo, docente=docente)


@router.get("/evolucion", response_model=list[PeriodoMetrica])
async def evolucion_periodos(
    db: DbSession,
    docente: str | None = Query(None),
):
    """Tendencia histórica: promedio por período."""
    svc = AnalyticsService(db)
    return await svc.evolucion(docente=docente)


@router.get("/ranking", response_model=list[RankingDocente])
async def ranking_docentes(
    db: DbSession,
    periodo: str | None = Query(None),
    limit: int = Query(10, ge=1, le=100),
):
    """Ranking de docentes por promedio general."""
    svc = AnalyticsService(db)
    return await svc.ranking(periodo=periodo, limit=limit)
