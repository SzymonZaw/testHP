"""Canonical spatial object and reconstruction contracts.

This is the shared boundary between Hand Surface, Photo 3D Reconstruction,
Spatial Model, Inspector, Navigation and Research Interpretation.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

ObjectType = Literal["hand", "generic"]


@dataclass(frozen=True)
class SpatialObject:
    """One canonical spatial entity used by all spatial-facing modules."""

    spatial_object_id: str
    object_type: ObjectType = "hand"
    subject_id: str = ""
    source: str = ""
    geometry_uri: str | None = None
    texture_uri: str | None = None
    transform: dict[str, Any] = field(default_factory=dict)
    coordinate_system: str = "world"
    quality: dict[str, Any] = field(default_factory=dict)
    provenance: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ReconstructionAsset:
    """Persistent identity linking reconstruction output to one spatial object."""

    reconstruction_id: str
    spatial_object_id: str
    subject_id: str
    timepoint_id: str
    source_photo_asset_ids: tuple[str, ...] = ()
    prepared_photo_asset_ids: tuple[str, ...] = ()
    registered_view_ids: tuple[str, ...] = ()
    method: str = ""
    version: str = "1"
    geometry_uri: str | None = None
    texture_uri: str | None = None
    coordinate_system: str = "hand-surface-v1"
    quality: dict[str, Any] = field(default_factory=dict)
    provenance: dict[str, Any] = field(default_factory=dict)
    status: str = "created"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def make_spatial_object_id(subject_id: str, reconstruction_id: str) -> str:
    return f"spatial-hand:{subject_id}:{reconstruction_id}"


def make_reconstruction_id(subject_id: str, timepoint_id: str, nonce: str) -> str:
    return f"reconstruction:{subject_id}:{timepoint_id}:{nonce}"


def make_photo_asset_id(asset_id: str) -> str:
    return f"photo:{asset_id}"


def make_prepared_photo_asset_id(asset_id: str) -> str:
    return f"prepared-photo:{asset_id}"


def make_registered_view_id(prepared_photo_id: str, view: str) -> str:
    return f"registered-view:{prepared_photo_id}:{view}"


def observation_id(photo_asset_id: str) -> str:
    return f"observation:{photo_asset_id}"


def lifecycle(status: str) -> str:
    """Normalize module-specific status into the shared lifecycle vocabulary."""
    aliases = {
        "uploaded": "created",
        "prepared": "prepared",
        "needs-registration-review": "needs_review",
        "registered": "registered",
        "reconstructed": "reconstructed",
        "ready": "published",
        "failed": "failed",
    }
    return aliases.get(status, status)
