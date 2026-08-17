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
    return {
        "hand": IMAGE_EXTENSIONS,
        "video": VIDEO_EXTENSIONS,
        "images": IMAGE_EXTENSIONS,
        "wsi": WSI_EXTENSIONS,
        "rna": RNA_EXTENSIONS,
        "metadata": {".json", ".yaml", ".yml", ".csv", ".tsv"},
    }.get(modality, set())


def destination_for(modality: str, subject_id: str, timepoint: str, subtype: str | None, view: str | None, filename: str) -> Path:
    subject = safe_component(subject_id, "subject")
    tp = safe_component(timepoint, "T0")
    name = safe_component(filename, "upload.bin")
    if modality == "hand":
        return RAW_ROOT / "hand" / "own_cohort" / tp / name
    if modality == "video":
        return RAW_ROOT / "hand" / "media" / tp / name
    if modality == "images":
        category = safe_component(subtype or "unclassified", "unclassified")
        return RAW_ROOT / "images" / category / subject / tp / name
    if modality == "wsi":
        category = safe_component(subtype or "skin", "skin")
        return RAW_ROOT / "wsi" / category / subject / tp / name
    if modality == "rna":
        category = safe_component(subtype or "own_cohort", "own_cohort")
        return RAW_ROOT / "rna" / category / subject / tp / name
    if modality == "metadata":
        return RAW_ROOT / "metadata" / subject / tp / name
    raise ValueError(f"unsupported modality: {modality}")


async def ingest_upload(
    upload: UploadFile,
    subject_id: str,
    timepoint: str,
    modality: str,
    subtype: str | None = None,
    view: str | None = None,
) -> DataAsset:
    ext = extension_for(upload.filename or "")
    if ext not in allowed_extensions(modality):
        raise ValueError(f"unsupported file extension {ext or '<none>'} for modality {modality}")
    target = destination_for(modality, subject_id, timepoint, subtype, view, upload.filename or "upload.bin")
    target.parent.mkdir(parents=True, exist_ok=True)
    content = await upload.read()
    target.write_bytes(content)
    asset = DataAsset(
        asset_id=f"asset_{uuid.uuid4().hex[:12]}",
        subject_id=safe_component(subject_id, "subject"),
        timepoint=safe_component(timepoint, "T0"),
        modality=modality,
        subtype=subtype,
        view=view,
        path=target.relative_to(ROOT).as_posix(),
        filename=target.name,
        size_bytes=len(content),
        status="available" if content else "unavailable",
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    registry = load_registry()
    registry.append(asset.to_dict())
    save_registry(registry)
    return asset


def registry_status() -> dict[str, Any]:
    assets = load_registry()
    return {
        "assets": assets,
        "count": len(assets),
        "available": sum(1 for asset in assets if asset.get("status") == "available"),
        "unavailable": sum(1 for asset in assets if asset.get("status") != "available"),
    }
