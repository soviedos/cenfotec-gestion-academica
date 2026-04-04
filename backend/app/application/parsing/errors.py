"""Error and result types for the PDF parser.

The parser *never* raises exceptions — it always returns a ``ParseResult``
containing either the parsed data or a list of structured errors.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from app.application.parsing.schemas import ParsedEvaluacion

Stage = Literal["open", "header", "metricas", "cursos", "comentarios", "validation"]


@dataclass(frozen=True)
class ParseError:
    """A non-recoverable problem found during parsing."""

    stage: Stage
    code: str
    message: str
    context: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ParseWarning:
    """A recoverable anomaly — data is still usable but not perfect."""

    code: str
    message: str
    context: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ParseMetadata:
    """Diagnostics about the parsing run."""

    parser_version: str
    pages_processed: int
    total_pages_declared: int | None = None
    tables_found: int = 0
    comment_sections_found: int = 0
    processing_time_ms: float = 0.0


@dataclass
class ParseResult:
    """Final output of ``parse_evaluacion()``."""

    success: bool
    data: ParsedEvaluacion | None = None
    errors: list[ParseError] = field(default_factory=list)
    warnings: list[ParseWarning] = field(default_factory=list)
    metadata: ParseMetadata = field(
        default_factory=lambda: ParseMetadata(parser_version="1.0.0", pages_processed=0)
    )
