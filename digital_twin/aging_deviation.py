"""Compare biological-age estimates against a hand-level baseline."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional


@dataclass(frozen=True)
class AgingDeviation:
    level: str
    identifier: str
    baseline_age: Optional[float]
    observed_age: Optional[float]
    deviation: Optional[float]
    normalized_deviation: Optional[float]
    confidence: float
    severity: str

    def to_dict(self) -> Dict[str, Any]:
        return self.__dict__.copy()


def classify_deviation(deviation: Optional[float], confidence: float) -> str:
    if deviation is None or confidence < 0.5:
        return "insufficient"
    magnitude = abs(deviation)
    if magnitude >= 10.0:
        return "significant"
    if magnitude >= 5.0:
        return "notable"
    return "normal"


def build_aging_deviation(
    level: str,
    identifier: str,
    baseline_age: Optional[float],
    observed_age: Optional[float],
    confidence: float,
) -> AgingDeviation:
    """Return an observational deviation, never a treatment recommendation."""
    bounded_confidence = max(0.0, min(1.0, float(confidence)))
    deviation = None
    normalized = None
    if baseline_age is not None and observed_age is not None:
        deviation = float(observed_age) - float(baseline_age)
        scale = max(abs(float(baseline_age)), 1.0)
        normalized = deviation / scale
    return AgingDeviation(
        level=level,
        identifier=identifier,
        baseline_age=baseline_age,
        observed_age=observed_age,
        deviation=deviation,
        normalized_deviation=normalized,
        confidence=bounded_confidence,
        severity=classify_deviation(deviation, bounded_confidence),
    )


def rank_aging_deviations(items: Iterable[AgingDeviation]) -> List[AgingDeviation]:
    """Rank strongest reliable deviations first."""
    return sorted(
        items,
        key=lambda item: abs(item.deviation or 0.0) * item.confidence,
        reverse=True,
    )
