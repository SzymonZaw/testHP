"""Traceable state estimates derived from observed biological evidence."""
from __future__ import annotations

from dataclasses import dataclass


HealthState = str


@dataclass(frozen=True)
class BiologicalStateEstimate:
    """An interpretation of observations, explicitly separated from measurements."""

    health_state: HealthState | None = None
    biological_age: float | None = None
    confidence: float | None = None
    evidence_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.biological_age is not None and self.biological_age < 0:
            raise ValueError("biological_age must not be negative")
        if self.confidence is not None and not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")
        if len(self.evidence_ids) != len(set(self.evidence_ids)):
            raise ValueError("evidence_ids must be unique")

    @property
    def has_evidence(self) -> bool:
        return bool(self.evidence_ids)

    def to_dict(self) -> dict[str, object]:
        return {
            "health_state": self.health_state,
            "biological_age": self.biological_age,
            "confidence": self.confidence,
            "evidence_ids": list(self.evidence_ids),
        }
