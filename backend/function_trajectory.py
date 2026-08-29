"""Longitudinal function-distribution analysis for hand observations."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .longitudinal_hand_twin import LongitudinalHandTwin


@dataclass(frozen=True)
class FunctionPoint:
    observed_at: str
    cell_count: int
    function_distribution: dict[str, int]

    @property
    def function_fractions(self) -> dict[str, float]:
        total = sum(self.function_distribution.values())
        if total <= 0:
            return {}
        return {name: count / total for name, count in self.function_distribution.items()}


@dataclass(frozen=True)
class FunctionTrajectory:
    """Describes observed changes in functional distributions over time."""

    points: tuple[FunctionPoint, ...]

    @classmethod
    def from_twin(cls, twin: LongitudinalHandTwin) -> "FunctionTrajectory":
        return cls(tuple(
            FunctionPoint(
                observed_at=item.observed_at,
                cell_count=item.state.cell_count,
                function_distribution=dict(item.state.function_distribution),
            )
            for item in twin.observations
        ))

    @property
    def latest(self) -> FunctionPoint | None:
        return self.points[-1] if self.points else None

    @property
    def first(self) -> FunctionPoint | None:
        return self.points[0] if self.points else None

    def fraction_delta(self, function_state: str) -> float | None:
        if not self.first or not self.latest:
            return None
        return (
            self.latest.function_fractions.get(function_state, 0.0)
            - self.first.function_fractions.get(function_state, 0.0)
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "points": [
                {
                    "observed_at": point.observed_at,
                    "cell_count": point.cell_count,
                    "function_distribution": point.function_distribution,
                    "function_fractions": point.function_fractions,
                }
                for point in self.points
            ],
            "latest": self.latest.function_distribution if self.latest else None,
        }
