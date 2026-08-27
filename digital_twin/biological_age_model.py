"""Conservative biological-age estimation from observable cellular markers."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, Optional


@dataclass(frozen=True)
class BiologicalAgeEstimate:
    """A biological-age estimate with explicit uncertainty and provenance."""

    chronological_age: Optional[float]
    biological_age: Optional[float]
    age_acceleration: Optional[float]
    aging_rate: Optional[float]
    confidence: float
    uncertainty: float
    marker_count: int
    method: str = "conservative_marker_average"

    def to_dict(self) -> Dict[str, Any]:
        return self.__dict__.copy()


def estimate_biological_age(
    chronological_age: Optional[float],
    markers: Iterable[float],
    *,
    confidence: float = 0.0,
    aging_rate: Optional[float] = None,
) -> BiologicalAgeEstimate:
    """Estimate biological age from supplied marker-derived age estimates.

    This is an aggregation primitive, not a clinically validated age clock.
    Empty or invalid inputs remain explicitly unknown rather than fabricated.
    """
    values = [float(value) for value in markers if value is not None]
    bounded_confidence = max(0.0, min(1.0, float(confidence)))
    biological_age = sum(values) / len(values) if values else None
    acceleration = None
    if biological_age is not None and chronological_age is not None:
        acceleration = biological_age - float(chronological_age)

    return BiologicalAgeEstimate(
        chronological_age=float(chronological_age) if chronological_age is not None else None,
        biological_age=biological_age,
        age_acceleration=acceleration,
        aging_rate=aging_rate,
        confidence=bounded_confidence,
        uncertainty=1.0 - bounded_confidence,
        marker_count=len(values),
    )
