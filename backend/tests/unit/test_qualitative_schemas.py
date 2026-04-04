"""Unit tests for qualitative analysis schemas."""

from app.domain.schemas.qualitative import (
    ComentarioAnalisisRead,
    NubePalabras,
    PalabraFrecuencia,
    ResumenCualitativo,
    SentimientoDistribucion,
    TemaDistribucion,
    TipoConteo,
)


class TestComentarioAnalisisRead:
    def test_from_dict(self):
        data = {
            "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            "evaluacion_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
            "fuente": "Estudiante",
            "asignatura": "Programación I",
            "tipo": "fortaleza",
            "texto": "Excelente profesor",
            "tema": "actitud",
            "tema_confianza": "regla",
            "sentimiento": "positivo",
            "sent_score": 0.75,
            "procesado_ia": False,
        }
        schema = ComentarioAnalisisRead(**data)
        assert schema.tipo == "fortaleza"
        assert schema.sentimiento == "positivo"

    def test_nullable_sentiment(self):
        data = {
            "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            "evaluacion_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
            "fuente": "Director",
            "asignatura": "BD I",
            "tipo": "mejora",
            "texto": "Algo",
            "tema": "otro",
            "tema_confianza": "regla",
            "sentimiento": None,
            "sent_score": None,
            "procesado_ia": False,
        }
        schema = ComentarioAnalisisRead(**data)
        assert schema.sentimiento is None


class TestResumenCualitativo:
    def test_empty_resumen(self):
        r = ResumenCualitativo(
            total_comentarios=0,
            por_tipo=[],
            por_sentimiento=[],
            temas_top=[],
            sentimiento_promedio=None,
        )
        assert r.total_comentarios == 0

    def test_populated_resumen(self):
        r = ResumenCualitativo(
            total_comentarios=100,
            por_tipo=[TipoConteo(tipo="fortaleza", count=60)],
            por_sentimiento=[
                SentimientoDistribucion(sentimiento="positivo", count=70, porcentaje=70.0)
            ],
            temas_top=[
                TemaDistribucion(tema="comunicacion", count=30, porcentaje=30.0)
            ],
            sentimiento_promedio=0.45,
        )
        assert r.por_tipo[0].tipo == "fortaleza"
        assert r.temas_top[0].porcentaje == 30.0


class TestNubePalabras:
    def test_creation(self):
        nube = NubePalabras(
            tipo="fortaleza",
            palabras=[
                PalabraFrecuencia(text="excelente", value=15),
                PalabraFrecuencia(text="claro", value=10),
            ],
        )
        assert len(nube.palabras) == 2
        assert nube.palabras[0].text == "excelente"
