from __future__ import annotations

"""Phase B: explicit imaging-to-hand spatial registration.

This module defines the registration result and a deterministic validation
boundary. It intentionally does not pretend to perform medical image
registration itself; a future ITK/ANTs/3D Slicer or other validated backend
can produce the transform and quality metrics consumed here.
"""

from dataclasses import dataclass, field
from typing import Any, Literal

from .anatomy_foundation import HandCoordinateSystem, Registration
from .data_foundation import Quality, Uncertainty, Provenance

RegistrationMethod = Literal["landmark", "rigid", "affine", "deformable", "manual", "external"]


@dataclass(frozen=True)
class ImageGeometry:
    frame_id: str
    dimensions: tuple[int, ...]
    spacing: tuple[float, ...]
    orientation: tuple[float, ...] = ()
    origin: tuple[float, ...] = ()

    def validate(self) -> None:
        if not self.dimensions or any(x <= 0 for x in self.dimensions):
            raise ValueError("image dimensions must be positive")
        if not self.spacing or any(x <= 0 for x in self.spacing):
            raise ValueError("image spacing must be positive")


@dataclass(frozen=True)
class RegistrationInput:
    registration_id: str
    source_data_ids: tuple[str, ...]
    source_geometry: ImageGeometry
    target_frame: HandCoordinateSystem
    method: RegistrationMethod
    transform: dict[str, Any]
    quality: Quality = field(default_factory=Quality)
    uncertainty: Uncertainty = field(default_factory=Uncertainty)
    provenance: Provenance = field(default_factory=Provenance)
    landmarks: tuple[dict[str, Any], ...] = ()

    def validate(self) -> None:
        if not self.source_data_ids:
            raise ValueError("registration requires source data")
        self.source_geometry.validate()
        if not self.transform:
            raise ValueError("registration requires an explicit transform")
        if self.method == "landmark" and not self.landmarks:
            raise ValueError("landmark registration requires landmarks")
        self.quality.validate()
        self.uncertainty.validate()


def build_registration(value: RegistrationInput) -> Registration:
    """Convert validated registration output into the canonical domain object."""
    value.validate()
    registration = Registration(
        registration_id=value.registration_id,
        subject_id=value.target_frame.subject_id,
        hand_id=value.target_frame.hand_id,
        timepoint_id=value.target_frame.timepoint_id,
        source_frame=value.source_geometry.frame_id,
        target_frame=value.target_frame.frame_id,
        modality="imaging",
        transform=value.transform,
        quality=value.quality,
        uncertainty=value.uncertainty,
        method=value.method,
        method_version=value.provenance.method_version,
        provenance=value.provenance,
    )
    registration.validate()
    return registration


def registration_summary(registration: Registration) -> dict[str, Any]:
    registration.validate()
    return {
        "registration_id": registration.registration_id,
        "source_frame": registration.source_frame,
        "target_frame": registration.target_frame,
        "method": registration.method,
        "quality": registration.quality.score,
        "uncertainty": registration.uncertainty.score,
        "validated": True,
    }
