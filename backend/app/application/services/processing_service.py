"""Processing service — runs the parser on an uploaded document and persists results.

This service encapsulates the full processing pipeline:

1. Transition document to ``procesando``
2. Download PDF bytes from storage
3. Run the deterministic parser
4. Persist the ``Evaluacion`` record with extracted data
5. Transition document to ``procesado`` (or ``error``)

Currently runs in-process via ``BackgroundTasks``.  To migrate to Celery
later, wrap ``process_document()`` in a Celery task — the interface stays
the same.
"""

from __future__ import annotations

import json
import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.classification import classify_comment
from app.application.parsing.errors import ParseResult
from app.application.parsing.parser import parse_evaluacion
from app.domain.entities.comentario_analisis import ComentarioAnalisis
from app.domain.entities.evaluacion import Evaluacion
from app.domain.entities.evaluacion_curso import EvaluacionCurso
from app.domain.entities.evaluacion_dimension import EvaluacionDimension
from app.infrastructure.repositories.documento import DocumentoRepository
from app.infrastructure.repositories.evaluacion import EvaluacionRepository
from app.infrastructure.storage.file_storage import FileStorage

logger = logging.getLogger(__name__)


class ProcessingService:
    """Orchestrates document parsing and result persistence."""

    def __init__(
        self,
        db: AsyncSession,
        storage: FileStorage,
    ) -> None:
        self.db = db
        self.storage = storage
        self.doc_repo = DocumentoRepository(db)
        self.eval_repo = EvaluacionRepository(db)

    async def process_document(self, documento_id: uuid.UUID) -> None:
        """Run the full processing pipeline for one document.

        This method **never raises** — errors are captured and persisted
        on the document record so the user can see what went wrong.

        Uses a savepoint so that a failure during parsing/persistence can
        be rolled back without losing the ability to mark the document as
        ``error``.  The caller is responsible for the final ``commit()``.
        """
        doc = await self.doc_repo.get_by_id(documento_id)
        if doc is None:
            logger.error("Document %s not found, skipping processing", documento_id)
            return

        if doc.estado not in ("subido", "error"):
            logger.warning(
                "Document %s in state '%s', skipping processing",
                documento_id,
                doc.estado,
            )
            return

        # ── Step 1: Mark as processing ──────────────────────────────
        doc.estado = "procesando"
        doc.error_detalle = None
        await self.db.flush()

        try:
            nested = await self.db.begin_nested()
            try:
                # ── Step 2: Download PDF bytes ──────────────────────
                pdf_bytes = await self.storage.download(doc.storage_path)

                # ── Step 3: Run parser ──────────────────────────────
                result = parse_evaluacion(pdf_bytes)

                if result.success and result.data is not None:
                    # ── Step 4: Persist evaluation ──────────────────
                    await self._persist_evaluation(doc.id, result)
                    doc.estado = "procesado"
                    doc.error_detalle = None
                else:
                    doc.estado = "error"
                    doc.error_detalle = self._format_errors(result)

                await nested.commit()
            except Exception:
                await nested.rollback()
                raise

            await self.db.flush()

            logger.info(
                "Document %s processed: estado=%s",
                documento_id,
                doc.estado,
            )

        except Exception:
            logger.exception("Unexpected error processing document %s", documento_id)
            doc.estado = "error"
            doc.error_detalle = "Error inesperado durante el procesamiento"
            await self.db.flush()

    async def _persist_evaluation(
        self,
        documento_id: uuid.UUID,
        result: ParseResult,
    ) -> Evaluacion:
        """Create an Evaluacion record from a successful parse result."""
        data = result.data
        assert data is not None  # noqa: S101 — caller guarantees this

        # Store the full parsed data as JSON for downstream use
        datos_json = data.model_dump(mode="json")

        evaluacion = Evaluacion(
            documento_id=documento_id,
            docente_nombre=data.header.profesor_nombre,
            periodo=data.header.periodo,
            materia=None,  # Multi-course — stored in datos_json
            puntaje_general=data.resumen_pct.promedio_general,
            estado="completado",
            datos_completos=json.dumps(datos_json, ensure_ascii=False),
        )
        evaluacion = await self.eval_repo.create(evaluacion)

        # ── Persist normalized dimensions (for analytics) ───────────
        for dim in data.dimensiones:
            self.db.add(EvaluacionDimension(
                evaluacion_id=evaluacion.id,
                nombre=dim.nombre,
                pct_estudiante=dim.estudiante.porcentaje,
                pct_director=dim.director.porcentaje,
                pct_autoeval=dim.autoevaluacion.porcentaje,
                pct_promedio=dim.promedio_general_pct,
            ))

        # ── Persist normalized courses (for analytics) ──────────────
        for curso in data.cursos:
            self.db.add(EvaluacionCurso(
                evaluacion_id=evaluacion.id,
                escuela=curso.escuela,
                codigo=curso.codigo,
                nombre=curso.nombre,
                grupo=curso.grupo,
                respondieron=curso.estudiantes_respondieron,
                matriculados=curso.estudiantes_matriculados,
                pct_estudiante=curso.pct_estudiante,
                pct_director=curso.pct_director,
                pct_autoeval=curso.pct_autoevaluacion,
                pct_promedio=curso.pct_promedio_general,
            ))

        # ── Persist normalized comments (for qualitative analysis) ────
        for seccion in data.secciones_comentarios:
            for comentario in seccion.comentarios:
                for tipo_col, campo in (
                    ("fortaleza", comentario.fortaleza),
                    ("mejora", comentario.mejora),
                    ("observacion", comentario.observacion),
                ):
                    if not campo:
                        continue
                    cls = classify_comment(campo, tipo_col)
                    self.db.add(ComentarioAnalisis(
                        evaluacion_id=evaluacion.id,
                        fuente=seccion.tipo_evaluacion,
                        asignatura=seccion.asignatura,
                        tipo=tipo_col,
                        texto=campo,
                        tema=cls["tema"],
                        tema_confianza=cls["tema_confianza"],
                        sentimiento=cls["sentimiento"],
                        sent_score=cls["sent_score"],
                        procesado_ia=False,
                    ))

        await self.db.flush()
        return evaluacion

    @staticmethod
    def _format_errors(result: ParseResult) -> str:
        """Serialize parse errors to a human-readable string for error_detalle."""
        lines = []
        for err in result.errors:
            lines.append(f"[{err.stage}/{err.code}] {err.message}")
        return "\n".join(lines) if lines else "Error desconocido en el parser"
