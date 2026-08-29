from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SimulationState:
    state_id: str
    observed_at: str
    values: dict[str, float]
    source_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class SimulationScenario:
    scenario_id: str
    baseline_state_id: str
    intervention: str = "none"
    parameters: dict[str, float] | None = None


@dataclass(frozen=True)
class TransitionModelRef:
    model_id: str
    model_version: str
    domain: str


@dataclass(frozen=True)
class SimulationResult:
    scenario_id: str
    transition_model: TransitionModelRef
    future_state: SimulationState
    confidence: float | None = None
    uncertainty: dict[str, float] | None = None
    evidence_ids: tuple[str, ...] = ()

    def validate(self) -> None:
        if not self.scenario_id or not self.transition_model.model_id:
            raise ValueError("simulation identity is required")
        if self.confidence is not None and not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")


def compare_results(results: tuple[SimulationResult, ...]) -> dict[str, SimulationResult]:
    return {result.scenario_id: result for result in results}
