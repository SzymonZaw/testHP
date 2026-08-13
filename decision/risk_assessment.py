"""Risk assessment from anomaly signals.

This layer ranks signals for follow-up; it does not diagnose disease or prescribe treatment.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

from anomaly.detector import Anomaly


@dataclass(frozen=True)
class RiskAssessment:
    score: float
    level: str
    signals: tuple[str, ...]
    rationale: tuple[str, ...]


class RiskAssessor:
    """Deterministic, explainable prioritization of abnormal signals."""

    def __init__(self, weights: Mapping[str, float] | None = None) -> None:
        self.weights = dict(weights or {"high": 2.0, "critical": 3.0})
        if any(weight <= 0 for weight in self.weights.values()):
            raise ValueError("Risk weights must be positive")

    def assess(self, anomalies: Iterable[Anomaly]) -> RiskAssessment:
        items = list(anomalies)
        score = sum(self.weights.get(item.severity, 1.0) for item in items)
        if score >= 6:
            level = "high"
        elif score >= 3:
            level = "moderate"
        elif score > 0:
            level = "low"
        else:
            level = "none"
        rationale = tuple(
            f"{item.feature}: {item.reason} ({item.severity})" for item in items
        )
        return RiskAssessment(
            score=score,
            level=level,
            signals=tuple(item.feature for item in items),
            rationale=rationale,
        )
