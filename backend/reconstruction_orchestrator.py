"""Single entry point for Photo 3D Reconstruction stages 6-10."""
from __future__ import annotations

from typing import Any

from .photo_reconstruction import _load_manifest
from .reconstruction_quality import validate_inputs
from .visual_hull import build_reconstruction, clear_reconstructions, latest_reconstruction


def run(subject_id: str, timepoint: str = "T0", resolution: int = 24) -> dict[str, Any]:
    """Validate, reconstruct, publish a SpatialObject and persist the result."""
    records = [r for r in _load_manifest() if r.get("subject_id") == subject_id and r.get("timepoint") == timepoint]
    quality = validate_inputs(records)
    if quality.get("status") != "ready":
        return {
            "status": "blocked",
            "reason": quality["errors"][0] if quality.get("errors") else "Reconstruction inputs are not ready",
            "quality": quality,
        }
    try:
        return build_reconstruction(subject_id, timepoint, resolution)
    except ValueError as exc:
        return {"status": "blocked", "reason": str(exc), "quality": quality}


def get_result(subject_id: str, timepoint: str = "T0") -> dict[str, Any] | None:
    return latest_reconstruction(subject_id, timepoint)


def clear(subject_id: str, timepoint: str = "T0") -> int:
    return clear_reconstructions(subject_id, timepoint)
