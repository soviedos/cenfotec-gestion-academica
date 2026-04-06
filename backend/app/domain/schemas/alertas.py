"""Response schemas for the alerts endpoints."""

from __future__ import annotations

from datetime import datetime

from pydantic import Field

from app.domain.schemas.common import BaseSchema, PaginatedItems


class AlertaResponse(BaseSchema):
    """Single alert detail — maps from the ``Alerta`` entity."""

    id: str
    evaluacion_id: str | None = None
    docente_nombre: str
    curso: str
    periodo: str
    modalidad: str
    tipo_alerta: str
    metrica_afectada: str
    valor_actual: float
    valor_anterior: float | None = None
    descripcion: str
    severidad: str
    estado: str
    created_at: datetime
    updated_at: datetime


class AlertasPaginadas(PaginatedItems[AlertaResponse]):
    """Paginated list of alerts."""


class AlertaSummary(BaseSchema):
    """Aggregated alert counts for the homepage dashboard."""

    total_activas: int = 0
    por_severidad: dict[str, int] = Field(
        default_factory=dict,
        description="Count per severity: {'alta': N, 'media': N, 'baja': N}",
    )
    por_tipo: dict[str, int] = Field(
        default_factory=dict,
        description="Count per alert type",
    )
    por_modalidad: dict[str, int] = Field(
        default_factory=dict,
        description="Count per modalidad",
    )
    docentes_afectados: int = 0


class AlertRebuildResponse(BaseSchema):
    """Result of a full alert rebuild."""

    candidates_generated: int
    created_or_updated: int
    modalidades_processed: int
    periodos_by_modalidad: dict[str, list[str]] = Field(default_factory=dict)
