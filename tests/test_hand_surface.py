from backend.hand_surface import build_registration, build_surface_evidence, normalize_landmarks, validate_landmarks
from backend.hand_surface_pipeline import PreparedImage, ViewRegistration, build_surface_manifest
from backend.spatial_contract import canonical_spatial_id, same_spatial_target


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
    assert registration.spatial_id == "hand"


def test_invalid_landmark_is_marked_without_crashing():
    registration = build_registration(view="front", landmarks=[{"x": 1.4, "y": 0.5}])
    assert registration.status == "invalid"
    assert validate_landmarks(registration.landmarks)


def test_unknown_view_is_normalized():
    registration = build_registration(view="diagonal")
    assert registration.view == "unknown"
    assert registration.status == "unregistered"


def test_display_alias_resolves_to_canonical_spatial_id():
    assert canonical_spatial_id("Palm") == "hand/palm"
    assert canonical_spatial_id("Śródręcze") == "hand/palm"
    assert same_spatial_target("palm", "hand/palm")


def test_surface_evidence_keeps_selected_target():
    evidence = build_surface_evidence(
        asset_id="asset-1",
        subject_id="own_cohort",
        timepoint_id="T0",
        spatial_id="Palm",
        uri="prepared/front.jpg",
        view="front",
    )
    assert evidence.spatial_id == "hand/palm"


def test_manifest_uses_one_target_and_counts_unique_views():
    prepared = [
        PreparedImage("a", "front.jpg", "front.png", spatial_id="Palm", view="front"),
        PreparedImage("b", "back.jpg", "back.png", spatial_id="hand/palm", view="back"),
        PreparedImage("x", "other.jpg", "other.png", spatial_id="hand", view="thumb"),
    ]
    registrations = [
        ViewRegistration("a", "front", spatial_id="Palm", quality=0.9, landmarks=4),
        ViewRegistration("b", "back", spatial_id="hand/palm", quality=0.8, landmarks=4),
    ]
    manifest = build_surface_manifest(
        subject_id="own_cohort",
        timepoint="T0",
        spatial_id="hand/palm",
        prepared=prepared,
        registrations=registrations,
    )
    assert manifest["spatial_id"] == "hand/palm"
    assert manifest["counts"] == {"prepared": 2, "registered": 2, "expected": 5}
    assert manifest["prepared_views"] == ["back", "front"]
    assert manifest["registered_views"] == ["back", "front"]
    assert manifest["projection_status"] == "ready-for-worker"
