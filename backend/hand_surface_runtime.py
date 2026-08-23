"""Runtime contracts for Hand Surface stages 16–19.

These contracts deliberately separate preparation, registration, projection and
geometry calibration. They do not claim photogrammetric reconstruction or
clinical interpretation.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from math import sqrt
from typing import Any, Iterable

from .hand_surface_pipeline import COORDINATE_SYSTEM, SUPPORTED_VIEWS, view_weight
from .spatial_contract import canonical_spatial_id


@dataclass(frozen=True)
class SegmentationMask:
    asset_id: str
    width: int
    height: int
    foreground_ratio: float
    spatial_id: str = "hand"
    method: str = "background-separation-v1"
    confidence: float = 0.0
    edge_quality: float = 0.0

    def __post_init__(self) -> None:
        object.__setattr__(self, "spatial_id", canonical_spatial_id(self.spatial_id))

    @property
    def usable(self) -> bool:
        return self.width >= 512 and self.height >= 512 and 0.02 <= self.foreground_ratio <= 0.98 and self.confidence >= 0.5


@dataclass(frozen=True)
class CameraView:
    asset_id: str
    view: str
    position: tuple[float, float, float]
    look_at: tuple[float, float, float]
    spatial_id: str = "hand"
    focal_length: float | None = None
    distortion: tuple[float, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "spatial_id", canonical_spatial_id(self.spatial_id))

    @property
    def valid(self) -> bool:
        return self.view in SUPPORTED_VIEWS and all(_finite(x) for x in (*self.position, *self.look_at))


@dataclass(frozen=True)
class SurfacePoint:
    point_id: str
    position: tuple[float, float, float]
    normal: tuple[float, float, float]


@dataclass(frozen=True)
class ProjectionCandidate:
    point_id: str
    asset_id: str
    view: str
    camera_alignment: float
    distance: float
    quality: float
    spatial_id: str = "hand"

    def __post_init__(self) -> None:
        object.__setattr__(self, "spatial_id", canonical_spatial_id(self.spatial_id))

    @property
    def weight(self) -> float:
        return view_weight(camera_alignment=self.camera_alignment, distance=self.distance, quality=self.quality)


@dataclass(frozen=True)
class GeometryCalibration:
    coordinate_system: str = COORDINATE_SYSTEM
    scale: float = 1.0
    palm_width: float = 1.0
    palm_length: float = 1.0
    finger_spread: float = 1.0
    thumb_angle: float = 0.0
    thickness: float = 1.0
    smoothness: float = 0.5

    def validate(self) -> list[str]:
        warnings: list[str] = []
        if self.coordinate_system != COORDINATE_SYSTEM:
            warnings.append("coordinate system mismatch")
        for name in ("scale", "palm_width", "palm_length", "finger_spread", "thickness"):
            if getattr(self, name) <= 0:
                warnings.append(f"{name} must be positive")
        if not 0 <= self.smoothness <= 1:
            warnings.append("smoothness must be between 0 and 1")
        if not -90 <= self.thumb_angle <= 90:
            warnings.append("thumb_angle is outside the recommended range")
        return warnings


@dataclass
class SurfaceRuntimeManifest:
    schema: str = "hand-surface-stages-16-19"
    coordinate_system: str = COORDINATE_SYSTEM
    spatial_id: str = "hand"
    segmentation: list[SegmentationMask] = field(default_factory=list)
    cameras: list[CameraView] = field(default_factory=list)
    geometry: GeometryCalibration = field(default_factory=GeometryCalibration)
    projection_status: str = "not-ready"
    geometry_status: str = "not-calibrated"
    provenance: list[dict[str, Any]] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.spatial_id = canonical_spatial_id(self.spatial_id)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["projection_status"] = projection_readiness(self.segmentation, self.cameras, self.spatial_id)
        data["geometry_status"] = "valid" if not self.geometry.validate() else "needs-review"
        return data


def _finite(value: float) -> bool:
    return value == value and abs(value) != float("inf")


def projection_readiness(segmentation: Iterable[SegmentationMask], cameras: Iterable[CameraView], spatial_id: str = "hand") -> str:
    target = canonical_spatial_id(spatial_id)
    masks = [m for m in segmentation if m.usable and canonical_spatial_id(m.spatial_id) == target]
    views = [c for c in cameras if c.valid and canonical_spatial_id(c.spatial_id) == target]
    if not masks:
        return "needs-segmentation"
    if not views:
        return "needs-camera-registration"
    return "ready-for-surface-projection"


def select_projection_source(candidates: Iterable[ProjectionCandidate], spatial_id: str = "hand") -> dict[str, Any] | None:
    """Select the strongest registered observation for one target and surface point."""
    target = canonical_spatial_id(spatial_id)
    valid = [c for c in candidates if c.view in SUPPORTED_VIEWS and c.spatial_id == target]
    if not valid:
        return None
    selected = max(valid, key=lambda candidate: candidate.weight)
    return {"point_id": selected.point_id, "asset_id": selected.asset_id, "view": selected.view, "spatial_id": target, "weight": selected.weight, "method": "weighted-multi-view-v1"}


def deformation_distance(before: tuple[float, float, float], after: tuple[float, float, float]) -> float:
    return round(sqrt(sum((a - b) ** 2 for a, b in zip(before, after))), 6)


def build_runtime_manifest(
    *,
    spatial_id: str = "hand",
    segmentation: Iterable[SegmentationMask] = (),
    cameras: Iterable[CameraView] = (),
    geometry: GeometryCalibration | None = None,
) -> dict[str, Any]:
    target = canonical_spatial_id(spatial_id)
    segmentation_items = [x for x in segmentation if canonical_spatial_id(x.spatial_id) == target]
    camera_items = [x for x in cameras if canonical_spatial_id(x.spatial_id) == target]
    manifest = SurfaceRuntimeManifest(
        spatial_id=target,
        segmentation=segmentation_items,
        cameras=camera_items,
        geometry=geometry or GeometryCalibration(),
    )
    manifest.provenance.append({
        "stage": "16-19",
        "coordinate_system": COORDINATE_SYSTEM,
        "spatial_id": target,
        "statement": "Runtime metadata records observations and transformations; it does not infer biological state.",
    })
    return manifest.to_dict()
