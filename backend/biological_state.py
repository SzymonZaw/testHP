from __future__ import annotations

"""Evidence-first biological interpretation contracts.

This layer deliberately separates observations/evidence from interpretation.
It does not diagnose disease or prescribe treatment. Assessments are derived
claims with explicit provenance, uncertainty and model/version metadata.
"""

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

from .data_foundation import Provenance, Uncertainty

HealthState = Literal[
    "normal",
    "atypical",
    "suspicious",
    "pathological",
    "indeterminate",
]


@dataclass(frozen=True)
class InterpretationEvidence:
    evidence_id: str
    source_object_ids: tuple[str, ...]
    kind: str
    value: Any
    confidence: float | None = None
    provenance: Provenance = field(default_factory=Provenance)

    def validate(self) -> None:
        if not self.evidence_id.strip():
            raise ValueError("evidence_id is required")
        if not self.source_object_ids:
            raise ValueError("interpretation evidence requires source_object_ids")
        if not self.kind.strip():
            raise ValueError("evidence kind is required")
        if self.confidence is not None and not 0 <= self.confidence <= 1:
            raise ValueError("evidence confidence must be between 0 and 1")


@dataclass(frozen=True)
class BiologicalStateAssessment:
    assessment_id: str
    subject_id: str
    hand_id: str
    timepoint_id: str
    target_object_id: str
    state: HealthState
    confidence: float | None
    evidence: tuple[InterpretationEvidence, ...]
    uncertainty: Uncertainty
    provenance: Provenance
    assessed_at: str
    model_id: str | None = None
    model_version: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.assessment_id.strip():
            raise ValueError("assessment_id is required")
        if not self.target_object_id.strip():
            raise ValueError("target_object_id is required")
        if self.confidence is not None and not 0 <= self.confidence <= 1:
            raise ValueError("assessment confidence must be between 0 and 1")
        if not self.evidence:
            raise ValueError("biological state assessment requires evidence")
        for item in self.evidence:
            item.validate()
        self.uncertainty.validate()

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)


@dataclass(frozen=True)
class BiologicalAgeEstimate:
    estimate_id: str
    subject_id: str
    hand_id: str
    timepoint_id: str
    target_object_id: str
    estimated_age_years: float
    uncertainty: Uncertainty
    evidence: tuple[InterpretationEvidence, ...]
    provenance: Provenance
    assessed_at: str
    model_id: str | None = None
    model_version: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if self.estimated_age_years < 0:
            raise ValueError("estimated biological age cannot be negative")
        if not self.evidence:
            raise ValueError("biological age estimate requires evidence")
        for item in self.evidence:
            item.validate()
        self.uncertainty.validate()

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)
