"""Longitudinal trajectory analysis for hand digital-twin observations."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional

from .hand_observation import HandObservation


@dataclass(frozen=True)
class TrajectoryPoint:
    observation_id: str
    observed_at: str
    biological_age: Optional[float]
    confidence: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "observation_id": self.observation_id,
            "observed_at": self.observed_at,
            "biological_age": self.biological_age,
            "confidence": self.confidence,
        }


@dataclass(frozen=True)
class HandTrajectory:
    """Summary of how the hand-level biological age changes over time."""

    hand_id: str
    points: List[TrajectoryPoint]
    direction: str
    change: Optional[float]
    age_slope_per_day: Optional[float]
    confidence: float
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "hand_id": self.hand_id,
            "points": [point.to_dict() for point in self.points],
            "direction": self.direction,
            "change": self.change,
            "age_slope_per_day": self.age_slope_per_day,
            "confidence": self.confidence,
            "metadata": dict(self.metadata),
        }


def analyze_hand_trajectory(
    observations: Iterable[HandObservation],
    *,
    tolerance: float = 0.5,
) -> HandTrajectory:
    """Compare chronological hand observations without making intervention claims."""
    ordered = sorted(observations, key=lambda item: item.observed_at)
    points = [
        TrajectoryPoint(
            observation_id=item.observation_id,
            observed_at=item.observed_at,
            biological_age=item.hand_state.biological_age if item.hand_state else None,
            confidence=item.confidence,
        )
        for item in ordered
    ]
    known = [point for point in points if point.biological_age is not None]
    if len(known) < 2:
        return HandTrajectory(
            hand_id=ordered[0].hand_id if ordered else "",
            points=points,
            direction="insufficient",
            change=None,
            age_slope_per_day=None,
            confidence=sum(p.confidence for p in points) / len(points) if points else 0.0,
        )

    first, last = known[0], known[-1]
    change = float(last.biological_age - first.biological_age)
    if abs(change) <= tolerance:
        direction = "stable"
    elif change > 0:
        direction = "increasing"
    else:
        direction = "decreasing"

    from datetime import datetime
    start = datetime.fromisoformat(first.observed_at)
    end = datetime.fromisoformat(last.observed_at)
    days = (end - start).total_seconds() / 86400.0
    slope = change / days if days > 0 else None
    confidence = sum(p.confidence for p in known) / len(known)
    return HandTrajectory(
        hand_id=first.observation_id and ordered[0].hand_id or "",
        points=points,
        direction=direction,
        change=change,
        age_slope_per_day=slope,
        confidence=confidence,
    )
