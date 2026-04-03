from fastapi import APIRouter, UploadFile

from app.api.deps import DbSession, FileStorageDep
from app.application.services.document_service import DocumentService
from app.domain.schemas import DocumentoList, DocumentoUploadResponse
from app.infrastructure.repositories.documento import DocumentoRepository

router = APIRouter()


@router.post("/upload", response_model=DocumentoUploadResponse, status_code=201)
async def upload_documento(
    file: UploadFile,
    db: DbSession,
    storage: FileStorageDep,
):
    """Cargar un documento PDF para procesamiento."""
    content = await file.read()
    filename = (file.filename or "unknown.pdf").split("/")[-1].split("\\")[-1]
    content_type = file.content_type or "application/octet-stream"

    repo = DocumentoRepository(db)
    service = DocumentService(repo, storage)
    return await service.upload(filename, content, content_type)


@router.get("/", response_model=DocumentoList)
async def list_documentos(
    db: DbSession,
    page: int = 1,
    page_size: int = 20,
):
    """Listar documentos subidos con paginacion."""
    repo = DocumentoRepository(db)
    offset = (page - 1) * page_size
    items = await repo.list(offset=offset, limit=page_size)
    total = await repo.count()
    return {"items": items, "total": total, "page": page, "page_size": page_size}
