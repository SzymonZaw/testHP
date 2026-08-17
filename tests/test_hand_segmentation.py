from pathlib import Path

from backend.hand_segmentation import detect_hand_landmarks, landmark_zone


def test_missing_image_is_safe(tmp_path: Path):
    result = detect_hand_landmarks(tmp_path / "missing.jpg")
    assert result["status"] == "unavailable"


def test_landmark_zone_is_deterministic():
    points = [{"x": 0.5, "y": 0.5, "z": 0.0}] * 21
    assert landmark_zone(points) == "hand-zone-05"
    assert landmark_zone([]) is None
