"""Alerta service — business layer between API and repository/engine."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.evaluacion_docente.application.services.alert_engine import (
    AlertEngine,
    AlertRunResult,
)
from app.modules.evaluacion_docente.domain.schemas.alertas import (
    AlertaResponse,
    AlertasPaginadas,
    AlertaSummary,
    AlertRebuildResponse,
)
from app.modules.evaluacion_docente.infrastructure.repositories.alerta_repo import AlertaRepository


class AlertaService:
    """Thin orchestration layer for alert queries and rebuild."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._repo = AlertaRepository(db)

    async def list_alerts(
        self,
        *,
        modalidad: str | None = None,
        año: int | None = None,
        periodo: str | None = None,
        severidad: str | None = None,
        estado: str | None = None,
        docente: str | None = None,
        curso: str | None = None,
        tipo_alerta: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> AlertasPaginadas:
        offset = (page - 1) * page_size
        items, total = await self._repo.list_filtered(
            modalidad=modalidad,
            año=año,
            periodo=periodo,
            severidad=severidad,
            estado=estado,
            docente=docente,
            curso=curso,
            tipo_alerta=tipo_alerta,
            offset=offset,
            limit=page_size,
        )
        return AlertasPaginadas(
            items=[AlertaResponse.model_validate(a) for a in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def summary(self, *, modalidad: str | None = None) -> AlertaSummary:
        data = await self._repo.summary(estado="activa", modalidad=modalidad)
        return AlertaSummary(**data)

    async def rebuild(self) -> AlertRebuildResponse:
        engine = AlertEngine(self._db)
        result: AlertRunResult = await engine.run_all()
        return AlertRebuildResponse(
            candidates_generated=result.candidates_generated,
            created_or_updated=result.created_or_updated,
            modalidades_processed=result.modalidades_processed,
            periodos_by_modalidad=result.periodos_by_modalidad,
        )

    async def update_estado(
        self,
        alerta_id: uuid.UUID,
        nuevo_estado: str,
    ) -> AlertaResponse | None:
        alerta = await self._repo.update_estado(alerta_id, nuevo_estado)
        if alerta is None:
            return None
        return AlertaResponse.model_validate(alerta)
