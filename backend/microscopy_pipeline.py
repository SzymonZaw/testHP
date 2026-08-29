from __future__ import annotations

"""Provenance-first microscopy ingestion primitives for the hand digital twin.

This module stores metadata and derived references; it does not pretend to
interpret pixels without a validated segmentation/classification model.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class MicroscopyImage:
    image_id: str
    subject_id: str
    hand_id: str
    timepoint_id: str
    tissue_id: str | None
    modality: str
    uri: str | None = None
    width: int | None = None
    height: int | None = None
    pixel_size_um: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.image_id or not self.subject_id or not self.hand_id or not self.timepoint_id:
            raise ValueError("microscopy image identity is required")
        if not self.modality:
            raise ValueError("microscopy modality is required")
        if self.pixel_size_um is not None and self.pixel_size_um <= 0:
            raise ValueError("pixel_size_um must be positive")


@dataclass(frozen=True)
class SegmentationMask:
    segmentation_id: str
    image_id: str
    algorithm: str
    algorithm_version: str
    mask_uri: str | None
    label_set: tuple[str, ...] = ()
    confidence: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.segmentation_id or not self.image_id or not self.algorithm:
            raise ValueError("segmentation identity is required")
        if not self.algorithm_version:
            raise ValueError("segmentation algorithm version is required")
        if self.confidence is not None and not 0 <= self.confidence <= 1:
            raise ValueError("segmentation confidence must be between 0 and 1")


def build_microscopy_image(**kwargs: Any) -> MicroscopyImage:
    image = MicroscopyImage(**kwargs)
    image.validate()
    return image


def build_segmentation(**kwargs: Any) -> SegmentationMask:
    segmentation = SegmentationMask(**kwargs)
    segmentation.validate()
    return segmentation
