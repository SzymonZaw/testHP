"""Conservative, image-only macro feature extraction.

This is intentionally not a diagnostic model. It extracts reproducible image
quality and morphology proxies that can be attached to an observation and
compared longitudinally.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any


def analyze_image(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    result: dict[str, Any] = {
        "status": "unavailable",
        "features": {},
        "interpretation": "No macro analysis performed.",
    }
    if not path.exists() or not path.is_file():
        result["interpretation"] = "Source image is unavailable."
        return result
    try:
        from PIL import Image, ImageStat
    except ImportError:
        result["status"] = "dependency_missing"
        result["interpretation"] = "Pillow is required for macro image analysis."
        return result

    with Image.open(path) as image:
        rgb = image.convert("RGB")
        stat = ImageStat.Stat(rgb)
        width, height = rgb.size
        mean = sum(stat.mean) / 3.0
        std = sum(stat.stddev) / 3.0
        result["status"] = "ok"
        result["features"] = {
            "width_px": width,
            "height_px": height,
            "channels": 3,
            "mean_intensity": round(mean, 3),
            "intensity_stddev": round(std, 3),
            "aspect_ratio": round(width / height, 4) if height else None,
        }
        result["interpretation"] = (
            "Macro image quality and basic intensity features extracted. "
            "No pathology or aging diagnosis is inferred."
        )
    return result
