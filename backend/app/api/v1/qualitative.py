"""Qualitative analysis endpoints — comment classification and sentiment."""

from fastapi import APIRouter, Query

from app.api.deps import DbSession
from app.application.services.qualitative_service import QualitativeService
from app.domain.schemas.qualitative import (
    ComentarioAnalisisRead,
    FiltrosCualitativos,
    NubePalabras,
    ResumenCualitativo,
    SentimientoDistribucion,
    TemaDistribucion,
)

router = APIRouter()


@router.get("/filtros", response_model=FiltrosCualitativos)
async def filtros_disponibles(db: DbSession):
    """Opciones disponibles para filtros: periodos, docentes, asignaturas."""
    svc = QualitativeService(db)
    return await svc.filtros_disponibles()


@router.get("/resumen", response_model=ResumenCualitativo)
async def resumen_cualitativo(
    db: DbSession,
    periodo: str | None = Query(None, description="Filtrar por período"),
    docente: str | None = Query(None, description="Filtrar por docente"),
    asignatura: str | None = Query(None, description="Filtrar por asignatura"),
    escuela: str | None = Query(None, description="Filtrar por escuela"),
):
    """Resumen de métricas cualitativas."""
    svc = QualitativeService(db)
    return await svc.resumen(
        periodo=periodo, docente=docente,
        asignatura=asignatura, escuela=escuela,
    )


@router.get("/comentarios", response_model=list[ComentarioAnalisisRead])
async def listar_comentarios(
    db: DbSession,
    periodo: str | None = Query(None),
    docente: str | None = Query(None),
    asignatura: str | None = Query(None),
    escuela: str | None = Query(None),
    tipo: str | None = Query(None, description="fortaleza | mejora | observacion"),
    tema: str | None = Query(None),
    sentimiento: str | None = Query(None, description="positivo | neutro | mixto | negativo"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """Lista paginada de comentarios clasificados."""
    svc = QualitativeService(db)
    items, _total = await svc.listar_comentarios(
        periodo=periodo,
        docente=docente,
        asignatura=asignatura,
        escuela=escuela,
        tipo=tipo,
        tema=tema,
        sentimiento=sentimiento,
        limit=limit,
        offset=offset,
    )
    return items


@router.get("/distribucion/temas", response_model=list[TemaDistribucion])
async def distribucion_temas(
    db: DbSession,
    periodo: str | None = Query(None),
    docente: str | None = Query(None),
    asignatura: str | None = Query(None),
    escuela: str | None = Query(None),
    tipo: str | None = Query(None),
):
    """Distribución de comentarios por tema."""
    svc = QualitativeService(db)
    return await svc.distribucion_temas(
        periodo=periodo, docente=docente, asignatura=asignatura, escuela=escuela, tipo=tipo
    )


@router.get("/distribucion/sentimiento", response_model=list[SentimientoDistribucion])
async def distribucion_sentimiento(
    db: DbSession,
    periodo: str | None = Query(None),
    docente: str | None = Query(None),
    asignatura: str | None = Query(None),
    escuela: str | None = Query(None),
    tipo: str | None = Query(None),
    tema: str | None = Query(None),
):
    """Distribución de comentarios por sentimiento."""
    svc = QualitativeService(db)
    return await svc.distribucion_sentimiento(
        periodo=periodo, docente=docente,
        asignatura=asignatura, escuela=escuela,
        tipo=tipo, tema=tema,
    )


@router.get("/nube-palabras", response_model=NubePalabras)
async def nube_palabras(
    db: DbSession,
    periodo: str | None = Query(None),
    docente: str | None = Query(None),
    asignatura: str | None = Query(None),
    escuela: str | None = Query(None),
    tipo: str | None = Query(None),
):
    """Frecuencia de palabras para visualización word-cloud."""
    svc = QualitativeService(db)
    return await svc.nube_palabras(
        periodo=periodo, docente=docente, asignatura=asignatura, escuela=escuela, tipo=tipo
    )
