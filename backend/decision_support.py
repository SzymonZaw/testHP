"""Transparent, non-prescriptive decision support from observed risk signals."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from .aging_priority import AgingPriority
from .future_state import FutureState
from .risk_model import RiskModel
from .scenario_comparison import ScenarioComparison


@dataclass(frozen=True)
class DecisionSupport:
    """Summarizes evidence into a follow-up category, not a treatment decision."""

    action: str
    reasons: tuple[str, ...]
    risk_level: str
    scenario_name: str | None
    evidence: dict[str, Any]

    @classmethod
    def from_analysis(
        cls,
        risk_model: RiskModel,
        comparison: ScenarioComparison | None = None,
        future_state: FutureState | None = None,
        aging_priorities: Iterable[AgingPriority] = (),
    ) -> "DecisionSupport":
        reasons: list[str] = []
        priorities = tuple(aging_priorities)
        high_priority = tuple(item for item in priorities if item.priority == "high")
        medium_priority = tuple(item for item in priorities if item.priority == "medium")

        if risk_model.overall_level == "insufficient_data":
            return cls(
                action="insufficient_data",
                reasons=("insufficient_risk_signals",),
                risk_level=risk_model.overall_level,
                scenario_name=future_state.scenario_name if future_state else None,
                evidence={
                    "signal_count": len(risk_model.signals),
                    "aging_priority_count": len(priorities),
                    "high_aging_priority_count": len(high_priority),
                },
            )

        if risk_model.overall_level == "low":
            action = "no_action"
            reasons.append("low_observed_risk")
        elif risk_model.overall_level == "moderate":
            action = "monitor"
            reasons.append("moderate_observed_risk")
        elif risk_model.overall_level in {"elevated", "high"}:
            action = "investigate"
            reasons.append(f"{risk_model.overall_level}_observed_risk")
        else:
            action = "monitor"
            reasons.append("unclassified_risk_level")

        # Aging priorities add an observation reason; they do not independently
        # escalate a clinical action or override the risk model.
        if high_priority:
            reasons.append("high_aging_observation_priority")
        elif medium_priority:
            reasons.append("medium_aging_observation_priority")

        if comparison is not None and comparison.meaningful_change:
            reasons.append("meaningful_projected_difference")

        if future_state is not None:
            reasons.append("hypothetical_future_projection_available")

        return cls(
            action=action,
            reasons=tuple(reasons),
            risk_level=risk_model.overall_level,
            scenario_name=future_state.scenario_name if future_state else None,
            evidence={
                "signal_count": len(risk_model.signals),
                "risk_confidence": risk_model.confidence,
                "meaningful_change": comparison.meaningful_change if comparison else False,
                "aging_priority_count": len(priorities),
                "high_aging_priority_count": len(high_priority),
                "medium_aging_priority_count": len(medium_priority),
                "aging_priorities": [item.to_dict() for item in priorities],
            },
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "reasons": self.reasons,
            "risk_level": self.risk_level,
            "scenario_name": self.scenario_name,
            "evidence": self.evidence,
        }
