from __future__ import annotations

"""Deterministic scenario simulation primitives for the digital twin."""

from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class SimulationScenario:
    scenario_id: str
    baseline_timepoint: str
    intervention: dict[str, Any]
    horizon: str


@dataclass(frozen=True)
class SimulationResult:
    scenario_id: str
    baseline_timepoint: str
    horizon: str
    predicted_state: dict[str, Any]
    assumptions: tuple[str, ...] = ()
    model_id: str | None = None
    model_version: str | None = None


def run_simulation(
    scenario: SimulationScenario,
    state: dict[str, Any],
    transition: Callable[[dict[str, Any], dict[str, Any]], dict[str, Any]],
    *,
    model_id: str,
    model_version: str,
    assumptions: tuple[str, ...] = (),
) -> SimulationResult:
    if not scenario.scenario_id or not scenario.baseline_timepoint or not scenario.horizon:
        raise ValueError("simulation scenario identity is required")
    predicted = transition(dict(state), dict(scenario.intervention))
    return SimulationResult(
        scenario.scenario_id, scenario.baseline_timepoint, scenario.horizon,
        predicted, assumptions, model_id, model_version,
    )
