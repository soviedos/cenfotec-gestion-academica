"""Alert detection rules — pure domain logic, no I/O.

Implements business rules [AL-20] through [AL-23].

Architecture
~~~~~~~~~~~~
*  ``AlertDetector`` — Protocol that every detector must satisfy.
*  Four concrete detectors (one per ``TipoAlerta``).
*  ``AlertCandidate`` — immutable value object returned by detectors.
*  ``DocenteCursoSnapshot`` — read-only aggregate input per
   docente+curso+periodo.
*  Threshold constants centralised here for easy tuning.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from app.modules.evaluacion_docente.domain.entities.enums import Severidad, TipoAlerta

# ── Threshold constants ──────────────────────────────────────────────────

# [AL-20] Bajo desempeño absoluto
ALERT_THRESHOLD_HIGH: float = 60.0
ALERT_THRESHOLD_MEDIUM: float = 70.0
ALERT_THRESHOLD_LOW: float = 80.0

# [AL-21] Caída significativa entre periodos
DROP_THRESHOLD_HIGH: float = 15.0
DROP_THRESHOLD_MEDIUM: float = 10.0
DROP_THRESHOLD_LOW: float = 5.0

# [AL-22] Cambio negativo en sentimiento
SENT_THRESHOLD_HIGH: float = 20.0
SENT_THRESHOLD_MEDIUM: float = 10.0
SENT_THRESHOLD_LOW: float = 5.0

# [AL-23] Patrones críticos en comentarios
PATTERN_MEJORA_NEG: float = 0.50  # 50 % mejora + negativo → alta
PATTERN_ACTITUD_NEG: float = 0.30  # 30 % actitud + negativo → media
PATTERN_OTRO: float = 0.40  # 40 % tema = otro → baja


# ── Value objects ────────────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class DocenteCursoSnapshot:
    """Pre-aggregated data for one docente+curso in a single periodo."""

    evaluacion_id: uuid.UUID
    docente_nombre: str
    curso: str
    periodo: str
    modalidad: str
    puntaje_general: float | None
    # Comment aggregations
    total_comentarios: int
    negativos_count: int
    mejora_negativo_count: int  # tipo=mejora AND sentimiento=negativo
    actitud_negativo_count: int  # tema=actitud AND sentimiento=negativo
    otro_count: int  # tema=otro


@dataclass(frozen=True, slots=True)
class AlertCandidate:
    """Immutable proposal for an alert — maps 1:1 to ``Alerta`` columns."""

    evaluacion_id: uuid.UUID
    docente_nombre: str
    curso: str
    periodo: str
    modalidad: str
    tipo_alerta: TipoAlerta
    metrica_afectada: str
    valor_actual: float
    valor_anterior: float | None
    descripcion: str
    severidad: Severidad


# ── Detector protocol ────────────────────────────────────────────────────


@runtime_checkable
class AlertDetector(Protocol):
    """Interface every alert detector must satisfy."""

    tipo: TipoAlerta

    def detect(
        self,
        actual: DocenteCursoSnapshot,
        anterior: DocenteCursoSnapshot | None,
    ) -> list[AlertCandidate]: ...


# ── Concrete detectors ───────────────────────────────────────────────────


class BajoDesempenoDetector:
    """[AL-20] Absolute low-performance thresholds."""

    tipo = TipoAlerta.BAJO_DESEMPENO

    def detect(
        self,
        actual: DocenteCursoSnapshot,
        anterior: DocenteCursoSnapshot | None,
    ) -> list[AlertCandidate]:
        p = actual.puntaje_general
        if p is None:
            return []

        if p < ALERT_THRESHOLD_HIGH:
            sev = Severidad.ALTA
        elif p < ALERT_THRESHOLD_MEDIUM:
            sev = Severidad.MEDIA
        elif p < ALERT_THRESHOLD_LOW:
            sev = Severidad.BAJA
        else:
            return []

        return [
            AlertCandidate(
                evaluacion_id=actual.evaluacion_id,
                docente_nombre=actual.docente_nombre,
                curso=actual.curso,
                periodo=actual.periodo,
                modalidad=actual.modalidad,
                tipo_alerta=self.tipo,
                metrica_afectada="puntaje_general",
                valor_actual=p,
                valor_anterior=anterior.puntaje_general if anterior else None,
                descripcion=(
                    f"Puntaje general de {p:.2f} en {actual.curso} "
                    f"({actual.periodo}) — por debajo del umbral de {sev.value}"
                ),
                severidad=sev,
            )
        ]


class CaidaDetector:
    """[AL-21] Significant drop between consecutive periods."""

    tipo = TipoAlerta.CAIDA

    def detect(
        self,
        actual: DocenteCursoSnapshot,
        anterior: DocenteCursoSnapshot | None,
    ) -> list[AlertCandidate]:
        if anterior is None:
            return []
        if actual.puntaje_general is None or anterior.puntaje_general is None:
            return []

        caida = anterior.puntaje_general - actual.puntaje_general
        if caida <= 0:
            return []

        if caida > DROP_THRESHOLD_HIGH:
            sev = Severidad.ALTA
        elif caida > DROP_THRESHOLD_MEDIUM:
            sev = Severidad.MEDIA
        elif caida > DROP_THRESHOLD_LOW:
            sev = Severidad.BAJA
        else:
            return []

        return [
            AlertCandidate(
                evaluacion_id=actual.evaluacion_id,
                docente_nombre=actual.docente_nombre,
                curso=actual.curso,
                periodo=actual.periodo,
                modalidad=actual.modalidad,
                tipo_alerta=self.tipo,
                metrica_afectada="puntaje_general",
                valor_actual=actual.puntaje_general,
                valor_anterior=anterior.puntaje_general,
                descripcion=(
                    f"Caída de {caida:.2f} puntos en puntaje general respecto a {anterior.periodo}"
                ),
                severidad=sev,
            )
        ]


class SentimientoDetector:
    """[AL-22] Increase in negative-sentiment comment percentage."""

    tipo = TipoAlerta.SENTIMIENTO

    def detect(
        self,
        actual: DocenteCursoSnapshot,
        anterior: DocenteCursoSnapshot | None,
    ) -> list[AlertCandidate]:
        if anterior is None:
            return []
        if actual.total_comentarios == 0 or anterior.total_comentarios == 0:
            return []

        pct_actual = (actual.negativos_count / actual.total_comentarios) * 100
        pct_anterior = (anterior.negativos_count / anterior.total_comentarios) * 100
        incremento = pct_actual - pct_anterior

        if incremento <= 0:
            return []

        if incremento > SENT_THRESHOLD_HIGH:
            sev = Severidad.ALTA
        elif incremento > SENT_THRESHOLD_MEDIUM:
            sev = Severidad.MEDIA
        elif incremento > SENT_THRESHOLD_LOW:
            sev = Severidad.BAJA
        else:
            return []

        return [
            AlertCandidate(
                evaluacion_id=actual.evaluacion_id,
                docente_nombre=actual.docente_nombre,
                curso=actual.curso,
                periodo=actual.periodo,
                modalidad=actual.modalidad,
                tipo_alerta=self.tipo,
                metrica_afectada="pct_negativo",
                valor_actual=round(pct_actual, 2),
                valor_anterior=round(pct_anterior, 2),
                descripcion=(
                    f"Incremento de {incremento:.1f}% en comentarios negativos "
                    f"respecto a {anterior.periodo}"
                ),
                severidad=sev,
            )
        ]


class PatronDetector:
    """[AL-23] Critical qualitative patterns in comments."""

    tipo = TipoAlerta.PATRON

    def detect(
        self,
        actual: DocenteCursoSnapshot,
        anterior: DocenteCursoSnapshot | None,
    ) -> list[AlertCandidate]:
        if actual.total_comentarios == 0:
            return []

        total = actual.total_comentarios

        # Check from highest severity first — return on first match
        ratio_mejora_neg = actual.mejora_negativo_count / total
        if ratio_mejora_neg > PATTERN_MEJORA_NEG:
            return [
                self._build(
                    actual,
                    metrica="pct_mejora_negativo",
                    valor=round(ratio_mejora_neg * 100, 2),
                    desc=(
                        f"{ratio_mejora_neg:.0%} de comentarios son de tipo mejora "
                        f"con sentimiento negativo"
                    ),
                    sev=Severidad.ALTA,
                )
            ]

        ratio_actitud_neg = actual.actitud_negativo_count / total
        if ratio_actitud_neg > PATTERN_ACTITUD_NEG:
            return [
                self._build(
                    actual,
                    metrica="pct_actitud_negativo",
                    valor=round(ratio_actitud_neg * 100, 2),
                    desc=(
                        f"{ratio_actitud_neg:.0%} de comentarios con tema actitud "
                        f"y sentimiento negativo"
                    ),
                    sev=Severidad.MEDIA,
                )
            ]

        ratio_otro = actual.otro_count / total
        if ratio_otro > PATTERN_OTRO:
            return [
                self._build(
                    actual,
                    metrica="pct_tema_otro",
                    valor=round(ratio_otro * 100, 2),
                    desc=f"{ratio_otro:.0%} de comentarios clasificados como tema 'otro'",
                    sev=Severidad.BAJA,
                )
            ]

        return []

    @staticmethod
    def _build(
        snap: DocenteCursoSnapshot,
        *,
        metrica: str,
        valor: float,
        desc: str,
        sev: Severidad,
    ) -> AlertCandidate:
        return AlertCandidate(
            evaluacion_id=snap.evaluacion_id,
            docente_nombre=snap.docente_nombre,
            curso=snap.curso,
            periodo=snap.periodo,
            modalidad=snap.modalidad,
            tipo_alerta=TipoAlerta.PATRON,
            metrica_afectada=metrica,
            valor_actual=valor,
            valor_anterior=None,
            descripcion=desc,
            severidad=sev,
        )


# ── Default detector registry ───────────────────────────────────────────

ALL_DETECTORS: list[AlertDetector] = [
    BajoDesempenoDetector(),
    CaidaDetector(),
    SentimientoDetector(),
    PatronDetector(),
]
