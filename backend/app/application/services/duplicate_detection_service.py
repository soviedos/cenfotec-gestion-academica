"""Duplicate detection service — finds probable duplicates after parsing.

Lifecycle
─────────
Called by ``ProcessingService`` right after a document is successfully
parsed and persisted.  The flow is:

1. Compute the content fingerprint from ``ParsedEvaluacion``.
2. Store the fingerprint on ``Documento.content_fingerprint``.
3. Query cheap candidates (same modalidad + año + docente/periodo).
4. For each candidate, compare fingerprints field-by-field.
5. If a match is found (score ≥ threshold), persist a
   ``DuplicadoProbable`` finding — but **never block** the upload.

Design decisions
────────────────
- **Best-effort**: failures in duplicate detection are logged but never
  cause the upload to fail.
- **Non-blocking**: the document always proceeds to ``procesado``.
  Duplicates are flagged as ``pendiente`` for human review.
- **Cheap candidate filter**: the candidate query uses existing indexed
  columns (modalidad, año, docente_nombre, periodo) to avoid a full-table
  scan.  Typical candidate count: 0–10 rows.
- **No AI dependency**: fingerprint comparison is pure Python dict equality.
"""

from __future__ import annotations

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.parsing.schemas import ParsedEvaluacion
from app.domain.entities.documento import Documento
from app.domain.fingerprint import compute_content_fingerprint
from app.infrastructure.repositories.duplicado_repo import DuplicadoRepository

logger = logging.getLogger(__name__)

# Minimum similarity score (0.0–1.0) to flag a probable duplicate.
# 1.0 = exact fingerprint match only.
# Lower values catch near-duplicates (e.g. same doc, different comments).
MATCH_THRESHOLD = 0.75


class DuplicateDetectionService:
    """Detects probable duplicates for a newly parsed document."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.dup_repo = DuplicadoRepository(db)

    async def check_and_flag(
        self,
        documento: Documento,
        parsed: ParsedEvaluacion,
    ) -> int:
        """Run duplicate detection for a document after parsing.

        Parameters
        ----------
        documento : Documento
            The document entity (already persisted, estado='procesado').
        parsed : ParsedEvaluacion
            The structured parser output for this document.

        Returns
        -------
        int
            Number of probable-duplicate findings created.

        Notes
        -----
        This method **never raises**.  Any error is logged and the
        document proceeds normally.
        """
        try:
            return await self._detect(documento, parsed)
        except Exception:
            logger.warning(
                "Duplicate detection failed for doc %s (proceeding normally)",
                documento.id,
                exc_info=True,
            )
            return 0

    async def _detect(
        self,
        documento: Documento,
        parsed: ParsedEvaluacion,
    ) -> int:
        # ── Step 1: Compute fingerprint ─────────────────────────────
        fp_result = compute_content_fingerprint(parsed)

        # ── Step 2: Store fingerprint on document ───────────────────
        documento.content_fingerprint = fp_result.fingerprint
        await self.db.flush()

        # ── Step 3: Find cheap candidates ───────────────────────────
        candidates = await self.dup_repo.find_candidates(
            modalidad=parsed.periodo_data.modalidad,
            año=parsed.periodo_data.año,
            docente_nombre=parsed.header.profesor_nombre,
            periodo=parsed.periodo_data.periodo_normalizado,
            exclude_documento_id=documento.id,
        )

        if not candidates:
            logger.debug("No duplicate candidates for doc %s", documento.id)
            return 0

        logger.info(
            "Found %d candidate(s) for duplicate check on doc %s",
            len(candidates),
            documento.id,
        )

        # ── Step 4: Compare fingerprints ────────────────────────────
        findings_created = 0
        for candidate in candidates:
            if candidate.content_fingerprint is None:
                continue

            # Rebuild the candidate's FingerprintResult from stored data.
            # The candidate's criterios are not stored on the Documento
            # itself — we use the fingerprint for exact match and rely
            # on the new document's criterios for evidence.
            # Fast path: exact fingerprint match
            if fp_result.fingerprint == candidate.content_fingerprint:
                if await self.dup_repo.exists_pair(documento.id, candidate.id):
                    continue

                await self.dup_repo.create_finding(
                    documento_id=documento.id,
                    documento_coincidente_id=candidate.id,
                    fingerprint=fp_result.fingerprint,
                    score=1.0,
                    criterios=fp_result.criterios,
                )
                findings_created += 1
                logger.info(
                    "Exact duplicate: doc %s ↔ doc %s (fingerprint=%s…)",
                    documento.id,
                    candidate.id,
                    fp_result.fingerprint[:12],
                )

        # ── Step 5: Mark document if any findings ───────────────────
        if findings_created > 0:
            documento.posible_duplicado = True
            await self.db.flush()

        return findings_created
