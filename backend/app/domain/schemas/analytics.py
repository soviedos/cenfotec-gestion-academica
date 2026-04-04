"""Response schemas for the analytics / BI dashboard endpoints."""

from pydantic import Field

from app.domain.schemas.common import BaseSchema


class ResumenGeneral(BaseSchema):
    """Summary cards for the dashboard."""

    promedio_global: float
    total_evaluaciones: int
    total_docentes: int
    total_periodos: int


class DocentePromedio(BaseSchema):
    """One row in the per-teacher average table."""

    docente_nombre: str
    promedio: float
    evaluaciones_count: int


class DimensionPromedio(BaseSchema):
    """One row in the radar/dimensions chart."""

    dimension: str
    pct_estudiante: float | None = None
    pct_director: float | None = None
    pct_autoeval: float | None = None
    pct_promedio: float | None = None


class PeriodoMetrica(BaseSchema):
    """One data point for the historical trend line."""

    periodo: str
    promedio: float
    evaluaciones_count: int = Field(default=0)


class RankingDocente(BaseSchema):
    """One entry in the teacher ranking list."""

    posicion: int
    docente_nombre: str
    promedio: float
    evaluaciones_count: int
