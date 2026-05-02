"""GeminiGateway — typed async wrapper around the google-genai SDK.

This gateway is a pure infrastructure component: it knows nothing about
SQLAlchemy, repositories, or domain entities.  It receives text, calls
Gemini, and returns typed DTOs.

All Gemini exceptions are caught and re-raised as domain exceptions so
that upper layers never depend on the SDK directly.

Includes a lightweight **circuit breaker** to avoid hammering an
already-failing Gemini API.  After ``_FAILURE_THRESHOLD`` consecutive
errors the circuit opens for ``_RECOVERY_TIMEOUT`` seconds, during which
all calls immediately raise ``GeminiUnavailableError`` without making a
network request.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any, Protocol

from google import genai
from google.genai import errors as genai_errors
from google.genai import types

from app.modules.evaluacion_docente.domain.exceptions import (
    GeminiError,
    GeminiRateLimitError,
    GeminiTimeoutError,
    GeminiUnavailableError,
)
from app.modules.evaluacion_docente.domain.schemas.query import GeminiCallResult
from app.modules.evaluacion_docente.infrastructure.external.prompt_templates import (
    COMMENT_ANALYSIS_SYSTEM_PROMPT,
    COMMENT_ANALYSIS_USER_TEMPLATE,
    QUERY_SYSTEM_PROMPT,
    QUERY_USER_TEMPLATE,
    format_comments_for_analysis,
    format_evidence_block,
)

logger = logging.getLogger(__name__)

_DEFAULT_MODEL = "gemini-2.5-flash"
_DEFAULT_TIMEOUT_MS = 30_000

# Circuit breaker defaults
_FAILURE_THRESHOLD = 3  # open after N consecutive failures
_RECOVERY_TIMEOUT = 60  # seconds before trying again


_ANALYSIS_BATCH_SIZE = 25

# Retry defaults (exponential backoff)
_MAX_RETRIES = 3
_RETRY_BASE_DELAY = 1.0  # seconds
_RETRY_MAX_DELAY = 16.0  # seconds
_RETRYABLE_EXCEPTIONS = (genai_errors.ServerError, TimeoutError)


class GeminiGatewayProtocol(Protocol):
    """Protocol for testing — swap with a fake in unit tests."""

    async def answer_query(
        self,
        question: str,
        comments: list[dict],
        metrics: list[dict],
    ) -> GeminiCallResult: ...

    async def analyze_comments(
        self,
        comments: list[dict],
    ) -> list[dict[str, Any]]: ...


class _CircuitBreaker:
    """Minimal circuit breaker: closed → open → half-open → closed."""

    def __init__(
        self,
        failure_threshold: int = _FAILURE_THRESHOLD,
        recovery_timeout: int = _RECOVERY_TIMEOUT,
    ) -> None:
        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout
        self._failure_count = 0
        self._last_failure_time: float = 0.0
        self._state: str = "closed"  # closed | open | half-open

    @property
    def state(self) -> str:
        if self._state == "open":
            if time.monotonic() - self._last_failure_time >= self._recovery_timeout:
                self._state = "half-open"
        return self._state

    def record_success(self) -> None:
        self._failure_count = 0
        self._state = "closed"

    def record_failure(self) -> None:
        self._failure_count += 1
        self._last_failure_time = time.monotonic()
        if self._failure_count >= self._failure_threshold:
            self._state = "open"
            logger.warning(
                "Circuit breaker OPEN after %d consecutive Gemini failures",
                self._failure_count,
            )

    def allow_request(self) -> bool:
        state = self.state
        if state == "closed":
            return True
        if state == "half-open":
            logger.info("Circuit breaker half-open, allowing probe request")
            return True
        return False


class GeminiGateway:
    """Async gateway to Google Gemini generative AI API."""

    def __init__(
        self,
        api_key: str,
        *,
        model: str = _DEFAULT_MODEL,
        timeout_ms: int = _DEFAULT_TIMEOUT_MS,
        failure_threshold: int = _FAILURE_THRESHOLD,
        recovery_timeout: int = _RECOVERY_TIMEOUT,
        max_retries: int = _MAX_RETRIES,
    ) -> None:
        if not api_key:
            raise GeminiUnavailableError()
        self._client = genai.Client(api_key=api_key)
        self._model = model
        self._timeout_ms = timeout_ms
        self._max_retries = max_retries
        self._breaker = _CircuitBreaker(
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
        )

    async def _call_with_retry(
        self,
        call: Any,
        *,
        model: str,
        contents: str,
        config: types.GenerateContentConfig,
    ) -> Any:
        """Execute a Gemini API call with exponential backoff on transient errors.

        Retries on server errors and timeouts up to ``_max_retries`` times.
        Client errors (4xx) are *not* retried — they propagate immediately.
        """
        last_exc: Exception | None = None
        for attempt in range(self._max_retries + 1):
            try:
                return await call.generate_content(
                    model=model,
                    contents=contents,
                    config=config,
                )
            except _RETRYABLE_EXCEPTIONS as exc:
                last_exc = exc
                if attempt < self._max_retries:
                    delay = min(
                        _RETRY_BASE_DELAY * (2**attempt),
                        _RETRY_MAX_DELAY,
                    )
                    logger.warning(
                        "Gemini transient error (attempt %d/%d), retrying in %.1fs: %s",
                        attempt + 1,
                        self._max_retries + 1,
                        delay,
                        exc,
                    )
                    await asyncio.sleep(delay)
                else:
                    raise
        raise last_exc  # pragma: no cover — unreachable, satisfies type checker

    async def answer_query(
        self,
        question: str,
        comments: list[dict],
        metrics: list[dict],
    ) -> GeminiCallResult:
        """Send a RAG-augmented query to Gemini and return the result.

        Parameters
        ----------
        question:
            The user's natural-language question.
        comments:
            Retrieved comment dicts with keys: texto, tipo, docente,
            asignatura, periodo, fuente.
        metrics:
            Retrieved metric dicts with keys: label, value, periodo, docente.

        Returns
        -------
        GeminiCallResult with the model's answer text and token usage.
        """
        if not self._breaker.allow_request():
            logger.warning("Circuit breaker OPEN — rejecting Gemini call")
            raise GeminiUnavailableError(
                detail="Servicio Gemini temporalmente deshabilitado (circuit breaker abierto)"
            )

        evidence_block = format_evidence_block(comments, metrics)
        user_prompt = QUERY_USER_TEMPLATE.format(
            question=question,
            evidence_block=evidence_block,
        )

        config = types.GenerateContentConfig(
            system_instruction=QUERY_SYSTEM_PROMPT,
            temperature=0.3,
            max_output_tokens=8192,
        )

        start = time.monotonic()
        try:
            response = await self._call_with_retry(
                self._client.aio.models,
                model=self._model,
                contents=user_prompt,
                config=config,
            )
        except genai_errors.ClientError as exc:
            self._breaker.record_failure()
            latency = int((time.monotonic() - start) * 1000)
            detail = str(exc)
            if "429" in detail or "rate" in detail.lower():
                logger.warning("Gemini rate limit hit (%dms): %s", latency, detail)
                raise GeminiRateLimitError() from exc
            logger.error("Gemini client error (%dms): %s", latency, detail)
            raise GeminiError(detail=f"Error de cliente Gemini: {detail}") from exc
        except genai_errors.ServerError as exc:
            self._breaker.record_failure()
            latency = int((time.monotonic() - start) * 1000)
            logger.error("Gemini server error (%dms): %s", latency, exc)
            raise GeminiError(detail="Error del servidor Gemini") from exc
        except TimeoutError as exc:
            self._breaker.record_failure()
            latency = int((time.monotonic() - start) * 1000)
            logger.warning("Gemini timeout after %dms", latency)
            raise GeminiTimeoutError() from exc
        except Exception as exc:
            self._breaker.record_failure()
            latency = int((time.monotonic() - start) * 1000)
            logger.exception("Unexpected Gemini error (%dms)", latency)
            raise GeminiError(detail=f"Error inesperado en Gemini: {exc}") from exc

        self._breaker.record_success()
        latency_ms = int((time.monotonic() - start) * 1000)
        text = response.text or ""
        usage = response.usage_metadata
        tokens_in = usage.prompt_token_count if usage else 0
        tokens_out = usage.candidates_token_count if usage else 0

        logger.info(
            "Gemini query OK: %d tok_in, %d tok_out, %dms",
            tokens_in,
            tokens_out,
            latency_ms,
        )

        return GeminiCallResult(
            text=text,
            model_name=self._model,
            tokens_input=tokens_in or 0,
            tokens_output=tokens_out or 0,
            latency_ms=latency_ms,
        )

    # ── Batch comment analysis ──────────────────────────────────────

    async def analyze_comments(
        self,
        comments: list[dict],
    ) -> list[dict[str, Any]]:
        """Classify a batch of comments using Gemini.

        Parameters
        ----------
        comments:
            List of dicts with keys ``idx`` (1-based), ``texto``, ``tipo``.

        Returns
        -------
        List of dicts with keys: ``idx``, ``tema``, ``sentimiento``,
        ``sent_score``, ``resumen``.  Order matches input.

        Raises
        ------
        GeminiError / GeminiUnavailableError on failure.
        """
        if not self._breaker.allow_request():
            raise GeminiUnavailableError(
                detail="Servicio Gemini temporalmente deshabilitado (circuit breaker abierto)"
            )

        comments_block = format_comments_for_analysis(comments)
        user_prompt = COMMENT_ANALYSIS_USER_TEMPLATE.format(
            count=len(comments),
            comments_block=comments_block,
        )

        config = types.GenerateContentConfig(
            system_instruction=COMMENT_ANALYSIS_SYSTEM_PROMPT,
            temperature=0.1,
            max_output_tokens=4096,
            thinking_config=types.ThinkingConfig(thinking_budget=0),
            response_mime_type="application/json",
        )

        start = time.monotonic()
        try:
            response = await self._call_with_retry(
                self._client.aio.models,
                model=self._model,
                contents=user_prompt,
                config=config,
            )
        except genai_errors.ClientError as exc:
            self._breaker.record_failure()
            detail = str(exc)
            if "429" in detail or "rate" in detail.lower():
                raise GeminiRateLimitError() from exc
            raise GeminiError(detail=f"Error de cliente Gemini: {detail}") from exc
        except genai_errors.ServerError as exc:
            self._breaker.record_failure()
            raise GeminiError(detail="Error del servidor Gemini") from exc
        except TimeoutError as exc:
            self._breaker.record_failure()
            raise GeminiTimeoutError() from exc
        except Exception as exc:
            self._breaker.record_failure()
            raise GeminiError(detail=f"Error inesperado en Gemini: {exc}") from exc

        self._breaker.record_success()
        latency_ms = int((time.monotonic() - start) * 1000)
        raw_text = response.text or ""

        logger.info("Gemini comment analysis OK (%d comments, %dms)", len(comments), latency_ms)

        parsed = self._extract_json_array(raw_text)
        if parsed is None:
            logger.warning(
                "Gemini returned unparseable response for comment analysis. "
                "Raw text (first 500 chars): %s",
                raw_text[:500],
            )
            raise GeminiError(detail="Respuesta de Gemini no es JSON válido")
        return parsed

    @staticmethod
    def _extract_json_array(text: str) -> list[dict[str, Any]] | None:
        """Best-effort extraction of a JSON array from Gemini response text.

        Gemini 2.5 Flash (thinking model) sometimes wraps JSON in markdown
        fences or includes partial trailing content.  This method tries:
        1. Direct ``json.loads``
        2. Regex extraction of ``[...]`` block
        3. Truncation repair (find last complete object in the array)
        """
        import re as _re

        # 1. Try direct parse
        try:
            result = json.loads(text)
            if isinstance(result, list):
                return result  # type: ignore[return-value]
        except json.JSONDecodeError:
            pass

        # 2. Try extracting the first [...] block (handles markdown fences)
        match = _re.search(r"\[.*\]", text, _re.DOTALL)
        if match:
            try:
                result = json.loads(match.group())
                if isinstance(result, list):
                    return result  # type: ignore[return-value]
            except json.JSONDecodeError:
                # 3. Try truncation repair: find last complete object "}"
                candidate = match.group()
                last_brace = candidate.rfind("}")
                if last_brace > 0:
                    repaired = candidate[: last_brace + 1] + "]"
                    try:
                        result = json.loads(repaired)
                        if isinstance(result, list):
                            return result  # type: ignore[return-value]
                    except json.JSONDecodeError:
                        pass

        return None
