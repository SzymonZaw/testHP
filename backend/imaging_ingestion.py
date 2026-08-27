from __future__ import annotations

"""Phase B imaging ingestion metadata for DICOM/NIfTI-like sources.

This module intentionally does not decode pixels/voxels or perform clinical
interpretation. It normalizes acquisition metadata and creates a provenance
record that can later feed registration and segmentation pipelines.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

SUPPORTED_FORMATS = {"dicom", "nifti", "nifti_gz", "unknown"}
SUPPORTED_MODALITIES = {"mri", "ultrasound", "ct", "3d_scan", "photo", "other"}


@dataclass(frozen=True)
class ImagingSeries:
    series_id: str
    subject_id: str
    hand_id: str
    timepoint_id: str
    modality: str
    format: str
    source_path: str
    source_data_ids: tuple[str, ...] = ()
    frame_id: str | None = None
    dimensions: tuple[int, ...] = ()
    spacing: tuple[float, ...] = ()
    orientation: tuple[float, ...] = ()
    acquisition_metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if self.modality not in SUPPORTED_MODALITIES:
            raise ValueError(f"unsupported imaging modality: {self.modality}")
        if self.format not in SUPPORTED_FORMATS:
            raise ValueError(f"unsupported imaging format: {self.format}")
        if not self.source_path.strip():
            raise ValueError("imaging series requires a source path")
        if not self.source_data_ids:
            raise ValueError("imaging series must reference canonical source data")

    @property
    def is_multidimensional(self) -> bool:
        return len(self.dimensions) >= 3


def detect_format(path: str) -> str:
    suffixes = [x.lower() for x in Path(path).suffixes]
    if ".nii" in suffixes:
        return "nifti"
    if ".nii.gz".endswith("".join(suffixes[-2:])) if len(suffixes) >= 2 else False:
        return "nifti_gz"
    if Path(path).suffix.lower() == ".dcm":
        return "dicom"
    return "unknown"


def normalize_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    """Keep imaging metadata serializable and explicitly mark missing fields."""
    normalized = dict(metadata)
    for key in ("patient_name", "patient_address", "patient_telephone"):
        if key in normalized:
            normalized[key] = "[REDACTED]"
    normalized.setdefault("pixel_data_loaded", False)
    normalized.setdefault("registration_status", "unregistered")
    return normalized
