from __future__ import annotations

"""Single orchestration gate for Surface T0.

The orchestrator does not hide failed prerequisites and never promotes a
research reconstruction to an accepted Surface T0 without all gates passing.
"""

from dataclasses import dataclass, field
from typing import Any

from hand_camera_calibration import quality_gate
from multiview_reconstruction import reconstruct_from_views


@dataclass
class SurfaceT0Result:
    status: str
    gates: dict[str, dict[str, Any]]
    reconstruction: dict[str, Any] | None = None
    measurements: dict[str, Any] = field(default_factory=dict)


def build_surface_t0(
    image_paths: list[str],
    calibration: dict[str, Any] | None,
    *,
    photo_quality: list[dict[str, Any]],
    scale: dict[str, Any] | None,
) -> SurfaceT0Result:
    gates: dict[str, dict[str, Any]] = {}

    gates["calibration"] = {
        "status": "pass" if calibration and calibration.get("status") == "calibrated" and "camera_matrix" in calibration else "fail",
        "reason": "validated camera intrinsics required",
    }
    gates["metric_scale"] = {
        "status": "pass" if scale and scale.get("status") == "scale-calibrated" else "fail",
        "reason": "validated physical scale required",
    }
    gates["photo_quality"] = {
        "status": "pass" if photo_quality and all(q.get("status") == "pass" for q in photo_quality) else "fail",
        "photo_count": len(photo_quality),
    }

    if any(g["status"] != "pass" for g in gates.values()):
        return SurfaceT0Result("blocked", gates)

    reconstruction = reconstruct_from_views(image_paths, calibration)
    gates["registration"] = {
        "status": "pass" if reconstruction.get("status") == "reconstructed" else "fail",
        "method": reconstruction.get("method"),
        "pairs": reconstruction.get("pairs", []),
    }
    gates["reconstruction_validation"] = {
        "status": "pass" if reconstruction.get("point_count", 0) >= 8 else "fail",
        "point_count": reconstruction.get("point_count", 0),
        "requires": "independent reprojection/measurement validation before clinical use",
    }

    accepted = all(g["status"] == "pass" for g in gates.values())
    return SurfaceT0Result("accepted" if accepted else "rejected", gates, reconstruction=reconstruction, measurements={"scale": scale})


def photo_quality_from_metrics(width: int, height: int, blur_score: float, exposure_fraction: float, hand_confidence: float) -> dict[str, Any]:
    return quality_gate(width=width, height=height, blur_score=blur_score, exposure_fraction=exposure_fraction, hand_confidence=hand_confidence)
