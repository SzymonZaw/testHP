from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class EvidenceItem:
    evidence_id: str
    source_object_ids: tuple[str, ...]
    kind: str
    value: Any
    confidence: float

    def validate(self) -> None:
        if not self.evidence_id or not self.source_object_ids or not self.kind:
            raise ValueError("evidence identity and source are required")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("evidence confidence must be between 0 and 1")


@dataclass(frozen=True)
class EvidenceBundle:
    items: tuple[EvidenceItem, ...]

    def validate(self) -> None:
        if not self.items:
            raise ValueError("at least one evidence item is required")
        for item in self.items:
            item.validate()

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {"items": [{
            "evidence_id": x.evidence_id,
            "source_object_ids": list(x.source_object_ids),
            "kind": x.kind,
            "value": x.value,
            "confidence": x.confidence,
        } for x in self.items]}


@dataclass(frozen=True)
class CellBiologicalState:
    cell_id: str
    subject_id: str
    hand_id: str
    timepoint_id: str
    state: str
    biological_age_years: float | None
    uncertainty: float
    evidence: EvidenceBundle
    spatial_reference: str | None = None
    tissue_id: str | None = None

    def validate(self) -> None:
        if not self.cell_id or not self.subject_id or not self.hand_id or not self.timepoint_id:
            raise ValueError("cell, subject, hand and timepoint are required")
        if self.state not in {"normal", "abnormal", "uncertain"}:
            raise ValueError("state must be normal, abnormal or uncertain")
        if self.biological_age_years is not None and self.biological_age_years < 0:
            raise ValueError("biological age cannot be negative")
        if not 0.0 <= self.uncertainty <= 1.0:
            raise ValueError("uncertainty must be between 0 and 1")
        self.evidence.validate()

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "cell_id": self.cell_id,
            "subject_id": self.subject_id,
            "hand_id": self.hand_id,
            "timepoint_id": self.timepoint_id,
            "state": self.state,
            "biological_age_years": self.biological_age_years,
            "uncertainty": self.uncertainty,
            "evidence": self.evidence.to_dict(),
            "spatial_reference": self.spatial_reference,
            "tissue_id": self.tissue_id,
        }
