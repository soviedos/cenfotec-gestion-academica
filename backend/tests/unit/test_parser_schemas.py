"""Unit tests for parser Pydantic schemas — validation rules."""

import pytest
from pydantic import ValidationError

from app.application.parsing.schemas import (
    Comentario,
    CursoGrupo,
    DimensionMetrica,
    FuentePuntaje,
    HeaderData,
    ParsedEvaluacion,
    ResumenPorcentajes,
)


class TestHeaderData:
    def test_valid(self):
        h = HeaderData(
            profesor_nombre="ALVARO CORDERO",
            profesor_codigo="P000001249",
            periodo="C2 2025",
            recinto="TODOS",
        )
        assert h.profesor_nombre == "ALVARO CORDERO"

    def test_nombre_too_short(self):
        with pytest.raises(ValidationError):
            HeaderData(profesor_nombre="A", periodo="C2 2025", recinto="X")

    def test_codigo_optional(self):
        h = HeaderData(profesor_nombre="TEST NAME", periodo="C1 2026", recinto="SEDE")
        assert h.profesor_codigo is None


class TestFuentePuntaje:
    def test_valid(self):
        f = FuentePuntaje(puntos_obtenidos=18.61, puntos_maximos=20.0, porcentaje=93.05)
        assert f.porcentaje == 93.05

    def test_negative_puntos(self):
        with pytest.raises(ValidationError):
            FuentePuntaje(puntos_obtenidos=-1, puntos_maximos=20.0, porcentaje=50.0)

    def test_zero_maximos(self):
        with pytest.raises(ValidationError):
            FuentePuntaje(puntos_obtenidos=0, puntos_maximos=0, porcentaje=0)

    def test_pct_over_100(self):
        with pytest.raises(ValidationError):
            FuentePuntaje(puntos_obtenidos=10, puntos_maximos=10, porcentaje=101.0)


class TestDimensionMetrica:
    def _make_fuente(self, pct=90.0):
        return FuentePuntaje(puntos_obtenidos=18.0, puntos_maximos=20.0, porcentaje=pct)

    def test_valid_dimension(self):
        d = DimensionMetrica(
            nombre="METODOLOGÍA",
            estudiante=self._make_fuente(93.05),
            director=self._make_fuente(100.0),
            autoevaluacion=self._make_fuente(80.0),
            promedio_general_puntos=14.87,
            promedio_general_pct=91.02,
        )
        assert d.nombre == "METODOLOGÍA"


class TestCursoGrupo:
    def test_valid(self):
        c = CursoGrupo(
            escuela="ESC ING",
            codigo="INF-02",
            nombre="Fundamentos de Programación",
            estudiantes_respondieron=13,
            estudiantes_matriculados=15,
            grupo="SCV0",
            pct_estudiante=92.75,
            pct_director=100.0,
            pct_autoevaluacion=82.60,
            pct_promedio_general=91.78,
        )
        assert c.estudiantes_respondieron == 13

    def test_negative_students(self):
        with pytest.raises(ValidationError):
            CursoGrupo(
                escuela="X", codigo="Y-1", nombre="Z",
                estudiantes_respondieron=-1, estudiantes_matriculados=10,
                grupo="G", pct_estudiante=0, pct_director=0,
                pct_autoevaluacion=0, pct_promedio_general=0,
            )


class TestComentario:
    def test_all_none(self):
        c = Comentario()
        assert c.fortaleza is None
        assert c.mejora is None
        assert c.observacion is None

    def test_partial(self):
        c = Comentario(fortaleza="Bueno")
        assert c.fortaleza == "Bueno"
        assert c.mejora is None


class TestParsedEvaluacion:
    def _make_minimal(self):
        return ParsedEvaluacion(
            header=HeaderData(
                profesor_nombre="TEST PROF",
                periodo="C1 2025",
                recinto="SEDE",
            ),
            dimensiones=[
                DimensionMetrica(
                    nombre="METODOLOGÍA",
                    estudiante=FuentePuntaje(
                        puntos_obtenidos=18, puntos_maximos=20, porcentaje=90,
                    ),
                    director=FuentePuntaje(
                        puntos_obtenidos=10, puntos_maximos=10, porcentaje=100,
                    ),
                    autoevaluacion=FuentePuntaje(
                        puntos_obtenidos=16, puntos_maximos=20, porcentaje=80,
                    ),
                    promedio_general_puntos=14.0,
                    promedio_general_pct=90.0,
                ),
            ],
            resumen_pct=ResumenPorcentajes(
                estudiante=90.0, director=100.0, autoevaluacion=80.0, promedio_general=90.0,
            ),
            cursos=[
                CursoGrupo(
                    escuela="ESC", codigo="X-01", nombre="Test",
                    estudiantes_respondieron=10, estudiantes_matriculados=12,
                    grupo="G1", pct_estudiante=90, pct_director=100,
                    pct_autoevaluacion=80, pct_promedio_general=90,
                ),
            ],
            total_respondieron=10,
            total_matriculados=12,
        )

    def test_valid_minimal(self):
        parsed = self._make_minimal()
        assert parsed.header.profesor_nombre == "TEST PROF"
        assert len(parsed.dimensiones) == 1
        assert len(parsed.cursos) == 1

    def test_no_dimensiones_fails(self):
        with pytest.raises(ValidationError):
            ParsedEvaluacion(
                header=HeaderData(profesor_nombre="X Y", periodo="C1", recinto="S"),
                dimensiones=[],
                resumen_pct=ResumenPorcentajes(
                    estudiante=0, director=0, autoevaluacion=0, promedio_general=0,
                ),
                cursos=[CursoGrupo(
                    escuela="E", codigo="Z-1", nombre="N",
                    estudiantes_respondieron=0, estudiantes_matriculados=0,
                    grupo="G", pct_estudiante=0, pct_director=0,
                    pct_autoevaluacion=0, pct_promedio_general=0,
                )],
                total_respondieron=0,
                total_matriculados=0,
            )

    def test_no_cursos_fails(self):
        with pytest.raises(ValidationError):
            ParsedEvaluacion(
                header=HeaderData(profesor_nombre="X Y", periodo="C1", recinto="S"),
                dimensiones=[
                    DimensionMetrica(
                        nombre="A",
                        estudiante=FuentePuntaje(
                            puntos_obtenidos=1, puntos_maximos=1, porcentaje=100,
                        ),
                        director=FuentePuntaje(
                            puntos_obtenidos=1, puntos_maximos=1, porcentaje=100,
                        ),
                        autoevaluacion=FuentePuntaje(
                            puntos_obtenidos=1, puntos_maximos=1, porcentaje=100,
                        ),
                        promedio_general_puntos=1,
                        promedio_general_pct=100,
                    ),
                ],
                resumen_pct=ResumenPorcentajes(
                    estudiante=100, director=100, autoevaluacion=100, promedio_general=100,
                ),
                cursos=[],
                total_respondieron=0,
                total_matriculados=0,
            )

    def test_comments_default_empty(self):
        parsed = self._make_minimal()
        assert parsed.secciones_comentarios == []
