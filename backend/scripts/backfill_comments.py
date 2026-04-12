"""Backfill comentario_analisis by re-parsing PDFs from MinIO.

The original parsing missed comments because of a header-detection bug.
This script downloads each PDF, re-extracts comments with the fixed parser,
classifies them, and inserts into comentario_analisis.  It also patches the
datos_completos JSON so future reads include the comment data.

Run once:  .venv/bin/python _backfill_comments.py
"""

import asyncio
import json
import logging

import sqlalchemy as sa

from app.modules.evaluacion_docente.application.classification import classify_comment
from app.modules.evaluacion_docente.application.parsing.parser import parse_evaluacion
from app.modules.evaluacion_docente.domain.entities.comentario_analisis import ComentarioAnalisis
from app.shared.infrastructure.database.session import async_session_factory, engine
from app.shared.infrastructure.storage.file_storage import MinioFileStorage

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger(__name__)

BATCH_SIZE = 25


async def backfill():
    storage = MinioFileStorage()

    # Current count
    async with async_session_factory() as s:
        r = await s.execute(sa.text("SELECT count(*) FROM comentario_analisis"))
        log.info("Existing comentario_analisis rows: %d", r.scalar())

    # Fetch evaluaciones joined with their documento storage path
    async with async_session_factory() as s:
        r = await s.execute(
            sa.text(
                "SELECT e.id, e.datos_completos, d.storage_path "
                "FROM evaluaciones e "
                "JOIN documentos d ON d.id = e.documento_id "
                "WHERE e.estado = 'completado' "
                "  AND d.storage_path IS NOT NULL"
            )
        )
        rows = r.fetchall()

    log.info("Evaluaciones to backfill: %d", len(rows))

    total_comments = 0
    skipped = 0
    errors = 0

    for i in range(0, len(rows), BATCH_SIZE):
        batch = rows[i : i + BATCH_SIZE]
        async with async_session_factory() as s:
            for eval_id, datos_str, storage_path in batch:
                # Skip if already backfilled
                r = await s.execute(
                    sa.text("SELECT count(*) FROM comentario_analisis WHERE evaluacion_id = :eid"),
                    {"eid": eval_id},
                )
                if r.scalar() > 0:
                    skipped += 1
                    continue

                # Download PDF from MinIO
                try:
                    pdf_bytes = await storage.download(storage_path)
                except Exception as exc:
                    log.warning("  SKIP %s – download error: %s", eval_id, exc)
                    errors += 1
                    continue

                # Re-parse to extract comments
                result = parse_evaluacion(pdf_bytes)
                if not result.data:
                    errors += 1
                    continue

                secciones = result.data.secciones_comentarios
                if not secciones:
                    continue  # PDF genuinely has no comments

                # Insert classified comments
                eval_comment_count = 0
                for seccion in secciones:
                    for comentario in seccion.comentarios:
                        for tipo_col, campo in (
                            ("fortaleza", comentario.fortaleza),
                            ("mejora", comentario.mejora),
                            ("observacion", comentario.observacion),
                        ):
                            if not campo:
                                continue
                            cls = classify_comment(campo, tipo_col)
                            s.add(
                                ComentarioAnalisis(
                                    evaluacion_id=eval_id,
                                    fuente=seccion.tipo_evaluacion,
                                    asignatura=seccion.asignatura,
                                    tipo=tipo_col,
                                    texto=campo,
                                    tema=cls["tema"],
                                    tema_confianza=cls["tema_confianza"],
                                    sentimiento=cls["sentimiento"],
                                    sent_score=cls["sent_score"],
                                    procesado_ia=False,
                                )
                            )
                            eval_comment_count += 1

                total_comments += eval_comment_count

                # Patch datos_completos JSON with the new comment data
                if datos_str:
                    try:
                        datos = json.loads(datos_str)
                        datos["secciones_comentarios"] = [
                            sec.model_dump(mode="json") for sec in secciones
                        ]
                        await s.execute(
                            sa.text(
                                "UPDATE evaluaciones SET datos_completos = :json WHERE id = :eid"
                            ),
                            {
                                "json": json.dumps(datos, ensure_ascii=False),
                                "eid": eval_id,
                            },
                        )
                    except Exception as exc:
                        log.warning("  JSON patch error for %s: %s", eval_id, exc)

            await s.commit()
            log.info(
                "  batch %d-%d committed  (comments so far: %d, errors: %d)",
                i + 1,
                min(i + BATCH_SIZE, len(rows)),
                total_comments,
                errors,
            )

    log.info(
        "Done. Inserted: %d  Skipped (existing): %d  Errors: %d",
        total_comments,
        skipped,
        errors,
    )

    async with async_session_factory() as s:
        r = await s.execute(sa.text("SELECT count(*) FROM comentario_analisis"))
        log.info("Final comentario_analisis rows: %d", r.scalar())

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(backfill())
