from backend.hand_surface import build_registration, normalize_landmarks, validate_landmarks


def test_normalize_mediapipe_landmarks():
    points = [{"x": 0.25, "y": 0.75, "z": -0.1}] * 21
    landmarks = normalize_landmarks(points)
    assert len(landmarks) == 21
    assert landmarks[0].landmark_id == "mp-00"
    assert landmarks[0].point.as_tuple() == (0.25, 0.75, -0.1)


def test_registration_accepts_partial_landmarks():
    registration = build_registration(
        view="front",
        landmarks=[{"x": 0.5, "y": 0.5, "z": 0.0}] * 4,
        method="mediapipe",
        quality=0.92,
    )
    assert registration.status == "registered"
    assert registration.coordinate_system == "hand-surface-v1"
    assert registration.method == "mediapipe"
    assert registration.quality == 0.92


def test_invalid_landmark_is_marked_without_crashing():
    registration = build_registration(view="front", landmarks=[{"x": 1.4, "y": 0.5}])
    assert registration.status == "invalid"
    assert validate_landmarks(registration.landmarks)


def test_unknown_view_is_normalized():
    registration = build_registration(view="diagonal")
    assert registration.view == "unknown"
    assert registration.status == "unregistered"
