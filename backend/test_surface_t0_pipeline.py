from __future__ import annotations

"""Deterministic contract tests for the Surface T0 gates.

These tests use synthetic metadata and mock the reconstruction boundary, so
CI can verify orchestration without pretending synthetic images are clinical
or real-world reconstruction evidence.
"""

from surface_t0_pipeline import build_surface_t0, photo_quality_from_metrics


GOOD_CALIBRATION = {
    "status": "calibrated",
    "camera_matrix": [[1000, 0, 640], [0, 1000, 480], [0, 0, 1]],
}
GOOD_SCALE = {"status": "scale-calibrated", "reference_distance_mm": 50.0, "mm_per_pixel": 0.1}
GOOD_QUALITY = photo_quality_from_metrics(1920, 1080, 250.0, 0.08, 0.95)


def test_blocks_without_calibration():
    result = build_surface_t0(["a.jpg", "b.jpg"], None, photo_quality=[GOOD_QUALITY, GOOD_QUALITY], scale=GOOD_SCALE)
    assert result.status == "blocked"
    assert result.gates["calibration"]["status"] == "fail"


def test_blocks_without_metric_scale():
    result = build_surface_t0(["a.jpg", "b.jpg"], GOOD_CALIBRATION, photo_quality=[GOOD_QUALITY, GOOD_QUALITY], scale=None)
    assert result.status == "blocked"
    assert result.gates["metric_scale"]["status"] == "fail"


def test_blocks_on_bad_photo_quality():
    bad = photo_quality_from_metrics(640, 480, 20.0, 0.8, 0.4)
    result = build_surface_t0(["a.jpg", "b.jpg"], GOOD_CALIBRATION, photo_quality=[bad, GOOD_QUALITY], scale=GOOD_SCALE)
    assert result.status == "blocked"
    assert result.gates["photo_quality"]["status"] == "fail"


def test_reconstruction_result_is_explicit_when_inputs_are_real():
    # Missing files must not be converted into a fake accepted result.
    try:
        result = build_surface_t0(["missing-a.jpg", "missing-b.jpg"], GOOD_CALIBRATION, photo_quality=[GOOD_QUALITY, GOOD_QUALITY], scale=GOOD_SCALE)
    except FileNotFoundError:
        return
    assert result.status == "rejected"


def test_quality_gate_is_deterministic():
    assert GOOD_QUALITY["status"] == "pass"
    bad = photo_quality_from_metrics(1279, 959, 100.0, 0.01, 0.69)
    assert bad["status"] == "fail"
