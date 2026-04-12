"""Domain enums — single source of truth for constrained string values.

These Python enums mirror CHECK constraints in the database and are used
by SQLAlchemy entities, Pydantic schemas, and application services.
"""

from enum import StrEnum

# ── Modalidad [BR-MOD-01] ───────────────────────────────────────────────


class Modalidad(StrEnum):
    """Academic programme modality.  Determines period structure."""

    CUATRIMESTRAL = "CUATRIMESTRAL"
    MENSUAL = "MENSUAL"
    B2B = "B2B"
    DESCONOCIDA = "DESCONOCIDA"


# ── Document states [§2.2 - documento FSM] ──────────────────────────────


class DocumentoEstado(StrEnum):
    SUBIDO = "subido"
    PROCESANDO = "procesando"
    PROCESADO = "procesado"
    ERROR = "error"


# ── Probable-duplicate finding states ────────────────────────────────────


class DuplicadoEstado(StrEnum):
    """Resolution state for a probable-duplicate finding."""

    PENDIENTE = "pendiente"  # Awaiting human review
    CONFIRMADO = "confirmado"  # User confirmed it is a real duplicate
    DESCARTADO = "descartado"  # User determined it is NOT a duplicate


# ── Evaluation states [§2.2 - evaluación FSM] ───────────────────────────


class EvaluacionEstado(StrEnum):
    PENDIENTE = "pendiente"
    PROCESANDO = "procesando"
    COMPLETADO = "completado"
    ERROR = "error"


# ── Processing-job states ────────────────────────────────────────────────


class JobEstado(StrEnum):
    PENDIENTE = "pendiente"
    PROCESANDO = "procesando"
    COMPLETADO = "completado"
    ERROR = "error"


# ── Alerts [AL-20 – AL-23] ──────────────────────────────────────────────


class TipoAlerta(StrEnum):
    """Alert type — each maps to a detection rule in the alert service."""

    BAJO_DESEMPENO = "BAJO_DESEMPEÑO"
    CAIDA = "CAIDA"
    SENTIMIENTO = "SENTIMIENTO"
    PATRON = "PATRON"


class Severidad(StrEnum):
    """Alert severity tier [AL-20]."""

    ALTA = "alta"
    MEDIA = "media"
    BAJA = "baja"


class AlertaEstado(StrEnum):
    """Alert lifecycle [AL-50]: activa → revisada → resuelta | descartada."""

    ACTIVA = "activa"
    REVISADA = "revisada"
    RESUELTA = "resuelta"
    DESCARTADA = "descartada"


# ── Comment classification [BR-CLAS-01, BR-CLAS-10] ─────────────────────


class TipoComentario(StrEnum):
    FORTALEZA = "fortaleza"
    MEJORA = "mejora"
    OBSERVACION = "observacion"


class Tema(StrEnum):
    METODOLOGIA = "metodologia"
    DOMINIO_TEMA = "dominio_tema"
    COMUNICACION = "comunicacion"
    EVALUACION = "evaluacion"
    PUNTUALIDAD = "puntualidad"
    MATERIAL = "material"
    ACTITUD = "actitud"
    TECNOLOGIA = "tecnologia"
    ORGANIZACION = "organizacion"
    OTRO = "otro"


class Sentimiento(StrEnum):
    POSITIVO = "positivo"
    NEGATIVO = "negativo"
    MIXTO = "mixto"
    NEUTRO = "neutro"


class TemaConfianza(StrEnum):
    REGLA = "regla"
    GEMINI = "gemini"
