from fastapi import APIRouter

from app.domain.schemas import DocumentoList

router = APIRouter()


@router.get("/", response_model=DocumentoList)
async def list_documentos():
    """Listar documentos subidos."""
    return {"items": [], "total": 0, "page": 1, "page_size": 20}
