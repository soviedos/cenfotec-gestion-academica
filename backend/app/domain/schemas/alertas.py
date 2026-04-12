"""Response schemas for the alerts endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import Field

from app.domain.entities.enums import AlertaEstado, Severidad, TipoAlerta
from app.domain.schemas.common import BaseSchema, PaginatedItems

# AlertaModalidad is a deliberate subset — excludes DESCONOCIDA [BR-MOD-05]
AlertaModalidad = Literal["CUATRIMESTRAL", "MENSUAL", "B2B"]


class AlertaResponse(BaseSchema):
    """Single alert detail — maps from the ``Alerta`` entity."""

    id: uuid.UUID
    evaluacion_id: uuid.UUID | None = None
    docente_nombre: str
    curso: str
    periodo: str
    modalidad: AlertaModalidad
    tipo_alerta: TipoAlerta
    metrica_afectada: str
    valor_actual: float
    valor_anterior: float | None = None
    descripcion: str
    severidad: Severidad
    estado: AlertaEstado
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
