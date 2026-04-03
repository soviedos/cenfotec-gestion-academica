"""Evaluacion repository — persistence operations for teacher evaluations."""

import uuid

from sqlalchemy import func, select

from app.domain.entities.evaluacion import Evaluacion
from app.infrastructure.repositories.base import BaseRepository


class EvaluacionRepository(BaseRepository[Evaluacion]):
    model = Evaluacion

    async def list_by_documento(
        self,
        documento_id: uuid.UUID,
        *,
        offset: int = 0,
        limit: int = 20,
    ) -> list[Evaluacion]:
        stmt = (
            select(Evaluacion)
            .where(Evaluacion.documento_id == documento_id)
            .offset(offset)
            .limit(limit)
            .order_by(Evaluacion.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_by_documento(self, documento_id: uuid.UUID) -> int:
        stmt = (
            select(func.count())
            .select_from(Evaluacion)
            .where(Evaluacion.documento_id == documento_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()
