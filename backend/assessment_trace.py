"""Auditable provenance and spatial trace for multiscale assessments."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .data_foundation import SpatialReference


@dataclass(frozen=True)
class AssessmentTrace:
    """Trace explaining where an assessment came from and where it is located."""

    assessment_id: str
    level: str
    node_id: str
    source_ids: tuple[str, ...] = ()
    parent_assessment_ids: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()
    provenance: tuple[str, ...] = ()
    confidence: float | None = None
    uncertainty: float | None = None
    spatial_references: tuple[SpatialReference, ...] = ()

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
        if self.assessment_id in self.parent_assessment_ids:
            raise ValueError("assessment cannot be its own parent")
        if len(set(self.parent_assessment_ids)) != len(self.parent_assessment_ids):
            raise ValueError("parent_assessment_ids must be unique")
        for reference in self.spatial_references:
            reference.validate()

    def to_dict(self) -> dict[str, Any]:
        return {
            "assessment_id": self.assessment_id,
            "level": self.level,
            "node_id": self.node_id,
            "source_ids": self.source_ids,
            "parent_assessment_ids": self.parent_assessment_ids,
            "evidence_ids": self.evidence_ids,
            "provenance": self.provenance,
            "confidence": self.confidence,
            "uncertainty": self.uncertainty,
            "spatial_references": tuple(
                {
                    "frame_id": item.frame_id,
                    "registration_status": item.registration_status,
                    "anatomical_target": item.anatomical_target,
                    "transform": item.transform,
                    "registration_quality": item.registration_quality,
                }
                for item in self.spatial_references
            ),
        }

    def explain(self) -> dict[str, Any]:
        """Return a machine-readable explanation of lineage and location."""
        return {
            "assessment_id": self.assessment_id,
            "level": self.level,
            "node_id": self.node_id,
            "parents": self.parent_assessment_ids,
            "sources": self.source_ids,
            "evidence": self.evidence_ids,
            "provenance": self.provenance,
            "confidence": self.confidence,
            "uncertainty": self.uncertainty,
            "spatial": self.to_dict()["spatial_references"],
        }

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "AssessmentTrace":
        spatial = tuple(
            item if isinstance(item, SpatialReference) else SpatialReference(
                frame_id=str(item["frame_id"]),
                registration_status=item.get("registration_status", "unknown"),
                anatomical_target=item.get("anatomical_target"),
                transform=item.get("transform", {}),
                registration_quality=item.get("registration_quality"),
            )
            for item in value.get("spatial_references", ())
        )
        return cls(
            assessment_id=str(value["assessment_id"]),
            level=str(value["level"]),
            node_id=str(value["node_id"]),
            source_ids=tuple(value.get("source_ids", ())),
            parent_assessment_ids=tuple(value.get("parent_assessment_ids", ())),
            evidence_ids=tuple(value.get("evidence_ids", ())),
            provenance=tuple(value.get("provenance", ())),
            confidence=value.get("confidence"),
            uncertainty=value.get("uncertainty"),
            spatial_references=spatial,
        )
