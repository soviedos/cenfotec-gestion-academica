"""Unit tests for /api/v1/config/alert-thresholds endpoint."""

import pytest

from app.modules.evaluacion_docente.api.config_routes import get_alert_thresholds
from app.modules.evaluacion_docente.domain.alert_rules import (
    ALERT_THRESHOLD_HIGH,
    ALERT_THRESHOLD_LOW,
    ALERT_THRESHOLD_MEDIUM,
    DROP_THRESHOLD_HIGH,
    DROP_THRESHOLD_LOW,
    DROP_THRESHOLD_MEDIUM,
    PATTERN_ACTITUD_NEG,
    PATTERN_MEJORA_NEG,
    PATTERN_OTRO,
    SENT_THRESHOLD_HIGH,
    SENT_THRESHOLD_LOW,
    SENT_THRESHOLD_MEDIUM,
)


@pytest.mark.asyncio
class TestGetAlertThresholds:
    async def test_returns_all_categories(self):
        result = await get_alert_thresholds()
        assert set(result.keys()) == {"bajo_desempeno", "caida", "sentimiento", "patron"}

    async def test_bajo_desempeno_matches_constants(self):
        result = await get_alert_thresholds()
        assert result["bajo_desempeno"] == {
            "high": ALERT_THRESHOLD_HIGH,
            "medium": ALERT_THRESHOLD_MEDIUM,
            "low": ALERT_THRESHOLD_LOW,
        }

    async def test_caida_matches_constants(self):
        result = await get_alert_thresholds()
        assert result["caida"] == {
            "high": DROP_THRESHOLD_HIGH,
            "medium": DROP_THRESHOLD_MEDIUM,
            "low": DROP_THRESHOLD_LOW,
        }

    async def test_sentimiento_matches_constants(self):
        result = await get_alert_thresholds()
        assert result["sentimiento"] == {
            "high": SENT_THRESHOLD_HIGH,
            "medium": SENT_THRESHOLD_MEDIUM,
            "low": SENT_THRESHOLD_LOW,
        }

    async def test_patron_matches_constants(self):
        result = await get_alert_thresholds()
        assert result["patron"] == {
            "mejora_negativo": PATTERN_MEJORA_NEG,
            "actitud_negativo": PATTERN_ACTITUD_NEG,
            "otro": PATTERN_OTRO,
        }

    async def test_all_values_are_numeric(self):
        result = await get_alert_thresholds()
        for category in result.values():
            for value in category.values():
                assert isinstance(value, (int, float))
