"""Longitudinal health-distribution analysis for hand observations."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .hand_state import HandState
from .longitudinal_hand_twin import LongitudinalHandTwin


@dataclass(frozen=True)
class HealthPoint:
    observed_at: str
    cell_count: int
    health_distribution: dict[str, int]

    @property
    def health_fractions(self) -> dict[str, float]:
        total = sum(self.health_distribution.values())
        if total <= 0:
            return {}
        return {name: count / total for name, count in self.health_distribution.items()}


@dataclass(frozen=True)
class HealthTrajectory:
    """Describes observed changes in health distributions over time."""

    points: tuple[HealthPoint, ...]

    @classmethod
    def from_twin(cls, twin: LongitudinalHandTwin) -> "HealthTrajectory":
        return cls(tuple(
            HealthPoint(
                observed_at=item.observed_at,
                cell_count=item.state.cell_count,
                health_distribution=dict(item.state.health_distribution),
            )
            for item in twin.observations
        ))

    @property
    def latest(self) -> HealthPoint | None:
        return self.points[-1] if self.points else None

    @property
    def first(self) -> HealthPoint | None:
        return self.points[0] if self.points else None

    def fraction_delta(self, health_state: str) -> float | None:
        if not self.first or not self.latest:
            return None
        return (
            self.latest.health_fractions.get(health_state, 0.0)
            - self.first.health_fractions.get(health_state, 0.0)
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "points": [
                {
                    "observed_at": point.observed_at,
                    "cell_count": point.cell_count,
                    "health_distribution": point.health_distribution,
                    "health_fractions": point.health_fractions,
                }
                for point in self.points
            ],
            "latest": self.latest.health_distribution if self.latest else None,
        }
