"""Research-safe contracts for the complete hand-surface acquisition pipeline.

Stages are intentionally separated: acquisition -> calibration -> landmarks
-> segmentation -> multi-view reconstruction. No stage silently invents
missing measurements or claims clinical validity.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from math import exp
from typing import Any, Iterable, Literal

from .hand_surface import SUPPORTED_VIEWS
from .spatial_contract import canonical_spatial_id

COORDINATE_SYSTEM = "hand-surface-v1"
Stage = Literal["acquired", "calibrated", "landmarked", "segmented", "reconstructed", "failed"]

@dataclass(frozen=True)
class PhotoAcquisition:
    photo_id: str
    subject_id: str
    hand_id: str
    timepoint_id: str
    view: str
    captured_at: str
    source_uri: str
    camera_metadata: dict[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class PhotoCalibration:
    calibration_id: str
    photo_id: str
    camera_model: str
    intrinsics: dict[str, Any]
    distortion: dict[str, Any]
    scale_reference: dict[str, Any] | None = None
    reprojection_error: float | None = None
    def validate(self) -> None:
        if not self.intrinsics: raise ValueError("calibration requires camera intrinsics")
        if self.reprojection_error is not None and self.reprojection_error < 0: raise ValueError("reprojection error cannot be negative")

@dataclass(frozen=True)
class AnatomicalLandmarkSet:
    landmark_set_id: str
    photo_id: str
    coordinate_frame: str
    landmarks: tuple[dict[str, Any], ...]
    method: str
    confidence: float | None = None
    reviewed: bool = False
    def validate(self) -> None:
        if not self.landmarks: raise ValueError("landmark set cannot be empty")
        if not self.coordinate_frame: raise ValueError("landmarks require a coordinate frame")

@dataclass(frozen=True)
class HandSegmentation:
    segmentation_id: str
    photo_id: str
    mask_reference: str
    classes: tuple[str, ...]
    model_id: str
    model_version: str
    confidence: float | None = None

@dataclass(frozen=True)
class HandSurfaceReconstruction:
    reconstruction_id: str
    subject_id: str
    hand_id: str
    timepoint_id: str
    source_photo_ids: tuple[str, ...]
    landmark_set_ids: tuple[str, ...]
    segmentation_ids: tuple[str, ...]
    coordinate_frame: str
    geometry_reference: str
    method: str
    quality: dict[str, Any] = field(default_factory=dict)
    uncertainty: dict[str, Any] = field(default_factory=dict)
    def validate(self) -> None:
        if len(self.source_photo_ids) < 2: raise ValueError("3D reconstruction requires at least two photos")
        if not self.coordinate_frame or not self.geometry_reference: raise ValueError("reconstruction requires geometry and coordinate frame")

@dataclass(frozen=True)
class ImageQuality:
    width: int
    height: int
    file_size: int = 0
    background_score: float = 0.0
    sharpness_score: float = 0.0
    exposure_score: float = 0.0
    @property
    def resolution_score(self) -> float:
        return min(1.0, max(0, self.width) * max(0, self.height) / (2048 * 2048))
    @property
    def overall(self) -> float:
        return round((self.background_score + self.sharpness_score + self.exposure_score + self.resolution_score) / 4, 4)

@dataclass
class PreparedImage:
    asset_id: str
    original_name: str
    prepared_name: str
    spatial_id: str = "hand"
    view: str = "unknown"
    status: str = "pending"
    width: int = 0
    height: int = 0
    background_method: str = "none"
    crop: dict[str, int] = field(default_factory=dict)
    quality: ImageQuality | None = None
    warnings: list[str] = field(default_factory=list)
    def __post_init__(self): self.spatial_id = canonical_spatial_id(self.spatial_id)
    def to_dict(self): return asdict(self)

@dataclass(frozen=True)
class ViewRegistration:
    asset_id: str
    view: str
    spatial_id: str = "hand"
    quality: float = 0.0
    reprojection_error: float | None = None
    landmarks: int = 0
    method: str = "manual-registration-v1"
    coordinate_system: str = COORDINATE_SYSTEM
    def __post_init__(self): object.__setattr__(self, "spatial_id", canonical_spatial_id(self.spatial_id))
    @property
    def usable(self): return self.view in SUPPORTED_VIEWS and self.quality > 0 and self.landmarks > 0
    def to_dict(self): return asdict(self)

def validate_prepared_image(image: PreparedImage) -> list[str]:
    warnings = list(image.warnings)
    if image.view not in SUPPORTED_VIEWS: warnings.append("view is not one of the supported surface views")
    if image.width < 512 or image.height < 512: warnings.append("prepared image is below the recommended 512px minimum")
    if image.background_method == "none": warnings.append("background was not explicitly separated")
    if image.quality and image.quality.overall < 0.5: warnings.append("overall image quality is below the preferred research threshold")
    return warnings

def view_weight(*, camera_alignment: float, distance: float, quality: float) -> float:
    return round(max(0, min(1, camera_alignment))*0.55 + max(0, min(1, quality))*0.35 + exp(-max(0, distance))*0.10, 6)

def rank_views(registrations: Iterable[ViewRegistration]) -> list[dict[str, Any]]:
    items = [r for r in registrations if r.usable]
    return [{**r.to_dict(), "priority": round(r.quality * 0.7 + min(1, r.landmarks / 21) * 0.3, 4)} for r in sorted(items, key=lambda x: (x.quality, x.landmarks), reverse=True)]

def build_surface_manifest(*, subject_id: str, timepoint: str, spatial_id: str, prepared: Iterable[PreparedImage] = (), registrations: Iterable[ViewRegistration] = ()) -> dict[str, Any]:
    target = canonical_spatial_id(spatial_id)
    prepared_items = [x for x in prepared if canonical_spatial_id(x.spatial_id) == target]
    registration_items = [x for x in registrations if canonical_spatial_id(x.spatial_id) == target]
    prepared_views = {x.view for x in prepared_items if x.view in SUPPORTED_VIEWS}
    registered_views = {x.view for x in registration_items if x.usable}
    return {"schema": "hand-surface-stages-11-15", "coordinate_system": COORDINATE_SYSTEM, "subject_id": subject_id, "timepoint": timepoint, "spatial_id": target, "prepared_images": [x.to_dict() for x in prepared_items], "registrations": [x.to_dict() for x in registration_items], "prepared_views": sorted(prepared_views), "registered_views": sorted(registered_views), "counts": {"prepared": len(prepared_views), "registered": len(registered_views), "expected": len(SUPPORTED_VIEWS)}, "duplicates": {"prepared": sorted(v for v in prepared_views if sum(x.view == v for x in prepared_items) > 1), "registered": sorted(v for v in registered_views if sum(x.view == v for x in registration_items) > 1)}, "ranked_views": rank_views(registration_items), "projection_status": "ready-for-worker" if len(registered_views) >= 2 else "not-registered"}

def validate_pipeline(acquisitions, calibrations, landmarks, segmentations, reconstruction: HandSurfaceReconstruction) -> Stage:
    if not acquisitions: raise ValueError("pipeline requires photo acquisition")
    if any(p.subject_id != reconstruction.subject_id or p.hand_id != reconstruction.hand_id or p.timepoint_id != reconstruction.timepoint_id for p in acquisitions): raise ValueError("all photos must belong to the same subject/hand/timepoint")
    ids = {p.photo_id for p in acquisitions}
    if not all(x.photo_id in ids for x in calibrations + landmarks + segmentations): raise ValueError("a pipeline stage references an unknown photo")
    for x in calibrations: x.validate()
    for x in landmarks: x.validate()
    reconstruction.validate()
    return "reconstructed"
