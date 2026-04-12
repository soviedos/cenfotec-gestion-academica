"""Repository for persisting Gemini API audit log entries."""

from __future__ import annotations

import hashlib
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.evaluacion_docente.domain.entities.gemini_audit_log import GeminiAuditLog
from app.modules.evaluacion_docente.domain.schemas.query import GeminiCallResult


class GeminiAuditRepository:
    """Write-only repository for Gemini call traceability."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def find_by_prompt_hash(self, prompt_hash: str) -> GeminiAuditLog | None:
        """Return the most recent successful entry for a given prompt hash."""
        stmt = (
            select(GeminiAuditLog)
            .where(
                GeminiAuditLog.prompt_hash == prompt_hash,
                GeminiAuditLog.status == "ok",
            )
            .order_by(GeminiAuditLog.created_at.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def log_call(
        self,
        *,
        operation: str,
        prompt_text: str,
        result: GeminiCallResult | None = None,
        evaluacion_id: uuid.UUID | None = None,
        error_detail: str | None = None,
    ) -> GeminiAuditLog:
        """Persist one Gemini call (success or failure) and return the entity."""
        prompt_hash = hashlib.sha256(prompt_text.encode()).hexdigest()

        entry = GeminiAuditLog(
            operation=operation,
            evaluacion_id=evaluacion_id,
            prompt_text=prompt_text,
            prompt_hash=prompt_hash,
            response_text=result.text if result else None,
            model_name=result.model_name if result else "unknown",
            tokens_input=result.tokens_input if result else None,
            tokens_output=result.tokens_output if result else None,
            latency_ms=result.latency_ms if result else None,
            status="ok" if result and not error_detail else "error",
            error_detail=error_detail,
        )
        self.session.add(entry)
        await self.session.flush()
        await self.session.refresh(entry)
        return entry
