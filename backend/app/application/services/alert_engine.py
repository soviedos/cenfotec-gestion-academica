"""Alert engine — orchestrates alert detection across modalidades.

Entry point: ``AlertEngine.run_all()`` iterates over each known modalidad,
loads the two most recent periods, runs all registered detectors, and
upserts the resulting alerts.

Usage::

    engine = AlertEngine(db)
    result = await engine.run_all()
    print(result)  # AlertRunResult(created=5, updated=2, skipped=0)

The engine can also be scoped to a single modalidad::

    result = await engine.run_for_modalidad("CUATRIMESTRAL")
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.alert_rules import (
    ALL_DETECTORS,
    AlertCandidate,
    AlertDetector,
    DocenteCursoSnapshot,
)
from app.domain.invariants import MODALIDADES_ANALISIS, require_modalidad
from app.infrastructure.repositories.alerta_repo import AlertaRepository

logger = logging.getLogger(__name__)

# Modalidades that can generate alerts (DESCONOCIDA is excluded) [BR-MOD-05]
_ALERTABLE_MODALIDADES: list[str] = sorted(MODALIDADES_ANALISIS)


@dataclass
class AlertRunResult:
    """Summary returned by ``AlertEngine.run_all()``."""

    created_or_updated: int = 0
    candidates_generated: int = 0
    modalidades_processed: int = 0
    periodos_by_modalidad: dict[str, list[str]] = field(default_factory=dict)


class AlertEngine:
    """Orchestrator for alert detection and persistence."""

    def __init__(
        self,
        db: AsyncSession,
        *,
        detectors: list[AlertDetector] | None = None,
    ) -> None:
        self._db = db
        self._repo = AlertaRepository(db)
        self._detectors: list[AlertDetector] = (
            list(detectors) if detectors is not None else list(ALL_DETECTORS)
        )

    # ── Public API ───────────────────────────────────────────────────

    def register_detector(self, detector: AlertDetector) -> None:
        """Add a custom detector at runtime."""
        self._detectors.append(detector)

    async def run_all(self) -> AlertRunResult:
        """Run detection across all alertable modalidades."""
        result = AlertRunResult()
        for modalidad in _ALERTABLE_MODALIDADES:
            partial = await self.run_for_modalidad(modalidad)
            result.created_or_updated += partial.created_or_updated
            result.candidates_generated += partial.candidates_generated
            result.modalidades_processed += partial.modalidades_processed
            result.periodos_by_modalidad.update(partial.periodos_by_modalidad)
        return result

    async def run_for_modalidad(self, modalidad: str) -> AlertRunResult:
        """Run detection for a single modalidad.

        Raises ``ModalidadInvalidaError`` if the modalidad is not
        analysis-eligible [BR-MOD-05].
        """
        modalidad = require_modalidad(modalidad)
        result = AlertRunResult()

        periodos = await self._repo.find_last_two_periods(modalidad)
        if not periodos:
            logger.info("No periodos found for modalidad=%s — skipping", modalidad)
            return result

        result.modalidades_processed = 1
        result.periodos_by_modalidad[modalidad] = periodos
        logger.info(
            "Processing modalidad=%s with periodos=%s",
            modalidad,
            periodos,
        )

        # Load snapshots
        snapshots = await self._repo.load_snapshots(modalidad, periodos)

        periodo_actual = periodos[0]
        periodo_anterior = periodos[1] if len(periodos) > 1 else None

        snap_actual = snapshots.get(periodo_actual, {})
        snap_anterior = snapshots.get(periodo_anterior, {}) if periodo_anterior else {}

        # Run detectors — scoped to this modalidad [BR-MOD-02]
        candidates = self._detect(snap_actual, snap_anterior, expected_modalidad=modalidad)
        result.candidates_generated = len(candidates)

        if candidates:
            rows = await self._repo.upsert_batch(candidates)
            result.created_or_updated = rows
            logger.info(
                "Modalidad=%s: %d candidates → %d upserted",
                modalidad,
                len(candidates),
                rows,
            )

        return result

    # ── Internal ─────────────────────────────────────────────────────

    def _detect(
        self,
        snap_actual: dict[tuple[str, str], DocenteCursoSnapshot],
        snap_anterior: dict[tuple[str, str], DocenteCursoSnapshot],
        *,
        expected_modalidad: str | None = None,
    ) -> list[AlertCandidate]:
        """Run all detectors for each docente+curso in the current period.

        Deduplicates candidates by their natural key
        ``(docente, curso, periodo, tipo_alerta, modalidad)`` [AL-10][AL-40].

        When *expected_modalidad* is set, any candidate carrying a
        different modalidad is silently filtered out [BR-MOD-02].
        """
        candidates: list[AlertCandidate] = []
        seen: set[tuple[str, str, str, str, str]] = set()

        for key, actual in snap_actual.items():
            anterior = snap_anterior.get(key)
            for detector in self._detectors:
                for candidate in detector.detect(actual, anterior):
                    # Cross-modalidad guard [BR-MOD-02]
                    if expected_modalidad is not None and candidate.modalidad != expected_modalidad:
                        logger.warning(
                            "cross_modalidad_candidate | expected=%s got=%s docente=%s — filtered",
                            expected_modalidad,
                            candidate.modalidad,
                            candidate.docente_nombre,
                        )
                        continue

                    dedup_key = (
                        candidate.docente_nombre,
                        candidate.curso,
                        candidate.periodo,
                        candidate.tipo_alerta.value,
                        candidate.modalidad,
                    )
                    if dedup_key not in seen:
                        seen.add(dedup_key)
                        candidates.append(candidate)

        return candidates
