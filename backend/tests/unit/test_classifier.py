"""Unit tests for the keyword-based comment classifier."""

from app.application.classification import classify_comment, classify_sentimiento, classify_tema

# ── classify_tema ────────────────────────────────────────────────────────


class TestClassifyTema:
    """Tema classification via keyword matching."""

    def test_metodologia_dinamica(self):
        tema, conf = classify_tema("Usa dinámicas muy buenas en clase")
        assert tema == "metodologia"
        assert conf == "regla"

    def test_metodologia_taller(self):
        tema, _ = classify_tema("Los talleres prácticos son excelentes")
        assert tema == "metodologia"

    def test_comunicacion_explica(self):
        tema, _ = classify_tema("Explica de forma clara")
        assert tema == "comunicacion"

    def test_comunicacion_interaccion(self):
        tema, _ = classify_tema("Buena interacción con estudiantes")
        assert tema == "comunicacion"

    def test_evaluacion_notas(self):
        tema, _ = classify_tema("Las notas no reflejan el esfuerzo")
        assert tema == "evaluacion"

    def test_evaluacion_retroalimentacion(self):
        tema, _ = classify_tema("Falta retroalimentación en los exámenes")
        assert tema == "evaluacion"

    def test_puntualidad(self):
        tema, _ = classify_tema("No es puntual, llega tarde siempre")
        assert tema == "puntualidad"

    def test_material(self):
        tema, _ = classify_tema("Las presentaciones están desactualizadas")
        assert tema == "material"

    def test_actitud_amable(self):
        tema, _ = classify_tema("Muy amable y respetuoso con todos")
        assert tema == "actitud"

    def test_actitud_buen_profesor(self):
        tema, _ = classify_tema("Es un excelente profesor")
        assert tema == "actitud"

    def test_tecnologia_camara(self):
        tema, _ = classify_tema("No enciende la cámara en clase virtual")
        assert tema == "tecnologia"

    def test_organizacion(self):
        tema, _ = classify_tema("El curso está bien organizado")
        assert tema == "organizacion"

    def test_dominio_tema(self):
        tema, _ = classify_tema("Tiene gran dominio del tema")
        assert tema == "dominio_tema"

    def test_fallback_otro(self):
        tema, conf = classify_tema("Lorem ipsum dolor sit amet")
        assert tema == "otro"
        assert conf == "regla"

    def test_first_match_wins(self):
        # "actividad" matches metodologia before comunicacion
        tema, _ = classify_tema("actividad de participación")
        assert tema == "metodologia"

    def test_case_insensitive(self):
        tema, _ = classify_tema("EXCELENTE METODOLOGÍA DE ENSEÑANZA")
        assert tema == "metodologia"


# ── classify_sentimiento ─────────────────────────────────────────────────


class TestClassifySentimiento:
    """Sentiment classification via keyword + tipo prior."""

    def test_positive_words(self):
        sent, score = classify_sentimiento("Excelente profesor, muy bien", "observacion")
        assert sent == "positivo"
        assert score > 0

    def test_negative_words(self):
        sent, score = classify_sentimiento("Terrible clase, muy malo", "observacion")
        assert sent == "negativo"
        assert score < 0

    def test_mixed(self):
        sent, score = classify_sentimiento("Bueno pero terrible organización", "observacion")
        assert sent == "mixto"

    def test_neutral_no_keywords(self):
        sent, score = classify_sentimiento("Asiste a todas las clases", "observacion")
        assert sent == "neutro"
        assert score == 0.0

    def test_fortaleza_prior_shifts_positive(self):
        # Plain text with no keywords, but fortaleza tipo gives +1 pos
        sent, _ = classify_sentimiento("Asiste puntualmente", "fortaleza")
        assert sent == "positivo"

    def test_mejora_prior_shifts_negative(self):
        sent, _ = classify_sentimiento("Asiste puntualmente", "mejora")
        assert sent == "negativo"

    def test_observacion_no_prior(self):
        sent, _ = classify_sentimiento("Asiste puntualmente", "observacion")
        assert sent == "neutro"

    def test_score_range(self):
        _, score = classify_sentimiento("Excelente genial perfecto increíble", "fortaleza")
        assert -1.0 <= score <= 1.0


# ── classify_comment (full pipeline) ────────────────────────────────────


class TestClassifyComment:
    """Integration of tema + sentimiento classification."""

    def test_returns_all_keys(self):
        result = classify_comment("Explica muy bien los temas", "fortaleza")
        assert set(result.keys()) == {"tema", "tema_confianza", "sentimiento", "sent_score"}

    def test_positive_fortaleza(self):
        result = classify_comment("Excelente dominio del tema", "fortaleza")
        assert result["tema"] == "dominio_tema"
        assert result["sentimiento"] == "positivo"
        assert result["sent_score"] > 0

    def test_negative_mejora(self):
        result = classify_comment("No explica bien, muy confuso", "mejora")
        assert result["tema"] == "comunicacion"
        assert result["sentimiento"] == "negativo"

    def test_otro_neutral(self):
        result = classify_comment("Sin datos adicionales", "observacion")
        assert result["tema"] == "otro"

    def test_tema_confianza_always_regla(self):
        result = classify_comment("Buen manejo de Zoom", "fortaleza")
        assert result["tema_confianza"] == "regla"


class TestNegationHandling:
    """Tests for negation-aware sentiment classification."""

    # ── Negated bare adjectives → positive ──────────────────────────────

    def test_negated_malo_is_positive(self):
        result = classify_comment("no es malo", "observacion")
        assert result["sentimiento"] == "positivo"

    def test_negated_deficiente_is_positive(self):
        result = classify_comment("no es deficiente", "observacion")
        assert result["sentimiento"] == "positivo"

    def test_negated_horrible_is_positive(self):
        result = classify_comment("no es horrible", "observacion")
        assert result["sentimiento"] == "positivo"

    def test_negated_terrible_is_positive(self):
        result = classify_comment("no hay nada terrible", "observacion")
        assert result["sentimiento"] == "positivo"

    # ── Non-negated bare adjectives → still negative ────────────────────

    def test_bare_malo_still_negative(self):
        result = classify_comment("es muy malo", "observacion")
        assert result["sentimiento"] == "negativo"

    def test_bare_terrible_still_negative(self):
        result = classify_comment("terrible clase", "observacion")
        assert result["sentimiento"] == "negativo"

    def test_bare_deficiente_still_negative(self):
        result = classify_comment("es deficiente", "observacion")
        assert result["sentimiento"] == "negativo"

    # ── Compound patterns → always negative ─────────────────────────────

    def test_no_explica_stays_negative(self):
        result = classify_comment("no explica nada", "observacion")
        assert result["sentimiento"] == "negativo"

    def test_no_sabe_stays_negative(self):
        result = classify_comment("no sabe del tema", "observacion")
        assert result["sentimiento"] == "negativo"

    def test_no_domina_stays_negative(self):
        result = classify_comment("no domina la materia", "observacion")
        assert result["sentimiento"] == "negativo"

    # ── Litote patterns → positive ──────────────────────────────────────

    def test_no_tengo_queja_is_positive(self):
        result = classify_comment("no tengo ninguna queja", "observacion")
        assert result["sentimiento"] == "positivo"

    def test_sin_problemas_is_positive(self):
        result = classify_comment("sin problemas", "observacion")
        assert result["sentimiento"] == "positivo"

    def test_no_hay_debilidades_is_positive(self):
        result = classify_comment("no hay debilidades", "observacion")
        assert result["sentimiento"] == "positivo"

    def test_sin_observaciones_is_neutral(self):
        result = classify_comment("sin observaciones", "observacion")
        assert result["sentimiento"] == "neutro"

    def test_no_hay_quejas_is_positive(self):
        result = classify_comment("no hay quejas", "observacion")
        assert result["sentimiento"] == "positivo"

    # ── Mixed scenarios ─────────────────────────────────────────────────

    def test_negated_negative_plus_positive_word(self):
        """Both positive word and negated adjective → positive."""
        result = classify_comment("excelente, no es malo", "observacion")
        assert result["sentimiento"] == "positivo"
        assert result["sent_score"] == 1.0

    def test_negated_negative_plus_non_negated_negative(self):
        """Conflicting: 'no es malo' (+1) and 'terrible' (-1) → mixto."""
        result = classify_comment("no es malo pero terrible evaluacion", "observacion")
        assert result["sentimiento"] == "mixto"

    # ── Edge: negator too far away (>3 words) ───────────────────────────

    def test_negator_beyond_window_does_not_flip(self):
        """Negator more than 3 words before adjective → no flip."""
        result = classify_comment("no creo que el profesor sea malo", "observacion")
        assert result["sentimiento"] == "negativo"
        result = classify_comment("no creo que el profesor sea malo", "observacion")
        assert result["sentimiento"] == "negativo"


class TestExplicitPhrases:
    """Tests for explicit idiomatic phrase detection (pre-scan layer)."""

    def test_no_tengo_ninguna_queja(self):
        result = classify_comment("no tengo ninguna queja", "observacion")
        assert result["sentimiento"] == "positivo"

    def test_no_hay_quejas(self):
        result = classify_comment("no hay quejas", "observacion")
        assert result["sentimiento"] == "positivo"

    def test_ninguna_queja(self):
        result = classify_comment("ninguna queja", "observacion")
        assert result["sentimiento"] == "positivo"

    def test_sin_observaciones(self):
        result = classify_comment("sin observaciones", "observacion")
        assert result["sentimiento"] == "neutro"
        assert result["sent_score"] == 0.0

    def test_no_hay_problemas(self):
        result = classify_comment("no hay problemas", "observacion")
        assert result["sentimiento"] == "positivo"

    def test_ningun_problema(self):
        result = classify_comment("ningún problema", "observacion")
        assert result["sentimiento"] == "positivo"

    def test_nada_que_mejorar(self):
        result = classify_comment("nada que mejorar", "observacion")
        assert result["sentimiento"] == "positivo"

    def test_no_aplica_is_neutral(self):
        result = classify_comment("no aplica", "observacion")
        assert result["sentimiento"] == "neutro"
        assert result["sent_score"] == 0.0

    def test_phrase_plus_positive_word(self):
        """Explicit phrase + positive keyword → still positive."""
        result = classify_comment("excelente, no tengo ninguna queja", "observacion")
        assert result["sentimiento"] == "positivo"

    def test_phrase_does_not_trigger_negative(self):
        """Phrase with negative words inside must not count as negative."""
        result = classify_comment("nada que mejorar, todo bien", "observacion")
        assert result["sentimiento"] == "positivo"

    def test_no_aplica_with_fortaleza_prior(self):
        """'no aplica' as fortaleza → positive from prior only."""
        result = classify_comment("no aplica", "fortaleza")
        assert result["sentimiento"] == "positivo"
        result = classify_comment("no aplica", "fortaleza")
        assert result["sentimiento"] == "positivo"


class TestSentimentRequired:
    """Required sentiment cases: negation-safe, real negatives, and mixed."""

    # ── Correctos: no deben ser negativos ───────────────────────────

    def test_no_tengo_ninguna_queja_not_negative(self):
        sent, _ = classify_sentimiento("no tengo ninguna queja", "observacion")
        assert sent != "negativo"

    def test_no_hay_debilidades_not_negative(self):
        sent, _ = classify_sentimiento("no hay debilidades", "observacion")
        assert sent != "negativo"

    def test_ningun_problema_not_negative(self):
        sent, _ = classify_sentimiento("ningún problema", "observacion")
        assert sent != "negativo"

    def test_sin_observaciones_neutro(self):
        sent, score = classify_sentimiento("sin observaciones", "observacion")
        assert sent == "neutro"
        assert score == 0.0

    def test_nada_que_mejorar_not_negative(self):
        sent, _ = classify_sentimiento("nada que mejorar", "observacion")
        assert sent != "negativo"

    # ── Negativos reales ───────────────────────────────────────

    def test_tengo_una_queja_negativo(self):
        sent, score = classify_sentimiento("tengo una queja", "observacion")
        assert sent == "negativo"
        assert score < 0

    def test_hay_problemas_negativo(self):
        sent, score = classify_sentimiento("hay problemas de comunicación", "observacion")
        assert sent == "negativo"
        assert score < 0

    def test_mala_actitud_negativo(self):
        sent, score = classify_sentimiento("mala actitud del docente", "observacion")
        assert sent == "negativo"
        assert score < 0

    # ── Mixto ────────────────────────────────────────────────

    def test_no_hay_problemas_pero_podria_mejorar_mixto(self):
        sent, _ = classify_sentimiento("no hay problemas pero podría mejorar", "observacion")
        assert sent == "mixto"
