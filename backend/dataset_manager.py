from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "data" / "registry" / "datasets.json"
DATASET_ROOT = ROOT / "data" / "raw"
SAFE = re.compile(r"[^A-Za-z0-9._-]+")

@dataclass
class DatasetRecord:
    dataset_id: str
    name: str
    modality: str
    description: str = ""
    source: str = ""
    version: str = "1.0"
    license: str | None = None
    tags: list[str] = field(default_factory=list)
    root_path: str = ""
    manifest_path: str = ""
    created_at: str = ""
    status: str = "draft"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

def _safe(value: str, fallback: str) -> str:
    value = SAFE.sub("_", value.strip()).strip("._")
    return value or fallback

def _load() -> list[dict[str, Any]]:
    if not REGISTRY_PATH.exists(): return []
    try: return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError): return []

def _save(items: list[dict[str, Any]]) -> None:
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = REGISTRY_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(items, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(REGISTRY_PATH)

def _dataset_id(name: str, modality: str) -> str:
    return f"DS-{hashlib.sha1(f'{modality}:{name}'.encode()).hexdigest()[:10].upper()}"

def _manifest(record: DatasetRecord) -> dict[str, Any]:
    root = ROOT / record.root_path
    files = []
    if root.exists():
        for path in sorted(p for p in root.rglob("*") if p.is_file()):
            rel = path.relative_to(ROOT).as_posix()
            size = path.stat().st_size
            files.append({"path": rel, "filename": path.name, "size_bytes": size, "status": "available" if size > 0 else "empty"})
    return {"dataset_id": record.dataset_id, "name": record.name, "modality": record.modality, "version": record.version, "description": record.description, "source": record.source, "license": record.license, "created_at": record.created_at, "status": record.status, "records": files}

def _write_manifest(record: DatasetRecord) -> None:
    path = ROOT / record.manifest_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_manifest(record), indent=2, ensure_ascii=False), encoding="utf-8")

def ensure_registry(configured: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    items = _load(); existing = {x.get("root_path") for x in items}; changed = False
    for spec in configured or []:
        root = spec.get("path")
        if not root or root in existing: continue
        path = ROOT / root
        if not path.exists(): continue
        modality = spec.get("modality", "unknown"); name = spec.get("name") or path.name; dataset_id = _dataset_id(name, modality)
        record = DatasetRecord(dataset_id, name, modality, spec.get("description", spec.get("task", "Existing research dataset")), spec.get("source", "existing raw input"), str(spec.get("version", "1.0")), spec.get("license"), list(spec.get("tags") or []), Path(root).as_posix(), (Path("data") / "registry" / "manifests" / f"{dataset_id}.json").as_posix(), datetime.now(timezone.utc).isoformat(), "ready" if any(p.is_file() and p.stat().st_size > 0 for p in path.rglob("*")) else "draft")
        items.append(record.to_dict()); existing.add(root); _write_manifest(record); changed = True
    if changed: _save(items)
    return items

def list_datasets(configured: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    result = []
    for item in ensure_registry(configured):
        record = DatasetRecord(**item); manifest = _manifest(record); available = sum(f["status"] == "available" for f in manifest["records"])
        result.append({**item, "file_count": len(manifest["records"]), "available_files": available, "empty_files": len(manifest["records"]) - available, "status": "ready" if available else "draft"})
    return result

def get_dataset(dataset_id: str, configured: list[dict[str, Any]] | None = None) -> dict[str, Any] | None:
    return next((x for x in list_datasets(configured) if x["dataset_id"] == dataset_id), None)

def create_dataset(*, name: str, modality: str, description: str = "", source: str = "", version: str = "1.0", license: str | None = None, tags: list[str] | None = None) -> dict[str, Any]:
    name = _safe(name, "dataset"); modality = _safe(modality, "unknown").lower()
    if modality not in {"hand", "image", "images", "video", "wsi", "rna", "metadata"}: raise ValueError("unsupported dataset modality")
    items = _load()
    if any(x.get("name") == name and x.get("modality") == modality for x in items): raise ValueError(f"dataset '{name}' already exists for modality '{modality}'")
    dataset_id = _dataset_id(name, modality); root = DATASET_ROOT / modality / "datasets" / dataset_id; root.mkdir(parents=True, exist_ok=True)
    record = DatasetRecord(dataset_id, name, modality, description.strip(), source.strip(), version.strip() or "1.0", license.strip() if license else None, sorted({_safe(t, "tag") for t in (tags or []) if t.strip()}), root.relative_to(ROOT).as_posix(), (Path("data") / "registry" / "manifests" / f"{dataset_id}.json").as_posix(), datetime.now(timezone.utc).isoformat(), "draft")
    items.append(record.to_dict()); _save(items); _write_manifest(record)
    return record.to_dict()

def refresh_manifest(dataset_id: str) -> dict[str, Any]:
    item = get_dataset(dataset_id)
    if item is None: raise KeyError(dataset_id)
    record = DatasetRecord(**item); manifest = _manifest(record)
    record.status = "ready" if any(f["status"] == "available" for f in manifest["records"]) else "draft"
    items = _load()
    for i, x in enumerate(items):
        if x.get("dataset_id") == dataset_id: items[i] = record.to_dict()
    _save(items); _write_manifest(record)
    return _manifest(record)
