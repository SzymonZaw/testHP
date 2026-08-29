from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MonitoringPlan:
    plan_id: str
    target_ids: tuple[str, ...]
    cadence: str
    rationale: str
    evidence_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class DiagnosticReferralSignal:
    target_id: str
    reason: str
    priority: str = "routine"
    confidence: float | None = None
    evidence_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class TherapyScenario:
    scenario_id: str
    target_id: str
    intervention: str
    parameters: dict[str, float] | None = None


@dataclass(frozen=True)
class ResponseObservation:
    target_id: str
    before_state_id: str
    after_state_id: str
    observed_at: str
    metrics: dict[str, float]
    evidence_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class TwinUpdate:
    twin_id: str
    timepoint_id: str
    source_ids: tuple[str, ...]
    update_reason: str
