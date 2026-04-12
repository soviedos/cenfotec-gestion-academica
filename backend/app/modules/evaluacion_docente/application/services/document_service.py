"""Document service — application-layer orchestration."""

import hashlib
import uuid

from app.modules.evaluacion_docente.domain.entities.documento import Documento
from app.modules.evaluacion_docente.domain.schemas.documento import DocumentoFilterParams
from app.modules.evaluacion_docente.infrastructure.repositories.documento import DocumentoRepository
from app.shared.domain.exceptions import DuplicateError, NotFoundError, ValidationError
from app.shared.infrastructure.storage.file_storage import FileStorage

ALLOWED_CONTENT_TYPES = {"application/pdf"}
PDF_MAGIC_BYTES = b"%PDF-"
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


class DocumentService:
    """Orchestrates document operations: upload, list, etc."""

    def __init__(self, repo: DocumentoRepository, storage: FileStorage | None = None) -> None:
        self.repo = repo
        self._storage = storage

    @property
    def storage(self) -> FileStorage:
        if self._storage is None:
            raise RuntimeError("FileStorage not configured for this operation")
        return self._storage

    async def upload(self, filename: str, content: bytes, content_type: str) -> Documento:
        """Upload a PDF document: validate, deduplicate, store, and persist."""
        self._validate(filename, content, content_type)

        hash_sha256 = hashlib.sha256(content).hexdigest()

        existing = await self.repo.get_by_hash(hash_sha256)
        if existing:
            raise DuplicateError(
                f"El archivo ya fue cargado previamente: {existing.nombre_archivo}"
            )

        storage_path = f"documentos/{uuid.uuid4().hex}.pdf"
        await self.storage.upload(storage_path, content, content_type)

        documento = Documento(
            nombre_archivo=filename,
            hash_sha256=hash_sha256,
            storage_path=storage_path,
            estado="subido",
            tamano_bytes=len(content),
        )
        try:
            return await self.repo.create(documento)
        except Exception:
            await self.storage.delete(storage_path)
            raise

    def _validate(self, filename: str, content: bytes, content_type: str) -> None:
        if not content:
            raise ValidationError("El archivo esta vacio")

        if len(content) > MAX_FILE_SIZE:
            raise ValidationError(
                f"El archivo excede el tamano maximo de {MAX_FILE_SIZE // (1024 * 1024)} MB"
            )

        if not filename.lower().endswith(".pdf"):
            raise ValidationError("Solo se aceptan archivos PDF (.pdf)")

        if content_type not in ALLOWED_CONTENT_TYPES:
            raise ValidationError(f"Tipo de contenido no valido: {content_type}")

        if not content[:5].startswith(PDF_MAGIC_BYTES):
            raise ValidationError("El contenido del archivo no corresponde a un PDF valido")

    async def list_documents(self, filters: DocumentoFilterParams) -> dict:
        """List documents with filters, pagination, and sorting."""
        offset = (filters.page - 1) * filters.page_size
        items = await self.repo.list_filtered(
            offset=offset,
            limit=filters.page_size,
            sort_by=filters.sort_by,
            sort_order=filters.sort_order,
            estado=filters.estado,
            docente=filters.docente,
            periodo=filters.periodo,
            nombre_archivo=filters.nombre_archivo,
            posible_duplicado=filters.posible_duplicado,
        )
        total = await self.repo.count_filtered(
            estado=filters.estado,
            docente=filters.docente,
            periodo=filters.periodo,
            nombre_archivo=filters.nombre_archivo,
            posible_duplicado=filters.posible_duplicado,
        )
        return {
            "items": items,
            "total": total,
            "page": filters.page,
            "page_size": filters.page_size,
        }

    async def delete_document(self, document_id: uuid.UUID) -> None:
        """Delete a document, its storage file, and all cascaded data."""
        documento = await self.repo.get_by_id(document_id)
        if not documento:
            raise NotFoundError("Documento", str(document_id))

        # Delete file from object storage (best-effort)
        if self._storage:
            try:
                await self.storage.delete(documento.storage_path)
            except Exception:
                pass  # Storage cleanup is best-effort; DB cascade is critical

        await self.repo.delete(documento)
        await self.repo.delete(documento)
