"""Tests for domain.fingerprint — content fingerprint construction & comparison."""

from __future__ import annotations

import pytest

from app.modules.evaluacion_docente.application.parsing.schemas import (
    Comentario,
    CursoGrupo,
    DimensionMetrica,
    FuentePuntaje,
    HeaderData,
    ParsedEvaluacion,
    PeriodoData,
    ResumenPorcentajes,
    SeccionComentarios,
)
from app.modules.evaluacion_docente.domain.fingerprint import (
    ComparisonResult,
    FingerprintResult,
    build_cursos_key,
    build_dimensiones_key,
    compare_fingerprints,
    compute_content_fingerprint,
    count_comments,
    normalize_name,
)

# ════════════════════════════════════════════════════════════════════════
# Helpers
# ════════════════════════════════════════════════════════════════════════


def _make_parsed(**overrides) -> ParsedEvaluacion:
    """Build a minimal ParsedEvaluacion with sensible defaults."""
    defaults = {
        "header": HeaderData(
            profesor_nombre="Juan Carlos Pérez",
            periodo="C1 2025",
            recinto="San José",
        ),
        "periodo_data": PeriodoData(
            periodo_raw="C1 2025",
            periodo_normalizado="C1 2025",
            modalidad="CUATRIMESTRAL",
            año=2025,
            periodo_orden=1,
            prefijo="C",
            numero=1,
        ),
        "dimensiones": [
            DimensionMetrica(
                nombre="METODOLOGÍA",
                estudiante=FuentePuntaje(puntos_obtenidos=18, puntos_maximos=20, porcentaje=90.0),
                director=FuentePuntaje(puntos_obtenidos=10, puntos_maximos=10, porcentaje=100.0),
                autoevaluacion=FuentePuntaje(
                    puntos_obtenidos=16, puntos_maximos=20, porcentaje=80.0
                ),
                promedio_general_puntos=14.0,
                promedio_general_pct=90.0,
            ),
            DimensionMetrica(
                nombre="Dominio de contenidos",
                estudiante=FuentePuntaje(puntos_obtenidos=16, puntos_maximos=20, porcentaje=80.0),
                director=FuentePuntaje(puntos_obtenidos=9, puntos_maximos=10, porcentaje=90.0),
                autoevaluacion=FuentePuntaje(
                    puntos_obtenidos=14, puntos_maximos=20, porcentaje=70.0
                ),
                promedio_general_puntos=13.0,
                promedio_general_pct=80.0,
            ),
        ],
        "resumen_pct": ResumenPorcentajes(
            estudiante=85.0,
            director=95.0,
            autoevaluacion=75.0,
            promedio_general=85.0,
        ),
        "cursos": [
            CursoGrupo(
                escuela="TI",
                codigo="MAT201",
                nombre="Cálculo II",
                estudiantes_respondieron=15,
                estudiantes_matriculados=20,
                grupo="01",
                pct_estudiante=85.0,
                pct_director=90.0,
                pct_autoevaluacion=80.0,
                pct_promedio_general=85.0,
            ),
            CursoGrupo(
                escuela="TI",
                codigo="FIS101",
                nombre="Física I",
                estudiantes_respondieron=12,
                estudiantes_matriculados=18,
                grupo="02",
                pct_estudiante=80.0,
                pct_director=85.0,
                pct_autoevaluacion=75.0,
                pct_promedio_general=80.0,
            ),
        ],
        "total_respondieron": 27,
        "total_matriculados": 38,
        "secciones_comentarios": [],
    }
    defaults.update(overrides)
    return ParsedEvaluacion(**defaults)


# ════════════════════════════════════════════════════════════════════════
# normalize_name
# ════════════════════════════════════════════════════════════════════════


class TestNormalizeName:
    def test_basic(self):
        assert normalize_name("Juan Pérez") == "juan perez"

    def test_accents_removed(self):
        assert normalize_name("María Ángela Gütiérrez") == "maria angela gutierrez"

    def test_ñ_removed(self):
        assert normalize_name("Muñoz Núñez") == "munoz nunez"

    def test_whitespace_collapsed(self):
        assert normalize_name("  Juan   Carlos   ") == "juan carlos"

    def test_tabs_and_newlines(self):
        assert normalize_name("Juan\t\n  Pérez") == "juan perez"

    def test_empty_string(self):
        assert normalize_name("") == ""

    def test_already_normalized(self):
        assert normalize_name("john doe") == "john doe"

    def test_uppercase_input(self):
        assert normalize_name("JOSÉ GARCÍA") == "jose garcia"

    def test_umlaut(self):
        # ü decomposes (u + combining diaeresis) but ß is a ligature, not a
        # combining-mark sequence, so NFKD leaves it intact.
        assert normalize_name("Über Straße") == "uber straße"


# ════════════════════════════════════════════════════════════════════════
# build_cursos_key
# ════════════════════════════════════════════════════════════════════════


class TestBuildCursosKey:
    def test_single_course(self):
        result = build_cursos_key([{"codigo": "MAT201", "grupo": "01"}])
        assert result == "MAT201:01"

    def test_sorts_alphabetically(self):
        result = build_cursos_key(
            [
                {"codigo": "MAT201", "grupo": "01"},
                {"codigo": "FIS101", "grupo": "02"},
            ]
        )
        assert result == "FIS101:02;MAT201:01"

    def test_normalizes_case_and_whitespace(self):
        result = build_cursos_key([{"codigo": " mat201 ", "grupo": "01"}])
        assert result == "MAT201:01"

    def test_empty_list(self):
        assert build_cursos_key([]) == ""

    def test_duplicate_codes_different_groups(self):
        result = build_cursos_key(
            [
                {"codigo": "MAT201", "grupo": "02"},
                {"codigo": "MAT201", "grupo": "01"},
            ]
        )
        assert result == "MAT201:01;MAT201:02"


# ════════════════════════════════════════════════════════════════════════
# build_dimensiones_key
# ════════════════════════════════════════════════════════════════════════


class TestBuildDimensionesKey:
    def test_sorts_by_normalized_name(self):
        result = build_dimensiones_key(
            [
                {"nombre": "Metodología", "pct": 85.50},
                {"nombre": "Dominio", "pct": 90.00},
            ]
        )
        assert result == "dominio:90.00;metodologia:85.50"

    def test_single_dimension(self):
        result = build_dimensiones_key([{"nombre": "Ética", "pct": 75.0}])
        assert result == "etica:75.00"

    def test_accent_normalization(self):
        result = build_dimensiones_key([{"nombre": "EVALUACIÓN", "pct": 80.0}])
        assert result == "evaluacion:80.00"

    def test_empty_list(self):
        assert build_dimensiones_key([]) == ""


# ════════════════════════════════════════════════════════════════════════
# count_comments
# ════════════════════════════════════════════════════════════════════════


class TestCountComments:
    def test_no_sections(self):
        parsed = _make_parsed(secciones_comentarios=[])
        assert count_comments(parsed) == 0

    def test_counts_all_nonempty_fields(self):
        parsed = _make_parsed(
            secciones_comentarios=[
                SeccionComentarios(
                    tipo_evaluacion="Estudiante",
                    asignatura="MAT201",
                    comentarios=[
                        Comentario(fortaleza="Bien", mejora="Regular", observacion=None),
                        Comentario(fortaleza=None, mejora=None, observacion="Nota"),
                    ],
                ),
            ]
        )
        assert count_comments(parsed) == 3  # fortaleza + mejora + observacion

    def test_skips_empty_strings(self):
        parsed = _make_parsed(
            secciones_comentarios=[
                SeccionComentarios(
                    tipo_evaluacion="Director",
                    asignatura="FIS101",
                    comentarios=[
                        Comentario(fortaleza="", mejora="Ok", observacion=""),
                    ],
                ),
            ]
        )
        # Empty strings are falsy → not counted
        assert count_comments(parsed) == 1

    def test_multiple_sections(self):
        parsed = _make_parsed(
            secciones_comentarios=[
                SeccionComentarios(
                    tipo_evaluacion="Estudiante",
                    asignatura="MAT201",
                    comentarios=[Comentario(fortaleza="A", mejora="B", observacion="C")],
                ),
                SeccionComentarios(
                    tipo_evaluacion="Director",
                    asignatura="MAT201",
                    comentarios=[Comentario(fortaleza="D")],
                ),
            ]
        )
        assert count_comments(parsed) == 4


# ════════════════════════════════════════════════════════════════════════
# compute_content_fingerprint
# ════════════════════════════════════════════════════════════════════════


class TestComputeContentFingerprint:
    def test_returns_fingerprint_result(self):
        result = compute_content_fingerprint(_make_parsed())
        assert isinstance(result, FingerprintResult)
        assert len(result.fingerprint) == 64  # SHA-256 hex
        assert isinstance(result.canonical, str)
        assert isinstance(result.criterios, dict)

    def test_deterministic(self):
        """Same input → same fingerprint every time."""
        a = compute_content_fingerprint(_make_parsed())
        b = compute_content_fingerprint(_make_parsed())
        assert a.fingerprint == b.fingerprint

    def test_different_docente_different_fingerprint(self):
        a = compute_content_fingerprint(_make_parsed())
        b = compute_content_fingerprint(
            _make_parsed(
                header=HeaderData(
                    profesor_nombre="María López",
                    periodo="C1 2025",
                    recinto="San José",
                ),
            )
        )
        assert a.fingerprint != b.fingerprint

    def test_different_periodo_different_fingerprint(self):
        a = compute_content_fingerprint(_make_parsed())
        b = compute_content_fingerprint(
            _make_parsed(
                periodo_data=PeriodoData(
                    periodo_raw="C2 2025",
                    periodo_normalizado="C2 2025",
                    modalidad="CUATRIMESTRAL",
                    año=2025,
                    periodo_orden=2,
                    prefijo="C",
                    numero=2,
                ),
            )
        )
        assert a.fingerprint != b.fingerprint

    def test_different_modalidad_different_fingerprint(self):
        a = compute_content_fingerprint(_make_parsed())
        b = compute_content_fingerprint(
            _make_parsed(
                periodo_data=PeriodoData(
                    periodo_raw="M1 2025",
                    periodo_normalizado="M1 2025",
                    modalidad="MENSUAL",
                    año=2025,
                    periodo_orden=1,
                    prefijo="M",
                    numero=1,
                ),
            )
        )
        assert a.fingerprint != b.fingerprint

    def test_different_puntaje_different_fingerprint(self):
        a = compute_content_fingerprint(_make_parsed())
        b = compute_content_fingerprint(
            _make_parsed(
                resumen_pct=ResumenPorcentajes(
                    estudiante=85.0,
                    director=95.0,
                    autoevaluacion=75.0,
                    promedio_general=86.0,  # changed
                ),
            )
        )
        assert a.fingerprint != b.fingerprint

    def test_different_cursos_different_fingerprint(self):
        a = compute_content_fingerprint(_make_parsed())
        b = compute_content_fingerprint(
            _make_parsed(
                cursos=[
                    CursoGrupo(
                        escuela="TI",
                        codigo="PROG301",
                        nombre="Programación III",
                        estudiantes_respondieron=10,
                        estudiantes_matriculados=15,
                        grupo="01",
                        pct_estudiante=80,
                        pct_director=85,
                        pct_autoevaluacion=70,
                        pct_promedio_general=78,
                    ),
                ],
            )
        )
        assert a.fingerprint != b.fingerprint

    def test_different_comment_count_different_fingerprint(self):
        a = compute_content_fingerprint(_make_parsed())
        b = compute_content_fingerprint(
            _make_parsed(
                secciones_comentarios=[
                    SeccionComentarios(
                        tipo_evaluacion="Estudiante",
                        asignatura="MAT201",
                        comentarios=[Comentario(fortaleza="Excelente")],
                    ),
                ],
            )
        )
        assert a.fingerprint != b.fingerprint

    def test_accent_insensitive_docente(self):
        """Pérez and Perez should produce the same fingerprint."""
        a = compute_content_fingerprint(
            _make_parsed(
                header=HeaderData(
                    profesor_nombre="Juan Pérez",
                    periodo="C1 2025",
                    recinto="San José",
                ),
            )
        )
        b = compute_content_fingerprint(
            _make_parsed(
                header=HeaderData(
                    profesor_nombre="Juan Perez",
                    periodo="C1 2025",
                    recinto="San José",
                ),
            )
        )
        assert a.fingerprint == b.fingerprint

    def test_whitespace_insensitive_docente(self):
        """Extra whitespace in docente name should not change fingerprint."""
        a = compute_content_fingerprint(
            _make_parsed(
                header=HeaderData(
                    profesor_nombre="Juan  Carlos  Pérez",
                    periodo="C1 2025",
                    recinto="San José",
                ),
            )
        )
        b = compute_content_fingerprint(
            _make_parsed(
                header=HeaderData(
                    profesor_nombre="Juan Carlos Pérez",
                    periodo="C1 2025",
                    recinto="San José",
                ),
            )
        )
        assert a.fingerprint == b.fingerprint

    def test_case_insensitive_docente(self):
        """UPPER vs lower docente name should produce same fingerprint."""
        a = compute_content_fingerprint(
            _make_parsed(
                header=HeaderData(
                    profesor_nombre="JUAN PÉREZ",
                    periodo="C1 2025",
                    recinto="San José",
                ),
            )
        )
        b = compute_content_fingerprint(
            _make_parsed(
                header=HeaderData(
                    profesor_nombre="juan pérez",
                    periodo="C1 2025",
                    recinto="San José",
                ),
            )
        )
        assert a.fingerprint == b.fingerprint

    def test_curso_order_insensitive(self):
        """Courses in different order should produce same fingerprint."""
        cursos_a = [
            CursoGrupo(
                escuela="TI",
                codigo="MAT201",
                nombre="Cálculo II",
                estudiantes_respondieron=15,
                estudiantes_matriculados=20,
                grupo="01",
                pct_estudiante=85,
                pct_director=90,
                pct_autoevaluacion=80,
                pct_promedio_general=85,
            ),
            CursoGrupo(
                escuela="TI",
                codigo="FIS101",
                nombre="Física I",
                estudiantes_respondieron=12,
                estudiantes_matriculados=18,
                grupo="02",
                pct_estudiante=80,
                pct_director=85,
                pct_autoevaluacion=75,
                pct_promedio_general=80,
            ),
        ]
        cursos_b = list(reversed(cursos_a))
        a = compute_content_fingerprint(_make_parsed(cursos=cursos_a))
        b = compute_content_fingerprint(_make_parsed(cursos=cursos_b))
        assert a.fingerprint == b.fingerprint

    def test_dimension_order_insensitive(self):
        """Dimensions in different order should produce same fingerprint."""
        parsed_a = _make_parsed()
        parsed_b = _make_parsed(dimensiones=list(reversed(parsed_a.dimensiones)))
        a = compute_content_fingerprint(parsed_a)
        b = compute_content_fingerprint(parsed_b)
        assert a.fingerprint == b.fingerprint

    def test_criterios_contains_all_fields(self):
        result = compute_content_fingerprint(_make_parsed())
        expected_keys = {
            "docente_nombre",
            "modalidad",
            "año",
            "periodo",
            "cursos",
            "promedio_general",
            "dimensiones",
            "total_comentarios",
        }
        assert set(result.criterios.keys()) == expected_keys

    def test_canonical_string_is_readable(self):
        result = compute_content_fingerprint(_make_parsed())
        assert "docente=" in result.canonical
        assert "modalidad=CUATRIMESTRAL" in result.canonical
        assert "año=2025" in result.canonical
        assert "periodo=C1 2025" in result.canonical

    def test_puntaje_rounding(self):
        """Tiny floating-point differences should not affect fingerprint."""
        a = compute_content_fingerprint(
            _make_parsed(
                resumen_pct=ResumenPorcentajes(
                    estudiante=85.0,
                    director=95.0,
                    autoevaluacion=75.0,
                    promedio_general=85.004,
                ),
            )
        )
        b = compute_content_fingerprint(
            _make_parsed(
                resumen_pct=ResumenPorcentajes(
                    estudiante=85.0,
                    director=95.0,
                    autoevaluacion=75.0,
                    promedio_general=85.001,
                ),
            )
        )
        assert a.fingerprint == b.fingerprint  # both round to 85.00

    def test_different_dimensiones_pct_different_fingerprint(self):
        """Same dimension names but different scores → different fingerprint."""
        dims_a = [
            DimensionMetrica(
                nombre="METODOLOGÍA",
                estudiante=FuentePuntaje(puntos_obtenidos=18, puntos_maximos=20, porcentaje=90.0),
                director=FuentePuntaje(puntos_obtenidos=10, puntos_maximos=10, porcentaje=100.0),
                autoevaluacion=FuentePuntaje(
                    puntos_obtenidos=16, puntos_maximos=20, porcentaje=80.0
                ),
                promedio_general_puntos=14.0,
                promedio_general_pct=90.0,
            ),
        ]
        dims_b = [
            DimensionMetrica(
                nombre="METODOLOGÍA",
                estudiante=FuentePuntaje(puntos_obtenidos=18, puntos_maximos=20, porcentaje=90.0),
                director=FuentePuntaje(puntos_obtenidos=10, puntos_maximos=10, porcentaje=100.0),
                autoevaluacion=FuentePuntaje(
                    puntos_obtenidos=16, puntos_maximos=20, porcentaje=80.0
                ),
                promedio_general_puntos=14.0,
                promedio_general_pct=85.0,  # different
            ),
        ]
        a = compute_content_fingerprint(_make_parsed(dimensiones=dims_a))
        b = compute_content_fingerprint(_make_parsed(dimensiones=dims_b))
        assert a.fingerprint != b.fingerprint


# ════════════════════════════════════════════════════════════════════════
# compare_fingerprints
# ════════════════════════════════════════════════════════════════════════


class TestCompareFingerprints:
    def test_identical_documents(self):
        a = compute_content_fingerprint(_make_parsed())
        b = compute_content_fingerprint(_make_parsed())
        result = compare_fingerprints(a, b)
        assert result.is_match is True
        assert result.score == 1.0
        assert len(result.matching_fields) == 8
        assert result.differing_fields == {}

    def test_completely_different(self):
        a = compute_content_fingerprint(_make_parsed())
        b = compute_content_fingerprint(
            _make_parsed(
                header=HeaderData(
                    profesor_nombre="Otra Persona",
                    periodo="C1 2025",
                    recinto="Otro",
                ),
                periodo_data=PeriodoData(
                    periodo_raw="M3 2024",
                    periodo_normalizado="M3 2024",
                    modalidad="MENSUAL",
                    año=2024,
                    periodo_orden=3,
                    prefijo="M",
                    numero=3,
                ),
                resumen_pct=ResumenPorcentajes(
                    estudiante=50.0,
                    director=60.0,
                    autoevaluacion=40.0,
                    promedio_general=50.0,
                ),
                cursos=[
                    CursoGrupo(
                        escuela="ADM",
                        codigo="ADM100",
                        nombre="Admin I",
                        estudiantes_respondieron=5,
                        estudiantes_matriculados=10,
                        grupo="A",
                        pct_estudiante=50,
                        pct_director=60,
                        pct_autoevaluacion=40,
                        pct_promedio_general=50,
                    ),
                ],
                dimensiones=[
                    DimensionMetrica(
                        nombre="Ética",
                        estudiante=FuentePuntaje(
                            puntos_obtenidos=8, puntos_maximos=20, porcentaje=40.0
                        ),
                        director=FuentePuntaje(
                            puntos_obtenidos=5, puntos_maximos=10, porcentaje=50.0
                        ),
                        autoevaluacion=FuentePuntaje(
                            puntos_obtenidos=6, puntos_maximos=20, porcentaje=30.0
                        ),
                        promedio_general_puntos=6.3,
                        promedio_general_pct=40.0,
                    ),
                ],
                secciones_comentarios=[
                    SeccionComentarios(
                        tipo_evaluacion="Estudiante",
                        asignatura="ADM100",
                        comentarios=[Comentario(fortaleza="X")],
                    ),
                ],
            )
        )
        result = compare_fingerprints(a, b)
        assert result.is_match is False
        assert result.score == 0.0
        assert len(result.differing_fields) == 8

    def test_partial_match(self):
        """Same docente and modalidad, different everything else."""
        a = compute_content_fingerprint(_make_parsed())
        b = compute_content_fingerprint(
            _make_parsed(
                periodo_data=PeriodoData(
                    periodo_raw="C2 2025",
                    periodo_normalizado="C2 2025",
                    modalidad="CUATRIMESTRAL",
                    año=2025,
                    periodo_orden=2,
                    prefijo="C",
                    numero=2,
                ),
            )
        )
        result = compare_fingerprints(a, b)
        assert result.is_match is False
        # docente, modalidad, año, cursos, promedio, dimensiones, comentarios match
        # Only periodo differs
        assert "periodo" in result.differing_fields
        assert "docente_nombre" in result.matching_fields
        assert result.score == pytest.approx(7 / 8, rel=1e-2)

    def test_returns_comparison_result(self):
        a = compute_content_fingerprint(_make_parsed())
        b = compute_content_fingerprint(_make_parsed())
        result = compare_fingerprints(a, b)
        assert isinstance(result, ComparisonResult)

    def test_differing_fields_contain_both_values(self):
        a = compute_content_fingerprint(_make_parsed())
        b = compute_content_fingerprint(
            _make_parsed(
                resumen_pct=ResumenPorcentajes(
                    estudiante=85.0,
                    director=95.0,
                    autoevaluacion=75.0,
                    promedio_general=99.0,
                ),
            )
        )
        result = compare_fingerprints(a, b)
        assert "promedio_general" in result.differing_fields
        val_a, val_b = result.differing_fields["promedio_general"]
        assert val_a == "85.00"
        assert val_b == "99.00"
