from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class AnatomicalStructureType(str, Enum):
    BONE = "bone"
    JOINT = "joint"
    MUSCLE = "muscle"
    TENDON = "tendon"
    LIGAMENT = "ligament"
    NERVE = "nerve"
    VESSEL = "vessel"
    SKIN = "skin"


@dataclass(frozen=True)
class CoordinateFrame:
    frame_id: str
    unit: str = "mm"
    handedness: str = "right"


@dataclass(frozen=True)
class Transform:
    transform_id: str
    source_frame: str
    target_frame: str
    matrix: tuple[float, ...]

    def validate(self) -> None:
        if len(self.matrix) != 16:
            raise ValueError("4x4 transform matrix requires 16 values")


@dataclass(frozen=True)
class HandStructure:
    structure_id: str
    spatial_id: str
    structure_type: AnatomicalStructureType
    name: str
    parent_spatial_id: str | None = None


@dataclass(frozen=True)
class TissueRegion:
    tissue_id: str
    spatial_id: str
    tissue_type: str
    sample_id: str
    timepoint_id: str
    histology_ref: str | None = None
