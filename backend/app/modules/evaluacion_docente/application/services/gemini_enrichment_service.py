"""GeminiEnrichmentService — post-processing enrichment of comments via Gemini.

After the deterministic keyword classifier assigns initial tema/sentimiento
values, this service sends comment batches to Gemini for deeper semantic
analysis.  It updates existing ``ComentarioAnalisis`` rows in-place and
sets ``procesado_ia = True``.

Design:
    - **Best-effort**: if Gemini fails (rate limit, timeout, circuit breaker),
      the keyword-based classification remains intact.  No data is lost.
    - **Batch-oriented**: comments are sent in groups to minimize API calls.
    - **Idempotent**: only processes rows where ``procesado_ia = False``.
"""

from __future__ import annotations

import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.evaluacion_docente.domain.entities.comentario_analisis import ComentarioAnalisis
from app.modules.evaluacion_docente.domain.exceptions import GeminiError
from app.modules.evaluacion_docente.infrastructure.external.gemini_gateway import GeminiGateway

logger = logging.getLogger(__name__)

_BATCH_SIZE = 10
_VALID_TEMAS = frozenset(
    {
        "metodologia",
        "dominio_tema",
        "comunicacion",
        "evaluacion",
        "puntualidad",
        "material",
        "actitud",
        "tecnologia",
        "organizacion",
        "otro",
    }
)
_VALID_SENTIMIENTOS = frozenset({"positivo", "neutro", "mixto", "negativo"})


class GeminiEnrichmentService:
    """Enriches persisted comments with Gemini-powered classification."""

    def __init__(self, db: AsyncSession, gateway: GeminiGateway) -> None:
        self.db = db
        self.gateway = gateway

    async def enrich_evaluation_comments(
        self,
        evaluacion_id: uuid.UUID,
    ) -> int:
        """Enrich all un-processed comments for one evaluation.

        Returns the number of comments successfully enriched.
        """
        stmt = (
            select(ComentarioAnalisis)
            .where(ComentarioAnalisis.evaluacion_id == evaluacion_id)
            .where(ComentarioAnalisis.procesado_ia == False)  # noqa: E712
            .order_by(ComentarioAnalisis.created_at)
        )
        rows = list((await self.db.execute(stmt)).scalars().all())

        if not rows:
            return 0

        enriched = 0
        for i in range(0, len(rows), _BATCH_SIZE):
            batch = rows[i : i + _BATCH_SIZE]
            count = await self._process_batch(batch)
            enriched += count

        if enriched:
            await self.db.flush()

        logger.info(
            "Gemini enrichment for evaluacion %s: %d/%d comments enriched",
            evaluacion_id,
            enriched,
            len(rows),
        )
        return enriched

    async def _process_batch(self, batch: list[ComentarioAnalisis]) -> int:
        """Send one batch to Gemini and apply results."""
        input_dicts = [
            {
                "idx": i + 1,
                "texto": row.texto,
                "tipo": row.tipo,
            }
            for i, row in enumerate(batch)
        ]

        try:
            results = await self.gateway.analyze_comments(input_dicts)
        except GeminiError as exc:
            logger.warning(
                "Gemini enrichment batch failed (keeping keyword results): %s", exc.detail
            )
            return 0

        enriched = 0
        for item in results:
            idx = item.get("idx")
            if not isinstance(idx, int) or idx < 1 or idx > len(batch):
                continue

            row = batch[idx - 1]
            tema = item.get("tema", "")
            sentimiento = item.get("sentimiento", "")
            sent_score = item.get("sent_score")

            # Validate Gemini output before applying
            if tema not in _VALID_TEMAS:
                tema = row.tema  # keep keyword result
            if sentimiento not in _VALID_SENTIMIENTOS:
                sentimiento = row.sentimiento  # keep keyword result
            if not isinstance(sent_score, (int, float)) or sent_score < -1 or sent_score > 1:
                sent_score = row.sent_score  # keep keyword result

            row.tema = tema
            row.tema_confianza = "gemini"
            row.sentimiento = sentimiento
            row.sent_score = (
                round(float(sent_score), 2) if sent_score is not None else row.sent_score
            )
            row.procesado_ia = True
            enriched += 1

        return enriched
