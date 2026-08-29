"""Orchestrate hand assessment into explainable decision support."""
from __future__ import annotations

from dataclasses import dataclass

from .decision_support import DecisionSupport
from .hand_assessment import HandAssessment
from .risk_model import RiskModel
from .risk_signal import RiskSignal


@dataclass(frozen=True)
class CellAssessmentEngine:
    """Bridge observed assessment evidence to risk and follow-up support."""

    assessment: HandAssessment
    risk_model: RiskModel
    decision_support: DecisionSupport

    @classmethod
    def from_assessment(cls, assessment: HandAssessment) -> "CellAssessmentEngine":
        signals = RiskSignal.from_assessment(assessment)
        risk_model = RiskModel.from_signals(signals)
        decision_support = DecisionSupport.from_analysis(risk_model)
        return cls(assessment, risk_model, decision_support)

    def to_dict(self) -> dict[str, object]:
        return {
            "assessment": self.assessment.to_dict(),
            "risk_model": self.risk_model.to_dict(),
            "decision_support": self.decision_support.to_dict(),
        }
