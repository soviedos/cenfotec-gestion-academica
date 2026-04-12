"""Evaluacion repository — persistence operations for teacher evaluations."""

import uuid

from sqlalchemy import func, select

from app.modules.evaluacion_docente.domain.entities.evaluacion import Evaluacion
from app.shared.infrastructure.repositories.base import BaseRepository


class EvaluacionRepository(BaseRepository[Evaluacion]):
    model = Evaluacion

    async def list_filtered(
        self,
        *,
        modalidad: str | None = None,
        periodo: str | None = None,
        docente: str | None = None,
        estado: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> list[Evaluacion]:
        stmt = select(Evaluacion).order_by(Evaluacion.created_at.desc())
        if modalidad:
            stmt = stmt.where(Evaluacion.modalidad == modalidad)
        if periodo:
            stmt = stmt.where(Evaluacion.periodo == periodo)
        if docente:
            stmt = stmt.where(Evaluacion.docente_nombre == docente)
        if estado:
            stmt = stmt.where(Evaluacion.estado == estado)
        stmt = stmt.offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_filtered(
        self,
        *,
        modalidad: str | None = None,
        periodo: str | None = None,
        docente: str | None = None,
        estado: str | None = None,
    ) -> int:
        stmt = select(func.count()).select_from(Evaluacion)
        if modalidad:
            stmt = stmt.where(Evaluacion.modalidad == modalidad)
        if periodo:
            stmt = stmt.where(Evaluacion.periodo == periodo)
        if docente:
            stmt = stmt.where(Evaluacion.docente_nombre == docente)
        if estado:
            stmt = stmt.where(Evaluacion.estado == estado)
        result = await self.session.execute(stmt)
        return result.scalar_one()

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
