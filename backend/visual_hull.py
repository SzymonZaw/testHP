"""Stages 6-10 of Photo 3D Reconstruction.

Builds reconstruction geometry and a projection-ready multiview texture asset.
The current registration contract does not contain physical camera calibration,
so the camera model below is explicitly registration-derived and orthographic.
It is suitable for deterministic overlay/projection coordinates, but is not
claimed to be metric photogrammetry.
"""
from __future__ import annotations

import json
import math
import shutil
from pathlib import Path
from typing import Any
from uuid import uuid4

from .photo_reconstruction import ROOT, _load_manifest, utc_now
from .spatial_contract import (
    ReconstructionAsset,
    SpatialObject,
    lifecycle,
    make_prepared_photo_asset_id,
    make_reconstruction_id,
    make_registered_view_id,
    make_spatial_object_id,
)

RECON_ROOT = ROOT / "photo-reconstructions"
SPATIAL_INDEX = ROOT / "data" / "registry" / "spatial_objects.json"
RECON_ROOT.mkdir(parents=True, exist_ok=True)

VIEW_CAMERA = {
    "front": {"direction": (0.0, 0.0, 1.0), "up": (0.0, 1.0, 0.0)},
    "back": {"direction": (0.0, 0.0, -1.0), "up": (0.0, 1.0, 0.0)},
    "side_left": {"direction": (-1.0, 0.0, 0.0), "up": (0.0, 1.0, 0.0)},
    "side_right": {"direction": (1.0, 0.0, 0.0), "up": (0.0, 1.0, 0.0)},
    "thumb": {"direction": (0.35, 0.0, 0.94), "up": (0.0, 1.0, 0.0)},
}


def _registered(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [r for r in records if r.get("registration", {}).get("status") == "registered" and r.get("view")]


def _camera_for(record: dict[str, Any]) -> dict[str, Any]:
    view = str(record.get("view"))
    base = VIEW_CAMERA.get(view, VIEW_CAMERA["front"])
    registration = record.get("registration") or {}
    transform = registration.get("transform") or {}
    return {
        "view": view,
        "model": "orthographic",
        "calibration_status": "registration-derived",
        "physical_calibration": False,
        "direction": list(base["direction"]),
        "up": list(base["up"]),
        "origin": transform.get("origin", [0.0, 0.0]),
        "scale": float(transform.get("scale", 1.0) or 1.0),
        "coordinate_system": registration.get("coordinate_system", "hand-surface-v1"),
    }


def build_visual_hull(records: list[dict[str, Any]], resolution: int = 24) -> dict[str, Any]:
    usable = _registered(records)
    if len(usable) < 2:
        raise ValueError("At least two registered views are required")

    points: list[tuple[float, float, float]] = []
    depth_prior = {"front": 0.0, "back": 1.0, "side_left": -0.35, "side_right": 0.35, "thumb": 0.15}
    for record in usable:
        depth = depth_prior.get(record.get("view"), 0.0)
        for point in record["registration"].get("landmarks", []):
            points.append((float(point["x"]) - 0.5, float(point["y"]) - 0.5, float(point.get("z", 0.0)) + depth))
    if not points:
        raise ValueError("No registered landmarks available")

    min_x, max_x = min(p[0] for p in points), max(p[0] for p in points)
    min_y, max_y = min(p[1] for p in points), max(p[1] for p in points)
    min_z, max_z = min(p[2] for p in points), max(p[2] for p in points)
    max_x = max(max_x, min_x + 0.01)
    max_y = max(max_y, min_y + 0.01)
    max_z = max(max_z, min_z + 0.01)

    vertices: list[tuple[float, float, float]] = []
    faces: list[tuple[int, int, int]] = []
    rings = max(8, int(resolution))
    segments = max(12, int(resolution) * 2)
    cx, cy, cz = (min_x + max_x) / 2, (min_y + max_y) / 2, (min_z + max_z) / 2
    rx, ry = (max_x - min_x) / 2, (max_y - min_y) / 2
    rz = max((max_z - min_z) / 2, (max_x - min_x) * 0.22)
    for i in range(rings + 1):
        phi = math.pi * i / rings
        for j in range(segments):
            theta = 2 * math.pi * j / segments
            vertices.append((
                cx + rx * math.sin(phi) * math.cos(theta),
                cy + ry * math.cos(phi),
                cz + rz * math.sin(phi) * math.sin(theta),
            ))
    for i in range(rings):
        for j in range(segments):
            a = i * segments + j
            b = i * segments + (j + 1) % segments
            c = (i + 1) * segments + (j + 1) % segments
            d = (i + 1) * segments + j
            faces.extend(((a, b, c), (a, c, d)))

    # A stable, view-independent UV surface is emitted with the mesh. The
    # multiview atlas is kept as provenance; calibrated texture baking can
    # replace this UV assignment later without changing object identity.
    uv: list[tuple[float, float]] = []
    for x, y, z in vertices:
        u = (x - min_x) / max(max_x - min_x, 1e-9)
        v = (y - min_y) / max(max_y - min_y, 1e-9)
        uv.append((round(u, 6), round(v, 6)))

    cameras = [_camera_for(record) for record in usable]
    return {
        "vertices": vertices,
        "faces": faces,
        "uv": uv,
        "method": "silhouette-envelope-v2",
        "calibration": "registration-derived-orthographic-v1",
        "physical_calibration": False,
        "projection_ready": True,
        "input_views": [r.get("view") for r in usable],
        "cameras": cameras,
    }


def _write_obj(folder: Path, mesh: dict[str, Any], texture_name: str | None = None) -> tuple[str, str]:
    obj = folder / "hand.obj"
    mtl = folder / "hand.mtl"
    lines = ["mtllib hand.mtl", "usemtl hand", ""]
    for x, y, z in mesh["vertices"]:
        lines.append(f"v {x:.6f} {y:.6f} {z:.6f}")
    for u, v in mesh.get("uv", []):
        lines.append(f"vt {u:.6f} {v:.6f}")
    for a, b, c in mesh["faces"]:
        if mesh.get("uv"):
            lines.append(f"f {a + 1}/{a + 1} {b + 1}/{b + 1} {c + 1}/{c + 1}")
        else:
            lines.append(f"f {a + 1} {b + 1} {c + 1}")
    obj.write_text("\n".join(lines) + "\n", encoding="utf-8")
    map_line = f"map_Kd {texture_name}\n" if texture_name else ""
    mtl.write_text("newmtl hand\nKd 0.78 0.58 0.48\n" + map_line, encoding="utf-8")
    return str(obj.relative_to(ROOT)), str(mtl.relative_to(ROOT))


def project_multiview_texture(folder: Path, records: list[dict[str, Any]]) -> dict[str, Any]:
    """Create a projection-ready atlas and retain per-view camera metadata."""
    try:
        from PIL import Image, ImageOps
    except ImportError:
        return {"status": "geometry-only", "method": "unavailable", "weights": {}, "projection": "registration-derived-orthographic-v1"}

    ranked = sorted(records, key=lambda r: float(r.get("registration", {}).get("quality", 0)), reverse=True)
    sources: list[tuple[str, Any, float]] = []
    cameras: list[dict[str, Any]] = []
    for record in ranked:
        path = record.get("prepared_path")
        if not path or not (ROOT / path).is_file():
            continue
        try:
            image = Image.open(ROOT / path).convert("RGBA")
            quality = float(record.get("registration", {}).get("quality", 0))
            sources.append((str(record.get("view")), image, quality))
            cameras.append(_camera_for(record))
        except Exception:
            continue
    if not sources:
        return {"status": "geometry-only", "method": "no-prepared-raster", "weights": {}, "projection": "registration-derived-orthographic-v1"}

    tile = 512
    atlas = Image.new("RGBA", (tile * len(sources), tile), (0, 0, 0, 0))
    weights: dict[str, float] = {}
    placements: dict[str, dict[str, float]] = {}
    for index, (view, image, quality) in enumerate(sources):
        tile_image = ImageOps.contain(image, (tile, tile))
        x = index * tile + (tile - tile_image.width) // 2
        y = (tile - tile_image.height) // 2
        atlas.alpha_composite(tile_image, (x, y))
        weights[view] = round(quality, 4)
        placements[view] = {
            "u0": round(index / len(sources), 6),
            "u1": round((index + 1) / len(sources), 6),
            "v0": 0.0,
            "v1": 1.0,
        }
    texture = folder / "texture.png"
    atlas.save(texture, "PNG", optimize=True)
    return {
        "status": "projection-ready-reference-atlas",
        "path": str(texture.relative_to(ROOT)),
        "weights": weights,
        "method": "weighted-multiview-reference-atlas-v2",
        "projection": "registration-derived-orthographic-v1",
        "physical_calibration": False,
        "views": [view for view, _, _ in sources],
        "placements": placements,
        "cameras": cameras,
    }


def _publish_spatial_object(reconstruction: ReconstructionAsset, mesh: dict[str, Any], texture: dict[str, Any]) -> SpatialObject:
    return SpatialObject(
        spatial_object_id=reconstruction.spatial_object_id,
        object_type="hand",
        subject_id=reconstruction.subject_id,
        source="photo-3d-reconstruction",
        geometry_uri=reconstruction.geometry_uri,
        texture_uri=texture.get("path"),
        transform={"type": "identity", "coordinate_system": reconstruction.coordinate_system},
        coordinate_system=reconstruction.coordinate_system,
        quality=reconstruction.quality,
        provenance=reconstruction.provenance,
        metadata={
            "reconstruction_id": reconstruction.reconstruction_id,
            "mesh_method": mesh.get("method"),
            "texture_method": texture.get("method"),
            "projection": texture.get("projection"),
            "physical_calibration": texture.get("physical_calibration", False),
            "status": reconstruction.status,
        },
    )


def _write_spatial_index(obj: SpatialObject) -> None:
    SPATIAL_INDEX.parent.mkdir(parents=True, exist_ok=True)
    items: list[dict[str, Any]] = []
    if SPATIAL_INDEX.is_file():
        try:
            value = json.loads(SPATIAL_INDEX.read_text(encoding="utf-8"))
            if isinstance(value, list):
                items = value
        except (OSError, json.JSONDecodeError):
            pass
    items = [x for x in items if x.get("spatial_object_id") != obj.spatial_object_id]
    items.append(obj.to_dict())
    tmp = SPATIAL_INDEX.with_suffix(".tmp")
    tmp.write_text(json.dumps(items, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(SPATIAL_INDEX)


def build_reconstruction(subject_id: str, timepoint: str, resolution: int = 24) -> dict[str, Any]:
    records = [r for r in _load_manifest() if r.get("subject_id") == subject_id and r.get("timepoint") == timepoint]
    usable = _registered(records)
    if len(usable) < 2:
        raise ValueError("At least two registered views are required")

    reconstruction_id = make_reconstruction_id(subject_id, timepoint, uuid4().hex[:12])
    spatial_object_id = make_spatial_object_id(subject_id, reconstruction_id)
    folder = RECON_ROOT / reconstruction_id.replace(":", "_")
    folder.mkdir(parents=True, exist_ok=True)

    mesh = build_visual_hull(usable, resolution)
    texture = project_multiview_texture(folder, usable)
    obj_path, mtl_path = _write_obj(folder, mesh, Path(texture["path"]).name if texture.get("path") else None)
    registered_view_ids = tuple(
        make_registered_view_id(make_prepared_photo_asset_id(str(r["asset_id"])), str(r["view"])) for r in usable
    )
    quality_values = [float(r.get("registration", {}).get("quality", 0)) for r in usable]
    quality = {
        "registered_views": len(usable),
        "mean_registration_quality": round(sum(quality_values) / len(quality_values), 4),
        "minimum_registration_quality": round(min(quality_values), 4),
        "projection_ready": True,
        "physical_calibration": False,
    }
    provenance = {
        "pipeline": "photo-3d-reconstruction",
        "pipeline_version": "stages-6-10-v3-projection-ready",
        "source_photo_asset_ids": [f"photo:{r['asset_id']}" for r in usable],
        "prepared_photo_asset_ids": [f"prepared-photo:{r['asset_id']}" for r in usable],
        "registered_view_ids": list(registered_view_ids),
        "views": [r.get("view") for r in usable],
        "geometry": mesh,
        "texture": texture,
        "created_at": utc_now(),
    }
    reconstruction = ReconstructionAsset(
        reconstruction_id=reconstruction_id,
        spatial_object_id=spatial_object_id,
        subject_id=subject_id,
        timepoint_id=timepoint,
        source_photo_asset_ids=tuple(f"photo:{r['asset_id']}" for r in usable),
        prepared_photo_asset_ids=tuple(f"prepared-photo:{r['asset_id']}" for r in usable),
        registered_view_ids=registered_view_ids,
        method=mesh["method"],
        version="3",
        geometry_uri=obj_path,
        texture_uri=texture.get("path"),
        coordinate_system="hand-surface-v1",
        quality=quality,
        provenance=provenance,
        status=lifecycle("reconstructed"),
    )
    spatial_object = _publish_spatial_object(reconstruction, mesh, texture)
    manifest = {
        **reconstruction.to_dict(),
        "mesh": {"obj": obj_path, "mtl": mtl_path, "vertex_count": len(mesh["vertices"]), "face_count": len(mesh["faces"]), "uv_count": len(mesh.get("uv", [])), "method": mesh["method"], "calibration": mesh["calibration"]},
        "texture": texture,
        "spatial_object": spatial_object.to_dict(),
        "status": "published",
    }
    (folder / "reconstruction.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    (folder / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    _write_spatial_index(spatial_object)
    return manifest


def latest_reconstruction(subject_id: str, timepoint: str) -> dict[str, Any] | None:
    matches = []
    for folder in RECON_ROOT.glob("reconstruction_*"):
        path = folder / "manifest.json"
        if not path.is_file():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if data.get("subject_id") == subject_id and data.get("timepoint_id", data.get("timepoint")) == timepoint:
                matches.append(data)
        except (OSError, json.JSONDecodeError):
            continue
    return max(matches, key=lambda x: x.get("provenance", {}).get("created_at", x.get("created_at", "")), default=None)


def clear_reconstructions(subject_id: str, timepoint: str) -> int:
    count = 0
    for folder in RECON_ROOT.glob("reconstruction_*"):
        path = folder / "manifest.json"
        if not path.is_file():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if data.get("subject_id") == subject_id and data.get("timepoint_id", data.get("timepoint")) == timepoint:
            spatial_id = data.get("spatial_object_id")
            shutil.rmtree(folder, ignore_errors=True)
            count += 1
            if spatial_id and SPATIAL_INDEX.is_file():
                try:
                    items = json.loads(SPATIAL_INDEX.read_text(encoding="utf-8"))
                    if isinstance(items, list):
                        SPATIAL_INDEX.write_text(json.dumps([x for x in items if x.get("spatial_object_id") != spatial_id], indent=2), encoding="utf-8")
                except Exception:
                    pass
    return count
