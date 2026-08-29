"""Projected future state for a hypothetical hand scenario."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .intervention_scenario import InterventionScenario
from .scenario_comparison import ScenarioComparison


@dataclass(frozen=True)
class FutureState:
    """A bounded, explicitly hypothetical future projection."""

    scenario_name: str
    horizon_years: float
    projected_health: float
    projected_function: float
    uncertainty: float
    evidence: dict[str, Any]

    @classmethod
    def from_scenario(
        cls, scenario: InterventionScenario, horizon_years: float, uncertainty: float = 0.0
    ) -> "FutureState":
        comparison = ScenarioComparison.from_scenario(scenario, uncertainty)
        return cls(
            scenario_name=scenario.name,
            horizon_years=max(0.0, float(horizon_years)),
            projected_health=scenario.projected_health,
            projected_function=scenario.projected_function,
            uncertainty=comparison.uncertainty,
            evidence={
                "baseline_health": scenario.baseline_health,
                "baseline_function": scenario.baseline_function,
                "health_delta": scenario.health_delta,
                "function_delta": scenario.function_delta,
            },
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "scenario_name": self.scenario_name,
            "horizon_years": self.horizon_years,
            "projected_health": self.projected_health,
            "projected_function": self.projected_function,
            "uncertainty": self.uncertainty,
            "evidence": self.evidence,
        }
