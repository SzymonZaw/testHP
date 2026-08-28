from __future__ import annotations

"""Auditable observations supporting cellular assessments."""

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class CellEvidence:
    """One measured observation; it does not represent a diagnosis."""

    source: str
    observation: str
    value: Any = None
    baseline: Any = None
    delta: float | None = None
    timepoint_id: str | None = None
    observation_id: str | None = None
    confidence: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.source or not self.observation:
            raise ValueError("evidence source and observation are required")
        if self.confidence is not None and not 0.0 <= self.confidence <= 1.0:
            raise ValueError("evidence confidence must be between 0 and 1")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CellEvidence":
        evidence = cls(**data)
        evidence.validate()
        return evidence
