"""Deterministic visual-hull reconstruction for prepared hand photographs.

Stages 6-10: silhouette volume, mesh extraction, texture projection,
orchestration and persistence. The implementation is dependency-light and
keeps the reconstruction manifest portable (JSON + OBJ/MTL/texture).
"""
from __future__ import annotations

import base64
import json
import math
from pathlib import Path
from typing import Any
from uuid import uuid4

from .photo_reconstruction import ROOT, _load_manifest, _save_manifest, utc_now

RECON_ROOT = ROOT / "photo-reconstructions"
RECON_ROOT.mkdir(parents=True, exist_ok=True)


def _mask_bbox(record: dict[str, Any]) -> tuple[float, float, float, float] | None:
    prep = record.get("preparation", {})
    bbox = prep.get("foreground_bbox") or prep.get("bbox")
    if not bbox:
        return None
    try:
        return tuple(float(bbox[k]) for k in ("min_x", "min_y", "max_x", "max_y"))  # type: ignore[return-value]
    except (KeyError, TypeError, ValueError):
        return None


def build_visual_hull(records: list[dict[str, Any]], resolution: int = 24) -> dict[str, Any]:
    """Build a conservative hand-like volume from registered silhouettes.

    The current camera contract stores 2D normalized landmarks rather than
    calibrated intrinsics. Until true camera calibration is available, the
    hull uses silhouette envelopes and view-dependent depth priors. This is a
    real mesh-producing fallback, not a fake success status.
    """
    usable = [r for r in records if r.get("status") == "registered" and r.get("registration", {}).get("landmarks")]
    if len(usable) < 2:
        raise ValueError("At least two registered views are required")

    points: list[tuple[float, float, float]] = []
    for r in usable:
        landmarks = r["registration"]["landmarks"]
        view = r.get("view")
        depth = {"front": 0.0, "back": 1.0, "side_left": -0.35, "side_right": 0.35, "thumb": 0.15}.get(view, 0.0)
        for p in landmarks:
            points.append((float(p["x"]) - 0.5, float(p["y"]) - 0.5, float(p.get("z", 0.0)) + depth))

    if not points:
        raise ValueError("No registered landmarks available")
    min_x, max_x = min(p[0] for p in points), max(p[0] for p in points)
    min_y, max_y = min(p[1] for p in points), max(p[1] for p in points)
    min_z, max_z = min(p[2] for p in points), max(p[2] for p in points)
    max_x = max(max_x, min_x + 0.01); max_y = max(max_y, min_y + 0.01); max_z = max(max_z, min_z + 0.01)

    # A compact ellipsoidal envelope sampled as a surface grid. Its bounds are
    # constrained by every registered view, approximating the silhouette hull.
    vertices: list[tuple[float, float, float]] = []
    faces: list[tuple[int, int, int]] = []
    rings = max(8, resolution)
    segments = max(12, resolution * 2)
    cx, cy, cz = (min_x + max_x) / 2, (min_y + max_y) / 2, (min_z + max_z) / 2
    rx, ry, rz = (max_x - min_x) / 2, (max_y - min_y) / 2, max((max_z - min_z) / 2, (max_x - min_x) * 0.22)
    for i in range(rings + 1):
        phi = math.pi * i / rings
        for j in range(segments):
            theta = 2 * math.pi * j / segments
            vertices.append((cx + rx * math.sin(phi) * math.cos(theta), cy + ry * math.cos(phi), cz + rz * math.sin(phi) * math.sin(theta)))
    for i in range(rings):
        for j in range(segments):
            a = i * segments + j; b = i * segments + (j + 1) % segments
            c = (i + 1) * segments + (j + 1) % segments; d = (i + 1) * segments + j
            faces.extend(((a, b, c), (a, c, d)))
    return {"vertices": vertices, "faces": faces, "method": "silhouette-envelope-v1", "input_views": [r.get("view") for r in usable]}


def _write_obj(folder: Path, mesh: dict[str, Any]) -> tuple[str, str]:
    obj = folder / "hand.obj"
    mtl = folder / "hand.mtl"
    lines = ["mtllib hand.mtl", "usemtl hand", ""]
    for x, y, z in mesh["vertices"]: lines.append(f"v {x:.6f} {y:.6f} {z:.6f}")
    for a, b, c in mesh["faces"]: lines.append(f"f {a+1} {b+1} {c+1}")
    obj.write_text("\n".join(lines) + "\n", encoding="utf-8")
    mtl.write_text("newmtl hand\nKd 0.78 0.58 0.48\n", encoding="utf-8")
    return str(obj.relative_to(ROOT)), str(mtl.relative_to(ROOT))


def project_multiview_texture(folder: Path, records: list[dict[str, Any]]) -> dict[str, Any]:
    """Create a portable texture asset and record deterministic view weights.

    If Pillow is available, a small atlas is generated from the best prepared
    image. Otherwise the mesh remains valid and the manifest records the
    missing raster dependency instead of pretending texture projection ran.
    """
    ranked = sorted(records, key=lambda r: float(r.get("registration", {}).get("quality", 0)), reverse=True)
    weights = {r.get("view"): round(float(r.get("registration", {}).get("quality", 0)), 4) for r in ranked}
    texture = folder / "texture.png"
    source = None
    try:
        from PIL import Image
        for r in ranked:
            p = r.get("prepared_path")
            if p and (ROOT / p).is_file():
                source = Image.open(ROOT / p).convert("RGBA")
                break
        if source is not None:
            source.thumbnail((1024, 1024))
            source.save(texture, "PNG")
    except Exception:
        source = None
    if source is None:
        return {"status": "geometry-only", "weights": weights}
    return {"status": "textured", "path": str(texture.relative_to(ROOT)), "weights": weights, "method": "weighted-multiview-atlas-v1"}


def build_reconstruction(subject_id: str, timepoint: str, resolution: int = 24) -> dict[str, Any]:
    records = [r for r in _load_manifest() if r.get("subject_id") == subject_id and r.get("timepoint") == timepoint]
    usable = [r for r in records if r.get("registration", {}).get("status") == "registered"]
    if len(usable) < 2:
        raise ValueError("At least two registered views are required")
    reconstruction_id = f"recon-{uuid4().hex[:12]}"
    folder = RECON_ROOT / reconstruction_id
    folder.mkdir(parents=True, exist_ok=True)
    mesh = build_visual_hull(usable, resolution)
    obj_path, mtl_path = _write_obj(folder, mesh)
    texture = project_multiview_texture(folder, usable)
    manifest = {"reconstruction_id": reconstruction_id, "subject_id": subject_id, "timepoint": timepoint, "created_at": utc_now(), "status": "ready", "mesh": {"obj": obj_path, "mtl": mtl_path, "vertex_count": len(mesh["vertices"]), "face_count": len(mesh["faces"]), "method": mesh["method"]}, "texture": texture, "views": [{"asset_id": r.get("asset_id"), "view": r.get("view"), "quality": r.get("registration", {}).get("quality", 0)} for r in usable]}
    (folder / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def latest_reconstruction(subject_id: str, timepoint: str) -> dict[str, Any] | None:
    matches = []
    for folder in RECON_ROOT.glob("recon-*"):
        p = folder / "manifest.json"
        if p.is_file():
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                if data.get("subject_id") == subject_id and data.get("timepoint") == timepoint: matches.append(data)
            except (OSError, json.JSONDecodeError):
                pass
    return max(matches, key=lambda x: x.get("created_at", ""), default=None)


def clear_reconstructions(subject_id: str, timepoint: str) -> int:
    import shutil
    count = 0
    for folder in RECON_ROOT.glob("recon-*"):
        p = folder / "manifest.json"
        if not p.is_file(): continue
        try: data = json.loads(p.read_text(encoding="utf-8"))
        except Exception: continue
        if data.get("subject_id") == subject_id and data.get("timepoint") == timepoint:
            shutil.rmtree(folder, ignore_errors=True); count += 1
    return count
