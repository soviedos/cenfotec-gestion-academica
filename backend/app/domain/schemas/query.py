"""Pydantic schemas for the intelligent query endpoint and Gemini interactions."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict, Field


class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ── Request ──────────────────────────────────────────────────────────────


class QueryRequest(BaseModel):
    """User's natural-language question with optional filters."""

    question: str = Field(..., min_length=3, max_length=1000)
    filters: QueryFilters = Field(..., description="Filtros (modalidad obligatorio) [BR-MOD-02]")


class QueryFilters(BaseModel):
    modalidad: str = Field(..., description="Modalidad (obligatorio) [BR-MOD-02]")
    periodo: str | None = None
    docente: str | None = None
    asignatura: str | None = None
    escuela: str | None = None


# ── Evidence items ───────────────────────────────────────────────────────


class CommentEvidence(BaseSchema):
    """A comment retrieved as supporting evidence."""

    type: str = "comment"
    texto: str
    source: CommentSource
    relevance_score: float | None = None


class CommentSource(BaseSchema):
    evaluacion_id: uuid.UUID
    docente: str
    periodo: str
    asignatura: str
    fuente: str


class MetricEvidence(BaseSchema):
    """A numeric metric retrieved as supporting evidence."""

    type: str = "metric"
    label: str
    value: float
    source: MetricSource


class MetricSource(BaseSchema):
    periodo: str | None = None
    docente: str | None = None


# ── Response ─────────────────────────────────────────────────────────────


class QueryResponseMetadata(BaseSchema):
    model: str
    tokens_used: int
    latency_ms: int
    audit_log_id: uuid.UUID


class QueryResponse(BaseSchema):
    answer: str
    confidence: float | None = None
    evidence: list[CommentEvidence | MetricEvidence]
    metadata: QueryResponseMetadata


# ── Internal DTOs used between Gateway and Service ───────────────────────


class GeminiCallResult(BaseModel):
    """Raw result from a single Gemini API call."""

    text: str
    model_name: str
    tokens_input: int
    tokens_output: int
    latency_ms: int
