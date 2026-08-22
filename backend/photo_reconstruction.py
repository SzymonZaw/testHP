"""Photo preparation and registration contracts for hand 3D reconstruction.

Stages 1-5 only: input, view assignment, preparation, validation and 2D hand
registration. This module intentionally stops before visual-hull reconstruction.
"""
from __future__ import annotations

import json
import math
import re
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageFilter

from .data_ingestion import ROOT, ingest_upload, load_registry, save_registry, registry_status, safe_component
from .hand_segmentation import detect_hand_landmarks
from .hand_surface import SUPPORTED_VIEWS

PHOTO_ROOT = ROOT / "data" / "prepared" / "hand"
MANIFEST_PATH = ROOT / "data" / "registry" / "photo_reconstruction.json"
MIN_PREPARED_SIZE = 512
VIEW_TOKENS = {
    "front": "front",
    "back": "back",
    "side_left": "side_left",
    "side-right": "side_right",
    "side right": "side_right",
    "side_left": "side_left",
    "left": "side_left",
    "right": "side_right",
    "thumb": "thumb",
    "kciuk": "thumb",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def infer_view(filename: str, explicit: str | None = None) -> str | None:
    """Resolve an explicit view first, then a conservative filename token."""
    value = str(explicit or "").strip().lower().replace("-", "_")
    if value in SUPPORTED_VIEWS:
        return value
    normalized = re.sub(r"[^a-z0-9]+", "_", Path(filename).stem.lower()).strip("_")
    for token, view in sorted(VIEW_TOKENS.items(), key=lambda item: len(item[0]), reverse=True):
        token_norm = re.sub(r"[^a-z0-9]+", "_", token.lower()).strip("_")
        if re.search(rf"(?:^|_){re.escape(token_norm)}(?:_|$)", normalized):
            return view
    return None


def _load_manifest() -> list[dict[str, Any]]:
    if not MANIFEST_PATH.exists():
        return []
    try:
        value = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        return value if isinstance(value, list) else []
    except (OSError, json.JSONDecodeError):
        return []


def _save_manifest(items: list[dict[str, Any]]) -> None:
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = MANIFEST_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(items, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(MANIFEST_PATH)


def _record(asset_id: str, subject_id: str, timepoint: str, filename: str, path: str, view: str | None) -> dict[str, Any]:
    return {
        "asset_id": asset_id,
        "subject_id": safe_component(subject_id, "subject"),
        "timepoint": safe_component(timepoint, "T0"),
        "filename": filename,
        "path": path,
        "view": view,
        "view_source": "explicit" if view else "filename" if infer_view(filename) else "unassigned",
        "status": "uploaded",
        "prepared": False,
        "prepared_asset_id": None,
        "prepared_path": None,
        "quality": None,
        "warnings": [],
        "registration": None,
        "updated_at": utc_now(),
    }


def _border_color(arr: np.ndarray) -> np.ndarray:
    h, w = arr.shape[:2]
    band = max(2, min(h, w) // 30)
    pixels = np.concatenate([
        arr[:band].reshape(-1, 3), arr[-band:].reshape(-1, 3),
        arr[:, :band].reshape(-1, 3), arr[:, -band:].reshape(-1, 3),
    ], axis=0)
    return np.median(pixels, axis=0)


def _foreground_mask(rgb: np.ndarray, alpha: np.ndarray | None) -> np.ndarray:
    if alpha is not None and np.percentile(alpha, 90) > 20:
        return alpha >= 24
    bg = _border_color(rgb)
    distance = np.sqrt(np.mean((rgb.astype(np.float32) - bg.astype(np.float32)) ** 2, axis=2))
    # Adaptive threshold: enough separation for common plain photo backgrounds,
    # while avoiding an arbitrary fixed RGB value.
    threshold = max(18.0, float(np.percentile(distance, 55)))
    mask = distance > threshold
    # Remove tiny isolated components using a cheap repeated neighbourhood vote.
    for _ in range(2):
        padded = np.pad(mask, 1, mode="edge")
        neighbours = sum(padded[dy:dy + mask.shape[0], dx:dx + mask.shape[1]] for dy in range(3) for dx in range(3))
        mask = neighbours >= 3
    return mask


def _quality(rgb: np.ndarray, mask: np.ndarray) -> dict[str, float]:
    gray = rgb.astype(np.float32).mean(axis=2)
    dx = np.diff(gray, axis=1)
    dy = np.diff(gray, axis=0)
    sharpness = min(1.0, float((np.var(dx) + np.var(dy)) / 5000.0))
    exposure = float(np.mean((gray > 8) & (gray < 247)))
    background = 1.0 if 0.02 <= float(mask.mean()) <= 0.80 else 0.25
    resolution = min(1.0, (rgb.shape[0] * rgb.shape[1]) / float(2048 * 2048))
    overall = round((sharpness + exposure + background + resolution) / 4.0, 4)
    return {"sharpness_score": round(sharpness, 4), "exposure_score": round(exposure, 4), "background_score": round(background, 4), "resolution_score": round(resolution, 4), "overall": overall}


def _crop_box(mask: np.ndarray) -> tuple[int, int, int, int]:
    ys, xs = np.where(mask)
    if len(xs) == 0:
        return (0, 0, mask.shape[1], mask.shape[0])
    pad_x = max(8, int((xs.max() - xs.min() + 1) * 0.06))
    pad_y = max(8, int((ys.max() - ys.min() + 1) * 0.06))
    return (
        max(0, int(xs.min()) - pad_x),
        max(0, int(ys.min()) - pad_y),
        min(mask.shape[1], int(xs.max()) + pad_x + 1),
        min(mask.shape[0], int(ys.max()) + pad_y + 1),
    )


def prepare_image(record: dict[str, Any]) -> dict[str, Any]:
    source = ROOT / record["path"]
    if not source.is_file():
        raise FileNotFoundError(record["path"])
    with Image.open(source) as opened:
        image = opened.convert("RGBA")
        rgba = np.asarray(image)
    rgb = rgba[:, :, :3]
    alpha = rgba[:, :, 3] if rgba.shape[2] == 4 else None
    mask = _foreground_mask(rgb, alpha)
    quality = _quality(rgb, mask)
    crop = _crop_box(mask)
    cropped = image.crop(crop)
    cropped_rgba = np.asarray(cropped).copy()
    local_mask = mask[crop[1]:crop[3], crop[0]:crop[2]]
    cropped_rgba[:, :, 3] = np.where(local_mask, 255, 0).astype(np.uint8)
    prepared = Image.fromarray(cropped_rgba, mode="RGBA")
    if min(prepared.size) < MIN_PREPARED_SIZE:
        scale = MIN_PREPARED_SIZE / min(prepared.size)
        prepared = prepared.resize((max(MIN_PREPARED_SIZE, round(prepared.width * scale)), max(MIN_PREPARED_SIZE, round(prepared.height * scale))), Image.Resampling.LANCZOS)
    prepared = prepared.filter(ImageFilter.UnsharpMask(radius=1, percent=75, threshold=3))

    prepared_id = f"prepared_{uuid.uuid4().hex[:12]}"
    subject = safe_component(record["subject_id"], "subject")
    timepoint = safe_component(record["timepoint"], "T0")
    view = record.get("view") or "unassigned"
    out_dir = PHOTO_ROOT / subject / timepoint
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{prepared_id}_{view}.png"
    prepared.save(out_path, format="PNG", optimize=True)

    warnings: list[str] = []
    if quality["overall"] < 0.5:
        warnings.append("overall image quality is below the preferred research threshold")
    if float(local_mask.mean()) < 0.02 or float(local_mask.mean()) > 0.80:
        warnings.append("foreground coverage is unusual; review the prepared mask")
    if view == "unassigned":
        warnings.append("view is not assigned")

    record.update({
        "status": "prepared",
        "prepared": True,
        "prepared_asset_id": prepared_id,
        "prepared_path": out_path.relative_to(ROOT).as_posix(),
        "quality": quality,
        "warnings": warnings,
        "crop": {"left": crop[0], "top": crop[1], "right": crop[2], "bottom": crop[3]},
        "prepared_width": prepared.width,
        "prepared_height": prepared.height,
        "background_method": "embedded-alpha" if alpha is not None and np.percentile(alpha, 90) > 20 else "adaptive-border-separation",
        "updated_at": utc_now(),
    })
    return record


def _records(subject_id: str, timepoint: str) -> list[dict[str, Any]]:
    subject = safe_component(subject_id, "subject")
    tp = safe_component(timepoint, "T0")
    manifest = [x for x in _load_manifest() if x.get("subject_id") == subject and x.get("timepoint") == tp]
    by_id = {x["asset_id"]: x for x in manifest}
    for asset in registry_status()["assets"]:
        if asset.get("modality") != "hand" or asset.get("subject_id") != subject or asset.get("timepoint") != tp or asset.get("status") != "available":
            continue
        if asset["asset_id"] not in by_id:
            view = infer_view(asset.get("filename", ""), asset.get("view"))
            by_id[asset["asset_id"]] = _record(asset["asset_id"], subject, tp, asset["filename"], asset["path"], view)
    merged = list(by_id.values())
    all_manifest = [x for x in _load_manifest() if not (x.get("subject_id") == subject and x.get("timepoint") == tp)] + merged
    _save_manifest(all_manifest)
    return merged


def state(subject_id: str, timepoint: str) -> dict[str, Any]:
    records = _records(subject_id, timepoint)
    prepared = [x for x in records if x.get("prepared") and x.get("view") in SUPPORTED_VIEWS]
    assigned = [x for x in records if x.get("view") in SUPPORTED_VIEWS]
    return {
        "schema": "photo-reconstruction-stages-1-5",
        "subject_id": safe_component(subject_id, "subject"),
        "timepoint": safe_component(timepoint, "T0"),
        "views": list(SUPPORTED_VIEWS),
        "inputs": records,
        "assigned_count": len(assigned),
        "prepared_count": len(prepared),
        "ready_views": sorted({x["view"] for x in prepared}),
        "minimum_views": 2,
        "can_register": len(prepared) >= 2,
        "can_reconstruct": len(prepared) >= 2,
    }


def assign_view(asset_id: str, view: str) -> dict[str, Any]:
    normalized = infer_view("", view)
    if normalized not in SUPPORTED_VIEWS:
        raise ValueError(f"unsupported view: {view}")
    items = _load_manifest()
    target = next((x for x in items if x.get("asset_id") == asset_id), None)
    if target is None:
        raise KeyError(asset_id)
    conflict = next((x for x in items if x.get("asset_id") != asset_id and x.get("subject_id") == target.get("subject_id") and x.get("timepoint") == target.get("timepoint") and x.get("view") == normalized), None)
    if conflict:
        raise ValueError(f"view {normalized} is already assigned to {conflict.get('filename')}")
    target["view"] = normalized
    target["view_source"] = "manual"
    target["updated_at"] = utc_now()
    _save_manifest(items)
    return target


def register_prepared(subject_id: str, timepoint: str) -> dict[str, Any]:
    records = _records(subject_id, timepoint)
    registered: list[dict[str, Any]] = []
    for record in records:
        if not record.get("prepared") or record.get("view") not in SUPPORTED_VIEWS:
            continue
        prepared_path = ROOT / str(record["prepared_path"])
        detected = detect_hand_landmarks(prepared_path)
        landmarks = detected.get("landmarks", [])
        if len(landmarks) < 4:
            record["registration"] = {"status": "needs-review", "method": detected.get("method", "none"), "landmarks": len(landmarks), "quality": 0.0}
            record["status"] = "needs-registration-review"
            registered.append(record)
            continue
        xs = [p["x"] for p in landmarks]
        ys = [p["y"] for p in landmarks]
        bbox = {"min_x": min(xs), "max_x": max(xs), "min_y": min(ys), "max_y": max(ys)}
        scale = max(bbox["max_x"] - bbox["min_x"], bbox["max_y"] - bbox["min_y"], 1e-6)
        normalized_landmarks = [{"id": f"mp-{i:02d}", "x": round((p["x"] - bbox["min_x"]) / scale, 6), "y": round((p["y"] - bbox["min_y"]) / scale, 6), "z": round(float(p.get("z", 0.0)), 6)} for i, p in enumerate(landmarks)]
        record["registration"] = {
            "status": "registered",
            "method": detected.get("method", "unknown"),
            "landmarks": normalized_landmarks,
            "landmark_count": len(landmarks),
            "bbox": bbox,
            "transform": {"origin": [bbox["min_x"], bbox["min_y"]], "scale": round(scale, 6)},
            "coordinate_system": "hand-surface-v1",
            "quality": round(min(1.0, len(landmarks) / 21.0), 4),
            "registered_at": utc_now(),
        }
        record["status"] = "registered"
        registered.append(record)
    items = _load_manifest()
    updated = {x["asset_id"]: x for x in registered}
    items = [updated.get(x.get("asset_id"), x) for x in items]
    _save_manifest(items)
    usable = [x for x in registered if x.get("registration", {}).get("status") == "registered"]
    return {"subject_id": subject_id, "timepoint": timepoint, "registered": registered, "registered_count": len(usable), "ready_for_projection": len(usable) >= 2}


def prepare_by_id(asset_id: str) -> dict[str, Any]:
    items = _load_manifest()
    target = next((x for x in items if x.get("asset_id") == asset_id), None)
    if target is None:
        # Bootstrap a record from the canonical ingestion registry.
        asset = next((x for x in registry_status()["assets"] if x.get("asset_id") == asset_id), None)
        if not asset:
            raise KeyError(asset_id)
        target = _record(asset_id, asset["subject_id"], asset["timepoint"], asset["filename"], asset["path"], infer_view(asset.get("filename", ""), asset.get("view")))
        items.append(target)
    result = prepare_image(target)
    items = [result if x.get("asset_id") == asset_id else x for x in items]
    _save_manifest(items)
    return result


def file_for(identifier: str, prepared: bool = False) -> Path:
    for item in _load_manifest():
        key = item.get("prepared_asset_id") if prepared else item.get("asset_id")
        if key == identifier:
            path = item.get("prepared_path") if prepared else item.get("path")
            if path:
                candidate = (ROOT / path).resolve()
                candidate.relative_to(ROOT.resolve())
                if candidate.is_file():
                    return candidate
    raise FileNotFoundError(identifier)


async def upload_photo(upload: Any, subject_id: str, timepoint: str, view: str | None = None) -> dict[str, Any]:
    asset = await ingest_upload(upload, subject_id, timepoint, "hand", None, view)
    resolved = infer_view(asset.filename, view)
    items = _load_manifest()
    record = _record(asset.asset_id, asset.subject_id, asset.timepoint, asset.filename, asset.path, resolved)
    items.append(record)
    _save_manifest(items)
    return record
