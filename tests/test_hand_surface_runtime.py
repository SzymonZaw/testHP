from backend.hand_surface_runtime import (
    CameraView,
    GeometryCalibration,
    ProjectionCandidate,
    SegmentationMask,
    SurfaceApplication,
    SurfaceAsset,
    build_runtime_manifest,
    deformation_distance,
    projection_readiness,
    reconstruction_readiness,
    select_projection_source,
    validate_surface_application,
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
    assert manifest["schema"] == "hand-surface-stages-11-16"
    assert manifest["coordinate_system"] == "hand-surface-v1"
    assert manifest["spatial_id"] == "hand"
    assert manifest["reconstruction_ready"] is False
    assert manifest["surface_ready"] is False
    assert manifest["surface_applied"] is False
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


def test_reconstruction_requires_two_registered_prepared_views():
    blocked = reconstruction_readiness(["front"], ["front"], "Palm")
    assert blocked.ready is False
    assert "at least 2 prepared views are required" in blocked.reasons
    ready = reconstruction_readiness(["front", "back"], ["front", "back"], "hand/palm")
    assert ready.ready is True
    assert ready.spatial_id == "hand/palm"


def test_reconstruction_rejects_registration_without_preparation():
    state = reconstruction_readiness(["front", "back"], ["front", "thumb"], "hand/palm")
    assert state.ready is False
    assert "registered views must also be prepared" in state.reasons


def test_surface_asset_must_match_target_before_application():
    surface = SurfaceAsset("surface-1", "hand/palm", "recon-1", source_views=("front", "back"), status="ready")
    applied = validate_surface_application(surface, "Palm")
    assert applied.applied is True
    mismatch = validate_surface_application(surface, "hand")
    assert mismatch.applied is False
    assert mismatch.reason == "surface spatial_id does not match model target"


def test_surface_application_is_explicit():
    application = SurfaceApplication("surface-1", "Palm", applied=True)
    assert application.spatial_id == "hand/palm"
    assert application.applied is True


def test_runtime_manifest_exposes_end_to_end_surface_state():
    surface = SurfaceAsset("surface-1", "hand/palm", "recon-1", source_views=("back", "front"), status="ready")
    application = SurfaceApplication("surface-1", "hand/palm", applied=True)
    manifest = build_runtime_manifest(
        spatial_id="Palm",
        prepared_views=["front", "back"],
        registered_views=["front", "back"],
        surface_asset=surface,
        application=application,
    )
    assert manifest["reconstruction_ready"] is True
    assert manifest["surface_ready"] is True
    assert manifest["surface_applied"] is True
    assert manifest["consistency"]["status"] == "consistent"


def test_deformation_distance_is_deterministic():
    assert deformation_distance((0, 0, 0), (3, 4, 0)) == 5.0
