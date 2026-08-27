from __future__ import annotations

"""Dense surface/reprojection validation boundary.

A generated surface is explicitly research geometry, not anatomical truth.
Promotion to Surface T0 requires measured reprojection quality.
"""

from pathlib import Path
from typing import Any


def reconstruct_dense_surface(sparse: dict[str, Any], *, output_path: str) -> dict[str, Any]:
    if sparse.get("status") != "reconstructed" or sparse.get("point_count", 0) < 8:
        return {"status": "blocked", "reason": "validated sparse reconstruction required"}
    points = sparse.get("points_3d") or []
    try:
        import numpy as np  # type: ignore
        from scipy.spatial import ConvexHull  # type: ignore
    except ImportError:
        return {"status": "dependency-missing", "required": ["numpy", "scipy"]}
    arr = np.asarray(points, dtype=float)
    if arr.ndim != 2 or arr.shape[1] != 3 or len(arr) < 8:
        return {"status": "blocked", "reason": "at least 8 Nx3 points required"}
    hull = ConvexHull(arr)
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        for p in arr:
            f.write("v %.9g %.9g %.9g\n" % tuple(p))
        for tri in hull.simplices:
            f.write("f %d %d %d\n" % tuple(int(i) + 1 for i in tri))
    return {"status": "surface-generated", "method": "convex-hull-of-sparse-points-v1", "geometry_reference": str(out), "vertex_count": int(len(arr)), "face_count": int(len(hull.simplices)), "volume": float(hull.volume), "surface_area": float(hull.area), "anatomical_quality": "not-validated"}


def validate_reprojection(*, projected_points: list[list[float]], observed_points: list[list[float]], max_rmse_px: float = 3.0) -> dict[str, Any]:
    if len(projected_points) != len(observed_points) or not projected_points:
        return {"status": "fail", "reason": "matching non-empty point sets required"}
    try:
        import numpy as np  # type: ignore
    except ImportError:
        return {"status": "dependency-missing", "required": ["numpy"]}
    a = np.asarray(projected_points, dtype=float)
    b = np.asarray(observed_points, dtype=float)
    if a.shape != b.shape or a.ndim != 2 or a.shape[1] != 2:
        raise ValueError("projected and observed points must both be Nx2")
    errors = np.linalg.norm(a - b, axis=1)
    rmse = float(np.sqrt(np.mean(errors ** 2)))
    return {"status": "pass" if rmse <= max_rmse_px else "fail", "rmse_px": rmse, "max_error_px": float(np.max(errors)), "threshold_px": max_rmse_px, "sample_count": int(len(errors))}
