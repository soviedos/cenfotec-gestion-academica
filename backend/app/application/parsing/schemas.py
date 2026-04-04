"""Canonical output schemas for the PDF parser.

These Pydantic models define the structured data extracted from a
CENFOTEC teacher-evaluation PDF.  They are *parser-internal* — the
persistence layer maps them to SQLAlchemy entities separately.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

# ── Header ──────────────────────────────────────────────────────────────


class HeaderData(BaseModel):
    """Top-of-page metadata that repeats on every page."""

    profesor_nombre: str = Field(..., min_length=2, max_length=300)
    profesor_codigo: str | None = Field(None, max_length=50)
    periodo: str = Field(..., min_length=2, max_length=50)
    recinto: str = Field(..., max_length=300)


# ── Métricas ────────────────────────────────────────────────────────────


class FuentePuntaje(BaseModel):
    """A single score from one evaluation source (Estudiante / Director / Autoeval)."""

    puntos_obtenidos: float = Field(..., ge=0)
    puntos_maximos: float = Field(..., gt=0)
    porcentaje: float = Field(..., ge=0, le=100)


class DimensionMetrica(BaseModel):
    """One row in the dimensions table (e.g. METODOLOGÍA, Dominio …)."""

    nombre: str
    estudiante: FuentePuntaje
    director: FuentePuntaje
    autoevaluacion: FuentePuntaje
    promedio_general_puntos: float = Field(..., ge=0)
    promedio_general_pct: float = Field(..., ge=0, le=100)


class ResumenPorcentajes(BaseModel):
    """Summary percentages row at the bottom of the dimensions table."""

    estudiante: float = Field(..., ge=0, le=100)
    director: float = Field(..., ge=0, le=100)
    autoevaluacion: float = Field(..., ge=0, le=100)
    promedio_general: float = Field(..., ge=0, le=100)


# ── Cursos ──────────────────────────────────────────────────────────────


class CursoGrupo(BaseModel):
    """One course-group row from the courses table."""

    escuela: str
    codigo: str
    nombre: str
    estudiantes_respondieron: int = Field(..., ge=0)
    estudiantes_matriculados: int = Field(..., ge=0)
    grupo: str
    pct_estudiante: float = Field(..., ge=0, le=100)
    pct_director: float = Field(..., ge=0, le=100)
    pct_autoevaluacion: float = Field(..., ge=0, le=100)
    pct_promedio_general: float = Field(..., ge=0, le=100)


# ── Comentarios ─────────────────────────────────────────────────────────


class Comentario(BaseModel):
    """A single qualitative-comment row (one student's or director's feedback)."""

    fortaleza: str | None = None
    mejora: str | None = None
    observacion: str | None = None


class SeccionComentarios(BaseModel):
    """A group of comments tied to one evaluation type + subject."""

    tipo_evaluacion: Literal["Estudiante", "Director"]
    asignatura: str
    comentarios: list[Comentario]


# ── Top-level parsed result ─────────────────────────────────────────────


class ParsedEvaluacion(BaseModel):
    """Complete structured data extracted from one evaluation PDF."""

    header: HeaderData
    dimensiones: list[DimensionMetrica] = Field(..., min_length=1)
    resumen_pct: ResumenPorcentajes
    cursos: list[CursoGrupo] = Field(..., min_length=1)
    total_respondieron: int = Field(..., ge=0)
    total_matriculados: int = Field(..., ge=0)
    secciones_comentarios: list[SeccionComentarios] = Field(default_factory=list)
