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
