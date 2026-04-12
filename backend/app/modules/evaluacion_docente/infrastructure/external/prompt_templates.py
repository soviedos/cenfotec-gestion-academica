"""Versioned prompt templates for Gemini API interactions.

All prompts are plain f-string templates.  Keeping them here (not inline
in the gateway) makes them easy to review, A/B test, and version.
"""

# ── Comment analysis prompts (sentiment / tema classification) ───────────

COMMENT_ANALYSIS_SYSTEM_PROMPT = """\
Eres un experto en análisis de evaluaciones docentes universitarias.

Tu tarea es clasificar comentarios de estudiantes y directores sobre
profesores.  Para CADA comentario devuelve un JSON con:

- "tema": categoría temática principal.  Valores permitidos:
    metodologia, dominio_tema, comunicacion, evaluacion, puntualidad,
    material, actitud, tecnologia, organizacion, otro
- "sentimiento": uno de: positivo, neutro, mixto, negativo
- "sent_score": float de -1.0 (muy negativo) a 1.0 (muy positivo)
- "resumen": una frase breve (máx 20 palabras) que capture la esencia

Reglas:
- Interpreta el contexto completo, no solo palabras sueltas.
- "mixto" significa que el comentario tiene aspectos positivos Y negativos.
- Si el comentario es genérico sin contenido evaluativo, usa tema="otro" y sentimiento="neutro".
- Si el comentario menciona múltiples temas, elige el PREDOMINANTE.

Responde EXCLUSIVAMENTE con un JSON array.  Sin texto adicional.
"""

COMMENT_ANALYSIS_USER_TEMPLATE = """\
Clasifica los siguientes {count} comentarios de evaluaciones docentes.

{comments_block}

Responde con un JSON array de exactamente {count} objetos, en el MISMO orden.
Cada objeto: {{"idx": <número>, "tema": "...",
"sentimiento": "...", "sent_score": <float>, "resumen": "..."}}
"""


def format_comments_for_analysis(comments: list[dict]) -> str:
    """Build the numbered comments block for the analysis prompt.

    Each dict must have keys: ``idx`` (1-based), ``texto``, ``tipo``.
    """
    lines: list[str] = []
    for c in comments:
        lines.append(f"[{c['idx']}] ({c['tipo']}) {c['texto']}")
    return "\n".join(lines)


# ── Query prompts (RAG) ─────────────────────────────────────────────────

QUERY_SYSTEM_PROMPT = """\
Eres un asistente experto en análisis de evaluaciones docentes universitarias.
Tu rol es responder preguntas sobre el desempeño de profesores basándote
EXCLUSIVAMENTE en la evidencia proporcionada.

Reglas:
- Responde siempre en español.
- Cita la evidencia usando referencias numéricas [1], [2], etc.
- Si la evidencia no es suficiente para responder, dilo explícitamente.
- No inventes datos. Solo usa la información proporcionada.
- Sé conciso pero completo. Máximo 3 párrafos.
- Si hay métricas numéricas, inclúyelas en tu respuesta.
"""

QUERY_USER_TEMPLATE = """\
Pregunta del usuario: {question}

=== EVIDENCIA ===

{evidence_block}

=== FIN EVIDENCIA ===

Responde la pregunta basándote únicamente en la evidencia anterior.
Cita las fuentes con [número] cuando las uses.
"""


def format_evidence_block(
    comments: list[dict],
    metrics: list[dict],
) -> str:
    """Build the evidence block injected into the prompt.

    Each item is numbered so Gemini can cite them as [1], [2], etc.
    """
    lines: list[str] = []
    idx = 1

    for m in metrics:
        lines.append(f"[{idx}] MÉTRICA — {m['label']}: {m['value']}")
        if m.get("periodo"):
            lines[-1] += f" (período: {m['periodo']})"
        if m.get("docente"):
            lines[-1] += f" (docente: {m['docente']})"
        idx += 1

    for c in comments:
        source_parts = [
            c.get("docente", ""),
            c.get("asignatura", ""),
            c.get("periodo", ""),
            c.get("fuente", ""),
        ]
        source_str = " | ".join(p for p in source_parts if p)
        lines.append(f'[{idx}] COMENTARIO ({c.get("tipo", "")}) — "{c["texto"]}" [{source_str}]')
        idx += 1

    return "\n".join(lines) if lines else "(Sin evidencia disponible)"
