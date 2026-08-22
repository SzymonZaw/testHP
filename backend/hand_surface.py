"""Coordinate and evidence contracts for the Hand Surface pipeline.

Hand Surface owns reusable hand-specific preparation primitives: landmarks,
segmentation evidence, normalized hand coordinates and per-view registration.
Photo 3D Reconstruction consumes these contracts and owns only multi-view
reconstruction. Spatial identity is supplied by ``spatial_contract``.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Iterable


HAND_LANDMARK_COUNT = 21
SUPPORTED_VIEWS = ("front", "back", "side_left", "side_right", "thumb")


@dataclass(frozen=True)
class SurfacePoint:
    """Canonical normalized hand-surface coordinate."""

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
    """Registration metadata linking one image observation to hand space."""

    view: str
    coordinate_system: str = "hand-surface-v1"
    transform: dict[str, Any] = field(default_factory=dict)
    landmarks: list[HandLandmark] = field(default_factory=list)
    status: str = "unregistered"
    quality: float | None = None
    method: str = "pending"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SurfaceEvidence:
    """A biological image reference plus its spatial registration."""

    asset_id: str
    subject_id: str
    timepoint_id: str
    spatial_id: str
    uri: str
    view: str = "unknown"
    modality: str = "skin_image"
    registration: SurfaceRegistration | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def validate_landmarks(landmarks: Iterable[HandLandmark]) -> list[str]:
    """Return validation errors without rejecting partial research data."""
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
    """Convert MediaPipe-style points into the stable surface contract."""
    result: list[HandLandmark] = []
    for index, point in enumerate(points):
        result.append(
            HandLandmark(
                landmark_id=f"mp-{index:02d}",
                point=SurfacePoint(
                    float(point["x"]),
                    float(point["y"]),
                    float(point.get("z", 0.0)),
                ),
                confidence=float(point.get("confidence", 1.0)),
            )
        )
    return result


def build_registration(
    *,
    view: str,
    landmarks: Iterable[dict[str, float]] = (),
    method: str = "pending",
    quality: float | None = None,
    transform: dict[str, Any] | None = None,
) -> SurfaceRegistration:
    """Create a validated registration record ready for later projection."""
    normalized_view = view if view in SUPPORTED_VIEWS else "unknown"
    normalized = normalize_landmarks(landmarks)
    errors = validate_landmarks(normalized)
    if errors:
        return SurfaceRegistration(
            view=normalized_view,
            transform=dict(transform or {}),
            landmarks=normalized,
            status="invalid",
            quality=quality,
            method=method,
        )
    status = "registered" if normalized else "unregistered"
    return SurfaceRegistration(
        view=normalized_view,
        transform=dict(transform or {}),
        landmarks=normalized,
        status=status,
        quality=quality,
        method=method,
    )


def build_surface_evidence(
    *,
    asset_id: str,
    subject_id: str,
    timepoint_id: str,
    uri: str,
    view: str = "unknown",
    registration: SurfaceRegistration | None = None,
) -> SurfaceEvidence:
    """Create canonical evidence consumed by downstream reconstruction."""
    from .spatial_contract import make_photo_asset_id

    return SurfaceEvidence(
        asset_id=make_photo_asset_id(asset_id),
        subject_id=subject_id,
        timepoint_id=timepoint_id,
        spatial_id=f"hand:{subject_id}:{timepoint_id}",
        uri=uri,
        view=view if view in SUPPORTED_VIEWS else "unknown",
        registration=registration,
    )
