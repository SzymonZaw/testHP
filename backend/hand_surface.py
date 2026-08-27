"""Coordinate and evidence contracts for the Hand Surface pipeline.

Hand Surface owns reusable hand-specific preparation primitives: landmarks,
segmentation evidence, normalized hand coordinates and per-view registration.
Photo 3D Reconstruction consumes these contracts and owns only multi-view
reconstruction. Spatial identity is supplied by ``spatial_contract``.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Iterable

from .spatial_contract import canonical_spatial_id, make_photo_asset_id

HAND_LANDMARK_COUNT = 21
SUPPORTED_VIEWS = ("front", "back", "side_left", "side_right", "thumb", "unknown")


@dataclass(frozen=True)
class SurfacePoint:
    x: float
    y: float
    z: float = 0.0

    def as_tuple(self) -> tuple[float, float, float]:
        return (self.x, self.y, self.z)


@dataclass(frozen=True)
class HandLandmark:
    landmark_id: str
    point: SurfacePoint
    confidence: float = 1.0


@dataclass
class SurfaceRegistration:
    """Registration metadata linking one image observation to one spatial target."""

    view: str
    spatial_id: str = "hand"
    asset_id: str | None = None
    coordinate_system: str = "hand-surface-v1"
    transform: dict[str, Any] = field(default_factory=dict)
    landmarks: list[HandLandmark] = field(default_factory=list)
    status: str = "unregistered"
    quality: float | None = None
    method: str = "pending"

    def __post_init__(self) -> None:
        self.spatial_id = canonical_spatial_id(self.spatial_id)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SurfaceEvidence:
    """A biological image reference plus its canonical spatial registration."""

    asset_id: str
    subject_id: str
    timepoint_id: str
    spatial_id: str
    uri: str
    view: str = "unknown"
    modality: str = "skin_image"
    registration: SurfaceRegistration | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "spatial_id", canonical_spatial_id(self.spatial_id))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def validate_landmarks(landmarks: Iterable[HandLandmark]) -> list[str]:
    errors: list[str] = []
    items = list(landmarks)
    if len(items) > HAND_LANDMARK_COUNT:
        errors.append(f"too many landmarks: {len(items)} > {HAND_LANDMARK_COUNT}")
    for item in items:
        p = item.point
        if not 0.0 <= p.x <= 1.0 or not 0.0 <= p.y <= 1.0:
            errors.append(f"landmark {item.landmark_id} is outside normalized x/y bounds")
        if not 0.0 <= item.confidence <= 1.0:
            errors.append(f"landmark {item.landmark_id} has invalid confidence")
    return errors


def normalize_landmarks(points: Iterable[dict[str, float]]) -> list[HandLandmark]:
    result: list[HandLandmark] = []
    for index, point in enumerate(points):
        result.append(
            HandLandmark(
                landmark_id=f"mp-{index:02d}",
                point=SurfacePoint(float(point["x"]), float(point["y"]), float(point.get("z", 0.0))),
                confidence=float(point.get("confidence", 1.0)),
            )
        )
    return result


def build_registration(
    *,
    view: str,
    spatial_id: str = "hand",
    asset_id: str | None = None,
    landmarks: Iterable[dict[str, float]] = (),
    method: str = "pending",
    quality: float | None = None,
    transform: dict[str, Any] | None = None,
) -> SurfaceRegistration:
    normalized_view = view if view in SUPPORTED_VIEWS else "unknown"
    normalized = normalize_landmarks(landmarks)
    errors = validate_landmarks(normalized)
    return SurfaceRegistration(
        view=normalized_view,
        spatial_id=canonical_spatial_id(spatial_id),
        asset_id=asset_id,
        transform=dict(transform or {}),
        landmarks=normalized,
        status="invalid" if errors else ("registered" if normalized else "unregistered"),
        quality=quality,
        method=method,
    )


def build_surface_evidence(
    *,
    asset_id: str,
    subject_id: str,
    timepoint_id: str,
    spatial_id: str = "hand",
    uri: str,
    view: str = "unknown",
    registration: SurfaceRegistration | None = None,
) -> SurfaceEvidence:
    """Create evidence that stays in the selected spatial scope."""
    target = canonical_spatial_id(spatial_id)
    if registration is not None and canonical_spatial_id(registration.spatial_id) != target:
        raise ValueError("registration spatial_id does not match evidence spatial_id")
    return SurfaceEvidence(
        asset_id=make_photo_asset_id(asset_id),
        subject_id=subject_id,
        timepoint_id=timepoint_id,
        spatial_id=target,
        uri=uri,
        view=view if view in SUPPORTED_VIEWS else "unknown",
        registration=registration,
    )
