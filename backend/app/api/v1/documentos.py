from fastapi import APIRouter, BackgroundTasks, Depends, UploadFile

from app.api.deps import DbSession, FileStorageDep
from app.application.services.document_service import DocumentService
from app.application.services.processing_service import ProcessingService
from app.domain.schemas import DocumentoFilterParams, DocumentoList, DocumentoUploadResponse
from app.infrastructure.repositories.documento import DocumentoRepository

router = APIRouter()


@router.post("/upload", response_model=DocumentoUploadResponse, status_code=201)
async def upload_documento(
    file: UploadFile,
    db: DbSession,
    storage: FileStorageDep,
    background_tasks: BackgroundTasks,
):
    """Cargar un documento PDF para procesamiento."""
    content = await file.read()
    filename = (file.filename or "unknown.pdf").split("/")[-1].split("\\")[-1]
    content_type = file.content_type or "application/octet-stream"

    repo = DocumentoRepository(db)
    service = DocumentService(repo, storage)
    documento = await service.upload(filename, content, content_type)

    processing = ProcessingService(db, storage)
    background_tasks.add_task(processing.process_document, documento.id)

    return documento


@router.get("/", response_model=DocumentoList)
async def list_documentos(
    db: DbSession,
    filters: DocumentoFilterParams = Depends(),
):
    """Listar documentos con filtros, paginación y ordenamiento."""
    repo = DocumentoRepository(db)
    service = DocumentService(repo)
    return await service.list_documents(filters)
