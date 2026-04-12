"""QueryService — orchestrates RAG retrieval + Gemini call + audit logging.

This is the main application service for intelligent queries.  It:

1. Retrieves relevant structured metrics (analytics repo)
2. Retrieves relevant comments (qualitative repo)
3. Builds context and calls GeminiGateway
4. Persists an audit log entry
5. Returns a typed QueryResponse with evidence
"""

from __future__ import annotations

import hashlib
import logging

from sqlalchemy import Float, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.evaluacion_docente.domain.entities.comentario_analisis import ComentarioAnalisis
from app.modules.evaluacion_docente.domain.entities.evaluacion import Evaluacion
from app.modules.evaluacion_docente.domain.entities.evaluacion_dimension import EvaluacionDimension
from app.modules.evaluacion_docente.domain.exceptions import GeminiError
from app.modules.evaluacion_docente.domain.schemas.query import (
    CommentEvidence,
    CommentSource,
    GeminiCallResult,
    MetricEvidence,
    MetricSource,
    QueryFilters,
    QueryResponse,
    QueryResponseMetadata,
)
from app.modules.evaluacion_docente.infrastructure.external.gemini_gateway import GeminiGateway
from app.modules.evaluacion_docente.infrastructure.external.prompt_templates import (
    QUERY_USER_TEMPLATE,
    format_evidence_block,
)
from app.modules.evaluacion_docente.infrastructure.repositories.gemini_audit import (
    GeminiAuditRepository,
)

logger = logging.getLogger(__name__)

_MAX_COMMENTS = 20
_MAX_METRICS = 10


class QueryService:
    """Orchestrates the full RAG pipeline for intelligent queries."""

    def __init__(
        self,
        db: AsyncSession,
        gateway: GeminiGateway,
    ) -> None:
        self.db = db
        self.gateway = gateway
        self.audit_repo = GeminiAuditRepository(db)

    async def ask(
        self,
        question: str,
        filters: QueryFilters,
    ) -> QueryResponse:
        """Execute a full RAG query and return the answer with evidence."""
        f = filters

        # ── Step 1: Retrieve structured metrics ─────────────────────
        metrics = await self._retrieve_metrics(f)

        # ── Step 2: Retrieve relevant comments ──────────────────────
        comments = await self._retrieve_comments(question, f)

        # ── Step 3: Build prompt and call Gemini ────────────────────
        metrics_dicts = [m["raw"] for m in metrics]
        comments_dicts = [c["raw"] for c in comments]

        evidence_block = format_evidence_block(comments_dicts, metrics_dicts)
        full_prompt = QUERY_USER_TEMPLATE.format(
            question=question,
            evidence_block=evidence_block,
        )

        prompt_hash = hashlib.sha256(full_prompt.encode()).hexdigest()

        # ── Step 3a: Check for cached response ──────────────────────
        cached = await self.audit_repo.find_by_prompt_hash(prompt_hash)
        if cached and cached.response_text:
            return QueryResponse(
                answer=cached.response_text,
                confidence=None,
                evidence=self._build_evidence(metrics, comments),
                metadata=QueryResponseMetadata(
                    model=cached.model_name,
                    tokens_used=(cached.tokens_input or 0) + (cached.tokens_output or 0),
                    latency_ms=0,
                    audit_log_id=cached.id,
                ),
            )

        # ── Step 3b: Call Gemini ────────────────────────────────────
        result: GeminiCallResult | None = None
        error_detail: str | None = None
        try:
            result = await self.gateway.answer_query(
                question=question,
                comments=comments_dicts,
                metrics=metrics_dicts,
            )
        except GeminiError as exc:
            error_detail = exc.detail
            # Log the failed call, then re-raise
            await self.audit_repo.log_call(
                operation="query",
                prompt_text=full_prompt,
                error_detail=error_detail,
            )
            raise

        # ── Step 4: Persist audit log ───────────────────────────────
        audit_entry = await self.audit_repo.log_call(
            operation="query",
            prompt_text=full_prompt,
            result=result,
        )

        # ── Step 5: Build response with evidence ───────────────────
        return QueryResponse(
            answer=result.text,
            confidence=None,
            evidence=self._build_evidence(metrics, comments),
            metadata=QueryResponseMetadata(
                model=result.model_name,
                tokens_used=result.tokens_input + result.tokens_output,
                latency_ms=result.latency_ms,
                audit_log_id=audit_entry.id,
            ),
        )

    @staticmethod
    def _build_evidence(
        metrics: list[dict],
        comments: list[dict],
    ) -> list[CommentEvidence | MetricEvidence]:
        """Build evidence list from retrieved metrics and comments."""
        evidence: list[CommentEvidence | MetricEvidence] = []

        for m in metrics:
            evidence.append(
                MetricEvidence(
                    label=m["raw"]["label"],
                    value=m["raw"]["value"],
                    source=MetricSource(
                        periodo=m["raw"].get("periodo"),
                        docente=m["raw"].get("docente"),
                    ),
                )
            )

        for c in comments:
            evidence.append(
                CommentEvidence(
                    texto=c["raw"]["texto"],
                    source=CommentSource(
                        evaluacion_id=c["evaluacion_id"],
                        docente=c["docente"],
                        periodo=c["periodo"],
                        asignatura=c["asignatura"],
                        fuente=c["fuente"],
                    ),
                )
            )

        return evidence

    # ── Private: retrieve structured metrics ────────────────────────

    async def _retrieve_metrics(
        self,
        f: QueryFilters,
    ) -> list[dict]:
        """Fetch summary metrics relevant to the query filters."""
        results: list[dict] = []

        # Global or filtered average
        avg_stmt = select(
            func.avg(Evaluacion.puntaje_general.cast(Float)).label("promedio"),
            func.count(Evaluacion.id).label("total"),
        ).where(Evaluacion.estado == "completado")
        avg_stmt = avg_stmt.where(Evaluacion.modalidad == f.modalidad)
        if f.periodo:
            avg_stmt = avg_stmt.where(Evaluacion.periodo == f.periodo)
        if f.docente:
            avg_stmt = avg_stmt.where(Evaluacion.docente_nombre == f.docente)

        row = (await self.db.execute(avg_stmt)).first()
        if row and row.promedio is not None:
            label = "Puntaje promedio general"
            if f.docente:
                label = f"Puntaje promedio de {f.docente}"
            results.append(
                {
                    "raw": {
                        "label": label,
                        "value": round(float(row.promedio), 2),
                        "periodo": f.periodo,
                        "docente": f.docente,
                    },
                }
            )

        # Dimension averages (if docente or periodo filter)
        if f.docente or f.periodo:
            dim_stmt = (
                select(
                    EvaluacionDimension.nombre,
                    func.avg(EvaluacionDimension.pct_promedio.cast(Float)).label("promedio"),
                )
                .join(Evaluacion, EvaluacionDimension.evaluacion_id == Evaluacion.id)
                .where(Evaluacion.estado == "completado")
                .group_by(EvaluacionDimension.nombre)
                .order_by(func.avg(EvaluacionDimension.pct_promedio.cast(Float)).desc())
                .limit(_MAX_METRICS)
            )
            dim_stmt = dim_stmt.where(Evaluacion.modalidad == f.modalidad)
            if f.periodo:
                dim_stmt = dim_stmt.where(Evaluacion.periodo == f.periodo)
            if f.docente:
                dim_stmt = dim_stmt.where(Evaluacion.docente_nombre == f.docente)

            dim_rows = (await self.db.execute(dim_stmt)).all()
            for dr in dim_rows:
                if dr.promedio is not None:
                    results.append(
                        {
                            "raw": {
                                "label": f"Dimensión {dr.nombre} (% promedio)",
                                "value": round(float(dr.promedio), 2),
                                "periodo": f.periodo,
                                "docente": f.docente,
                            },
                        }
                    )

        return results[:_MAX_METRICS]

    # ── Private: retrieve relevant comments ─────────────────────────

    async def _retrieve_comments(
        self,
        question: str,
        f: QueryFilters,
    ) -> list[dict]:
        """Fetch comments matching the query filters.

        Strategy:
        1. Detect topic hint from the question.
        2. Fetch topic-matched comments (prioritised).
        3. If not enough, backfill with general comments from other topics.
        4. Prefer Gemini-enriched rows (procesado_ia=True) — they have
           higher-quality classification.
        """
        base = (
            select(
                ComentarioAnalisis,
                Evaluacion.docente_nombre,
                Evaluacion.periodo,
            )
            .join(Evaluacion, ComentarioAnalisis.evaluacion_id == Evaluacion.id)
            .where(Evaluacion.estado == "completado")
        )

        base = base.where(Evaluacion.modalidad == f.modalidad)
        if f.periodo:
            base = base.where(Evaluacion.periodo == f.periodo)
        if f.docente:
            base = base.where(Evaluacion.docente_nombre == f.docente)
        if f.asignatura:
            base = base.where(ComentarioAnalisis.asignatura == f.asignatura)

        results: list[dict] = []

        # Phase A: topic-matched comments (Gemini-enriched first)
        tema_hint = self._detect_tema(question)
        if tema_hint:
            topic_stmt = (
                base.where(ComentarioAnalisis.tema == tema_hint)
                .order_by(
                    ComentarioAnalisis.procesado_ia.desc(),
                    ComentarioAnalisis.created_at.desc(),
                )
                .limit(_MAX_COMMENTS)
            )
            topic_rows = (await self.db.execute(topic_stmt)).all()
            results.extend(self._rows_to_dicts(topic_rows))

        # Phase B: backfill with general comments if we have room
        remaining = _MAX_COMMENTS - len(results)
        if remaining > 0:
            seen_ids = {r["comment_id"] for r in results}
            general_stmt = (
                base.order_by(
                    ComentarioAnalisis.procesado_ia.desc(),
                    ComentarioAnalisis.created_at.desc(),
                ).limit(remaining + len(seen_ids))  # over-fetch to account for dupes
            )
            if tema_hint:
                general_stmt = general_stmt.where(ComentarioAnalisis.tema != tema_hint)
            general_rows = (await self.db.execute(general_stmt)).all()
            for r in self._rows_to_dicts(general_rows):
                if r["comment_id"] not in seen_ids and len(results) < _MAX_COMMENTS:
                    results.append(r)

        return results

    @staticmethod
    def _rows_to_dicts(rows: list) -> list[dict]:
        """Convert SQLAlchemy result rows to internal dicts."""
        out = []
        for comment, docente, periodo in rows:
            out.append(
                {
                    "comment_id": comment.id,
                    "evaluacion_id": comment.evaluacion_id,
                    "docente": docente,
                    "periodo": periodo,
                    "asignatura": comment.asignatura,
                    "fuente": comment.fuente,
                    "raw": {
                        "texto": comment.texto,
                        "tipo": comment.tipo,
                        "docente": docente,
                        "asignatura": comment.asignatura,
                        "periodo": periodo,
                        "fuente": comment.fuente,
                    },
                }
            )
        return out

    @staticmethod
    def _detect_tema(question: str) -> str | None:
        """Simple keyword detection to narrow comment retrieval by tema.

        Uses word-boundary matching to avoid false positives from substrings.
        Returns a tema string or None if no strong signal is found.
        """
        import re

        q = question.lower()
        tema_keywords = {
            "metodologia": [r"\bmetodolog", r"\bmétodo", r"\bdinám", r"\bdidáctic"],
            "comunicacion": [r"\bcomunic", r"\bexplic", r"\bclar\w", r"\binterac"],
            "evaluacion": [r"\bevalua", r"\bexamen", r"\bnota\b", r"\bcalifica"],
            "puntualidad": [r"\bpuntual", r"\bhora\b", r"\btarde\b", r"\basisten"],
            "material": [r"\bmaterial", r"\bpresentaci", r"\brecurso", r"\bdiapositiva"],
            "actitud": [r"\bactitud", r"\bamable", r"\brespetuos", r"\bmotiv", r"\btrato\b"],
            "dominio_tema": [r"\bdominio", r"\bconocimiento", r"\bexperto", r"\bsabe\b"],
            "organizacion": [r"\borganiz", r"\bestructur", r"\bplanific"],
            "tecnologia": [r"\bvirtual", r"\btecnolog", r"\bplataforma", r"\bherramienta"],
        }
        for tema, patterns in tema_keywords.items():
            if any(re.search(pat, q) for pat in patterns):
                return tema
        return None
