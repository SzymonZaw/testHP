from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from .spatial_contract import canonical_spatial_id

MicroscopyModality = Literal["brightfield", "fluorescence", "confocal", "multiplex", "wsi", "unknown"]

@dataclass(frozen=True)
class MicroscopyImage:
    image_id: str
    subject_id: str
    hand_id: str
    tissue_id: str
    timepoint_id: str
    spatial_id: str
    modality: MicroscopyModality
    width_px: int
    height_px: int
    pixel_size_um: float | None = None
    uri: str | None = None
    provenance: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if not all((self.image_id, self.subject_id, self.hand_id, self.tissue_id, self.timepoint_id)):
            raise ValueError("microscopy identity is incomplete")
        if self.width_px <= 0 or self.height_px <= 0:
            raise ValueError("microscopy dimensions must be positive")
        if self.pixel_size_um is not None and self.pixel_size_um <= 0:
            raise ValueError("pixel_size_um must be positive")
        canonical_spatial_id(self.spatial_id)

@dataclass(frozen=True)
class SegmentationResult:
    segmentation_id: str
    image_id: str
    algorithm: str
    algorithm_version: str
    instance_count: int
    nucleus_count: int | None = None
    confidence: float | None = None
    mask_uri: str | None = None
    provenance: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if not all((self.segmentation_id, self.image_id, self.algorithm, self.algorithm_version)):
            raise ValueError("segmentation provenance is incomplete")
        if self.instance_count < 0 or (self.nucleus_count is not None and self.nucleus_count < 0):
            raise ValueError("segmentation counts cannot be negative")
        if self.confidence is not None and not 0 <= self.confidence <= 1:
            raise ValueError("segmentation confidence must be between 0 and 1")
