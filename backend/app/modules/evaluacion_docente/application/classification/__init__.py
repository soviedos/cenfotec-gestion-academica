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

from app.modules.evaluacion_docente.domain.entities.enums import Sentimiento, TemaConfianza

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
    r"destaca|felicit|recomiendo|mejor(?!a)|increíble|fantástic|maravill|"
    r"sobresaliente|extraordinari|impecable|dedicad",
    re.IGNORECASE,
)

# Negative keywords split into two groups:
#  1. Compound "no + verb" patterns — these are intentionally negative and
#     should NOT be affected by the negation window (the "no" is integral).
#  2. Bare adjective/adverb keywords — these CAN be negated by a preceding
#     negator ("no es malo" → flip to positive).
_NEG_COMPOUNDS = re.compile(
    r"no explic|no entien|no sabe|no domin|no recomiendo|"
    r"dejar mucho que desear|mejorar mucho|"
    r"podría mejorar|debe mejorar|puede mejorar|"
    r"falta mejorar|necesita mejorar|tiene que mejorar",
    re.IGNORECASE,
)
_NEG_BARE = re.compile(
    r"malo|mala|terrible|pésim|deficiente|horrible|"
    r"confus|desorganizad|impuntual|irrespet|"
    r"aburrido|monóton|flojo|queja|problem",
    re.IGNORECASE,
)

# Combined pattern used for backward-compat imports in tests
_NEG_WORDS = re.compile(
    r"malo|mala|terrible|pésim|deficiente|horrible|no explic|"
    r"no entien|confus|desorganizad|impuntual|irrespet|"
    r"no sabe|no domin|aburrido|monóton|dejar mucho que desear|"
    r"flojo|mejorar mucho|no recomiendo",
    re.IGNORECASE,
)

# ── Negation handling ────────────────────────────────────────────────────
# Negators that can invert the polarity of a bare negative keyword
# within a window of up to 3 preceding words.
_NEGATORS = {
    "no",
    "ni",
    "sin",
    "nunca",
    "ningún",
    "ningun",
    "ninguna",
    "ninguno",
    "nada",
    "jamás",
    "jamas",
}

# Litote patterns: negator + negative noun → implicit positive.
# "no tengo queja", "sin problemas", "no hay debilidades".
_LITOTE = re.compile(
    r"(?:no|ni|sin|nunca|ningún|ningun|ninguna|ninguno|jamás|jamas)\b"
    r"(?:\s+\w+){0,3}\s+"
    r"(?:queja|problema|debilidad|falla|defecto|inconveniente|"
    r"dificultad|observacion|observación|objecion|objeción|reproche|reclamo|"
    r"fallo|falencia|carencia|insuficiencia|déficit|critica|crítica)",
    re.IGNORECASE,
)

# ── Explicit phrase patterns (pre-scan) ──────────────────────────────
# Common idiomatic expressions detected BEFORE keyword counting.
# Positive phrases imply satisfaction despite containing negative words.
# Neutral phrases are non-evaluative meta-comments; masked to prevent
# accidental negative hits but contribute no score.
_POSITIVE_PHRASES = re.compile(
    r"no tengo (?:ninguna )?quejas?|"
    r"no hay problemas?|"
    r"no hay quejas?|"
    r"ninguna queja|"
    r"ningún problema|"
    r"nada que mejorar",
    re.IGNORECASE,
)

_NEUTRAL_PHRASES = re.compile(
    r"\bno aplica\b|sin observaciones",
    re.IGNORECASE,
)

# Non-evaluative / empty comments — students who have nothing to say.
# Detected BEFORE keyword counting; forces neutro regardless of tipo.
_NON_EVALUATIVE = re.compile(
    r"^\s*(?:"
    r"nada\.?|na\.?|n/?a\.?|ninguno\.?|ninguna\.?|---?|\.\.?\.?|"
    r"nada que (?:agregar|comentar|decir|añadir|mencionar|reportar|aportar)|"
    r"no tengo (?:nada |nada que |ningún )?(?:comentario|observaci[oó]n|aporte|nada)s?(?:\b.*)?|"
    r"sin (?:comentarios?|nada|novedad(?:es)?)|"
    r"todo bien|todo(?:\s+está)?\s+bien|nada(?:\s+más)?\s+que\s+decir"
    r")\s*\.?\s*$",
    re.IGNORECASE,
)


def _is_negated(texto: str, match_start: int) -> bool:
    """Check if a keyword match is preceded by a negator within 3 words."""
    prefix = texto[:match_start].rstrip()
    words = prefix.split()
    window = words[-3:] if len(words) >= 3 else words
    return any(w.lower().rstrip(",;:.") in _NEGATORS for w in window)


def _mask_phrases(texto: str) -> tuple[str, int]:
    """Detect explicit idiomatic phrases, mask them, return (masked_text, pos_hits).

    Positive phrases contribute +1 each.  Neutral phrases are masked
    without adding score.
    """
    pos = len(_POSITIVE_PHRASES.findall(texto))
    masked = _POSITIVE_PHRASES.sub("", texto)
    masked = _NEUTRAL_PHRASES.sub("", masked)
    return masked, pos


def _count_hits(texto: str) -> tuple[int, int]:
    """Count positive and negative keyword hits in already-masked text.

    Applies patterns in priority order, masking each layer to prevent
    double-counting:
        1. Positive keywords
        2. Compound negations (always negative)
        3. Litote patterns (positive)
        4. Bare negative adjectives (negation-window aware)
    """
    pos = len(_POS_WORDS.findall(texto))
    neg = len(_NEG_COMPOUNDS.findall(texto))
    texto = _NEG_COMPOUNDS.sub("", texto)

    pos += len(_LITOTE.findall(texto))
    texto = _LITOTE.sub("", texto)

    for m in _NEG_BARE.finditer(texto):
        if _is_negated(texto, m.start()):
            pos += 1
        else:
            neg += 1

    return pos, neg


def _score_to_label(pos: int, neg: int) -> tuple[str, float]:
    """Convert hit counts to (sentimiento, score)."""
    total = pos + neg
    if total == 0:
        return Sentimiento.NEUTRO, 0.0

    raw = (pos - neg) / total

    if raw > 0.25:
        label = Sentimiento.POSITIVO
    elif raw < -0.25:
        label = Sentimiento.NEGATIVO
    elif pos > 0 and neg > 0:
        label = Sentimiento.MIXTO
    else:
        label = Sentimiento.NEUTRO

    return label, round(raw, 2)


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
            return tema, TemaConfianza.REGLA
    return "otro", TemaConfianza.REGLA


def classify_sentimiento(texto: str, tipo: str) -> tuple[str, float]:
    """Return (sentimiento, score) using keyword rules.

    The ``tipo`` field (fortaleza/mejora/observacion) indicates which
    section of the evaluation form the comment came from.  It acts as
    a weak prior that only applies when evaluative keywords are present.

    Score range: -1.0 (very negative) to 1.0 (very positive).
    """
    # 0. Non-evaluative / empty comments → always neutro
    if _NON_EVALUATIVE.match(texto):
        return Sentimiento.NEUTRO, 0.0

    # 1. Mask idiomatic phrases
    masked, pos_hits = _mask_phrases(texto)

    # 2. Count keyword hits
    kw_pos, neg_hits = _count_hits(masked)
    pos_hits += kw_pos

    # 3. Apply tipo prior ONLY when evaluative keywords are present.
    #    Without keywords the tipo alone should not determine sentiment.
    if pos_hits > 0 or neg_hits > 0:
        if tipo == "fortaleza":
            pos_hits += 1
        elif tipo == "mejora":
            neg_hits += 1

    # 4. Score → label
    return _score_to_label(pos_hits, neg_hits)


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
