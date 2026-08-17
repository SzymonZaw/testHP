"""Map hand landmarks to stable anatomical regions for the Digital Twin.

The mapping is a research coordinate system, not a clinical segmentation model.
"""
from __future__ import annotations

from typing import Any

REGIONS = {
    "wrist": [0],
    "thumb": list(range(1, 5)),
    "index": list(range(5, 9)),
    "middle": list(range(9, 13)),
    "ring": list(range(13, 17)),
    "little": list(range(17, 21)),
}


def landmark_centroid(landmarks: list[dict[str, float]], indices: list[int]) -> dict[str, float] | None:
    points = [landmarks[i] for i in indices if i < len(landmarks)]
    if not points:
        return None
    return {
        "x": round(sum(p["x"] for p in points) / len(points), 6),
        "y": round(sum(p["y"] for p in points) / len(points), 6),
        "z": round(sum(p.get("z", 0.0) for p in points) / len(points), 6),
    }


def map_anatomical_regions(landmarks: list[dict[str, float]]) -> list[dict[str, Any]]:
    regions = []
    for region_id, indices in REGIONS.items():
        centroid = landmark_centroid(landmarks, indices)
        if centroid is None:
            continue
        regions.append({
            "region_id": region_id,
            "landmark_indices": indices,
            "centroid": centroid,
            "mapping_method": "landmark-group",
        })
    return regions
