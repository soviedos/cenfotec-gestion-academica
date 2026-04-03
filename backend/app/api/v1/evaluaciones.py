from fastapi import APIRouter

from app.api.deps import DbSession
from app.domain.schemas import EvaluacionList
from app.infrastructure.repositories.evaluacion import EvaluacionRepository

router = APIRouter()


@router.get("/", response_model=EvaluacionList)
async def list_evaluaciones(
    db: DbSession,
    page: int = 1,
    page_size: int = 20,
):
    """Listar evaluaciones procesadas con paginación."""
    repo = EvaluacionRepository(db)
    offset = (page - 1) * page_size
    items = await repo.list(offset=offset, limit=page_size)
    total = await repo.count()
    return {"items": items, "total": total, "page": page, "page_size": page_size}
