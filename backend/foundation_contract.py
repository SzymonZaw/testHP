from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class SpatialLevel(str, Enum):
    HAND = "hand"
    STRUCTURE = "structure"
    REGION = "region"
    TISSUE = "tissue"
    MICROSCOPY = "microscopy"
    CELL = "cell"
    POINT = "point"


@dataclass(frozen=True)
class Evidence:
    evidence_id: str
    source_type: str
    source_id: str
    provenance: dict[str, Any] = field(default_factory=dict)
    observed_at: str | None = None


@dataclass(frozen=True)
class SpatialRef:
    spatial_id: str
    level: SpatialLevel
    parent_id: str | None = None
    coordinates: tuple[float, float, float] | None = None

    def validate(self) -> None:
        if not self.spatial_id:
            raise ValueError("spatial_id is required")
        if self.parent_id == self.spatial_id:
            raise ValueError("spatial reference cannot parent itself")


@dataclass(frozen=True)
class DigitalTwin:
    twin_id: str
    subject_id: str
    hand_ids: tuple[str, ...] = ()
    spatial_refs: tuple[SpatialRef, ...] = ()
    evidence: tuple[Evidence, ...] = ()
    timepoint_ids: tuple[str, ...] = ()

    def validate(self) -> None:
        if not self.twin_id or not self.subject_id:
            raise ValueError("twin_id and subject_id are required")
        spatial_ids = {item.spatial_id for item in self.spatial_refs}
        for item in self.spatial_refs:
            item.validate()
            if item.parent_id and item.parent_id not in spatial_ids:
                raise ValueError("spatial parent must exist in the same twin")
