"""Longitudinal biological-age trajectory for a hand."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .longitudinal_hand_twin import LongitudinalHandTwin


@dataclass(frozen=True)
class HandTrajectoryPoint:
    observed_at: str
    biological_age: float
    confidence: float


@dataclass(frozen=True)
class HandTrajectory:
    """Observed hand-level biological-age changes over time."""

    points: tuple[HandTrajectoryPoint, ...]

    @classmethod
    def from_twin(cls, twin: LongitudinalHandTwin) -> "HandTrajectory":
        return cls(
            tuple(
                HandTrajectoryPoint(
                    observed_at=observation.observed_at,
                    biological_age=observation.state.biological_age,
                    confidence=observation.state.confidence,
                )
                for observation in twin.observations
                if observation.state.biological_age is not None
            )
        )

    @property
    def age_delta(self) -> float | None:
        if len(self.points) < 2:
            return None
        return self.points[-1].biological_age - self.points[0].biological_age

    def ageing_rate(self) -> float | None:
        if len(self.points) < 2:
            return None
        first, last = self.points[0], self.points[-1]
        start = datetime.fromisoformat(first.observed_at.replace("Z", "+00:00"))
        end = datetime.fromisoformat(last.observed_at.replace("Z", "+00:00"))
        years = (end - start).total_seconds() / (365.2425 * 24 * 3600)
        return self.age_delta / years if years > 0 and self.age_delta is not None else None

    def to_dict(self) -> dict[str, object]:
        return {
            "points": [point.__dict__ for point in self.points],
            "age_delta": self.age_delta,
            "ageing_rate": self.ageing_rate(),
        }
