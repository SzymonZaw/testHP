"""Comparison of baseline and hypothetical intervention projections."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .intervention_scenario import InterventionScenario


@dataclass(frozen=True)
class ScenarioComparison:
    """Describes projected differences without recommending an intervention."""

    scenario_name: str
    health_delta: float
    function_delta: float
    uncertainty: float = 0.0

    @classmethod
    def from_scenario(
        cls, scenario: InterventionScenario, uncertainty: float = 0.0
    ) -> "ScenarioComparison":
        return cls(
            scenario_name=scenario.name,
            health_delta=scenario.expected_delta["health"],
            function_delta=scenario.expected_delta["function"],
            uncertainty=_clamp(uncertainty),
        )

    @property
    def combined_delta(self) -> float:
        return (self.health_delta + self.function_delta) / 2

    @property
    def meaningful_change(self) -> bool:
        return max(abs(self.health_delta), abs(self.function_delta)) > self.uncertainty

    def to_dict(self) -> dict[str, Any]:
        return {
            "scenario_name": self.scenario_name,
            "health_delta": self.health_delta,
            "function_delta": self.function_delta,
            "combined_delta": self.combined_delta,
            "uncertainty": self.uncertainty,
            "meaningful_change": self.meaningful_change,
        }


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))
