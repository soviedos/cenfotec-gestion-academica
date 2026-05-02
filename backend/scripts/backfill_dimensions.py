"""Backfill evaluacion_dimensiones — re-extract dimensions from stored PDFs.

Fixes the issue where only 'Dominio' was being extracted due to
case-sensitive matching in KNOWN_DIMENSIONS.

Usage:
    .venv/bin/python scripts/backfill_dimensions.py
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys

# Ensure project root is on sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger(__name__)


async def main() -> None:
    from sqlalchemy import delete, select, text
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.orm import sessionmaker

    from app.modules.evaluacion_docente.application.parsing.extractors.metrics import (
        extract_metrics,
    )
    from app.modules.evaluacion_docente.application.parsing.parser import _extract_tables
    from app.modules.evaluacion_docente.domain.entities.evaluacion import Evaluacion
    from app.modules.evaluacion_docente.domain.entities.evaluacion_dimension import (
        EvaluacionDimension,
    )
    from app.shared.infrastructure.storage.file_storage import MinioFileStorage

    db_url = os.environ.get(
        "DATABASE_URL",
        "postgresql+asyncpg://eval_user:eval_pass_dev@localhost:5432/evaluaciones_docentes",
    )
    engine = create_async_engine(db_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    storage = MinioFileStorage()

    async with async_session() as db:
        # Get all evaluaciones with their documento storage_path
        result = await db.execute(
            text("""
                SELECT e.id, e.docente_nombre, d.storage_path
                FROM evaluaciones e
                JOIN documentos d ON e.documento_id = d.id
                WHERE e.estado = 'completado'
                ORDER BY e.docente_nombre
            """)
        )
        rows = result.fetchall()
        logger.info("Found %d evaluaciones to re-process dimensions", len(rows))

        updated = 0
        skipped = 0
        errors = 0

        for eval_id, docente, storage_path in rows:
            try:
                # Download PDF
                pdf_bytes = await storage.download(storage_path)
                if not pdf_bytes:
                    logger.warning("  SKIP %s — PDF not found at %s", docente, storage_path)
                    skipped += 1
                    continue

                # Extract tables from page 1
                import fitz

                doc = fitz.open(stream=pdf_bytes, filetype="pdf")
                if len(doc) == 0:
                    skipped += 1
                    continue
                page1_tables = _extract_tables(doc[0])
                doc.close()

                # Parse dimensions
                dimensiones, resumen_pct = extract_metrics(page1_tables)

                if not dimensiones:
                    logger.warning("  SKIP %s — no dimensions found", docente)
                    skipped += 1
                    continue

                # Delete old dimensions for this evaluation
                await db.execute(
                    delete(EvaluacionDimension).where(EvaluacionDimension.evaluacion_id == eval_id)
                )

                # Insert new dimensions
                for dim in dimensiones:
                    db.add(
                        EvaluacionDimension(
                            evaluacion_id=eval_id,
                            nombre=dim.nombre,
                            pct_estudiante=dim.estudiante.porcentaje,
                            pct_director=dim.director.porcentaje,
                            pct_autoeval=dim.autoevaluacion.porcentaje,
                            pct_promedio=dim.promedio_general_pct,
                        )
                    )

                # Also update datos_completos with the corrected dimensions
                datos_raw = (
                    await db.execute(
                        select(Evaluacion.datos_completos).where(Evaluacion.id == eval_id)
                    )
                ).scalar_one_or_none()
                if datos_raw:
                    datos = json.loads(datos_raw)
                    datos["dimensiones"] = [
                        {
                            "nombre": d.nombre,
                            "estudiante": {
                                "puntos_obtenidos": d.estudiante.puntos_obtenidos,
                                "puntos_maximos": d.estudiante.puntos_maximos,
                                "porcentaje": d.estudiante.porcentaje,
                            },
                            "director": {
                                "puntos_obtenidos": d.director.puntos_obtenidos,
                                "puntos_maximos": d.director.puntos_maximos,
                                "porcentaje": d.director.porcentaje,
                            },
                            "autoevaluacion": {
                                "puntos_obtenidos": d.autoevaluacion.puntos_obtenidos,
                                "puntos_maximos": d.autoevaluacion.puntos_maximos,
                                "porcentaje": d.autoevaluacion.porcentaje,
                            },
                            "promedio_general_puntos": d.promedio_general_puntos,
                            "promedio_general_pct": d.promedio_general_pct,
                        }
                        for d in dimensiones
                    ]
                    if resumen_pct:
                        datos["resumen_pct"] = {
                            "estudiante": resumen_pct.estudiante,
                            "director": resumen_pct.director,
                            "autoevaluacion": resumen_pct.autoevaluacion,
                            "promedio_general": resumen_pct.promedio_general,
                        }
                    await db.execute(
                        text("UPDATE evaluaciones SET datos_completos = :d WHERE id = :id"),
                        {"d": json.dumps(datos, ensure_ascii=False), "id": str(eval_id)},
                    )

                updated += 1
                dim_names = [d.nombre for d in dimensiones]
                logger.info("  OK  %s — %d dims: %s", docente, len(dimensiones), dim_names)

            except Exception as e:
                logger.error("  ERR %s — %s", docente, e)
                errors += 1

        await db.commit()
        logger.info(
            "Done: %d updated, %d skipped, %d errors (of %d total)",
            updated,
            skipped,
            errors,
            len(rows),
        )

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
