from __future__ import annotations

"""Camera calibration and metric-scale contracts for the hand surface pipeline.

Calibration is explicit: no synthetic/default intrinsics are accepted as a
real calibration. The numeric solver consumes chessboard observations produced
by an acquisition tool and returns OpenCV-compatible intrinsics.
"""

from typing import Any


def calibrate_from_chessboard(
    object_points: list[list[list[float]]],
    image_points: list[list[list[float]]],
    image_size: tuple[int, int],
) -> dict[str, Any]:
    if len(object_points) < 3 or len(object_points) != len(image_points):
        raise ValueError("at least three matching calibration views are required")
    try:
        import cv2  # type: ignore
        import numpy as np  # type: ignore
    except ImportError:
        return {"status": "dependency-missing", "required": ["opencv-python", "numpy"]}

    obj = [np.asarray(v, dtype=np.float32) for v in object_points]
    img = [np.asarray(v, dtype=np.float32) for v in image_points]
    if any(len(a) != len(b) for a, b in zip(obj, img)):
        raise ValueError("each calibration view must contain matching points")
    rms, camera_matrix, distortion, rvecs, tvecs = cv2.calibrateCamera(obj, img, image_size, None, None)
    return {
        "status": "calibrated",
        "camera_matrix": camera_matrix.tolist(),
        "distortion_coefficients": distortion.ravel().tolist(),
        "image_size": list(image_size),
        "rms_reprojection_error": float(rms),
        "calibration_method": "opencv-chessboard-v1",
        "view_count": len(obj),
        "extrinsics": [
            {"rvec": r.ravel().tolist(), "tvec": t.ravel().tolist()}
            for r, t in zip(rvecs, tvecs)
        ],
    }


def metric_scale_from_reference(
    measured_distance_px: float,
    reference_distance_mm: float,
) -> dict[str, Any]:
    if measured_distance_px <= 0 or reference_distance_mm <= 0:
        raise ValueError("reference distances must be positive")
    return {
        "status": "scale-calibrated",
        "reference_distance_mm": reference_distance_mm,
        "measured_distance_px": measured_distance_px,
        "mm_per_pixel": reference_distance_mm / measured_distance_px,
        "method": "known-reference-v1",
    }


def quality_gate(
    *,
    width: int,
    height: int,
    blur_score: float,
    exposure_fraction: float,
    hand_confidence: float,
    min_width: int = 1280,
    min_height: int = 960,
) -> dict[str, Any]:
    checks = {
        "resolution": width >= min_width and height >= min_height,
        "sharpness": blur_score > 100.0,
        "exposure": 0.01 <= exposure_fraction <= 0.20,
        "hand_detection": hand_confidence >= 0.70,
    }
    return {"status": "pass" if all(checks.values()) else "fail", "checks": checks}
