from __future__ import annotations

from pathlib import Path
from typing import Any

VIDEO_EXTENSIONS = {".mp4", ".mov", ".m4v", ".avi", ".mkv"}


def inspect_video(path: Path) -> dict[str, Any]:
    """Return safe metadata and basic availability for a video asset.

    Decoding is optional: if OpenCV cannot open the file, the asset is reported as
    unavailable rather than generating fabricated temporal measurements.
    """
    result: dict[str, Any] = {
        "path": path.as_posix(),
        "status": "unavailable",
        "frames": 0,
        "fps": None,
        "duration_seconds": None,
        "temporal_features": {},
        "reason": None,
    }
    if not path.exists() or path.suffix.lower() not in VIDEO_EXTENSIONS:
        result["reason"] = "file missing or unsupported video format"
        return result
    if path.stat().st_size == 0:
        result["reason"] = "empty video file"
        return result
    try:
        import cv2
        cap = cv2.VideoCapture(str(path))
        if not cap.isOpened():
            result["reason"] = "video decoder could not open the file"
            return result
        frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        fps = float(cap.get(cv2.CAP_PROP_FPS) or 0)
        duration = frames / fps if frames > 0 and fps > 0 else None
        result.update({"status": "available", "frames": frames, "fps": fps or None, "duration_seconds": duration})
        cap.release()
    except Exception as exc:
        result["reason"] = f"video inspection failed: {exc}"
    return result


def analyze_video_directory(root: Path) -> list[dict[str, Any]]:
    return [inspect_video(path) for path in sorted(root.rglob("*")) if path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS]
