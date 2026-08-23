from backend.hand_surface_runtime import (
    CameraView,
    GeometryCalibration,
    ProjectionCandidate,
    SegmentationMask,
    build_runtime_manifest,
    deformation_distance,
    projection_readiness,
    select_projection_source,
)


def test_projection_requires_segmentation_and_camera_registration():
    assert projection_readiness([], []) == "needs-segmentation"
    mask = SegmentationMask("front", 2048, 2048, 0.45, confidence=0.9)
    assert projection_readiness([mask], []) == "needs-camera-registration"
    camera = CameraView("front", "front", (0, 0, 2), (0, 0, 0))
    assert projection_readiness([mask], [camera]) == "ready-for-surface-projection"


def test_projection_selects_highest_weighted_candidate():
    candidates = [
        ProjectionCandidate("p1", "front", "front", 0.8, 0.4, 0.8),
        ProjectionCandidate("p1", "side", "side_left", 0.3, 0.8, 0.95),
    ]
    result = select_projection_source(candidates)
    assert result is not None
    assert result["asset_id"] == "front"
    assert result["method"] == "weighted-multi-view-v1"


def test_geometry_calibration_is_explicit_and_validated():
    geometry = GeometryCalibration(palm_width=1.2, palm_length=1.1, finger_spread=0.95, thumb_angle=12)
    assert geometry.validate() == []
    assert GeometryCalibration(palm_width=0).validate()


def test_runtime_manifest_keeps_research_boundary():
    manifest = build_runtime_manifest()
    assert manifest["schema"] == "hand-surface-stages-16-19"
    assert manifest["coordinate_system"] == "hand-surface-v1"
    assert manifest["spatial_id"] == "hand"
    assert manifest["provenance"]


def test_runtime_projection_is_scoped_to_target():
    mask = SegmentationMask("front", 2048, 2048, 0.45, confidence=0.9, spatial_id="Palm")
    camera = CameraView("front", "front", (0, 0, 2), (0, 0, 0), spatial_id="hand/palm")
    assert projection_readiness([mask], [camera], "hand/palm") == "ready-for-surface-projection"
    assert projection_readiness([mask], [camera], "hand") == "needs-segmentation"


def test_projection_candidate_ignores_other_target():
    candidates = [
        ProjectionCandidate("p1", "wrong", "front", 1.0, 0.1, 1.0, spatial_id="hand"),
        ProjectionCandidate("p1", "right", "front", 0.8, 0.4, 0.8, spatial_id="hand/palm"),
    ]
    result = select_projection_source(candidates, "hand/palm")
    assert result["asset_id"] == "right"
    assert result["spatial_id"] == "hand/palm"


def test_deformation_distance_is_deterministic():
    assert deformation_distance((0, 0, 0), (3, 4, 0)) == 5.0
