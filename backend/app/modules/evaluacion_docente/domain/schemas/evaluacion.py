"""Evaluacion DTOs."""

import uuid

from app.modules.evaluacion_docente.domain.entities.enums import (
    EvaluacionEstado as EvaluacionEstadoEnum,
)
from app.modules.evaluacion_docente.domain.entities.enums import Modalidad
from app.shared.domain.schemas.common import PaginatedItems, TimestampSchema


class EvaluacionRead(TimestampSchema):
    id: uuid.UUID
    documento_id: uuid.UUID
    docente_nombre: str
    periodo: str
    modalidad: Modalidad
    año: int
    periodo_orden: int
    materia: str | None
    puntaje_general: float | None
    resumen_ia: str | None
    estado: EvaluacionEstadoEnum


class EvaluacionList(PaginatedItems[EvaluacionRead]):
    pass
