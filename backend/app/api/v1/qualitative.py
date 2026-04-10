"""Qualitative analysis endpoints — comment classification and sentiment.

Analytical qualitative endpoints **require** a ``modalidad`` parameter to
enforce the fundamental isolation rule [BR-MOD-02].  The ``/filtros`` endpoint
keeps it optional (dropdown population).
"""

from fastapi import APIRouter, Query

from app.api.deps import DbSession
from app.application.services.qualitative_service import QualitativeService
from app.domain.invariants import require_modalidad
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
    periodo: str | None = Query(None, max_length=50, description="Filtrar por período"),
    docente: str | None = Query(None, max_length=300, description="Filtrar por docente"),
    asignatura: str | None = Query(None, max_length=300, description="Filtrar por asignatura"),
    escuela: str | None = Query(None, max_length=300, description="Filtrar por escuela"),
    modalidad: str = Query(..., max_length=50, description="Modalidad (obligatorio) [BR-MOD-02]"),
):
    """Resumen de métricas cualitativas."""
    mod = require_modalidad(modalidad)
    svc = QualitativeService(db)
    return await svc.resumen(
        periodo=periodo,
        docente=docente,
        asignatura=asignatura,
        escuela=escuela,
        modalidad=mod,
    )


@router.get("/comentarios", response_model=list[ComentarioAnalisisRead])
async def listar_comentarios(
    db: DbSession,
    periodo: str | None = Query(None, max_length=50),
    docente: str | None = Query(None, max_length=300),
    asignatura: str | None = Query(None, max_length=300),
    escuela: str | None = Query(None, max_length=300),
    modalidad: str = Query(..., max_length=50, description="Modalidad (obligatorio) [BR-MOD-02]"),
    tipo: str | None = Query(None, max_length=20, description="fortaleza | mejora | observacion"),
    tema: str | None = Query(None, max_length=50),
    sentimiento: str | None = Query(
        None, max_length=10, description="positivo | neutro | mixto | negativo"
    ),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """Lista paginada de comentarios clasificados."""
    mod = require_modalidad(modalidad)
    svc = QualitativeService(db)
    items, _total = await svc.listar_comentarios(
        periodo=periodo,
        docente=docente,
        asignatura=asignatura,
        escuela=escuela,
        modalidad=mod,
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
    periodo: str | None = Query(None, max_length=50),
    docente: str | None = Query(None, max_length=300),
    asignatura: str | None = Query(None, max_length=300),
    escuela: str | None = Query(None, max_length=300),
    modalidad: str = Query(..., max_length=50, description="Modalidad (obligatorio) [BR-MOD-02]"),
    tipo: str | None = Query(None, max_length=20),
):
    """Distribución de comentarios por tema."""
    mod = require_modalidad(modalidad)
    svc = QualitativeService(db)
    return await svc.distribucion_temas(
        periodo=periodo,
        docente=docente,
        asignatura=asignatura,
        escuela=escuela,
        modalidad=mod,
        tipo=tipo,
    )


@router.get("/distribucion/sentimiento", response_model=list[SentimientoDistribucion])
async def distribucion_sentimiento(
    db: DbSession,
    periodo: str | None = Query(None, max_length=50),
    docente: str | None = Query(None, max_length=300),
    asignatura: str | None = Query(None, max_length=300),
    escuela: str | None = Query(None, max_length=300),
    modalidad: str = Query(..., max_length=50, description="Modalidad (obligatorio) [BR-MOD-02]"),
    tipo: str | None = Query(None, max_length=20),
    tema: str | None = Query(None, max_length=50),
):
    """Distribución de comentarios por sentimiento."""
    mod = require_modalidad(modalidad)
    svc = QualitativeService(db)
    return await svc.distribucion_sentimiento(
        periodo=periodo,
        docente=docente,
        asignatura=asignatura,
        escuela=escuela,
        modalidad=mod,
        tipo=tipo,
        tema=tema,
    )


@router.get("/nube-palabras", response_model=NubePalabras)
async def nube_palabras(
    db: DbSession,
    periodo: str | None = Query(None, max_length=50),
    docente: str | None = Query(None, max_length=300),
    asignatura: str | None = Query(None, max_length=300),
    escuela: str | None = Query(None, max_length=300),
    modalidad: str = Query(..., max_length=50, description="Modalidad (obligatorio) [BR-MOD-02]"),
    tipo: str | None = Query(None, max_length=20),
):
    """Frecuencia de palabras para visualización word-cloud."""
    mod = require_modalidad(modalidad)
    svc = QualitativeService(db)
    return await svc.nube_palabras(
        periodo=periodo,
        docente=docente,
        asignatura=asignatura,
        escuela=escuela,
        modalidad=mod,
        tipo=tipo,
    )
