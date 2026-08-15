from __future__ import annotations

from typing import Any

from .app import app
from .hand_analysis import ZONE_LANDMARKS, run_hand_analysis


def _bbox(points: list[dict[str, Any]], indices: list[int]) -> dict[str, float] | None:
    selected = [points[i] for i in indices if i < len(points)]
    if not selected:
        return None
    xs = [float(p["x"]) for p in selected]
    ys = [float(p["y"]) for p in selected]
    return {
        "x_min": round(min(xs), 6),
        "y_min": round(min(ys), 6),
        "x_max": round(max(xs), 6),
        "y_max": round(max(ys), 6),
    }


def _pixel_bbox(norm: dict[str, float] | None, width: int | None, height: int | None) -> dict[str, int] | None:
    if not norm or not width or not height:
        return None
    return {
        "x_min": max(0, min(width, round(norm["x_min"] * width))),
        "y_min": max(0, min(height, round(norm["y_min"] * height))),
        "x_max": max(0, min(width, round(norm["x_max"] * width))),
        "y_max": max(0, min(height, round(norm["y_max"] * height))),
    }


def _evidence_slots() -> list[dict[str, Any]]:
    return [
        {"id": "macro_rgb", "level": "macro", "status": "available", "purpose": "Attach the original RGB observation and spatial crop for this ROI."},
        {"id": "depth", "level": "macro", "status": "future", "purpose": "Depth/3D acquisition for surface geometry and volume."},
        {"id": "temporal", "level": "longitudinal", "status": "future", "purpose": "Compare the same ROI across timepoints."},
        {"id": "micro_wsi", "level": "tissue", "status": "future", "purpose": "Bind a validated microscopic/WSI region to this spatial target."},
        {"id": "cellular", "level": "cell", "status": "future", "purpose": "Bind cell-level measurements after a real cellular acquisition/analysis exists."},
        {"id": "molecular", "level": "molecular", "status": "future", "purpose": "Bind RNA or other non-image molecular evidence only with validated spatial/sample linkage."},
    ]


@app.get("/api/hand/roi/{zone_id}")
def hand_roi_detail(zone_id: str):
    result = run_hand_analysis()
    zone_id = zone_id.strip().lower()
    if zone_id not in ZONE_LANDMARKS:
        return {"status": "not_found", "stage": "H10", "zone": zone_id, "available_zones": list(ZONE_LANDMARKS)}

    bindings: list[dict[str, Any]] = []
    for image in result.get("images", []):
        for hand in image.get("hands", []):
            points = hand.get("landmarks_2d", [])
            norm = _bbox(points, ZONE_LANDMARKS[zone_id])
            if not norm:
                continue
            quality = image.get("quality") or {}
            bindings.append({
                "file": image.get("file"),
                "hand_index": hand.get("index"),
                "handedness": hand.get("handedness"),
                "bbox_norm": norm,
                "bbox_px": _pixel_bbox(norm, quality.get("width"), quality.get("height")),
                "source_observation": "landmark-derived spatial binding; not a biological segmentation",
            })

    summary = next((z for z in result.get("zone_summary", []) if z.get("id") == zone_id), None)
    return {
        "status": "ready" if bindings else "no_binding",
        "stage": "H10",
        "zone": zone_id,
        "zone_summary": summary,
        "spatial_bindings": bindings,
        "evidence_slots": _evidence_slots(),
        "evidence_boundary": {
            "observed": ["landmark-derived ROI coordinates", "source image and image dimensions"],
            "not_observed": ["tissue state", "cell state", "molecular state", "disease state"],
        },
        "next_action": "Use the spatial binding as the coordinate contract for attaching deeper measurements when those acquisitions become available.",
    }
