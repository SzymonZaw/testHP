"""Hypothetical, non-prescriptive intervention scenario projections."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class InterventionScenario:
    """Projects simple parameter deltas without making treatment recommendations."""

    name: str
    baseline_health: float
    baseline_function: float
    health_delta: float = 0.0
    function_delta: float = 0.0

    @property
    def projected_health(self) -> float:
        return _clamp(self.baseline_health + self.health_delta)

    @property
    def projected_function(self) -> float:
        return _clamp(self.baseline_function + self.function_delta)

    @property
    def expected_delta(self) -> dict[str, float]:
        return {
            "health": self.projected_health - self.baseline_health,
            "function": self.projected_function - self.baseline_function,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "baseline_health": self.baseline_health,
            "baseline_function": self.baseline_function,
            "health_delta": self.health_delta,
            "function_delta": self.function_delta,
            "projected_health": self.projected_health,
            "projected_function": self.projected_function,
            "expected_delta": self.expected_delta,
        }


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))
