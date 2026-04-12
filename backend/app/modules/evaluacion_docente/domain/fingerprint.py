"""Content fingerprint — logical signature for probabilistic dedup.

Builds a deterministic fingerprint from structured fields extracted by
the PDF parser.  Two PDFs with different bytes but identical logical
content will produce the same fingerprint.

The fingerprint is a SHA-256 hex digest of a canonical string built from:

1. docente_nombre  (normalized: lowercase, stripped, unaccented)
2. modalidad       (already normalized UPPER by parser)
3. año             (integer)
4. periodo         (normalized string from parser)
5. cursos          (sorted codigo:grupo pairs)
6. promedio_general (rounded to 2 decimals)
7. dimensiones     (sorted nombre:pct_promedio pairs)
8. total_comentarios (count of non-empty comment fields)

Design decisions:
- Pure function, no I/O, no DB access → easy to test.
- Uses only ParsedEvaluacion (parser output) → no SQLAlchemy dependency.
- ``normalize_name`` strips accents with ``unicodedata`` (stdlib) to
  handle minor OCR/encoding variations without external deps.
- Returns both the hash and the structured criteria dict so callers
  can persist evidence in ``duplicados_probables.criterios``.
"""

from __future__ import annotations

import hashlib
import unicodedata
from dataclasses import dataclass, field

from app.modules.evaluacion_docente.application.parsing.schemas import ParsedEvaluacion

# ── Name normalization ──────────────────────────────────────────────────


def normalize_name(name: str) -> str:
    """Normalize a person name for fingerprint comparison.

    1. Strip leading/trailing whitespace
    2. Collapse internal whitespace to single spaces
    3. Lowercase
    4. Remove diacritics (á→a, ñ→n, ü→u)
    """
    collapsed = " ".join(name.split())
    lowered = collapsed.lower()
    # Decompose → strip combining marks → recompose
    nfkd = unicodedata.normalize("NFKD", lowered)
    return "".join(c for c in nfkd if unicodedata.category(c) != "Mn")


# ── Course key normalization ────────────────────────────────────────────


def build_cursos_key(cursos: list[dict[str, str]]) -> str:
    """Build a canonical sorted string from course codigo:grupo pairs.

    >>> build_cursos_key([{"codigo": "MAT201", "grupo": "02"}, {"codigo": "FIS101", "grupo": "01"}])
    'FIS101:01;MAT201:02'
    """
    pairs = sorted(f"{c['codigo'].strip().upper()}:{c['grupo'].strip()}" for c in cursos)
    return ";".join(pairs)


# ── Dimension key normalization ─────────────────────────────────────────


def build_dimensiones_key(dimensiones: list[dict[str, str | float]]) -> str:
    """Build a canonical sorted string from dimension nombre:pct pairs.

    >>> build_dimensiones_key(
    ...     [{"nombre": "Metodología", "pct": 85.50}, {"nombre": "Dominio", "pct": 90.00}]
    ... )
    'dominio:90.00;metodologia:85.50'
    """
    pairs = sorted(f"{normalize_name(str(d['nombre']))}:{float(d['pct']):.2f}" for d in dimensiones)
    return ";".join(pairs)


# ── Comment counting ────────────────────────────────────────────────────


def count_comments(parsed: ParsedEvaluacion) -> int:
    """Count total non-empty comment fields across all sections."""
    total = 0
    for seccion in parsed.secciones_comentarios:
        for comentario in seccion.comentarios:
            if comentario.fortaleza:
                total += 1
            if comentario.mejora:
                total += 1
            if comentario.observacion:
                total += 1
    return total


# ── Fingerprint result ──────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class FingerprintResult:
    """Output of ``compute_content_fingerprint``.

    Attributes:
        fingerprint: SHA-256 hex digest (64 chars) of the canonical string.
        canonical:   The pre-hash canonical string (useful for debugging).
        criterios:   Structured dict of normalized fields for evidence storage
                     in ``duplicados_probables.criterios``.
    """

    fingerprint: str
    canonical: str
    criterios: dict[str, object] = field(default_factory=dict)


# ── Main function ───────────────────────────────────────────────────────


def compute_content_fingerprint(parsed: ParsedEvaluacion) -> FingerprintResult:
    """Compute the logical fingerprint of a parsed evaluation.

    Parameters
    ----------
    parsed : ParsedEvaluacion
        The complete structured output from the PDF parser.

    Returns
    -------
    FingerprintResult
        Contains the hash, the canonical string, and a criterios dict
        suitable for storing as JSONB evidence.
    """
    docente = normalize_name(parsed.header.profesor_nombre)
    modalidad = parsed.periodo_data.modalidad.upper()
    año = parsed.periodo_data.año
    periodo = parsed.periodo_data.periodo_normalizado.upper().strip()

    cursos_raw = [{"codigo": c.codigo, "grupo": c.grupo} for c in parsed.cursos]
    cursos_key = build_cursos_key(cursos_raw)

    promedio = f"{parsed.resumen_pct.promedio_general:.2f}"

    dimensiones_raw = [
        {"nombre": d.nombre, "pct": d.promedio_general_pct} for d in parsed.dimensiones
    ]
    dimensiones_key = build_dimensiones_key(dimensiones_raw)

    total_comentarios = count_comments(parsed)

    # Build canonical string — order matters, separator "|" is safe
    # because none of the normalized fields can contain it.
    parts = [
        f"docente={docente}",
        f"modalidad={modalidad}",
        f"año={año}",
        f"periodo={periodo}",
        f"cursos={cursos_key}",
        f"promedio={promedio}",
        f"dimensiones={dimensiones_key}",
        f"comentarios={total_comentarios}",
    ]
    canonical = "|".join(parts)
    fingerprint = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    criterios = {
        "docente_nombre": docente,
        "modalidad": modalidad,
        "año": año,
        "periodo": periodo,
        "cursos": cursos_key,
        "promedio_general": promedio,
        "dimensiones": dimensiones_key,
        "total_comentarios": total_comentarios,
    }

    return FingerprintResult(
        fingerprint=fingerprint,
        canonical=canonical,
        criterios=criterios,
    )


# ── Comparison helper ───────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class ComparisonResult:
    """Result of comparing two fingerprint results field by field.

    Attributes:
        is_match:          True if fingerprints are identical.
        score:             Float 0.0–1.0 representing fraction of matching fields.
        matching_fields:   List of field names that match.
        differing_fields:  Dict of field names → (value_a, value_b) for mismatches.
    """

    is_match: bool
    score: float
    matching_fields: list[str]
    differing_fields: dict[str, tuple[object, object]]


_COMPARE_FIELDS = [
    "docente_nombre",
    "modalidad",
    "año",
    "periodo",
    "cursos",
    "promedio_general",
    "dimensiones",
    "total_comentarios",
]


def compare_fingerprints(a: FingerprintResult, b: FingerprintResult) -> ComparisonResult:
    """Compare two fingerprint results field by field.

    Useful when fingerprints differ but you want to know *how close*
    two documents are — e.g. for future fuzzy matching thresholds.

    Parameters
    ----------
    a, b : FingerprintResult
        The two results to compare.

    Returns
    -------
    ComparisonResult
        Detailed comparison with per-field match/mismatch info.
    """
    matching: list[str] = []
    differing: dict[str, tuple[object, object]] = {}

    for field_name in _COMPARE_FIELDS:
        val_a = a.criterios.get(field_name)
        val_b = b.criterios.get(field_name)
        if val_a == val_b:
            matching.append(field_name)
        else:
            differing[field_name] = (val_a, val_b)

    total = len(_COMPARE_FIELDS)
    score = len(matching) / total if total > 0 else 0.0

    return ComparisonResult(
        is_match=a.fingerprint == b.fingerprint,
        score=round(score, 2),
        matching_fields=matching,
        differing_fields=differing,
    )
