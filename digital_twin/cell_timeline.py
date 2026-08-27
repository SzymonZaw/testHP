"""Longitudinal cell observations for the digital twin.

Research-only infrastructure: trends describe observed/modelled change and do
not constitute a diagnosis or treatment recommendation.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional


@dataclass(frozen=True)
class CellObservation:
    cell_id: str
    observed_at: datetime
    biological_age: Optional[float] = None
    health_score: Optional[float] = None
    abnormality_score: Optional[float] = None
    uncertainty: Optional[float] = None
    evidence_count: int = 0
    confidence: float = 0.0
    health_state: str = "unknown"

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["observed_at"] = self.observed_at.isoformat()
        return data


@dataclass(frozen=True)
class CellTrend:
    cell_id: str
    direction: str
    age_delta: Optional[float]
    abnormality_delta: Optional[float]
    health_delta: Optional[float]
    confidence: float
    observations: int
    status: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _delta(first: Optional[float], last: Optional[float]) -> Optional[float]:
    if first is None or last is None:
        return None
    return last - first


def assess_cell_trend(observations: Iterable[CellObservation]) -> CellTrend:
    ordered = sorted(observations, key=lambda item: item.observed_at)
    if not ordered:
        raise ValueError("at least one cell observation is required")
    first, last = ordered[0], ordered[-1]
    age_delta = _delta(first.biological_age, last.biological_age)
    abnormality_delta = _delta(first.abnormality_score, last.abnormality_score)
    health_delta = _delta(first.health_score, last.health_score)
    confidence = sum(item.confidence for item in ordered) / len(ordered)

    if len(ordered) < 2:
        direction = "uncertain"
    elif abnormality_delta is not None and health_delta is not None:
        if abnormality_delta >= 0.15 and health_delta <= -0.10:
            direction = "worsening"
        elif abnormality_delta <= -0.15 and health_delta >= 0.10:
            direction = "improving"
        elif age_delta is not None and age_delta > 0.0:
            direction = "aging"
        else:
            direction = "stable"
    else:
        direction = "uncertain"

    status = "estimated" if confidence > 0 and len(ordered) >= 2 else "insufficient_evidence"
    return CellTrend(
        cell_id=last.cell_id,
        direction=direction,
        age_delta=age_delta,
        abnormality_delta=abnormality_delta,
        health_delta=health_delta,
        confidence=confidence,
        observations=len(ordered),
        status=status,
    )


class CellTimeline:
    def __init__(self) -> None:
        self._observations: Dict[str, List[CellObservation]] = {}

    def add(self, observation: CellObservation) -> None:
        self._observations.setdefault(observation.cell_id, []).append(observation)
        self._observations[observation.cell_id].sort(key=lambda item: item.observed_at)

    def get(self, cell_id: str) -> List[CellObservation]:
        return list(self._observations.get(cell_id, []))

    def trend(self, cell_id: str) -> CellTrend:
        return assess_cell_trend(self.get(cell_id))

    def snapshot(self, cell_id: str) -> Dict[str, Any]:
        observations = self.get(cell_id)
        return {
            "cell_id": cell_id,
            "observations": [item.to_dict() for item in observations],
            "trend": self.trend(cell_id).to_dict() if observations else None,
        }
