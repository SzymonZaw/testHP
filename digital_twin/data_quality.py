"""Data quality and uncertainty primitives for multiscale assessments."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Optional


@dataclass(frozen=True)
class DataQuality:
    """Quality metadata attached to an observation or derived assessment."""

    measurement_quality: float = 0.0
    completeness: float = 0.0
    temporal_freshness: float = 0.0
    provenance_quality: float = 0.0

    def score(self) -> float:
        values = (self.measurement_quality, self.completeness, self.temporal_freshness, self.provenance_quality)
        return sum(max(0.0, min(1.0, value)) for value in values) / len(values)

    def to_dict(self):
        return {**asdict(self), "score": self.score()}


@dataclass(frozen=True)
class Uncertainty:
    """Explicit uncertainty; higher value means less certainty."""

    confidence: float = 0.0
    data_quality: Optional[DataQuality] = None
    reason: Optional[str] = None

    @property
    def uncertainty(self) -> float:
        return 1.0 - max(0.0, min(1.0, self.confidence))

    def to_dict(self):
        return {
            "confidence": self.confidence,
            "uncertainty": self.uncertainty,
            "data_quality": self.data_quality.to_dict() if self.data_quality else None,
            "reason": self.reason,
        }


def combine_confidence(confidence: float, quality: Optional[DataQuality]) -> float:
    base = max(0.0, min(1.0, confidence))
    if quality is None:
        return base
    return base * quality.score()
