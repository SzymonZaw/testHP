"""Longitudinal trajectory analysis for hand-state observations."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .longitudinal_hand_twin import HandObservation, LongitudinalHandTwin


@dataclass(frozen=True)
class TrajectoryPoint:
    observed_at: str
    biological_age: float | None
    cell_count: int
    confidence: float


@dataclass(frozen=True)
class HandTrajectory:
    """Derived changes between chronological hand observations."""

    points: tuple[TrajectoryPoint, ...]

    @classmethod
    def from_twin(cls, twin: LongitudinalHandTwin) -> "HandTrajectory":
        points = tuple(
            TrajectoryPoint(
                observed_at=item.observed_at,
                biological_age=item.state.biological_age,
                cell_count=item.state.cell_count,
                confidence=item.state.confidence,
            )
            for item in twin.observations
        )
        return cls(points)

    @property
    def age_delta(self) -> float | None:
        """Change in the model's biological-age estimate across available endpoints."""
        ages = [point.biological_age for point in self.points if point.biological_age is not None]
        return ages[-1] - ages[0] if len(ages) >= 2 else None

    def ageing_rate(self) -> float | None:
        """Return estimated change in biological-age estimate per calendar year."""
        if len(self.points) < 2:
            return None
        first = self.points[0]
        last = self.points[-1]
        if first.biological_age is None or last.biological_age is None:
            return None
        start = datetime.fromisoformat(first.observed_at.replace("Z", "+00:00"))
        end = datetime.fromisoformat(last.observed_at.replace("Z", "+00:00"))
        years = (end - start).total_seconds() / (365.2425 * 24 * 3600)
        return (last.biological_age - first.biological_age) / years if years > 0 else None

    @property
    def cell_count_delta(self) -> int | None:
        if len(self.points) < 2:
            return None
        return self.points[-1].cell_count - self.points[0].cell_count

    @property
    def confidence_delta(self) -> float | None:
        if len(self.points) < 2:
            return None
        return self.points[-1].confidence - self.points[0].confidence

    def to_dict(self) -> dict[str, Any]:
        return {
            "points": [
                {
                    "observed_at": point.observed_at,
                    "biological_age": point.biological_age,
                    "cell_count": point.cell_count,
                    "confidence": point.confidence,
                }
                for point in self.points
            ],
            "age_delta": self.age_delta,
            "ageing_rate": self.ageing_rate(),
            "cell_count_delta": self.cell_count_delta,
            "confidence_delta": self.confidence_delta,
        }
