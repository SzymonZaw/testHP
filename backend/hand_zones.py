"""Deterministic hand-zone mapping for the first Digital Twin vertical slice."""
from __future__ import annotations

from typing import Any


def zone_layout(width: int, height: int, rows: int = 3, columns: int = 3) -> list[dict[str, Any]]:
    if width <= 0 or height <= 0:
        return []
    zones = []
    zone_w, zone_h = width / columns, height / rows
    number = 1
    for row in range(rows):
        for col in range(columns):
            x, y = col * zone_w, row * zone_h
            zones.append({
                "zone_id": f"hand-zone-{number:02d}",
                "label": f"Zone {number:02d}",
                "bbox": {
                    "x": round(x), "y": round(y),
                    "width": round(zone_w), "height": round(zone_h),
                },
            })
            number += 1
    return zones


def assign_feature_to_zone(feature_x: float, feature_y: float, width: int, height: int) -> str | None:
    if width <= 0 or height <= 0 or not (0 <= feature_x <= width and 0 <= feature_y <= height):
        return None
    col = min(2, int(feature_x / (width / 3)))
    row = min(2, int(feature_y / (height / 3)))
    return f"hand-zone-{row * 3 + col + 1:02d}"
