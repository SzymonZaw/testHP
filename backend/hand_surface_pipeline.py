"""Research-safe contracts for Hand Surface stages 12–14.

This module intentionally does not claim to reconstruct a clinical 3D hand.
It provides deterministic metadata, quality checks, and multi-view weighting
contracts that can later be connected to an image-processing worker.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from math import exp
from typing import Any, Iterable

SUPPORTED_VIEWS = ("front", "back", "side_left", "side_right", "thumb")
COORDINATE_SYSTEM = "hand-surface-v1"


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
        pixels = max(0, self.width) * max(0, self.height)
        return min(1.0, pixels / (2048 * 2048))

    @property
    def overall(self) -> float:
        values = [self.background_score, self.sharpness_score, self.exposure_score, self.resolution_score]
        return round(sum(values) / len(values), 4)


@dataclass
class PreparedImage:
    asset_id: str
    original_name: str
    prepared_name: str
    view: str = "unknown"
    status: str = "pending"
    width: int = 0
    height: int = 0
    background_method: str = "none"
    crop: dict[str, int] = field(default_factory=dict)
    quality: ImageQuality | None = None
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ViewRegistration:
    asset_id: str
    view: str
    spatial_id: str
    quality: float = 0.0
    reprojection_error: float | None = None
    landmarks: int = 0
    method: str = "manual-registration-v1"
    coordinate_system: str = COORDINATE_SYSTEM

    @property
    def usable(self) -> bool:
        return self.view in SUPPORTED_VIEWS and self.quality > 0 and self.landmarks > 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def validate_prepared_image(image: PreparedImage) -> list[str]:
    """Return non-fatal warnings so research data is never silently rejected."""
    warnings = list(image.warnings)
    if image.view not in SUPPORTED_VIEWS:
        warnings.append("view is not one of the supported surface views")
    if image.width < 512 or image.height < 512:
        warnings.append("prepared image is below the recommended 512px minimum")
    if image.background_method == "none":
        warnings.append("background was not explicitly separated")
    if image.quality and image.quality.overall < 0.5:
        warnings.append("overall image quality is below the preferred research threshold")
    return warnings


def view_weight(*, camera_alignment: float, distance: float, quality: float) -> float:
    """Score a candidate image for a surface point without inventing geometry."""
    alignment = max(0.0, min(1.0, camera_alignment))
    q = max(0.0, min(1.0, quality))
    d = max(0.0, distance)
    distance_term = exp(-d)
    return round(alignment * 0.55 + q * 0.35 + distance_term * 0.10, 6)


def rank_views(registrations: Iterable[ViewRegistration]) -> list[dict[str, Any]]:
    """Return stable view records for a future projection worker."""
    items = [r for r in registrations if r.usable]
    return [
        {**r.to_dict(), "priority": round(r.quality * 0.7 + min(1.0, r.landmarks / 21) * 0.3, 4)}
        for r in sorted(items, key=lambda x: (x.quality, x.landmarks), reverse=True)
    ]


def build_surface_manifest(
    *,
    subject_id: str,
    timepoint: str,
    spatial_id: str,
    prepared: Iterable[PreparedImage] = (),
    registrations: Iterable[ViewRegistration] = (),
) -> dict[str, Any]:
    """Create a portable manifest shared by UI, ingestion, and future workers."""
    prepared_items = list(prepared)
    registration_items = list(registrations)
    return {
        "schema": "hand-surface-stages-11-15",
        "coordinate_system": COORDINATE_SYSTEM,
        "subject_id": subject_id,
        "timepoint": timepoint,
        "spatial_id": spatial_id,
        "prepared_images": [x.to_dict() for x in prepared_items],
        "registrations": [x.to_dict() for x in registration_items],
        "ranked_views": rank_views(registration_items),
        "projection_status": "ready-for-worker" if registration_items else "not-registered",
        "evidence_boundary": "Prepared photographs and registrations are observations; the manifest does not infer anatomy.",
    }
