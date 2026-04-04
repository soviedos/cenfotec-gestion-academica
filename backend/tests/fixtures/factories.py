"""Entity factories for tests.

Usage:
    doc = make_documento(nombre_archivo="mi_archivo.pdf")
    eval_ = make_evaluacion(documento_id=doc.id, docente_nombre="Prof. López")

All fields have sensible defaults so you only override what matters for each test.
"""

import hashlib
import uuid

from app.domain.entities.comentario_analisis import ComentarioAnalisis
from app.domain.entities.documento import Documento
from app.domain.entities.evaluacion import Evaluacion
from app.domain.entities.evaluacion_curso import EvaluacionCurso
from app.domain.entities.evaluacion_dimension import EvaluacionDimension


def make_documento(**overrides) -> Documento:
    """Build a Documento with defaults. Pass keyword args to override any field."""
    uid = overrides.pop("id", uuid.uuid4())
    defaults = {
        "id": uid,
        "nombre_archivo": f"test_{uid.hex[:8]}.pdf",
        "hash_sha256": overrides.pop("hash_sha256", hashlib.sha256(uid.bytes).hexdigest()),
        "storage_path": f"evaluaciones/{uid.hex[:8]}.pdf",
        "estado": "subido",
        "tamano_bytes": 1024,
    }
    defaults.update(overrides)
    return Documento(**defaults)


def make_evaluacion(**overrides) -> Evaluacion:
    """Build an Evaluacion with defaults. Requires ``documento_id``."""
    uid = overrides.pop("id", uuid.uuid4())
    defaults = {
        "id": uid,
        "docente_nombre": "Prof. García",
        "periodo": "2025-2",
        "materia": "Ingeniería de Software",
        "puntaje_general": 4.5,
        "estado": "pendiente",
    }
    defaults.update(overrides)
    return Evaluacion(**defaults)


def make_dimension(**overrides) -> EvaluacionDimension:
    """Build an EvaluacionDimension with defaults."""
    defaults = {
        "nombre": "Metodología",
        "pct_estudiante": 85.0,
        "pct_director": 90.0,
        "pct_autoeval": 88.0,
        "pct_promedio": 87.67,
    }
    defaults.update(overrides)
    return EvaluacionDimension(**defaults)


def make_curso(**overrides) -> EvaluacionCurso:
    """Build an EvaluacionCurso with defaults."""
    defaults = {
        "escuela": "Ingeniería",
        "codigo": "ISW-101",
        "nombre": "Programación I",
        "grupo": "01",
        "respondieron": 20,
        "matriculados": 25,
        "pct_estudiante": 80.0,
        "pct_director": 85.0,
        "pct_autoeval": 82.0,
        "pct_promedio": 82.33,
    }
    defaults.update(overrides)
    return EvaluacionCurso(**defaults)


def make_comentario(**overrides) -> ComentarioAnalisis:
    """Build a ComentarioAnalisis with defaults."""
    defaults = {
        "fuente": "Estudiante",
        "asignatura": "Programación I",
        "tipo": "fortaleza",
        "texto": "Excelente profesor, explica muy bien",
        "tema": "comunicacion",
        "tema_confianza": "regla",
        "sentimiento": "positivo",
        "sent_score": 0.75,
        "procesado_ia": False,
    }
    defaults.update(overrides)
    return ComentarioAnalisis(**defaults)
