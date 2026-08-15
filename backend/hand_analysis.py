from __future__ import annotations

from math import hypot
from pathlib import Path
from typing import Any

import numpy as np
from fastapi import HTTPException

from .app import IMAGE_FORMATS, RAW_ROOT, app

OWN_HAND_ROOT = RAW_ROOT / "hand" / "own_cohort"

# MediaPipe landmark indices. The grouping is intentionally anatomical/technical,
# not a disease classifier.
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
    return hypot(float(a.x) - float(b.x), float(a.y) - float(b.y))


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


def _image_quality(path: Path) -> dict[str, Any]:
    try:
        from PIL import Image, ImageStat
        with Image.open(path) as image:
            rgb = image.convert("RGB")
            stat = ImageStat.Stat(rgb)
            brightness = sum(stat.mean) / 3.0
            return {
                "width": int(rgb.width),
                "height": int(rgb.height),
                "mean_brightness": round(float(brightness), 4),
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
        return {"file": path.name, "status": "error", "error": f"Hand model failed: {exc}", "quality": quality}

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

        fingers = {}
        for name, indices in FINGER_PATHS.items():
            length = sum(_distance(landmarks[a], landmarks[b]) for a, b in zip(indices, indices[1:]))
            fingers[name] = round(length, 6)

        palm_length = _distance(landmarks[0], landmarks[9])
        palm_width = _distance(landmarks[5], landmarks[17])
        hand_span = max(_distance(landmarks[4], landmarks[20]), _distance(landmarks[8], landmarks[20]))
        landmark_visibility = round(sum(float(getattr(x, "visibility", 1.0)) for x in landmarks) / 21, 4)

        zones = []
        for zone, indices in ZONE_LANDMARKS.items():
            confidence = _zone_confidence(landmarks, indices)
            zones.append({
                "id": zone,
                "landmark_count": len(indices),
                "confidence": confidence,
                "review_priority": _priority(confidence),
                "interpretation": "technical visibility/landmark quality only",
            })

        hand_record: dict[str, Any] = {
            "index": hand_index,
            "handedness": label,
            "handedness_confidence": handedness_score,
            "landmark_count": len(landmarks),
            "landmarks_2d": [_landmark_dict(x) for x in landmarks],
            "geometry_normalized": {
                "palm_length": round(palm_length, 6),
                "palm_width": round(palm_width, 6),
                "hand_span": round(hand_span, 6),
                "finger_lengths": fingers,
                "palm_aspect_ratio": round(palm_length / palm_width, 6) if palm_width else None,
            },
            "zones": zones,
            "technical_quality": {
                "mean_landmark_visibility": landmark_visibility,
                "review_priority": _priority(landmark_visibility),
            },
        }
        if hand_index < len(world):
            hand_record["landmarks_3d_world"] = [_landmark_dict(x) for x in world[hand_index].landmark]
        output["hands"].append(hand_record)

    return output


def _empty_response(reason: str) -> dict[str, Any]:
    return {
        "status": "insufficient_data",
        "stage": "H0",
        "source": "own_cohort",
        "digital_twin": None,
        "observations": [],
        "limitations": [reason],
    }


def run_hand_analysis() -> dict[str, Any]:
    files = sorted(p for p in OWN_HAND_ROOT.rglob("*") if p.is_file() and p.suffix.lower() in IMAGE_FORMATS) if OWN_HAND_ROOT.exists() else []
    if not files:
        return _empty_response("No supported images are available in data/raw/hand/own_cohort.")

    try:
        import mediapipe as mp
        hands_api = mp.solutions.hands
    except Exception as exc:
        return _empty_response(f"MediaPipe is not available: {exc}")

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
    zones = []
    for hand in all_hands:
        for zone in hand.get("zones", []):
            zones.append({**zone, "hand_index": hand.get("index"), "handedness": hand.get("handedness")})

    # v0 digital twin: a normalized landmark representation plus stable anatomical
    # zones. It is a geometry/observation layer, not a medical model.
    twin = None
    if all_hands:
        twin = {
            "version": "v0",
            "representation": "MediaPipe 21-landmark normalized hand geometry",
            "hands": len(all_hands),
            "zones": ["wrist", "palm", "thumb", "index", "middle", "ring", "little"],
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
        observations.append({
            "type": "geometry",
            "level": "hand",
            "text": "Computed normalized palm, span and finger geometry for detected hands. These are measured geometric observations, not health conclusions.",
        })
        observations.append({
            "type": "spatial_zones",
            "level": "region",
            "text": "Mapped detected landmarks to wrist, palm and five finger zones for later ROI selection.",
        })

    limitations = [
        "Current v0 uses RGB images only; it does not infer tissue, cell or molecular state.",
        "Review priority indicates landmark/visibility quality, not disease risk.",
        "No biological or pathological conclusion is produced from hand geometry alone.",
        "A true longitudinal digital twin will require subject identity, timepoint and acquisition metadata.",
    ]
    if len(detected_images) < len(files):
        limitations.append("Some input images did not yield a detectable hand and require acquisition or segmentation review.")

    return {
        "status": "ready" if all_hands else "review",
        "stage": "H7",
        "source": "own_cohort",
        "files": len(files),
        "images_with_hands": len(detected_images),
        "hand_instances": len(all_hands),
        "observations": observations,
        "digital_twin": twin,
        "zones": zones,
        "images": image_results,
        "limitations": limitations,
    }


@app.get("/api/hand/analysis")
def hand_analysis():
    return run_hand_analysis()
