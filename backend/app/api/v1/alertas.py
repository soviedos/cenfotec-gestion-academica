"""Alertas API — CRUD and rebuild endpoints for academic alerts."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, Query

from app.api.deps import DbSession
from app.application.services.alerta_service import AlertaService
from app.domain.invariants import require_modalidad
from app.domain.schemas.alertas import (
    AlertaResponse,
    AlertasPaginadas,
    AlertaSummary,
    AlertRebuildResponse,
)

router = APIRouter()


@router.get("", response_model=AlertasPaginadas)
async def list_alerts(
    db: DbSession,
    modalidad: str = Query(..., description="Modalidad (obligatorio) [BR-MOD-02]"),
    año: int | None = Query(None, alias="anio", description="Filtrar por año"),
    periodo: str | None = Query(None, description="Filtrar por periodo"),
    severidad: str | None = Query(None, description="Filtrar por severidad"),
    estado: str | None = Query(None, description="Filtrar por estado"),
    docente: str | None = Query(None, description="Buscar por nombre de docente"),
    curso: str | None = Query(None, description="Buscar por nombre de curso"),
    tipo_alerta: str | None = Query(None, description="Filtrar por tipo de alerta"),
    page: int = Query(1, ge=1, description="Número de página"),
    page_size: int = Query(20, ge=1, le=100, description="Elementos por página"),
):
    """Lista paginada de alertas con filtros opcionales."""
    mod = require_modalidad(modalidad)
    svc = AlertaService(db)
    return await svc.list_alerts(
        modalidad=mod,
        año=año,
        periodo=periodo,
        severidad=severidad,
        estado=estado,
        docente=docente,
        curso=curso,
        tipo_alerta=tipo_alerta,
        page=page,
        page_size=page_size,
    )


@router.get("/summary", response_model=AlertaSummary)
async def alert_summary(
    db: DbSession,
    modalidad: str = Query(..., description="Modalidad (obligatorio) [BR-MOD-02]"),
):
    """Resumen agregado de alertas activas para el dashboard."""
    mod = require_modalidad(modalidad)
    svc = AlertaService(db)
    return await svc.summary(modalidad=mod)


@router.post("/rebuild", response_model=AlertRebuildResponse)
async def rebuild_alerts(db: DbSession):
    """Recalcular todas las alertas desde las evaluaciones actuales."""
    svc = AlertaService(db)
    return await svc.rebuild()


@router.patch("/{alerta_id}/estado", response_model=AlertaResponse)
async def update_alert_estado(
    db: DbSession,
    alerta_id: uuid.UUID,
    estado: str = Query(..., description="Nuevo estado: revisada, resuelta, descartada"),
):
    """Transicionar el estado de una alerta [AL-50]."""
    valid_states = {"revisada", "resuelta", "descartada"}
    if estado not in valid_states:
        raise HTTPException(
            status_code=422,
            detail=f"Estado inválido. Permitidos: {', '.join(sorted(valid_states))}",
        )
    svc = AlertaService(db)
    result = await svc.update_estado(alerta_id, estado)
    if result is None:
        raise HTTPException(status_code=404, detail="Alerta no encontrada")
    return result
