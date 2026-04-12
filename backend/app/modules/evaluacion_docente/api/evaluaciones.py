from fastapi import APIRouter, Query

from app.api.deps import DbSession
from app.modules.evaluacion_docente.domain.schemas.evaluacion import EvaluacionList
from app.modules.evaluacion_docente.infrastructure.repositories.evaluacion import (
    EvaluacionRepository,
)

router = APIRouter()


@router.get("/", response_model=EvaluacionList)
async def list_evaluaciones(
    db: DbSession,
    page: int = 1,
    page_size: int = 20,
    modalidad: str | None = Query(None, description="Filtrar por modalidad [BR-MOD-02]"),
    periodo: str | None = Query(None, description="Filtrar por período"),
    docente: str | None = Query(None, description="Filtrar por docente"),
    estado: str | None = Query(None, description="Filtrar por estado"),
):
    """Listar evaluaciones procesadas con paginación y filtros."""
    repo = EvaluacionRepository(db)
    offset = (page - 1) * page_size
    items = await repo.list_filtered(
        modalidad=modalidad,
        periodo=periodo,
        docente=docente,
        estado=estado,
        offset=offset,
        limit=page_size,
    )
    total = await repo.count_filtered(
        modalidad=modalidad,
        periodo=periodo,
        docente=docente,
        estado=estado,
    )
    return {"items": items, "total": total, "page": page, "page_size": page_size}
