"""Configuration endpoint — exposes runtime thresholds and constants.

This allows the frontend to fetch alert thresholds from the backend
(single source of truth) instead of maintaining hardcoded duplicates.
"""

from fastapi import APIRouter

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

router = APIRouter()


@router.get("/alert-thresholds")
async def get_alert_thresholds() -> dict:
    """Return the current alert detection thresholds.

    Used by the frontend to stay in sync with backend business rules
    without hardcoding values.
    """
    return {
        "bajo_desempeno": {
            "high": ALERT_THRESHOLD_HIGH,
            "medium": ALERT_THRESHOLD_MEDIUM,
            "low": ALERT_THRESHOLD_LOW,
        },
        "caida": {
            "high": DROP_THRESHOLD_HIGH,
            "medium": DROP_THRESHOLD_MEDIUM,
            "low": DROP_THRESHOLD_LOW,
        },
        "sentimiento": {
            "high": SENT_THRESHOLD_HIGH,
            "medium": SENT_THRESHOLD_MEDIUM,
            "low": SENT_THRESHOLD_LOW,
        },
        "patron": {
            "mejora_negativo": PATTERN_MEJORA_NEG,
            "actitud_negativo": PATTERN_ACTITUD_NEG,
            "otro": PATTERN_OTRO,
        },
    }
