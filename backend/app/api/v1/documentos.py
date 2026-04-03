from fastapi import APIRouter

from app.api.deps import DbSession
from app.domain.schemas import DocumentoList
from app.infrastructure.repositories.documento import DocumentoRepository

router = APIRouter()


@router.get("/", response_model=DocumentoList)
async def list_documentos(
    db: DbSession,
    page: int = 1,
    page_size: int = 20,
):
    """Listar documentos subidos con paginación."""
    repo = DocumentoRepository(db)
    offset = (page - 1) * page_size
    items = await repo.list(offset=offset, limit=page_size)
    total = await repo.count()
    return {"items": items, "total": total, "page": page, "page_size": page_size}
