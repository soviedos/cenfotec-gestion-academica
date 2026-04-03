"""Evaluacion DTOs."""

import uuid
from typing import Literal

from app.domain.schemas.common import PaginatedItems, TimestampSchema

EvaluacionEstado = Literal["pendiente", "procesando", "completado", "error"]


class EvaluacionRead(TimestampSchema):
    id: uuid.UUID
    documento_id: uuid.UUID
    docente_nombre: str
    periodo: str
    materia: str | None
    puntaje_general: float | None
    resumen_ia: str | None
    estado: EvaluacionEstado


class EvaluacionList(PaginatedItems[EvaluacionRead]):
    pass
