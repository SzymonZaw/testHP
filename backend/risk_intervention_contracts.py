"""Contracts for risk, intervention and downstream predictive stages.

Research/decision-support only. These contracts do not make clinical diagnoses
or prescribe treatment.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Literal

RiskLevel = Literal["normal", "monitor", "elevated", "high", "unknown"]
Action = Literal["observe", "investigate", "treat", "regenerate", "none"]

@dataclass(frozen=True)
class EvidenceRef:
    evidence_id: str
    source: str
    version: str | None = None

@dataclass(frozen=True)
class RiskSignal:
    signal_id: str
    spatial_id: str
    level: RiskLevel
    score: float | None = None
    evidence: tuple[EvidenceRef, ...] = ()
    confidence: float | None = None

    def validate(self) -> None:
        if self.score is not None and not 0 <= self.score <= 1:
            raise ValueError("risk score must be between 0 and 1")
        if self.confidence is not None and not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")
        if self.level != "unknown" and not self.evidence:
            raise ValueError("non-unknown risk requires evidence")

@dataclass(frozen=True)
class RiskMap:
    hand_id: str
    cell_signals: tuple[RiskSignal, ...] = ()
    tissue_signals: tuple[RiskSignal, ...] = ()
    region_signals: tuple[RiskSignal, ...] = ()

@dataclass(frozen=True)
class InterventionRecommendation:
    recommendation_id: str
    spatial_id: str
    action: Action
    priority: int
    rationale: str
    evidence: tuple[EvidenceRef, ...] = ()
    confidence: float | None = None
    limitations: tuple[str, ...] = ()
    expert_review_required: bool = True

    def validate(self) -> None:
        if self.priority < 0:
            raise ValueError("priority must be non-negative")
        if not self.rationale:
            raise ValueError("intervention recommendation requires rationale")
        if self.confidence is not None and not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")
        if not self.expert_review_required:
            raise ValueError("expert review cannot be disabled")

@dataclass(frozen=True)
class InterventionMap:
    hand_id: str
    recommendations: tuple[InterventionRecommendation, ...] = ()

@dataclass(frozen=True)
class MedicalDecisionSupportRecord:
    record_id: str
    twin_id: str
    detection: str
    risk: RiskSignal
    simulation_ids: tuple[str, ...] = ()
    prediction_ids: tuple[str, ...] = ()
    monitoring_plan_id: str | None = None
    evidence: tuple[EvidenceRef, ...] = ()
    audit_id: str | None = None
    expert_review_required: bool = True

    def validate(self) -> None:
        self.risk.validate()
        if not self.evidence:
            raise ValueError("medical decision support requires evidence")
        if not self.audit_id:
            raise ValueError("medical decision support requires an audit id")
        if not self.expert_review_required:
            raise ValueError("expert review cannot be disabled")
