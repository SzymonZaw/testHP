"""Apply anomaly detection to BiologicalState dimensions."""

from __future__ import annotations

from typing import Mapping

from core.biological_state import BiologicalState
from .detector import Anomaly, AnomalyDetector


def detect_state_anomalies(
    state: BiologicalState,
    reference: Mapping[str, tuple[float, float]],
    detector: AnomalyDetector | None = None,
    rates: Mapping[str, float] | None = None,
) -> list[Anomaly]:
    """Screen a BiologicalState while preserving its dimension names."""
    detector = detector or AnomalyDetector()
    return detector.detect(state.dimensions, reference, rates=rates)
