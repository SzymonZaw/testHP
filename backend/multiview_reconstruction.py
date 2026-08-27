from __future__ import annotations

"""Research-grade multi-view reconstruction adapter.

Uses OpenCV when available. It creates an actual sparse 3-D point cloud from
registered multi-view observations; it never fabricates a dense hand mesh.
"""

from pathlib import Path
from typing import Any


def reconstruct_from_views(image_paths: list[str], calibration: dict[str, Any] | None = None) -> dict[str, Any]:
    if len(image_paths) < 2:
        raise ValueError("at least two views are required")
    try:
        import cv2  # type: ignore
        import numpy as np  # type: ignore
    except ImportError:
        return {"status": "dependency-missing", "method": "opencv-sfm", "required": ["opencv-python", "numpy"], "point_count": 0, "geometry_reference": None}

    images = []
    for raw in image_paths:
        p = Path(raw)
        if not p.is_file():
            raise FileNotFoundError(raw)
        image = cv2.imread(str(p), cv2.IMREAD_GRAYSCALE)
        if image is None:
            raise ValueError(f"cannot decode image: {raw}")
        images.append(image)

    detector = cv2.SIFT_create(nfeatures=4000)
    keypoints, descriptors = [], []
    for image in images:
        kp, des = detector.detectAndCompute(image, None)
        keypoints.append(kp)
        descriptors.append(des)

    matcher = cv2.BFMatcher(cv2.NORM_L2)
    pair = []
    for i in range(len(images) - 1):
        if descriptors[i] is None or descriptors[i + 1] is None:
            continue
        matches = matcher.knnMatch(descriptors[i], descriptors[i + 1], k=2)
        good = [m for m, n in matches if m.distance < 0.7 * n.distance]
        pair.append({"left": i, "right": i + 1, "matches": len(good)})

    if not pair or max(p["matches"] for p in pair) < 8:
        return {"status": "insufficient-correspondence", "method": "opencv-sfm", "pairs": pair, "point_count": 0, "geometry_reference": None}

    if not calibration or "camera_matrix" not in calibration:
        return {"status": "needs-calibration", "method": "opencv-sfm", "pairs": pair, "point_count": 0, "geometry_reference": None}

    K = np.asarray(calibration["camera_matrix"], dtype=np.float64)
    if K.shape != (3, 3):
        raise ValueError("camera_matrix must be 3x3")
    points_3d = []
    for i in range(len(images) - 1):
        if descriptors[i] is None or descriptors[i + 1] is None:
            continue
        matches = matcher.knnMatch(descriptors[i], descriptors[i + 1], k=2)
        good = [m for m, n in matches if m.distance < 0.7 * n.distance]
        if len(good) < 8:
            continue
        pts1 = np.float32([keypoints[i][m.queryIdx].pt for m in good])
        pts2 = np.float32([keypoints[i + 1][m.trainIdx].pt for m in good])
        E, mask = cv2.findEssentialMat(pts1, pts2, K, method=cv2.RANSAC, prob=0.999, threshold=1.0)
        if E is None:
            continue
        _, R, t, pose_mask = cv2.recoverPose(E, pts1, pts2, K)
        P1 = K @ np.hstack([np.eye(3), np.zeros((3, 1))])
        P2 = K @ np.hstack([R, t])
        valid = pose_mask.ravel() > 0
        if valid.sum() < 8:
            continue
        points = cv2.triangulatePoints(P1, P2, pts1[valid].T, pts2[valid].T)
        points /= points[3:4]
        points_3d.extend(points[:3].T.tolist())

    return {"status": "reconstructed" if points_3d else "no-triangulated-points", "method": "opencv-sfm-sparse", "pairs": pair, "point_count": len(points_3d), "points_3d": points_3d, "coordinate_system": "camera-derived-sparse-v1", "metric_scale": calibration.get("scale_reference")}
