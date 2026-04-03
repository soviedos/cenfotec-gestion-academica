from fastapi import APIRouter

from app.domain.schemas import EvaluacionList

router = APIRouter()


@router.get("/", response_model=EvaluacionList)
async def list_evaluaciones():
    """Listar evaluaciones procesadas."""
    return {"items": [], "total": 0, "page": 1, "page_size": 20}
