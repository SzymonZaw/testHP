"""Observational health-state classification for individual cells."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Mapping, Optional


@dataclass(frozen=True)
class CellHealthState:
    """Evidence-based cellular state; not a clinical diagnosis."""

    status: str
    score: Optional[float]
    confidence: float
    evidence: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "score": self.score,
            "confidence": self.confidence,
            "evidence": dict(self.evidence),
        }


def classify_cell_health(
    markers: Mapping[str, float],
    confidence: float = 0.0,
) -> CellHealthState:
    """Classify a cell into a coarse observational state.

    Marker values are expected to be normalized to [0, 1], where higher
    values indicate stronger evidence of cellular abnormality.
    """
    bounded_confidence = max(0.0, min(1.0, float(confidence)))
    values = [float(v) for v in markers.values()]
    if not values or bounded_confidence < 0.5:
        return CellHealthState("unknown", None, bounded_confidence, dict(markers))

    score = max(0.0, min(1.0, sum(values) / len(values)))
    if score >= 0.75:
        status = "abnormal"
    elif score >= 0.4:
        status = "atypical"
    else:
        status = "within_expected_range"
    return CellHealthState(status, score, bounded_confidence, dict(markers))
