from __future__ import annotations

"""Phase B adapters for turning ingested assets into multimodal acquisitions.

No image segmentation or clinical interpretation happens here. The adapter
only normalizes metadata and makes missing spatial registration explicit.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .multiscale_registry import ModalityAcquisition, MultiscaleRegistry

MODALITY_ALIASES = {
    "mri": "mri",
    "magnetic_resonance": "mri",
    "ultrasound": "ultrasound",
    "us": "ultrasound",
    "ct": "ct",
    "3d": "3d_scan",
    "3d_scan": "3d_scan",
    "photo": "photo",
    "hand": "photo",
}


@dataclass(frozen=True)
class ModalityAdapterResult:
    acquisition: ModalityAcquisition
    source_exists: bool
    spatial_status: str
    warnings: tuple[str, ...] = ()


def normalize_modality(value: str) -> str:
    key = value.strip().lower().replace("-", "_").replace(" ", "_")
    return MODALITY_ALIASES.get(key, key)


def acquisition_from_asset(
    asset: dict[str, Any],
    *,
    source_data_ids: list[str] | None = None,
    source_frame: str | None = None,
) -> ModalityAdapterResult:
    asset_id = str(asset.get("asset_id") or asset.get("id") or "")
    if not asset_id:
        raise ValueError("asset requires asset_id")
    subject_id = str(asset.get("subject_id") or "")
    hand_id = str(asset.get("hand_id") or "left")
    timepoint_id = str(asset.get("timepoint") or asset.get("timepoint_id") or "")
    modality = normalize_modality(str(asset.get("modality") or ""))
    if not subject_id or not timepoint_id or not modality:
        raise ValueError("asset requires subject_id, timepoint and modality")
    path = asset.get("path")
    exists = bool(path and Path(str(path)).is_file())
    frame = source_frame or asset.get("coordinate_frame") or f"{modality}-frame:{asset_id}"
    warnings: list[str] = []
    if not exists:
        warnings.append("source file is not available locally")
    warnings.append("spatial registration is required before anatomy can be placed in hand space")
    acquisition = ModalityAcquisition(
        acquisition_id=f"acq:{asset_id}",
        subject_id=subject_id,
        hand_id=hand_id,
        timepoint_id=timepoint_id,
        modality=modality,
        source_data_ids=source_data_ids or [asset_id],
        source_frame=frame,
        metadata={"asset_id": asset_id, "filename": asset.get("filename"), "path": path},
    )
    return ModalityAdapterResult(acquisition, exists, "unregistered", tuple(warnings))


def register_asset_acquisition(registry: MultiscaleRegistry, result: ModalityAdapterResult) -> None:
    """Add an acquisition while deliberately refusing implicit registration."""
    registry.add_acquisition(result.acquisition)
