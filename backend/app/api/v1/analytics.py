"""Analytics / BI dashboard endpoints.

All analytics endpoints accept an optional ``modalidad`` parameter to enforce
the fundamental isolation rule [BR-MOD-02].
"""

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


@router.get("/escuelas", response_model=list[str])
async def listar_escuelas(
    db: DbSession,
    modalidad: str | None = Query(None, description="Filtrar por modalidad"),
    periodo: str | None = Query(None, description="Filtrar por período"),
):
    """Escuelas disponibles para poblar filtros."""
    svc = AnalyticsService(db)
    return await svc.escuelas(modalidad=modalidad, periodo=periodo)


@router.get("/cursos", response_model=list[str])
async def listar_cursos(
    db: DbSession,
    escuela: str | None = Query(None, description="Filtrar por escuela"),
    modalidad: str | None = Query(None, description="Filtrar por modalidad"),
    periodo: str | None = Query(None, description="Filtrar por período"),
):
    """Cursos disponibles para poblar filtros."""
    svc = AnalyticsService(db)
    return await svc.cursos(escuela=escuela, modalidad=modalidad, periodo=periodo)


@router.get("/resumen", response_model=ResumenGeneral)
async def resumen_general(
    db: DbSession,
    periodo: str | None = Query(None, description="Filtrar por período"),
    modalidad: str | None = Query(None, description="Filtrar por modalidad [BR-MOD-02]"),
    escuela: str | None = Query(None, description="Filtrar por escuela"),
    curso: str | None = Query(None, description="Filtrar por curso"),
):
    """Tarjetas resumen del dashboard: promedio global, totales."""
    svc = AnalyticsService(db)
    return await svc.resumen(periodo=periodo, modalidad=modalidad, escuela=escuela, curso=curso)


@router.get("/docentes", response_model=list[DocentePromedio])
async def promedios_por_docente(
    db: DbSession,
    periodo: str | None = Query(None),
    modalidad: str | None = Query(None, description="Filtrar por modalidad [BR-MOD-02]"),
    escuela: str | None = Query(None, description="Filtrar por escuela"),
    curso: str | None = Query(None, description="Filtrar por curso"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """Promedio ponderado por docente."""
    svc = AnalyticsService(db)
    return await svc.promedios_docentes(
        periodo=periodo,
        modalidad=modalidad,
        escuela=escuela,
        curso=curso,
        limit=limit,
        offset=offset,
    )


@router.get("/dimensiones", response_model=list[DimensionPromedio])
async def promedios_por_dimension(
    db: DbSession,
    periodo: str | None = Query(None),
    docente: str | None = Query(None),
    modalidad: str | None = Query(None, description="Filtrar por modalidad [BR-MOD-02]"),
    escuela: str | None = Query(None, description="Filtrar por escuela"),
    curso: str | None = Query(None, description="Filtrar por curso"),
):
    """Promedios por dimensión (para gráfico radar)."""
    svc = AnalyticsService(db)
    return await svc.dimensiones(
        periodo=periodo,
        docente=docente,
        modalidad=modalidad,
        escuela=escuela,
        curso=curso,
    )


@router.get("/evolucion", response_model=list[PeriodoMetrica])
async def evolucion_periodos(
    db: DbSession,
    docente: str | None = Query(None),
    modalidad: str | None = Query(None, description="Filtrar por modalidad [BR-MOD-02]"),
    escuela: str | None = Query(None, description="Filtrar por escuela"),
    curso: str | None = Query(None, description="Filtrar por curso"),
):
    """Tendencia histórica: promedio por período."""
    svc = AnalyticsService(db)
    return await svc.evolucion(
        docente=docente,
        modalidad=modalidad,
        escuela=escuela,
        curso=curso,
    )


@router.get("/ranking", response_model=list[RankingDocente])
async def ranking_docentes(
    db: DbSession,
    periodo: str | None = Query(None),
    modalidad: str | None = Query(None, description="Filtrar por modalidad [BR-MOD-02]"),
    escuela: str | None = Query(None, description="Filtrar por escuela"),
    curso: str | None = Query(None, description="Filtrar por curso"),
    limit: int = Query(10, ge=1, le=100),
):
    """Ranking de docentes por promedio general."""
    svc = AnalyticsService(db)
    return await svc.ranking(
        periodo=periodo,
        modalidad=modalidad,
        escuela=escuela,
        curso=curso,
        limit=limit,
    )
