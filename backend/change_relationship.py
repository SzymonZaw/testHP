"""Relationship between observed health and function changes."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .health_trajectory import HealthTrajectory
from .function_trajectory import FunctionTrajectory


@dataclass(frozen=True)
class ChangeRelationship:
    """Descriptive comparison of health and function endpoint changes."""

    health_deltas: dict[str, float]
    function_deltas: dict[str, float]

    @classmethod
    def from_trajectories(
        cls, health: HealthTrajectory, function: FunctionTrajectory
    ) -> "ChangeRelationship":
        health_states = set()
        if health.first:
            health_states.update(health.first.health_fractions)
        if health.latest:
            health_states.update(health.latest.health_fractions)

        function_states = set()
        if function.first:
            function_states.update(function.first.function_fractions)
        if function.latest:
            function_states.update(function.latest.function_fractions)

        return cls(
            health_deltas={
                state: health.fraction_delta(state) or 0.0
                for state in sorted(health_states)
            },
            function_deltas={
                state: function.fraction_delta(state) or 0.0
                for state in sorted(function_states)
            },
        )

    @property
    def health_change_magnitude(self) -> float:
        return sum(abs(value) for value in self.health_deltas.values()) / 2

    @property
    def function_change_magnitude(self) -> float:
        return sum(abs(value) for value in self.function_deltas.values()) / 2

    @property
    def interpretation(self) -> str:
        health = self.health_change_magnitude
        function = self.function_change_magnitude
        if health == 0 and function == 0:
            return "stable"
        if health > function * 2:
            return "health_change_exceeds_function_change"
        if function > health * 2:
            return "function_change_exceeds_health_change"
        return "health_and_function_change_together"

    def to_dict(self) -> dict[str, Any]:
        return {
            "health_deltas": self.health_deltas,
            "function_deltas": self.function_deltas,
            "health_change_magnitude": self.health_change_magnitude,
            "function_change_magnitude": self.function_change_magnitude,
            "interpretation": self.interpretation,
        }
