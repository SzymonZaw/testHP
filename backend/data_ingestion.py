from __future__ import annotations

import json
import re
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import UploadFile

ROOT = Path(__file__).resolve().parents[1]
RAW_ROOT = ROOT / "data" / "raw"
REGISTRY_PATH = ROOT / "data" / "registry" / "assets.json"

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff", ".bmp"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".m4v", ".avi", ".mkv"}
WSI_EXTENSIONS = {".dcm", ".svs", ".ndpi", ".mrxs", ".tif", ".tiff", ".ome.tif", ".ome.tiff"}
RNA_EXTENSIONS = {".csv", ".tsv", ".txt", ".mtx", ".gz", ".h5", ".h5ad", ".tar"}
SAFE_COMPONENT = re.compile(r"[^A-Za-z0-9._-]+")


@dataclass
class DataAsset:
    asset_id: str
    subject_id: str
    timepoint: str
    modality: str
    subtype: str | None
    view: str | None
    path: str
    filename: str
    size_bytes: int
    status: str
    created_at: str
    source: str = "upload"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def safe_component(value: str, fallback: str) -> str:
    cleaned = SAFE_COMPONENT.sub("_", value.strip()).strip("._")
    return cleaned or fallback


def load_registry() -> list[dict[str, Any]]:
    if not REGISTRY_PATH.exists():
        return []
    try:
        return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []


def save_registry(items: list[dict[str, Any]]) -> None:
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = REGISTRY_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(items, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(REGISTRY_PATH)


def extension_for(filename: str) -> str:
    lower = filename.lower()
    if lower.endswith(".ome.tiff"):
        return ".ome.tiff"
    if lower.endswith(".ome.tif"):
        return ".ome.tif"
    return Path(lower).suffix


def allowed_extensions(modality: str) -> set[str]:
    return {"hand": IMAGE_EXTENSIONS, "video": VIDEO_EXTENSIONS, "images": IMAGE_EXTENSIONS, "wsi": WSI_EXTENSIONS, "rna": RNA_EXTENSIONS, "metadata": {".json", ".yaml", ".yml", ".csv", ".tsv"}}.get(modality, set())


def destination_for(modality: str, subject_id: str, timepoint: str, subtype: str | None, view: str | None, filename: str) -> Path:
    subject = safe_component(subject_id, "subject")
    tp = safe_component(timepoint, "T0")
    name = safe_component(filename, "upload.bin")
    if modality == "hand": return RAW_ROOT / "hand" / subject / tp / name
    if modality == "video": return RAW_ROOT / "hand" / "media" / subject / tp / name
    if modality == "images": return RAW_ROOT / "images" / safe_component(subtype or "unclassified", "unclassified") / subject / tp / name
    if modality == "wsi": return RAW_ROOT / "wsi" / safe_component(subtype or "skin", "skin") / subject / tp / name
    if modality == "rna": return RAW_ROOT / "rna" / safe_component(subtype or "own_cohort", "own_cohort") / subject / tp / name
    if modality == "metadata": return RAW_ROOT / "metadata" / subject / tp / name
    raise ValueError(f"unsupported modality: {modality}")


def unique_destination(target: Path) -> Path:
    if not target.exists(): return target
    stem, suffix = target.stem, target.suffix
    index = 2
    while True:
        candidate = target.with_name(f"{stem}_v{index}{suffix}")
        if not candidate.exists(): return candidate
        index += 1


async def ingest_upload(upload: UploadFile, subject_id: str, timepoint: str, modality: str, subtype: str | None = None, view: str | None = None) -> DataAsset:
    ext = extension_for(upload.filename or "")
    if ext not in allowed_extensions(modality):
        raise ValueError(f"unsupported file extension {ext or '<none>'} for modality {modality}")
    target = unique_destination(destination_for(modality, subject_id, timepoint, subtype, view, upload.filename or "upload.bin"))
    target.parent.mkdir(parents=True, exist_ok=True)
    content = await upload.read()
    target.write_bytes(content)
    asset = DataAsset(f"asset_{uuid.uuid4().hex[:12]}", safe_component(subject_id, "subject"), safe_component(timepoint, "T0"), modality, subtype, view, target.relative_to(ROOT).as_posix(), target.name, len(content), "available" if content else "unavailable", datetime.now(timezone.utc).isoformat(), "upload")
    registry = load_registry()
    registry.append(asset.to_dict())
    save_registry(registry)
    return asset


def _raw_extension(path: Path) -> str:
    lower = path.name.lower()
    if lower.endswith(".ome.tiff"): return ".ome.tiff"
    if lower.endswith(".ome.tif"): return ".ome.tif"
    return path.suffix.lower()


def _raw_modality(path: Path) -> str:
    parts = path.relative_to(RAW_ROOT).parts
    if not parts: return "unknown"
    if parts[0] == "hand": return "video" if "media" in parts else "hand"
    return {"images": "images", "wsi": "wsi", "rna": "rna", "metadata": "metadata"}.get(parts[0], parts[0])


def _raw_metadata(path: Path) -> tuple[str, str, str | None, str | None]:
    parts = path.relative_to(RAW_ROOT).parts
    modality = _raw_modality(path)
    subject, timepoint, subtype, view = "unknown", "unknown", None, None
    if modality == "hand" and len(parts) >= 4: subject, timepoint, view = parts[1], parts[2], path.stem
    elif modality == "video" and len(parts) >= 4: subject, timepoint = parts[2], parts[3]
    elif modality in {"images", "wsi", "rna"} and len(parts) >= 2:
        subtype = parts[1]
        if len(parts) >= 4: subject, timepoint = parts[2], parts[3]
    elif modality == "metadata" and len(parts) >= 3: subject, timepoint = parts[1], parts[2]
    return subject, timepoint, subtype, view


def raw_inventory() -> list[dict[str, Any]]:
    """Return every file under data/raw, including files placed manually."""
    if not RAW_ROOT.exists(): return []
    registered = {item.get("path"): item for item in load_registry()}
    inventory: list[dict[str, Any]] = []
    for path in sorted(p for p in RAW_ROOT.rglob("*") if p.is_file()):
        relative = path.relative_to(ROOT).as_posix()
        if relative in registered:
            item = dict(registered[relative])
            item["source"] = "upload"
            item["status"] = "available" if path.stat().st_size > 0 else "unavailable"
            inventory.append(item)
            continue
        modality = _raw_modality(path)
        ext = _raw_extension(path)
        supported = ext in (IMAGE_EXTENSIONS if modality in {"hand", "images"} else VIDEO_EXTENSIONS if modality == "video" else WSI_EXTENSIONS if modality == "wsi" else RNA_EXTENSIONS if modality == "rna" else {".json", ".yaml", ".yml", ".csv", ".tsv"} if modality == "metadata" else set())
        subject, timepoint, subtype, view = _raw_metadata(path)
        size = path.stat().st_size
        inventory.append({"asset_id": f"raw_{uuid.uuid5(uuid.NAMESPACE_URL, relative).hex[:12]}", "subject_id": subject, "timepoint": timepoint, "modality": modality, "subtype": subtype, "view": view, "path": relative, "filename": path.name, "size_bytes": size, "status": "available" if supported and size > 0 else "unavailable", "created_at": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(), "source": "raw", "supported": supported})
    return inventory


def registry_status() -> dict[str, Any]:
    uploaded = load_registry()
    assets = raw_inventory()
    return {"assets": assets, "uploaded_assets": uploaded, "count": len(assets), "available": sum(1 for x in assets if x.get("status") == "available"), "unavailable": sum(1 for x in assets if x.get("status") != "available"), "uploaded_count": len(uploaded), "raw_count": len(assets), "raw_available": sum(1 for x in assets if x.get("status") == "available")}
