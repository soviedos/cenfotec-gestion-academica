"""Response schemas for the executive dashboard endpoint."""

from __future__ import annotations

from pydantic import Field

from app.modules.evaluacion_docente.domain.schemas.analytics import PeriodoMetrica
from app.shared.domain.schemas.common import BaseSchema


class DashboardKpis(BaseSchema):
    """Top-level KPI cards."""

    documentos_procesados: int
    docentes_evaluados: int
    promedio_general: float
    alertas_criticas: int


class AlertaDocente(BaseSchema):
    """A docente triggering an alert (low score or negative trend)."""

    docente_nombre: str
    promedio: float
    evaluaciones_count: int
    motivo: str  # e.g. "Promedio < 60", "Tendencia negativa"


class DocenteResumen(BaseSchema):
    """Compact docente entry for top/bottom lists."""

    posicion: int
    docente_nombre: str
    promedio: float
    evaluaciones_count: int


class InsightItem(BaseSchema):
    """An auto-generated insight."""

    icono: str  # emoji or icon key
    texto: str


class ActividadReciente(BaseSchema):
    """Recent processing activity entry."""

    documento_nombre: str
    estado: str
    evaluaciones_extraidas: int
    fecha: str  # ISO string


class DashboardSummary(BaseSchema):
    """Aggregated executive dashboard payload."""

    kpis: DashboardKpis
    alertas: list[AlertaDocente] = Field(default_factory=list)
    tendencia: list[PeriodoMetrica] = Field(default_factory=list)
    top_docentes: list[DocenteResumen] = Field(default_factory=list)
    bottom_docentes: list[DocenteResumen] = Field(default_factory=list)
    insights: list[InsightItem] = Field(default_factory=list)
    actividad_reciente: list[ActividadReciente] = Field(default_factory=list)
