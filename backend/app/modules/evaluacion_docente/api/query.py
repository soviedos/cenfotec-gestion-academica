"""Intelligent query endpoint — natural-language questions over evaluation data.

Gemini can access all data; ``modalidad`` is an optional filter.
"""

from fastapi import APIRouter, Depends

from app.api.deps import DbSession, GeminiDep
from app.api.rate_limit import query_rate_limiter
from app.modules.evaluacion_docente.application.services.query_service import QueryService
from app.modules.evaluacion_docente.domain.schemas.query import QueryRequest, QueryResponse

router = APIRouter()


@router.post("", response_model=QueryResponse, dependencies=[Depends(query_rate_limiter)])
async def ask_query(
    body: QueryRequest,
    db: DbSession,
    gemini: GeminiDep,
):
    """Recibe una pregunta en lenguaje natural y responde con evidencia."""
    svc = QueryService(db, gemini)
    return await svc.ask(question=body.question, filters=body.filters)
