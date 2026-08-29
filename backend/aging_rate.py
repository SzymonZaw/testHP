"""Longitudinal biological-age rate estimation.

This module reports change in estimated biological age over elapsed time. It is
an analytical signal only and must not be interpreted as a diagnosis or a
recommendation for treatment.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable


@dataclass(frozen=True)
class AgingRateEstimate:
    level: str
    node_id: str
    aging_rate: float | None
    age_delta: float | None
    elapsed_years: float | None
    trend: str
    confidence: float | None
    uncertainty: float | None
    evidence_ids: tuple[str, ...] = ()
    provenance: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "level": self.level,
            "node_id": self.node_id,
            "aging_rate": self.aging_rate,
            "age_delta": self.age_delta,
            "elapsed_years": self.elapsed_years,
            "trend": self.trend,
            "confidence": self.confidence,
            "uncertainty": self.uncertainty,
            "evidence_ids": self.evidence_ids,
            "provenance": self.provenance,
        }


def estimate_aging_rate(
    observations: Iterable[tuple[datetime, float]],
    *,
    level: str,
    node_id: str,
    baseline_rate: float = 1.0,
    confidence: float | None = None,
    uncertainty: float | None = None,
    evidence_ids: Iterable[str] = (),
    provenance: Iterable[str] = (),
) -> AgingRateEstimate:
    """Estimate biological-age change per unit chronological time.

    ``aging_rate`` is normalized to ``baseline_rate``. A value near 1 means the
    observed biological-age change matches the supplied baseline. At least two
    observations are required; duplicate or reversed timestamps are rejected.
    """
    points = tuple(sorted(observations, key=lambda item: item[0]))
    if baseline_rate <= 0:
        raise ValueError("baseline_rate must be positive")
    if confidence is not None and not 0.0 <= confidence <= 1.0:
        raise ValueError("confidence must be between 0 and 1")
    if uncertainty is not None and uncertainty < 0:
        raise ValueError("uncertainty cannot be negative")
    if len(points) < 2:
        return AgingRateEstimate(level, node_id, None, None, None, "insufficient_data", confidence, uncertainty,
                                 tuple(sorted(set(evidence_ids))), tuple(sorted(set(provenance))))
    if any(points[i][0] == points[i - 1][0] for i in range(1, len(points))):
        raise ValueError("observations must have unique timestamps")

    start_time, start_age = points[0]
    end_time, end_age = points[-1]
    elapsed_years = (end_time - start_time).total_seconds() / (365.2425 * 24 * 3600)
    if elapsed_years <= 0:
        raise ValueError("observations must span positive elapsed time")
    age_delta = float(end_age) - float(start_age)
    raw_rate = age_delta / elapsed_years
    normalized_rate = raw_rate / baseline_rate
    if age_delta > 0:
        trend = "accelerating" if normalized_rate > 1.0 else "aging"
    elif age_delta < 0:
        trend = "improving"
    else:
        trend = "stable"

    return AgingRateEstimate(level, node_id, normalized_rate, age_delta, elapsed_years, trend,
                             confidence, uncertainty,
                             tuple(sorted(set(evidence_ids))), tuple(sorted(set(provenance))))
