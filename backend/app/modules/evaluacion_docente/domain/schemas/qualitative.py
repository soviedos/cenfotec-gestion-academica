"""Pydantic schemas (DTOs) for qualitative analysis endpoints."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ── Read DTOs ────────────────────────────────────────────────────────────


class ComentarioAnalisisRead(BaseSchema):
    id: uuid.UUID
    evaluacion_id: uuid.UUID
    fuente: str
    asignatura: str
    tipo: str
    texto: str
    tema: str
    tema_confianza: str
    sentimiento: str | None
    sent_score: float | None
    procesado_ia: bool


# ── Aggregate DTOs ───────────────────────────────────────────────────────


class TemaDistribucion(BaseSchema):
    tema: str
    count: int
    porcentaje: float


class SentimientoDistribucion(BaseSchema):
    sentimiento: str
    count: int
    porcentaje: float


class TipoConteo(BaseSchema):
    tipo: str
    count: int


class ResumenCualitativo(BaseSchema):
    total_comentarios: int
    por_tipo: list[TipoConteo]
    por_sentimiento: list[SentimientoDistribucion]
    temas_top: list[TemaDistribucion]
    sentimiento_promedio: float | None


class PalabraFrecuencia(BaseSchema):
    text: str
    value: int


class NubePalabras(BaseSchema):
    tipo: str
    palabras: list[PalabraFrecuencia]


class FiltrosCualitativos(BaseSchema):
    periodos: list[str]
    docentes: list[str]
    asignaturas: list[str]
    escuelas: list[str]
