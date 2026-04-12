"""Duplicado repository — persistence for probable-duplicate findings.

Candidate search strategy
─────────────────────────
Instead of comparing a new document against the entire ``documentos`` table,
we narrow the search to a small set of **cheap-to-filter** candidates via
the ``evaluaciones`` table:

1. Same ``modalidad``  (indexed — very selective: 3-4 values)
2. Same ``año``        (indexed — small cardinality per modalidad)
3. Same ``docente_nombre`` *or* same ``periodo``  (both indexed)

This produces a short candidate list (typically < 10 rows) before we ever
compute or compare fingerprints.  The existing composite indexes
``ix_evaluaciones_modalidad_periodo`` and ``ix_evaluaciones_modalidad_año_orden``
make this query efficient.

Performance note
────────────────
The candidate query hits only B-tree indexes.  The fingerprint comparison
that follows is pure Python (dict key equality) on already-computed
``criterios`` dicts — no additional I/O.  Total cost per upload: one
indexed SELECT returning ≤ ~20 rows + in-memory comparison.
"""

from __future__ import annotations

import uuid

from sqlalchemy import and_, or_, select

from app.modules.evaluacion_docente.domain.entities.documento import Documento
from app.modules.evaluacion_docente.domain.entities.duplicado_probable import DuplicadoProbable
from app.modules.evaluacion_docente.domain.entities.evaluacion import Evaluacion
from app.shared.infrastructure.repositories.base import BaseRepository


class DuplicadoRepository(BaseRepository[DuplicadoProbable]):
    """Persistence operations for probable-duplicate findings."""

    model = DuplicadoProbable

    async def find_candidates(
        self,
        *,
        modalidad: str,
        año: int,
        docente_nombre: str,
        periodo: str,
        exclude_documento_id: uuid.UUID,
    ) -> list[Documento]:
        """Return documents that *could* be duplicates based on cheap filters.

        Criteria (all must hold):
            - Same ``modalidad``
            - Same ``año``
            - Same ``docente_nombre`` OR same ``periodo``
            - Document in terminal state ``procesado``
            - Not the document being checked

        The result set is typically very small (< 10 rows) because
        modalidad × año × (docente ∪ periodo) is highly selective.
        """
        stmt = (
            select(Documento)
            .join(Evaluacion, Evaluacion.documento_id == Documento.id)
            .where(
                Evaluacion.modalidad == modalidad,
                Evaluacion.año == año,
                or_(
                    Evaluacion.docente_nombre == docente_nombre,
                    Evaluacion.periodo == periodo,
                ),
                Documento.estado == "procesado",
                Documento.id != exclude_documento_id,
                Documento.content_fingerprint.is_not(None),
            )
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def exists_pair(
        self,
        doc_a_id: uuid.UUID,
        doc_b_id: uuid.UUID,
    ) -> bool:
        """Check whether a duplicate finding already exists for this pair.

        Checks both orderings so the constraint ``uq_duplicados_par``
        is respected.
        """
        stmt = select(DuplicadoProbable.id).where(
            or_(
                and_(
                    DuplicadoProbable.documento_id == doc_a_id,
                    DuplicadoProbable.documento_coincidente_id == doc_b_id,
                ),
                and_(
                    DuplicadoProbable.documento_id == doc_b_id,
                    DuplicadoProbable.documento_coincidente_id == doc_a_id,
                ),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def create_finding(
        self,
        *,
        documento_id: uuid.UUID,
        documento_coincidente_id: uuid.UUID,
        fingerprint: str,
        score: float,
        criterios: dict,
    ) -> DuplicadoProbable:
        """Persist a new probable-duplicate finding."""
        finding = DuplicadoProbable(
            documento_id=documento_id,
            documento_coincidente_id=documento_coincidente_id,
            fingerprint=fingerprint,
            score=score,
            criterios=criterios,
            estado="pendiente",
        )
        return await self.create(finding)

    async def list_pending(
        self,
        *,
        offset: int = 0,
        limit: int = 20,
    ) -> list[DuplicadoProbable]:
        """Return pending duplicate findings for review."""
        stmt = (
            select(DuplicadoProbable)
            .where(DuplicadoProbable.estado == "pendiente")
            .order_by(DuplicadoProbable.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_documento(
        self,
        documento_id: uuid.UUID,
    ) -> list[DuplicadoProbable]:
        """Return all duplicate findings where this document is involved."""
        stmt = (
            select(DuplicadoProbable)
            .where(
                or_(
                    DuplicadoProbable.documento_id == documento_id,
                    DuplicadoProbable.documento_coincidente_id == documento_id,
                )
            )
            .order_by(DuplicadoProbable.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
