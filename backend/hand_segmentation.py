"""Optional anatomy-aware hand segmentation adapter."""
from __future__ import annotations
from pathlib import Path
from typing import Any


def _fallback(reason: str) -> dict[str, Any]:
    return {"status": "fallback", "landmarks": [], "method": "bbox-fallback", "reason": reason}


def detect_hand_landmarks(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    if not path.exists():
        return {"status": "unavailable", "landmarks": [], "method": "none"}
    try:
        import cv2
        import mediapipe as mp
    except ImportError:
        return _fallback("Optional MediaPipe/OpenCV dependencies are not installed.")

    # MediaPipe versions using the newer Tasks API may not expose the legacy
    # mp.solutions namespace. Hand segmentation is enrichment, so ingestion
    # must remain functional when that optional API is unavailable.
    hands_api = getattr(mp, "solutions", None)
    if hands_api is None or not hasattr(hands_api, "hands"):
        return _fallback("Installed MediaPipe version does not expose the legacy solutions.hands API.")

    image = cv2.imread(str(path))
    if image is None:
        return {"status": "unavailable", "landmarks": [], "method": "none"}
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    try:
        with hands_api.hands.Hands(static_image_mode=True, max_num_hands=1, min_detection_confidence=0.5) as detector:
            result = detector.process(rgb)
    except Exception as exc:
        return _fallback(f"MediaPipe hand detection failed: {exc}")
    if not result.multi_hand_landmarks:
        return {"status": "not_detected", "landmarks": [], "method": "mediapipe"}
    points = [{"x": round(p.x, 6), "y": round(p.y, 6), "z": round(p.z, 6)} for p in result.multi_hand_landmarks[0].landmark]
    return {"status": "ok", "landmarks": points, "method": "mediapipe"}


def landmark_zone(landmarks: list[dict[str, float]]) -> str | None:
    """Map the landmark centroid to the current 3x3 Digital Twin coordinate grid."""
    if not landmarks:
        return None
    x = sum(p["x"] for p in landmarks) / len(landmarks)
    y = sum(p["y"] for p in landmarks) / len(landmarks)
    col = min(2, max(0, int(x * 3)))
    row = min(2, max(0, int(y * 3)))
    return f"hand-zone-{row * 3 + col + 1:02d}"
