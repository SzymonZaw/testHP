"""High-level orchestration of longitudinal hand analysis."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .change_relationship import ChangeRelationship
from .decision_support import DecisionSupport
from .future_state import FutureState
from .function_trajectory import FunctionTrajectory
from .hand_assessment import HandAssessment
from .hand_trajectory import HandTrajectory
from .health_trajectory import HealthTrajectory
from .intervention_scenario import InterventionScenario
from .longitudinal_hand_twin import LongitudinalHandTwin
from .risk_model import RiskModel
from .risk_signal import RiskSignal
from .scenario_comparison import ScenarioComparison


@dataclass(frozen=True)
class HandAnalysis:
    """Single entry point for the descriptive analysis pipeline."""

    assessment: HandAssessment
    risk_signals: tuple[RiskSignal, ...]
    risk_model: RiskModel
    scenarios: tuple[InterventionScenario, ...]
    future_states: tuple[FutureState, ...]
    comparisons: tuple[ScenarioComparison, ...]
    decision_support: DecisionSupport

    @classmethod
    def from_twin(
        cls,
        twin: LongitudinalHandTwin,
        scenarios: tuple[InterventionScenario, ...] = (),
        uncertainty: float = 0.0,
    ) -> "HandAnalysis":
        hand = HandTrajectory.from_twin(twin)
        health = HealthTrajectory.from_twin(twin)
        function = FunctionTrajectory.from_twin(twin)
        relationship = ChangeRelationship.from_trajectories(health, function)
        assessment = HandAssessment.from_trajectories(
            hand, health, function, relationship
        )
        signals = RiskSignal.from_assessment(assessment)
        risk_model = RiskModel.from_signals(signals)
        comparisons = tuple(
            ScenarioComparison.from_scenario(scenario, uncertainty)
            for scenario in scenarios
        )
        future_states = tuple(
            FutureState.from_scenario(scenario, horizon_years=1.0, uncertainty=uncertainty)
            for scenario in scenarios
        )
        decision = DecisionSupport.from_analysis(
            risk_model,
            comparisons[0] if comparisons else None,
            future_states[0] if future_states else None,
        )
        return cls(
            assessment=assessment,
            risk_signals=signals,
            risk_model=risk_model,
            scenarios=tuple(scenarios),
            future_states=future_states,
            comparisons=comparisons,
            decision_support=decision,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "assessment": self.assessment.to_dict(),
            "risk_signals": [signal.to_dict() for signal in self.risk_signals],
            "risk_model": self.risk_model.to_dict(),
            "scenarios": [scenario.to_dict() for scenario in self.scenarios],
            "future_states": [state.to_dict() for state in self.future_states],
            "comparisons": [comparison.to_dict() for comparison in self.comparisons],
            "decision_support": self.decision_support.to_dict(),
        }
