"""Deterministic keyword-based classifier for teacher evaluation comments.

Classifies comments by:
- **tema**: thematic category based on keyword matching
- **sentimiento**: rule-based sentiment (placeholder for future Gemini integration)

Design:
    The classifier is a pure function with no I/O.  It receives a comment text
    and returns a classification dict.  This makes it trivially testable and
    allows swapping the implementation (e.g., to Gemini) via the
    ``SentimentClassifier`` protocol.
"""

from __future__ import annotations

import re
from typing import Protocol, TypedDict

# ── Tema keyword map ─────────────────────────────────────────────────────
# Each key is a tema. Values are stem-like prefixes matched case-insensitively.
# Order matters: first match wins.

TEMA_KEYWORDS: dict[str, list[str]] = {
    "metodologia": [
        "dinám",
        "método",
        "metodolog",
        "actividad",
        "práctic",
        "ejercicio",
        "taller",
        "didáctic",
        "creativ",
        "innovador",
    ],
    "dominio_tema": [
        "dominio",
        "conocimiento",
        "experto",
        "experiencia",
        "sabe",
        "manejo del tema",
        "preparad",
    ],
    "comunicacion": [
        "explic",
        "clar",
        "comunic",
        "interac",
        "entend",
        "escucha",
        "atenci",
        "pregunt",
        "participac",
    ],
    "evaluacion": [
        "nota",
        "examen",
        "exámen",
        "evalua",
        "rúbrica",
        "califica",
        "retroaliment",
        "feedback",
        "prueba",
        "quiz",
    ],
    "puntualidad": [
        "puntual",
        "hora",
        "tarde",
        "asisten",
        "falt",
        "llega tarde",
        "cumpl",
        "responsab",
    ],
    "material": [
        "material",
        "presentaci",
        "plataforma",
        "recurso",
        "slide",
        "diapositiva",
        "document",
        "guía",
        "bibliograf",
    ],
    "actitud": [
        "amable",
        "respetuos",
        "motiv",
        "disposici",
        "pacien",
        "trato",
        "empat",
        "comprensiv",
        "cordial",
        "agradable",
        "buen profesor",
        "excelente profesor",
        "buen docente",
        "excelente docente",
    ],
    "tecnologia": [
        "cámara",
        "virtual",
        "zoom",
        "teams",
        "micrófono",
        "herramienta",
        "tecnolog",
        "plataforma virtual",
        "en línea",
        "online",
    ],
    "organizacion": [
        "organiz",
        "estructur",
        "programa",
        "continu",
        "planific",
        "orden",
        "secuencia",
        "syllabus",
    ],
}

# Pre-compile patterns for performance
_TEMA_PATTERNS: dict[str, re.Pattern[str]] = {
    tema: re.compile("|".join(re.escape(kw) for kw in keywords), re.IGNORECASE)
    for tema, keywords in TEMA_KEYWORDS.items()
}

# ── Sentiment keywords ───────────────────────────────────────────────────
# Simple rule-based sentiment as Phase 1 placeholder.  Will be replaced by
# Gemini in Phase 2.

_POS_WORDS = re.compile(
    r"excelente|muy bien|bien|bueno|buena|genial|gran|perfecto|"
    r"destaca|felicit|recomiendo|mejor|increíble|fantástic|maravill|"
    r"sobresaliente|extraordinari|impecable|dedicad",
    re.IGNORECASE,
)
_NEG_WORDS = re.compile(
    r"malo|mala|terrible|pésim|deficiente|horrible|no explic|"
    r"no entien|confus|desorganizad|impuntual|irrespet|"
    r"no sabe|no domin|aburrido|monóton|dejar mucho que desear|"
    r"flojo|mejorar mucho|no recomiendo",
    re.IGNORECASE,
)


class ClassificationResult(TypedDict):
    tema: str
    tema_confianza: str
    sentimiento: str
    sent_score: float


class SentimentClassifier(Protocol):
    """Protocol for future classifier implementations (e.g., Gemini)."""

    def classify(self, texto: str, tipo: str) -> ClassificationResult: ...


# ── Public API ───────────────────────────────────────────────────────────


def classify_tema(texto: str) -> tuple[str, str]:
    """Return (tema, confianza) for a comment text.

    Confianza is ``"regla"`` for keyword-matched or ``"regla"`` for the
    fallback ``"otro"``.
    """
    for tema, pattern in _TEMA_PATTERNS.items():
        if pattern.search(texto):
            return tema, "regla"
    return "otro", "regla"


def classify_sentimiento(texto: str, tipo: str) -> tuple[str, float]:
    """Return (sentimiento, score) using keyword rules.

    The ``tipo`` field (fortaleza/mejora/observacion) provides a strong
    prior: fortalezas skew positive, mejoras skew negative.

    Score range: -1.0 (very negative) to 1.0 (very positive).
    """
    pos_hits = len(_POS_WORDS.findall(texto))
    neg_hits = len(_NEG_WORDS.findall(texto))

    # tipo-based prior
    if tipo == "fortaleza":
        pos_hits += 1
    elif tipo == "mejora":
        neg_hits += 1

    total = pos_hits + neg_hits
    if total == 0:
        return "neutro", 0.0

    raw_score = (pos_hits - neg_hits) / total  # range -1 to 1

    if raw_score > 0.25:
        label = "positivo"
    elif raw_score < -0.25:
        label = "negativo"
    elif pos_hits > 0 and neg_hits > 0:
        label = "mixto"
    else:
        label = "neutro"

    return label, round(raw_score, 2)


def classify_comment(texto: str, tipo: str) -> ClassificationResult:
    """Full classification of a single comment.

    This is the main entry point used by the processing pipeline.
    """
    tema, confianza = classify_tema(texto)
    sentimiento, score = classify_sentimiento(texto, tipo)
    return ClassificationResult(
        tema=tema,
        tema_confianza=confianza,
        sentimiento=sentimiento,
        sent_score=score,
    )
