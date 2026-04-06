from fastapi import APIRouter, BackgroundTasks, Depends, UploadFile

from app.api.deps import DbSession, FileStorageDep, get_gemini_gateway
from app.application.services.document_service import DocumentService
from app.application.services.processing_service import ProcessingService
from app.domain.exceptions import GeminiUnavailableError
from app.domain.schemas import DocumentoFilterParams, DocumentoList, DocumentoUploadResponse
from app.infrastructure.external.gemini_gateway import GeminiGateway
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

    # Gemini gateway is optional — enrichment degrades gracefully without it
    gemini_gw: GeminiGateway | None = None
    try:
        gemini_gw = get_gemini_gateway()
    except GeminiUnavailableError:
        pass

    processing = ProcessingService(db, storage, gemini_gateway=gemini_gw)
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


@router.get("/periodos", response_model=list[str])
async def list_periodos(db: DbSession):
    """Devolver lista de períodos distintos presentes en evaluaciones."""
    repo = DocumentoRepository(db)
    return await repo.distinct_periodos()


@router.delete("/{documento_id}", status_code=204)
async def delete_documento(
    documento_id: str,
    db: DbSession,
    storage: FileStorageDep,
):
    """Eliminar un documento y todos sus datos asociados (evaluaciones, comentarios, etc.)."""
    import uuid

    doc_uuid = uuid.UUID(documento_id)
    repo = DocumentoRepository(db)
    service = DocumentService(repo, storage)
    await service.delete_document(doc_uuid)
    await db.commit()
