"""One-shot script: re-classify ALL comments and enrich with Gemini.

Usage:
    cd backend && source .venv/bin/activate
    python _reanalyze_comments.py

Steps:
    1. Reset every ComentarioAnalisis row to keyword classification
    2. Send batches to Gemini for semantic enrichment
    3. Report summary
"""

import asyncio
import logging

from sqlalchemy import func, select

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-7s | %(message)s")
logger = logging.getLogger("reanalyze")


async def main() -> None:
    # Import inside main so .env is loaded first
    from app.core.config import settings
    from app.modules.evaluacion_docente.application.classification import classify_comment
    from app.modules.evaluacion_docente.application.services.gemini_enrichment_service import (
        GeminiEnrichmentService,
    )
    from app.modules.evaluacion_docente.domain.entities.comentario_analisis import (
        ComentarioAnalisis,
    )
    from app.modules.evaluacion_docente.domain.entities.evaluacion import Evaluacion
    from app.modules.evaluacion_docente.infrastructure.external.gemini_gateway import GeminiGateway
    from app.shared.infrastructure.database.session import async_session_factory
    from app.shared.infrastructure.database.session import engine as async_engine

    # ── Phase 0: Check state ────────────────────────────────────────
    async with async_session_factory() as db:
        total = (await db.execute(select(func.count(ComentarioAnalisis.id)))).scalar() or 0
        eval_count = (
            await db.execute(
                select(func.count(Evaluacion.id)).where(Evaluacion.estado == "completado")
            )
        ).scalar() or 0

    logger.info("Found %d comments across %d completed evaluations", total, eval_count)

    if total == 0:
        logger.warning("No comments to analyze. Upload some PDFs first.")
        await async_engine.dispose()
        return

    # ── Phase 1: Re-classify ALL with keyword rules ─────────────────
    logger.info("Phase 1: Re-classifying all %d comments with keyword rules...", total)

    reclassified = 0
    async with async_session_factory() as db:
        stmt = select(ComentarioAnalisis).order_by(ComentarioAnalisis.created_at)
        rows = list((await db.execute(stmt)).scalars().all())

        for row in rows:
            cls = classify_comment(row.texto, row.tipo)
            row.tema = cls["tema"]
            row.tema_confianza = "regla"
            row.sentimiento = cls["sentimiento"]
            row.sent_score = cls["sent_score"]
            row.procesado_ia = False
            reclassified += 1

        await db.commit()

    logger.info("Phase 1 complete: %d comments re-classified with keywords", reclassified)

    # ── Phase 2: Gemini enrichment ──────────────────────────────────
    api_key = settings.gemini_api_key.get_secret_value()
    if not api_key:
        logger.warning("GEMINI_API_KEY not set — skipping Gemini enrichment (keyword results kept)")
        await async_engine.dispose()
        return

    logger.info("Phase 2: Enriching comments with Gemini...")
    gateway = GeminiGateway(api_key=api_key)

    enriched_total = 0
    async with async_session_factory() as db:
        # Get all evaluation IDs that have comments
        eval_ids_stmt = (
            select(ComentarioAnalisis.evaluacion_id)
            .distinct()
            .order_by(ComentarioAnalisis.evaluacion_id)
        )
        eval_ids = list((await db.execute(eval_ids_stmt)).scalars().all())

    logger.info("Processing %d evaluations...", len(eval_ids))

    for i, eval_id in enumerate(eval_ids, 1):
        async with async_session_factory() as db:
            enrichment = GeminiEnrichmentService(db, gateway)
            try:
                count = await enrichment.enrich_evaluation_comments(eval_id)
                await db.commit()
                enriched_total += count
                logger.info(
                    "  [%d/%d] Evaluation %s: %d comments enriched",
                    i,
                    len(eval_ids),
                    eval_id,
                    count,
                )
            except Exception:
                logger.exception(
                    "  [%d/%d] Evaluation %s: enrichment failed", i, len(eval_ids), eval_id
                )

    # ── Summary ─────────────────────────────────────────────────────
    async with async_session_factory() as db:
        ia_count = (
            await db.execute(
                select(func.count(ComentarioAnalisis.id)).where(
                    ComentarioAnalisis.procesado_ia.is_(True)
                )
            )
        ).scalar() or 0

    logger.info("=" * 60)
    logger.info("DONE")
    logger.info("  Total comments:       %d", total)
    logger.info("  Keyword-classified:   %d", reclassified)
    logger.info("  Gemini-enriched:      %d", enriched_total)
    logger.info("  procesado_ia = True:  %d", ia_count)
    logger.info("=" * 60)

    await async_engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
