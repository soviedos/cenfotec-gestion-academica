import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile
from fastapi.responses import Response

from app.api.deps import DbSession, FileStorageDep, get_gemini_gateway
from app.modules.evaluacion_docente.application.services.document_service import DocumentService
from app.modules.evaluacion_docente.application.services.processing_service import ProcessingService
from app.modules.evaluacion_docente.domain.exceptions import GeminiUnavailableError
from app.modules.evaluacion_docente.domain.schemas.documento import (
    DocumentoFilterParams,
    DocumentoList,
    DocumentoUploadResponse,
    DuplicadoDocumentoRef,
    DuplicadoRead,
)
from app.modules.evaluacion_docente.infrastructure.external.gemini_gateway import GeminiGateway
from app.modules.evaluacion_docente.infrastructure.repositories.documento import DocumentoRepository
from app.modules.evaluacion_docente.infrastructure.repositories.duplicado_repo import (
    DuplicadoRepository,
)

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
    doc_uuid = uuid.UUID(documento_id)
    repo = DocumentoRepository(db)
    service = DocumentService(repo, storage)
    await service.delete_document(doc_uuid)
    await db.commit()


@router.get("/{documento_id}/duplicados", response_model=list[DuplicadoRead])
async def list_duplicados(
    documento_id: str,
    db: DbSession,
):
    """Listar los duplicados probables asociados a un documento."""
    doc_uuid = uuid.UUID(documento_id)
    doc_repo = DocumentoRepository(db)

    documento = await doc_repo.get_by_id(doc_uuid)
    if documento is None:
        raise HTTPException(status_code=404, detail="Documento no encontrado")

    dup_repo = DuplicadoRepository(db)
    findings = await dup_repo.list_by_documento(doc_uuid)

    results = []
    for f in findings:
        # Resolve the "other" document reference
        if f.documento_id == doc_uuid:
            other = f.documento_coincidente
        else:
            other = f.documento

        results.append(
            DuplicadoRead(
                id=f.id,
                documento_id=f.documento_id,
                documento_coincidente_id=f.documento_coincidente_id,
                documento_coincidente=DuplicadoDocumentoRef(
                    id=other.id,
                    nombre_archivo=other.nombre_archivo,
                ),
                fingerprint=f.fingerprint,
                score=float(f.score),
                criterios=f.criterios,
                estado=f.estado,
                notas=f.notas,
                created_at=f.created_at,
                updated_at=f.updated_at,
            )
        )
    return results


@router.get("/{documento_id}/download")
async def download_documento(
    documento_id: str,
    db: DbSession,
    storage: FileStorageDep,
):
    """Descargar el archivo PDF original de un documento."""
    doc_uuid = uuid.UUID(documento_id)
    repo = DocumentoRepository(db)
    documento = await repo.get_by_id(doc_uuid)
    if documento is None:
        raise HTTPException(status_code=404, detail="Documento no encontrado")

    pdf_bytes = await storage.download(documento.storage_path)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="{documento.nombre_archivo}"',
        },
    )
