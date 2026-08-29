"""Domain contracts for Digital Twin stages 15-20.

These are research/decision-support contracts, not clinical claims or treatment rules.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Literal

Horizon = Literal["5y", "10y", "20y", "50y"]
Organ = Literal["hand", "skin", "muscle", "bone", "blood", "heart", "brain", "liver", "kidney", "other"]

@dataclass(frozen=True)
class TransitionModelRef:
    model_id: str
    model_version: str
    validation_status: Literal["unvalidated", "validated", "prospective"] = "unvalidated"

@dataclass(frozen=True)
class Scenario:
    scenario_id: str
    label: str
    intervention: str = "none"
    parameters: dict[str, float] = field(default_factory=dict)

@dataclass(frozen=True)
class SimulationResult:
    scenario_id: str
    initial_state_id: str
    future_state: dict[str, float]
    horizon_years: float
    uncertainty: dict[str, float] = field(default_factory=dict)
    model: TransitionModelRef | None = None

@dataclass(frozen=True)
class Prediction:
    horizon: Horizon
    target_time: str
    values: dict[str, float]
    prediction_interval: dict[str, tuple[float, float]]
    uncertainty: dict[str, float]

@dataclass(frozen=True)
class AgingTrajectory:
    subject_id: str
    horizons_years: tuple[int, ...] = (0, 5, 10, 20, 50)
    values: dict[str, dict[int, float]] = field(default_factory=dict)
    uncertainty: dict[str, dict[int, float]] = field(default_factory=dict)

@dataclass(frozen=True)
class OrganTwin:
    organ_id: str
    organ: Organ
    current_state_id: str
    history_ids: tuple[str, ...] = ()

@dataclass(frozen=True)
class HumanDigitalTwin:
    human_id: str
    organs: tuple[OrganTwin, ...]
    timepoints: tuple[str, ...] = ()
    systemic_risk: dict[str, float] = field(default_factory=dict)

@dataclass(frozen=True)
class PredictiveMedicineRecord:
    record_id: str
    twin_id: str
    signal: str
    evidence_ids: tuple[str, ...]
    confidence: float | None = None
    expert_review_required: bool = True
    audit_id: str | None = None

    def validate(self) -> None:
        if self.confidence is not None and not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")
        if not self.evidence_ids:
            raise ValueError("predictive medicine records require evidence")
        if not self.expert_review_required:
            raise ValueError("expert review cannot be disabled")
