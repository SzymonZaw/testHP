"""Auditable provenance trace for multiscale assessments."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class AssessmentTrace:
    """Trace explaining where an assessment came from and how certain it is."""

    assessment_id: str
    level: str
    node_id: str
    source_ids: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()
    provenance: tuple[str, ...] = ()
    confidence: float | None = None
    uncertainty: float | None = None

    def __post_init__(self) -> None:
        if not self.assessment_id:
            raise ValueError("assessment_id is required")
        if not self.level:
            raise ValueError("level is required")
        if not self.node_id:
            raise ValueError("node_id is required")
        if self.confidence is not None and not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        if self.uncertainty is not None and not 0.0 <= self.uncertainty <= 1.0:
            raise ValueError("uncertainty must be between 0 and 1")

    def to_dict(self) -> dict[str, Any]:
        return {
            "assessment_id": self.assessment_id,
            "level": self.level,
            "node_id": self.node_id,
            "source_ids": self.source_ids,
            "evidence_ids": self.evidence_ids,
            "provenance": self.provenance,
            "confidence": self.confidence,
            "uncertainty": self.uncertainty,
        }

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "AssessmentTrace":
        return cls(
            assessment_id=str(value["assessment_id"]),
            level=str(value["level"]),
            node_id=str(value["node_id"]),
            source_ids=tuple(value.get("source_ids", ())),
            evidence_ids=tuple(value.get("evidence_ids", ())),
            provenance=tuple(value.get("provenance", ())),
            confidence=value.get("confidence"),
            uncertainty=value.get("uncertainty"),
        )
