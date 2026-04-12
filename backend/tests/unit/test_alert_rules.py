"""Unit tests for alert detectors — pure domain logic, no DB.

Tests every detector against boundary values for each severity tier,
edge cases (None puntaje, zero comments, no anterior), and threshold
boundaries.
"""

from __future__ import annotations

import uuid

from app.modules.evaluacion_docente.domain.alert_rules import (
    ALERT_THRESHOLD_HIGH,
    ALERT_THRESHOLD_LOW,
    ALERT_THRESHOLD_MEDIUM,
    BajoDesempenoDetector,
    CaidaDetector,
    DocenteCursoSnapshot,
    PatronDetector,
    SentimientoDetector,
)
from app.modules.evaluacion_docente.domain.entities.enums import Severidad, TipoAlerta

# ── Helpers ──────────────────────────────────────────────────────────────

_DEFAULT_UUID = uuid.UUID("00000000-0000-0000-0000-000000000001")
_ANTERIOR_UUID = uuid.UUID("00000000-0000-0000-0000-000000000002")


def _snap(
    *,
    puntaje: float | None = 85.0,
    total: int = 10,
    negativos: int = 1,
    mejora_neg: int = 0,
    actitud_neg: int = 0,
    otro: int = 0,
    periodo: str = "C1 2025",
    eval_id: uuid.UUID = _DEFAULT_UUID,
) -> DocenteCursoSnapshot:
    return DocenteCursoSnapshot(
        evaluacion_id=eval_id,
        docente_nombre="Prof. García",
        curso="ISW-101 Programación I",
        periodo=periodo,
        modalidad="CUATRIMESTRAL",
        puntaje_general=puntaje,
        total_comentarios=total,
        negativos_count=negativos,
        mejora_negativo_count=mejora_neg,
        actitud_negativo_count=actitud_neg,
        otro_count=otro,
    )


# ═══════════════════════════════════════════════════════════════════════
# BajoDesempeñoDetector [AL-20]
# ═══════════════════════════════════════════════════════════════════════


class TestBajoDesempenoDetector:
    detector = BajoDesempenoDetector()

    def test_above_threshold_no_alert(self):
        actual = _snap(puntaje=80.0)
        assert self.detector.detect(actual, None) == []

    def test_exactly_at_low_threshold_no_alert(self):
        actual = _snap(puntaje=ALERT_THRESHOLD_LOW)
        assert self.detector.detect(actual, None) == []

    def test_just_below_low_threshold_baja(self):
        actual = _snap(puntaje=ALERT_THRESHOLD_LOW - 0.01)
        alerts = self.detector.detect(actual, None)
        assert len(alerts) == 1
        assert alerts[0].severidad == Severidad.BAJA
        assert alerts[0].tipo_alerta == TipoAlerta.BAJO_DESEMPENO

    def test_below_medium_threshold_media(self):
        actual = _snap(puntaje=ALERT_THRESHOLD_MEDIUM - 0.01)
        alerts = self.detector.detect(actual, None)
        assert len(alerts) == 1
        assert alerts[0].severidad == Severidad.MEDIA

    def test_below_high_threshold_alta(self):
        actual = _snap(puntaje=ALERT_THRESHOLD_HIGH - 0.01)
        alerts = self.detector.detect(actual, None)
        assert len(alerts) == 1
        assert alerts[0].severidad == Severidad.ALTA

    def test_zero_puntaje_alta(self):
        actual = _snap(puntaje=0.0)
        alerts = self.detector.detect(actual, None)
        assert len(alerts) == 1
        assert alerts[0].severidad == Severidad.ALTA

    def test_none_puntaje_no_alert(self):
        actual = _snap(puntaje=None)
        assert self.detector.detect(actual, None) == []

    def test_includes_anterior_value_when_present(self):
        actual = _snap(puntaje=55.0)
        anterior = _snap(puntaje=90.0, periodo="C3 2024", eval_id=_ANTERIOR_UUID)
        alerts = self.detector.detect(actual, anterior)
        assert alerts[0].valor_anterior == 90.0

    def test_alert_fields_complete(self):
        actual = _snap(puntaje=50.0)
        alert = self.detector.detect(actual, None)[0]
        assert alert.docente_nombre == "Prof. García"
        assert alert.curso == "ISW-101 Programación I"
        assert alert.periodo == "C1 2025"
        assert alert.modalidad == "CUATRIMESTRAL"
        assert alert.metrica_afectada == "puntaje_general"
        assert alert.valor_actual == 50.0
        assert alert.valor_anterior is None
        assert "50.00" in alert.descripcion


# ═══════════════════════════════════════════════════════════════════════
# CaídaDetector [AL-21]
# ═══════════════════════════════════════════════════════════════════════


class TestCaidaDetector:
    detector = CaidaDetector()

    def test_no_anterior_no_alert(self):
        actual = _snap(puntaje=50.0)
        assert self.detector.detect(actual, None) == []

    def test_no_drop_no_alert(self):
        actual = _snap(puntaje=85.0)
        anterior = _snap(puntaje=85.0, periodo="C3 2024", eval_id=_ANTERIOR_UUID)
        assert self.detector.detect(actual, anterior) == []

    def test_improvement_no_alert(self):
        actual = _snap(puntaje=90.0)
        anterior = _snap(puntaje=80.0, periodo="C3 2024", eval_id=_ANTERIOR_UUID)
        assert self.detector.detect(actual, anterior) == []

    def test_drop_at_boundary_no_alert(self):
        """Exactly 5.0 drop — not > 5.0, so no alert."""
        actual = _snap(puntaje=80.0)
        anterior = _snap(puntaje=85.0, periodo="C3 2024", eval_id=_ANTERIOR_UUID)
        assert self.detector.detect(actual, anterior) == []

    def test_small_drop_baja(self):
        actual = _snap(puntaje=80.0)
        anterior = _snap(puntaje=85.01, periodo="C3 2024", eval_id=_ANTERIOR_UUID)
        alerts = self.detector.detect(actual, anterior)
        assert len(alerts) == 1
        assert alerts[0].severidad == Severidad.BAJA

    def test_medium_drop_media(self):
        actual = _snap(puntaje=70.0)
        anterior = _snap(puntaje=80.01, periodo="C3 2024", eval_id=_ANTERIOR_UUID)
        alerts = self.detector.detect(actual, anterior)
        assert len(alerts) == 1
        assert alerts[0].severidad == Severidad.MEDIA

    def test_large_drop_alta(self):
        actual = _snap(puntaje=60.0)
        anterior = _snap(puntaje=75.01, periodo="C3 2024", eval_id=_ANTERIOR_UUID)
        alerts = self.detector.detect(actual, anterior)
        assert len(alerts) == 1
        assert alerts[0].severidad == Severidad.ALTA

    def test_none_actual_no_alert(self):
        actual = _snap(puntaje=None)
        anterior = _snap(puntaje=90.0, periodo="C3 2024", eval_id=_ANTERIOR_UUID)
        assert self.detector.detect(actual, anterior) == []

    def test_none_anterior_puntaje_no_alert(self):
        actual = _snap(puntaje=50.0)
        anterior = _snap(puntaje=None, periodo="C3 2024", eval_id=_ANTERIOR_UUID)
        assert self.detector.detect(actual, anterior) == []

    def test_alert_references_anterior_periodo(self):
        actual = _snap(puntaje=60.0)
        anterior = _snap(puntaje=90.0, periodo="C3 2024", eval_id=_ANTERIOR_UUID)
        alert = self.detector.detect(actual, anterior)[0]
        assert "C3 2024" in alert.descripcion
        assert alert.valor_anterior == 90.0
        assert alert.valor_actual == 60.0


# ═══════════════════════════════════════════════════════════════════════
# SentimientoDetector [AL-22]
# ═══════════════════════════════════════════════════════════════════════


class TestSentimientoDetector:
    detector = SentimientoDetector()

    def test_no_anterior_no_alert(self):
        actual = _snap(total=10, negativos=8)
        assert self.detector.detect(actual, None) == []

    def test_no_increase_no_alert(self):
        actual = _snap(total=10, negativos=2)
        anterior = _snap(total=10, negativos=2, periodo="C3 2024", eval_id=_ANTERIOR_UUID)
        assert self.detector.detect(actual, anterior) == []

    def test_decrease_no_alert(self):
        actual = _snap(total=10, negativos=1)
        anterior = _snap(total=10, negativos=5, periodo="C3 2024", eval_id=_ANTERIOR_UUID)
        assert self.detector.detect(actual, anterior) == []

    def test_small_increase_baja(self):
        # anterior: 10% neg, actual: 10+5.01=15.01% → increment 5.01%
        actual = _snap(total=100, negativos=16)
        anterior = _snap(total=100, negativos=10, periodo="C3 2024", eval_id=_ANTERIOR_UUID)
        alerts = self.detector.detect(actual, anterior)
        assert len(alerts) == 1
        assert alerts[0].severidad == Severidad.BAJA

    def test_medium_increase_media(self):
        # anterior: 5%, actual: 16% → increment 11%
        actual = _snap(total=100, negativos=16)
        anterior = _snap(total=100, negativos=5, periodo="C3 2024", eval_id=_ANTERIOR_UUID)
        alerts = self.detector.detect(actual, anterior)
        assert len(alerts) == 1
        assert alerts[0].severidad == Severidad.MEDIA

    def test_large_increase_alta(self):
        # anterior: 5%, actual: 26% → increment 21%
        actual = _snap(total=100, negativos=26)
        anterior = _snap(total=100, negativos=5, periodo="C3 2024", eval_id=_ANTERIOR_UUID)
        alerts = self.detector.detect(actual, anterior)
        assert len(alerts) == 1
        assert alerts[0].severidad == Severidad.ALTA

    def test_zero_comments_actual_no_alert(self):
        actual = _snap(total=0, negativos=0)
        anterior = _snap(total=10, negativos=1, periodo="C3 2024", eval_id=_ANTERIOR_UUID)
        assert self.detector.detect(actual, anterior) == []

    def test_zero_comments_anterior_no_alert(self):
        actual = _snap(total=10, negativos=5)
        anterior = _snap(total=0, negativos=0, periodo="C3 2024", eval_id=_ANTERIOR_UUID)
        assert self.detector.detect(actual, anterior) == []

    def test_at_boundary_no_alert(self):
        # Exactly 5% increase — not > 5%, so no alert
        actual = _snap(total=100, negativos=15)
        anterior = _snap(total=100, negativos=10, periodo="C3 2024", eval_id=_ANTERIOR_UUID)
        assert self.detector.detect(actual, anterior) == []

    def test_metrica_afectada_is_pct_negativo(self):
        actual = _snap(total=100, negativos=30)
        anterior = _snap(total=100, negativos=5, periodo="C3 2024", eval_id=_ANTERIOR_UUID)
        alert = self.detector.detect(actual, anterior)[0]
        assert alert.metrica_afectada == "pct_negativo"
        assert alert.tipo_alerta == TipoAlerta.SENTIMIENTO


# ═══════════════════════════════════════════════════════════════════════
# PatrónDetector [AL-23]
# ═══════════════════════════════════════════════════════════════════════


class TestPatronDetector:
    detector = PatronDetector()

    def test_no_comments_no_alert(self):
        actual = _snap(total=0)
        assert self.detector.detect(actual, None) == []

    def test_below_all_thresholds_no_alert(self):
        actual = _snap(total=10, mejora_neg=4, actitud_neg=2, otro=3)
        assert self.detector.detect(actual, None) == []

    def test_mejora_negativo_alta(self):
        # 51% mejora+negativo → alta
        actual = _snap(total=100, mejora_neg=51, actitud_neg=0, otro=0)
        alerts = self.detector.detect(actual, None)
        assert len(alerts) == 1
        assert alerts[0].severidad == Severidad.ALTA
        assert alerts[0].metrica_afectada == "pct_mejora_negativo"

    def test_mejora_negativo_at_boundary_no_alert(self):
        # Exactly 50% — not > 50%, so no alert for mejora
        actual = _snap(total=100, mejora_neg=50, actitud_neg=0, otro=0)
        assert self.detector.detect(actual, None) == []

    def test_actitud_negativo_media(self):
        # 31% actitud+negativo, mejora below threshold
        actual = _snap(total=100, mejora_neg=10, actitud_neg=31, otro=0)
        alerts = self.detector.detect(actual, None)
        assert len(alerts) == 1
        assert alerts[0].severidad == Severidad.MEDIA
        assert alerts[0].metrica_afectada == "pct_actitud_negativo"

    def test_actitud_at_boundary_no_alert(self):
        actual = _snap(total=100, mejora_neg=0, actitud_neg=30, otro=0)
        assert self.detector.detect(actual, None) == []

    def test_otro_baja(self):
        # 41% otro
        actual = _snap(total=100, mejora_neg=0, actitud_neg=0, otro=41)
        alerts = self.detector.detect(actual, None)
        assert len(alerts) == 1
        assert alerts[0].severidad == Severidad.BAJA
        assert alerts[0].metrica_afectada == "pct_tema_otro"

    def test_otro_at_boundary_no_alert(self):
        actual = _snap(total=100, mejora_neg=0, actitud_neg=0, otro=40)
        assert self.detector.detect(actual, None) == []

    def test_highest_severity_wins(self):
        """When multiple patterns match, mejora_neg (alta) takes priority."""
        actual = _snap(total=100, mejora_neg=60, actitud_neg=35, otro=45)
        alerts = self.detector.detect(actual, None)
        assert len(alerts) == 1
        assert alerts[0].severidad == Severidad.ALTA

    def test_actitud_wins_over_otro(self):
        """When actitud and otro match, actitud (media) takes priority."""
        actual = _snap(total=100, mejora_neg=10, actitud_neg=35, otro=45)
        alerts = self.detector.detect(actual, None)
        assert len(alerts) == 1
        assert alerts[0].severidad == Severidad.MEDIA

    def test_patron_does_not_need_anterior(self):
        actual = _snap(total=100, mejora_neg=60)
        alerts = self.detector.detect(actual, None)
        assert len(alerts) == 1

    def test_valor_anterior_always_none(self):
        actual = _snap(total=100, otro=50)
        anterior = _snap(periodo="C3 2024", eval_id=_ANTERIOR_UUID)
        alerts = self.detector.detect(actual, anterior)
        assert alerts[0].valor_anterior is None


# ═══════════════════════════════════════════════════════════════════════
# Cross-cutting: AlertDetector protocol conformance
# ═══════════════════════════════════════════════════════════════════════


class TestProtocolConformance:
    def test_all_detectors_have_tipo(self):
        detectors = [
            BajoDesempenoDetector(),
            CaidaDetector(),
            SentimientoDetector(),
            PatronDetector(),
        ]
        tipos = {d.tipo for d in detectors}
        assert tipos == {
            TipoAlerta.BAJO_DESEMPENO,
            TipoAlerta.CAIDA,
            TipoAlerta.SENTIMIENTO,
            TipoAlerta.PATRON,
        }

    def test_detectors_satisfy_protocol(self):
        from app.modules.evaluacion_docente.domain.alert_rules import AlertDetector

        for cls in (BajoDesempenoDetector, CaidaDetector, SentimientoDetector, PatronDetector):
            assert isinstance(cls(), AlertDetector)
