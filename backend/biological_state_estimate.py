"""Traceable state estimates and risk assessment contracts."""
from __future__ import annotations

from dataclasses import dataclass

from .biological_trajectory import BiologicalTrajectory


HealthState = str
RiskLevel = str


@dataclass(frozen=True)
class BiologicalStateEstimate:
    """An interpretation of observations, explicitly separated from measurements."""

    health_state: HealthState | None = None
    biological_age: float | None = None
    confidence: float | None = None
    evidence_ids: tuple[str, ...] = ()
    trajectory_key: str | None = None
    trajectory_direction: str | None = None
    trajectory_delta: float | None = None

    @classmethod
    def from_trajectory(
        cls,
        trajectory: BiologicalTrajectory,
        *,
        health_state: HealthState | None = None,
        biological_age: float | None = None,
        confidence: float | None = None,
        evidence_ids: tuple[str, ...] = (),
    ) -> "BiologicalStateEstimate":
        return cls(health_state, biological_age, confidence, evidence_ids, trajectory.key, trajectory.direction, trajectory.total_delta if trajectory.changes else None)

    def __post_init__(self) -> None:
        if self.biological_age is not None and self.biological_age < 0:
            raise ValueError("biological_age must not be negative")
        if self.confidence is not None and not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")
        if len(self.evidence_ids) != len(set(self.evidence_ids)):
            raise ValueError("evidence_ids must be unique")

    @property
    def has_evidence(self) -> bool:
        return bool(self.evidence_ids) or self.trajectory_key is not None

    def to_dict(self) -> dict[str, object]:
        return {
            "health_state": self.health_state,
            "biological_age": self.biological_age,
            "confidence": self.confidence,
            "evidence_ids": list(self.evidence_ids),
            "trajectory_key": self.trajectory_key,
            "trajectory_direction": self.trajectory_direction,
            "trajectory_delta": self.trajectory_delta,
        }


@dataclass(frozen=True)
class BiologicalRiskAssessment:
    """Non-diagnostic risk signal attached to a state estimate."""

    risk_level: RiskLevel
    rationale: str
    confidence: float | None = None
    evidence_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.confidence is not None and not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")
        if not self.rationale.strip():
            raise ValueError("rationale must not be empty")
        if len(self.evidence_ids) != len(set(self.evidence_ids)):
            raise ValueError("evidence_ids must be unique")

    @classmethod
    def from_estimate(
        cls,
        estimate: BiologicalStateEstimate,
        *,
        risk_level: RiskLevel,
        rationale: str,
        confidence: float | None = None,
    ) -> "BiologicalRiskAssessment":
        return cls(risk_level, rationale, confidence, estimate.evidence_ids)

    def to_dict(self) -> dict[str, object]:
        return {
            "risk_level": self.risk_level,
            "rationale": self.rationale,
            "confidence": self.confidence,
            "evidence_ids": list(self.evidence_ids),
        }
