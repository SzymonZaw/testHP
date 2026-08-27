"""Temporal history for evidence-derived cell inference."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from .cell_inference import CellInference


@dataclass(frozen=True)
class InferenceSnapshot:
    observed_at: datetime
    inference: CellInference

    def to_dict(self) -> Dict[str, Any]:
        return {"observed_at": self.observed_at.isoformat(), "inference": self.inference.to_dict()}


@dataclass(frozen=True)
class InferenceTrend:
    direction: str
    age_delta: Optional[float]
    confidence_delta: float
    previous_health: Optional[str]
    current_health: str
    abrupt_change: bool
    rationale: tuple[str, ...]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "direction": self.direction,
            "age_delta": self.age_delta,
            "confidence_delta": self.confidence_delta,
            "previous_health": self.previous_health,
            "current_health": self.current_health,
            "abrupt_change": self.abrupt_change,
            "rationale": list(self.rationale),
        }


class CellInferenceHistory:
    """Keep ordered inference snapshots and derive conservative temporal trends."""

    def __init__(self) -> None:
        self._items: Dict[str, List[InferenceSnapshot]] = {}

    def add(self, cell_id: str, observed_at: datetime, inference: CellInference) -> None:
        items = self._items.setdefault(cell_id, [])
        items.append(InferenceSnapshot(observed_at, inference))
        items.sort(key=lambda item: item.observed_at)

    def get(self, cell_id: str) -> List[InferenceSnapshot]:
        return list(self._items.get(cell_id, []))

    def trend(self, cell_id: str) -> Optional[InferenceTrend]:
        items = self.get(cell_id)
        if not items:
            return None
        current = items[-1].inference
        previous = items[-2].inference if len(items) > 1 else None
        if previous is None:
            return InferenceTrend("baseline", None, 0.0, None, current.health_state, False, ("Only one inference snapshot is available.",))

        age_delta = None
        if current.biological_age is not None and previous.biological_age is not None:
            age_delta = current.biological_age - previous.biological_age

        confidence_delta = current.confidence - previous.confidence
        if age_delta is None or abs(age_delta) < 0.5:
            direction = "stable"
        elif age_delta > 0:
            direction = "aging"
        else:
            direction = "younger_signal"

        health_change = current.health_state != previous.health_state
        abrupt = health_change or (age_delta is not None and abs(age_delta) >= 2.0)
        rationale = [f"Compared the latest two inference snapshots for {cell_id}."]
        if age_delta is not None:
            rationale.append(f"Biological-age estimate changed by {age_delta:+.2f}.")
        if health_change:
            rationale.append(f"Health state changed from {previous.health_state} to {current.health_state}.")
        if abrupt:
            rationale.append("Change exceeds the conservative abrupt-change threshold.")
        return InferenceTrend(direction, age_delta, confidence_delta, previous.health_state, current.health_state, abrupt, tuple(rationale))

    def to_dict(self) -> Dict[str, List[Dict[str, Any]]]:
        return {cell_id: [item.to_dict() for item in items] for cell_id, items in self._items.items()}
