from __future__ import annotations

from math import atan2, degrees, hypot, sqrt
from pathlib import Path
from typing import Any

import numpy as np

from .app import IMAGE_FORMATS, RAW_ROOT, app

OWN_HAND_ROOT = RAW_ROOT / "hand" / "own_cohort"

ZONE_LANDMARKS = {
    "wrist": [0],
    "palm": [0, 1, 5, 9, 13, 17],
    "thumb": [1, 2, 3, 4],
    "index": [5, 6, 7, 8],
    "middle": [9, 10, 11, 12],
    "ring": [13, 14, 15, 16],
    "little": [17, 18, 19, 20],
}

FINGER_PATHS = {
    "thumb": [1, 2, 3, 4],
    "index": [5, 6, 7, 8],
    "middle": [9, 10, 11, 12],
    "ring": [13, 14, 15, 16],
    "little": [17, 18, 19, 20],
}


def _distance(a: Any, b: Any) -> float:
    """Normalized 2D landmark distance used only for image geometry."""
    return hypot(float(a.x) - float(b.x), float(a.y) - float(b.y))


def _distance_3d(a: Any, b: Any) -> float:
    """World-landmark distance when MediaPipe provides a 3D coordinate frame."""
    return sqrt(
        (float(a.x) - float(b.x)) ** 2
        + (float(a.y) - float(b.y)) ** 2
        + (float(a.z) - float(b.z)) ** 2
    )


def _landmark_dict(lm: Any) -> dict[str, float]:
    return {
        "x": round(float(lm.x), 6),
        "y": round(float(lm.y), 6),
        "z": round(float(lm.z), 6),
        "visibility": round(float(getattr(lm, "visibility", 1.0)), 6),
    }


def _zone_confidence(landmarks: list[Any], indices: list[int]) -> float:
    values = [float(getattr(landmarks[i], "visibility", 1.0)) for i in indices]
    return round(sum(values) / len(values), 4) if values else 0.0


def _priority(confidence: float) -> str:
    if confidence < 0.65:
        return "high"
    if confidence < 0.85:
        return "review"
    return "normal"


def _orientation_degrees(landmarks: list[Any]) -> float:
    """Orientation of the wrist-to-middle-MCP axis in image coordinates."""
    wrist = landmarks[0]
    middle_mcp = landmarks[9]
    return round(degrees(atan2(float(middle_mcp.y) - float(wrist.y), float(middle_mcp.x) - float(wrist.x))), 3)


def _image_quality(path: Path) -> dict[str, Any]:
    try:
        from PIL import Image, ImageStat
        with Image.open(path) as image:
            rgb = image.convert("RGB")
            stat = ImageStat.Stat(rgb)
            return {
                "width": int(rgb.width),
                "height": int(rgb.height),
                "mean_brightness": round(float(sum(stat.mean) / 3.0), 4),
                "mean_rgb": [round(float(x), 4) for x in stat.mean],
            }
    except Exception as exc:
        return {"error": str(exc)}


def _analyze_image(path: Path, hands: Any) -> dict[str, Any]:
    try:
        from PIL import Image
        with Image.open(path) as image:
            rgb = np.asarray(image.convert("RGB"))
    except Exception as exc:
        return {"file": path.name, "status": "error", "error": f"Could not read image: {exc}"}

    quality = _image_quality(path)
    try:
        result = hands.process(rgb)
    except Exception as exc:
        return {
            "file": path.name,
            "status": "error",
            "error": f"Hand model failed: {exc}",
            "quality": quality,
        }

    detected = len(result.multi_hand_landmarks or [])
    output: dict[str, Any] = {
        "file": path.name,
        "status": "ok" if detected else "no_hand_detected",
        "quality": quality,
        "hands_detected": detected,
        "hands": [],
    }
    handedness = result.multi_handedness or []
    world = result.multi_hand_world_landmarks or []

    for hand_index, landmarks_obj in enumerate(result.multi_hand_landmarks or []):
        landmarks = list(landmarks_obj.landmark)
        label = "unknown"
        handedness_score = None
        if hand_index < len(handedness) and handedness[hand_index].classification:
            cls = handedness[hand_index].classification[0]
            label = str(cls.label)
            handedness_score = round(float(cls.score), 4)

        fingers_2d = {}
        for name, indices in FINGER_PATHS.items():
            fingers_2d[name] = round(
                sum(_distance(landmarks[a], landmarks[b]) for a, b in zip(indices, indices[1:])),
                6,
            )

        palm_length = _distance(landmarks[0], landmarks[9])
        palm_width = _distance(landmarks[5], landmarks[17])
        hand_span = max(
            _distance(landmarks[4], landmarks[20]),
            _distance(landmarks[8], landmarks[20]),
        )
        landmark_visibility = round(
            sum(float(getattr(x, "visibility", 1.0)) for x in landmarks) / 21,
            4,
        )

        geometry: dict[str, Any] = {
            "coordinate_space": "normalized_image_2d",
            "palm_length": round(palm_length, 6),
            "palm_width": round(palm_width, 6),
            "hand_span": round(hand_span, 6),
            "finger_lengths": fingers_2d,
            "palm_aspect_ratio": round(palm_length / palm_width, 6) if palm_width else None,
            "orientation_degrees": _orientation_degrees(landmarks),
        }

        hand_record: dict[str, Any] = {
            "index": hand_index,
            "handedness": label,
            "handedness_confidence": handedness_score,
            "landmark_count": len(landmarks),
            "landmarks_2d": [_landmark_dict(x) for x in landmarks],
            "geometry_normalized": geometry,
            "zones": [],
            "technical_quality": {
                "mean_landmark_visibility": landmark_visibility,
                "review_priority": _priority(landmark_visibility),
            },
        }

        if hand_index < len(world):
            world_landmarks = list(world[hand_index].landmark)
            fingers_3d = {
                name: round(
                    sum(
                        _distance_3d(world_landmarks[a], world_landmarks[b])
                        for a, b in zip(indices, indices[1:])
                    ),
                    6,
                )
                for name, indices in FINGER_PATHS.items()
            }
            palm_length_3d = _distance_3d(world_landmarks[0], world_landmarks[9])
            palm_width_3d = _distance_3d(world_landmarks[5], world_landmarks[17])
            hand_span_3d = max(
                _distance_3d(world_landmarks[4], world_landmarks[20]),
                _distance_3d(world_landmarks[8], world_landmarks[20]),
            )
            hand_record["landmarks_3d_world"] = [_landmark_dict(x) for x in world_landmarks]
            hand_record["geometry_3d"] = {
                "coordinate_space": "mediapipe_world_landmarks",
                "palm_length": round(palm_length_3d, 6),
                "palm_width": round(palm_width_3d, 6),
                "hand_span": round(hand_span_3d, 6),
                "finger_lengths": fingers_3d,
                "palm_aspect_ratio": round(palm_length_3d / palm_width_3d, 6) if palm_width_3d else None,
                "units": "MediaPipe world-landmark coordinate units; not calibrated millimetres",
            }

        for zone, indices in ZONE_LANDMARKS.items():
            confidence = _zone_confidence(landmarks, indices)
            hand_record["zones"].append(
                {
                    "id": zone,
                    "landmark_count": len(indices),
                    "confidence": confidence,
                    "review_priority": _priority(confidence),
                    "interpretation": "technical visibility/landmark quality only",
                }
            )

        output["hands"].append(hand_record)

    return output


def _stages(all_hands: bool, detected_images: int, total_images: int) -> list[dict[str, str]]:
    detected = bool(all_hands)
    return [
        {"id": "H0", "name": "Input validation", "purpose": "Check own-cohort image availability and readability.", "status": "completed" if total_images else "blocked"},
        {"id": "H1", "name": "Hand detection", "purpose": "Locate one or more hands in each image.", "status": "completed" if detected_images else "review"},
        {"id": "H2", "name": "Landmarks", "purpose": "Estimate 21 anatomical hand landmarks.", "status": "completed" if detected else "blocked"},
        {"id": "H3", "name": "Geometry", "purpose": "Measure normalized 2D geometry and available MediaPipe world geometry.", "status": "completed" if detected else "blocked"},
        {"id": "H4", "name": "Zones", "purpose": "Map landmarks to stable anatomical regions.", "status": "completed" if detected else "blocked"},
        {"id": "H5", "name": "Digital Twin v0", "purpose": "Create a normalized spatial representation for later evidence.", "status": "completed" if detected else "blocked"},
        {"id": "H6", "name": "Observation mapping", "purpose": "Attach measured geometry and quality to hand regions.", "status": "completed" if detected else "blocked"},
        {"id": "H7", "name": "ROI / attention", "purpose": "Identify regions needing technical review before deeper analysis.", "status": "completed" if detected else "blocked"},
        {"id": "H8", "name": "Evidence boundary", "purpose": "Separate measured observations from future biological interpretation.", "status": "completed" if detected else "blocked"},
    ]


def _zone_summary(zones: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[float]] = {}
    for zone in zones:
        grouped.setdefault(str(zone.get("id")), []).append(float(zone.get("confidence", 0.0)))
    summary = []
    for zone_id, values in grouped.items():
        confidence = round(sum(values) / len(values), 4)
        summary.append(
            {
                "id": zone_id,
                "observations": len(values),
                "mean_confidence": confidence,
                "review_priority": _priority(confidence),
                "purpose": "technical ROI prioritization only",
            }
        )
    return sorted(summary, key=lambda x: (x["review_priority"] != "high", x["mean_confidence"]))


def _empty_response(reason: str) -> dict[str, Any]:
    return {
        "status": "insufficient_data",
        "stage": "H0",
        "source": "own_cohort",
        "files": 0,
        "images_with_hands": 0,
        "hand_instances": 0,
        "stages": _stages(False, 0, 0),
        "digital_twin": None,
        "observations": [],
        "zones": [],
        "zone_summary": [],
        "evidence_contract": {
            "observations": [],
            "interpretations": [],
            "medical_conclusions": [],
        },
        "limitations": [reason],
        "next_action": "Add at least one supported own-cohort hand image.",
    }


def run_hand_analysis() -> dict[str, Any]:
    files = (
        sorted(
            p
            for p in OWN_HAND_ROOT.rglob("*")
            if p.is_file() and p.suffix.lower() in IMAGE_FORMATS
        )
        if OWN_HAND_ROOT.exists()
        else []
    )
    if not files:
        return _empty_response("No supported images are available in data/raw/hand/own_cohort.")

    try:
        import mediapipe as mp
        hands_api = mp.solutions.hands
    except Exception as exc:
        result = _empty_response(f"MediaPipe is not available: {exc}")
        result["files"] = len(files)
        result["stages"] = _stages(False, 0, len(files))
        return result

    image_results = []
    with hands_api.Hands(
        static_image_mode=True,
        max_num_hands=2,
        model_complexity=1,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    ) as hands:
        for path in files:
            image_results.append(_analyze_image(path, hands))

    detected_images = [x for x in image_results if x.get("hands_detected", 0) > 0]
    all_hands = [h for image in image_results for h in image.get("hands", [])]
    zones = [
        {
            **zone,
            "hand_index": hand.get("index"),
            "handedness": hand.get("handedness"),
            "source_file": image.get("file"),
        }
        for image in image_results
        for hand in image.get("hands", [])
        for zone in hand.get("zones", [])
    ]
    zone_summary = _zone_summary(zones)

    twin = None
    if all_hands:
        twin = {
            "version": "v0",
            "representation": "MediaPipe 21-landmark normalized hand geometry",
            "hands": len(all_hands),
            "zones": list(ZONE_LANDMARKS),
            "coordinate_spaces": ["normalized_image_2d", "mediapipe_world_landmarks"],
            "purpose": "spatial index for later observations and ROI selection",
            "not_a_diagnosis": True,
        }

    observations = [
        {
            "type": "input_coverage",
            "level": "macro",
            "text": f"Analyzed {len(files)} own-cohort image file(s); {len(detected_images)} image(s) contained at least one detected hand.",
        },
        {
            "type": "hand_detection",
            "level": "hand",
            "text": f"Detected {len(all_hands)} hand instance(s) with 21 landmark points each in the current v0 routine.",
        },
    ]
    if all_hands:
        observations.extend(
            [
                {
                    "type": "geometry",
                    "level": "hand",
                    "text": "Computed normalized 2D palm, span, finger geometry and image orientation. Where MediaPipe world landmarks are available, 3D geometry is also reported in its native coordinate units.",
                },
                {
                    "type": "spatial_zones",
                    "level": "region",
                    "text": "Mapped detected landmarks to stable wrist, palm and finger zones for later ROI selection.",
                },
                {
                    "type": "technical_attention",
                    "level": "region",
                    "text": "Assigned technical review priority from landmark visibility; this is an acquisition/model-quality signal, not a disease signal.",
                },
            ]
        )

    limitations = [
        "Current v0 uses RGB images only; it does not infer tissue, cell or molecular state.",
        "3D values use MediaPipe world-landmark coordinates and are not calibrated physical millimetres.",
        "Review priority indicates landmark/visibility quality, not disease risk.",
        "No biological or pathological conclusion is produced from hand geometry alone.",
        "A true longitudinal digital twin will require subject identity, timepoint and acquisition metadata.",
    ]
    if len(detected_images) < len(files):
        limitations.append("Some input images did not yield a detectable hand and require acquisition or segmentation review.")

    return {
        "status": "ready" if all_hands else "review",
        "stage": "H8" if all_hands else "H1",
        "source": "own_cohort",
        "files": len(files),
        "images_with_hands": len(detected_images),
        "hand_instances": len(all_hands),
        "stages": _stages(bool(all_hands), len(detected_images), len(files)),
        "observations": observations,
        "digital_twin": twin,
        "zones": zones,
        "zone_summary": zone_summary,
        "evidence_contract": {
            "observations": [
                "image availability",
                "hand detection",
                "landmark coordinates",
                "normalized 2D geometry",
                "world-landmark 3D geometry when available",
                "orientation",
                "zone mapping",
                "technical visibility",
            ],
            "interpretations": ["ROI review priority based on technical visibility"],
            "medical_conclusions": [],
        },
        "limitations": limitations,
        "next_action": "Use the prioritized ROI as the input to the next hand-analysis layer; do not interpret it biologically yet.",
        "images": image_results,
    }


@app.get("/api/hand/analysis")
def hand_analysis():
    return run_hand_analysis()


@app.get("/api/hand/roi")
def hand_roi():
    result = run_hand_analysis()
    return {
        "status": result["status"],
        "stage": result["stage"],
        "source": result["source"],
        "zone_summary": result.get("zone_summary", []),
        "next_action": result.get("next_action", ""),
        "limitations": result.get("limitations", []),
    }
