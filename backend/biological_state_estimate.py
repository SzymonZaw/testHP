"""Traceable state estimates derived from observed biological evidence."""
from __future__ import annotations

from dataclasses import dataclass

from .biological_trajectory import BiologicalTrajectory


HealthState = str


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
        """Create an estimate while retaining the trajectory used as evidence context."""
        return cls(
            health_state=health_state,
            biological_age=biological_age,
            confidence=confidence,
            evidence_ids=evidence_ids,
            trajectory_key=trajectory.key,
            trajectory_direction=trajectory.direction,
            trajectory_delta=trajectory.total_delta if trajectory.changes else None,
        )

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
