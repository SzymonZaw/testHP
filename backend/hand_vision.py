from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
import math

from PIL import Image, ImageStat


IMAGE_FORMATS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}

ZONE_LANDMARKS = {
    "wrist": (0,),
    "thumb": (1, 2, 3, 4),
    "index": (5, 6, 7, 8),
    "middle": (9, 10, 11, 12),
    "ring": (13, 14, 15, 16),
    "little": (17, 18, 19, 20),
}

FINGER_TIPS = {"thumb": 4, "index": 8, "middle": 12, "ring": 16, "little": 20}
FINGER_BASES = {"thumb": 1, "index": 5, "middle": 9, "ring": 13, "little": 17}


@dataclass(frozen=True)
class Landmark:
    index: int
    x: float
    y: float
    z: float


@dataclass(frozen=True)
class ImageQuality:
    width: int
    height: int
    mean_brightness: float
    contrast: float


class HandVisionError(RuntimeError):
    pass


def _distance(a: Landmark, b: Landmark) -> float:
    return math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2 + (a.z - b.z) ** 2)


def _image_quality(image: Image.Image) -> ImageQuality:
    rgb = image.convert("RGB")
    stat = ImageStat.Stat(rgb)
    brightness = sum(stat.mean) / 3.0
    contrast = sum(stat.stddev) / 3.0
    return ImageQuality(rgb.width, rgb.height, round(brightness, 4), round(contrast, 4))


def _mediapipe_hands():
    """Load Hands across MediaPipe package layouts.

    MediaPipe 0.10.35 no longer exposes ``mp.solutions`` at the top level,
    while older releases do. The internal solutions module is kept as a
    compatibility path when available.
    """
    try:
        import mediapipe as mp
        if hasattr(mp, "solutions"):
            return mp.solutions.hands
    except Exception as exc:
        raise HandVisionError("MediaPipe could not be imported.") from exc

    try:
        from mediapipe.python.solutions import hands
        return hands
    except Exception as exc:
        raise HandVisionError(
            "MediaPipe Hands is unavailable in this installation. "
            "The installed package exposes the Tasks API but not the legacy Hands solution. "
            "Use a MediaPipe build that provides mediapipe.python.solutions.hands, "
            "or add a Tasks HandLandmarker adapter with its .task model asset."
        ) from exc


def _landmarks(hand_landmarks: Any) -> list[Landmark]:
    return [
        Landmark(i, float(point.x), float(point.y), float(point.z))
        for i, point in enumerate(hand_landmarks.landmark)
    ]


def _bbox(points: list[Landmark]) -> dict[str, float]:
    xs = [p.x for p in points]
    ys = [p.y for p in points]
    return {
        "min_x": round(min(xs), 6),
        "max_x": round(max(xs), 6),
        "min_y": round(min(ys), 6),
        "max_y": round(max(ys), 6),
        "width": round(max(xs) - min(xs), 6),
        "height": round(max(ys) - min(ys), 6),
        "area_ratio": round(max(0.0, max(xs) - min(xs)) * max(0.0, max(ys) - min(ys)), 6),
    }


def _zone_measurements(points: list[Landmark]) -> dict[str, dict[str, float]]:
    result: dict[str, dict[str, float]] = {}
    for zone, indices in ZONE_LANDMARKS.items():
        selected = [points[i] for i in indices if i < len(points)]
        if not selected:
            continue
        result[zone] = {
            "centroid_x": round(sum(p.x for p in selected) / len(selected), 6),
            "centroid_y": round(sum(p.y for p in selected) / len(selected), 6),
            "span_x": round(max(p.x for p in selected) - min(p.x for p in selected), 6),
            "span_y": round(max(p.y for p in selected) - min(p.y for p in selected), 6),
        }
    for finger, tip_idx in FINGER_TIPS.items():
        base_idx = FINGER_BASES[finger]
        if tip_idx < len(points) and base_idx < len(points):
            result.setdefault(finger, {})["centerline_length_3d_norm"] = round(_distance(points[base_idx], points[tip_idx]), 6)
    return result


def analyze_image(path: Path, max_hands: int = 2) -> dict[str, Any]:
    path = Path(path)
    if path.suffix.lower() not in IMAGE_FORMATS:
        raise HandVisionError(f"Unsupported hand image format: {path.suffix}")
    try:
        with Image.open(path) as image:
            quality = _image_quality(image)
            rgb = image.convert("RGB")
            pixels = __import__("numpy").ascontiguousarray(rgb)
    except Exception as exc:
        raise HandVisionError(f"Could not read image: {path}") from exc

    hands = _mediapipe_hands()
    detections: list[dict[str, Any]] = []
    with hands.Hands(
        static_image_mode=True,
        max_num_hands=max_hands,
        model_complexity=1,
        min_detection_confidence=0.5,
    ) as detector:
        result = detector.process(pixels)

    handedness = result.multi_handedness or []
    landmark_sets = result.multi_hand_landmarks or []
    for idx, hand_landmarks in enumerate(landmark_sets):
        points = _landmarks(hand_landmarks)
        label = "unknown"
        score = None
        if idx < len(handedness) and handedness[idx].classification:
            cls = handedness[idx].classification[0]
            label = str(cls.label).lower()
            score = round(float(cls.score), 6)
        detections.append({
            "hand_index": idx,
            "laterality": label if label in {"left", "right"} else "unknown",
            "handedness_confidence": score,
            "bbox": _bbox(points),
            "landmarks": [asdict(p) for p in points],
            "zones": _zone_measurements(points),
        })

    return {
        "source_file": str(path),
        "image": asdict(quality),
        "hand_count": len(detections),
        "hands": detections,
        "evidence_boundary": "measured visual geometry only; no diagnosis, age estimate or biological conclusion",
    }


def analyze_own_cohort(root: str | Path, max_hands: int = 2) -> dict[str, Any]:
    root = Path(root)
    files = sorted(p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in IMAGE_FORMATS)
    results: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    for path in files:
        try:
            results.append(analyze_image(path, max_hands=max_hands))
        except HandVisionError as exc:
            errors.append({"source_file": str(path), "error": str(exc)})
    return {
        "root": str(root),
        "files_found": len(files),
        "files_analyzed": len(results),
        "files_failed": len(errors),
        "results": results,
        "errors": errors,
        "evidence_boundary": "own_cohort vision analysis produces observations for geometry, image quality and hand detection; it does not infer disease or biological age",
    }


def observations_from_analysis(
    analysis: dict[str, Any],
    subject_id: str,
    session_id: str,
    timepoint: str,
    hand_id_prefix: str = "capture",
) -> list[dict[str, Any]]:
    observations: list[dict[str, Any]] = []
    for capture_index, result in enumerate(analysis.get("results", [])):
        image = result["image"]
        source = result["source_file"]
        hand_id = f"{hand_id_prefix}-{capture_index}"
        for metric, value, unit in (
            ("image_width", image["width"], "px"),
            ("image_height", image["height"], "px"),
            ("mean_brightness", image["mean_brightness"], "0-255"),
            ("image_contrast", image["contrast"], "0-255"),
            ("detected_hand_count", result["hand_count"], "count"),
        ):
            observations.append({
                "subject_id": subject_id,
                "session_id": session_id,
                "timepoint": timepoint,
                "hand_id": hand_id,
                "laterality": "unknown",
                "zone": "wrist",
                "observation_type": "image_quality" if metric.startswith("image_") or metric in {"mean_brightness", "image_contrast"} else "landmark_quality",
                "metric": metric,
                "value": value,
                "unit": unit,
                "source_file": source,
                "evidence_level": "observed",
            })
        for hand_index, hand in enumerate(result.get("hands", [])):
            concrete_hand_id = f"{hand_id}-hand-{hand_index}"
            bbox = hand["bbox"]
            observations.extend([
                {
                    "subject_id": subject_id, "session_id": session_id, "timepoint": timepoint,
                    "hand_id": concrete_hand_id, "laterality": hand["laterality"], "zone": "wrist",
                    "observation_type": "geometry", "metric": "bbox_area_ratio", "value": bbox["area_ratio"],
                    "unit": "normalized_area", "source_file": source, "confidence": hand.get("handedness_confidence"), "evidence_level": "observed",
                },
                {
                    "subject_id": subject_id, "session_id": session_id, "timepoint": timepoint,
                    "hand_id": concrete_hand_id, "laterality": hand["laterality"], "zone": "wrist",
                    "observation_type": "landmark_quality", "metric": "landmark_count", "value": len(hand.get("landmarks", [])),
                    "unit": "count", "source_file": source, "confidence": hand.get("handedness_confidence"), "evidence_level": "observed",
                },
            ])
            for zone, metrics in hand.get("zones", {}).items():
                for metric, value in metrics.items():
                    observations.append({
                        "subject_id": subject_id,
                        "session_id": session_id,
                        "timepoint": timepoint,
                        "hand_id": concrete_hand_id,
                        "laterality": hand["laterality"],
                        "zone": zone,
                        "observation_type": "geometry",
                        "metric": metric,
                        "value": value,
                        "unit": "normalized" if metric != "centerline_length_3d_norm" else "normalized_3d",
                        "source_file": source,
                        "confidence": hand.get("handedness_confidence"),
                        "evidence_level": "observed",
                    })
    return observations
