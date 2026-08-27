from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

from .longitudinal_observation import LongitudinalObservation


@dataclass(frozen=True)
class TemporalSeries:
    subject_id: str
    hand_id: str
    zone_id: str
    metric: str
    observations: tuple[LongitudinalObservation, ...]
    deltas: tuple[float, ...]
    trend: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "subject_id": self.subject_id,
            "hand_id": self.hand_id,
            "zone_id": self.zone_id,
            "metric": self.metric,
            "observations": [x.to_dict() for x in self.observations],
            "deltas": list(self.deltas),
            "trend": self.trend,
        }


def build_temporal_series(observations: Sequence[LongitudinalObservation]) -> TemporalSeries:
    if len(observations) < 2:
        raise ValueError("at least two observations are required")
    ordered = tuple(observations)
    for observation in ordered:
        observation.validate()
    first = ordered[0]
    if any((x.subject_id, x.hand_id, x.zone_id, x.metric) !=
           (first.subject_id, first.hand_id, first.zone_id, first.metric) for x in ordered):
        raise ValueError("observations must share subject, hand, zone and metric")
    deltas = tuple(round(b.value - a.value, 6) for a, b in zip(ordered, ordered[1:]))
    eps = 1e-9
    if all(abs(x) <= eps for x in deltas):
        trend = "stable"
    elif all(x > eps for x in deltas):
        trend = "increasing"
    elif all(x < -eps for x in deltas):
        trend = "decreasing"
    else:
        trend = "changing"
    return TemporalSeries(first.subject_id, first.hand_id, first.zone_id, first.metric, ordered, deltas, trend)
