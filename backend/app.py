from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .data_ingestion import ingest_upload, registry_status
from .hand_twin_v2 import build_twin

ROOT = Path(__file__).resolve().parents[1]
RAW_ROOT = ROOT / "data" / "raw"
CONFIG_PATH = ROOT / "configs" / "datasets.yaml"
HAND_ONTOLOGY_PATH = ROOT / "configs" / "hand_zones.yaml"
WEB_ROOT = ROOT / "web"

IMAGE_FORMATS = {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff", ".bmp"}
WSI_FORMATS = {".dcm", ".svs", ".ndpi", ".mrxs", ".tif", ".tiff"}
RNA_FORMATS = {".gz", ".mtx", ".tsv", ".csv", ".txt", ".h5", ".h5ad", ".tar"}

app = FastAPI(title="Human Pathology Platform", version="0.5.0")


class PipelineRequest(BaseModel):
    datasets: list[str] = []


class HandValidationRequest(BaseModel):
    subject_id: str
    timepoint: str
    session_id: str = "session-001"


def load_config() -> dict[str, Any]:
    if not CONFIG_PATH.exists():
        return {}
    with CONFIG_PATH.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def load_hand_ontology() -> dict[str, Any]:
    if not HAND_ONTOLOGY_PATH.exists():
        return {"hand": []}
    with HAND_ONTOLOGY_PATH.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {"hand": []}


def iter_files(path: Path):
    if not path.exists():
        return []
    return [p for p in path.rglob("*") if p.is_file()]


def dataset_registry() -> list[dict[str, Any]]:
    cfg = load_config().get("datasets", {})
    registry: list[dict[str, Any]] = []
    for modality, entries in (("image", cfg.get("images", {})), ("wsi", cfg.get("wsi", {})), ("rna", cfg.get("rna", {})), ("hand", cfg.get("hand", {}))):
        for name, spec in entries.items():
            path_value = spec.get("path") or spec.get("root") or spec.get("images")
            if not path_value:
                continue
            path = ROOT / path_value
            files = iter_files(path)
            enabled = bool(spec.get("enabled", True))
            formats = set(spec.get("formats") or spec.get("image_formats") or [])
            if modality == "image":
                formats |= IMAGE_FORMATS
            elif modality == "wsi":
                formats |= WSI_FORMATS
            elif modality == "rna":
                formats |= RNA_FORMATS
            supported = [p for p in files if p.suffix.lower() in {x.lower() for x in formats}]
            empty = [p for p in supported if p.stat().st_size == 0]
            registry.append({
                "name": name,
                "modality": modality,
                "task": spec.get("task") or spec.get("source_type") or "research dataset",
                "path": path_value,
                "exists": path.exists(),
                "enabled": enabled,
                "files": len(files),
                "supported_files": len(supported),
                "bytes": sum(p.stat().st_size for p in files),
                "empty_files": len(empty),
                "available": bool(supported),
                "reason": spec.get("reason"),
            })
    return registry


def validate_dataset(item: dict[str, Any]) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []
    if not item["exists"]:
        errors.append("dataset directory is missing")
    if not item["enabled"]:
        warnings.append(item["reason"] or "dataset is disabled in configuration")
    if item["exists"] and item["supported_files"] == 0:
        warnings.append("no supported data files are available locally")
    if item["empty_files"]:
        warnings.append(f"{item['empty_files']} empty file(s) present")
    valid = not errors and (item["supported_files"] > 0 or not item["enabled"])
    return {**item, "valid": valid, "warnings": warnings, "errors": errors}


def run_pipeline(selected: list[str]) -> dict[str, Any]:
    registry = dataset_registry()
    by_name = {x["name"]: x for x in registry}
    chosen = selected or list(by_name)
    missing = [name for name in chosen if name not in by_name]
    validations = {name: validate_dataset(by_name[name]) for name in chosen if name in by_name}
    valid_items = [x for x in validations.values() if x["valid"]]
    modalities = sorted({x["modality"] for x in valid_items})
    total_files = sum(x["supported_files"] for x in valid_items)
    total_bytes = sum(x["bytes"] for x in valid_items)
    steps = [
        {"id": "input", "name": "Input", "purpose": "Identify selected research datasets", "status": "ok" if not missing else "warning"},
        {"id": "ingestion", "name": "Ingestion", "purpose": "Read available files from data/raw", "status": "ok" if valid_items else "warning"},
        {"id": "validation", "name": "Validation", "purpose": "Check files, formats and empty inputs", "status": "ok" if all(x["valid"] for x in validations.values()) and validations else "warning"},
        {"id": "normalization", "name": "Normalization", "purpose": "Convert sources into common observations", "status": "ok" if valid_items else "warning"},
        {"id": "fusion", "name": "Multimodal fusion", "purpose": "Aggregate dataset-level evidence without inventing subject links", "status": "ok" if valid_items else "warning"},
        {"id": "results", "name": "Research view", "purpose": "Present evidence, coverage and limitations", "status": "ok" if valid_items else "warning"},
    ]
    warnings = [w for item in validations.values() for w in item["warnings"]]
    return {
        "status": "ready" if valid_items and not missing else "warning",
        "selected": chosen,
        "missing": missing,
        "datasets": list(validations.values()),
        "steps": steps,
        "summary": {"datasets": len(valid_items), "files": total_files, "bytes": total_bytes, "modalities": modalities, "linked_subjects": 0},
        "warnings": warnings + (["Subject-level links are not inferred without a shared identifier."] if valid_items else []),
        "results": {
            "evidence_level": "dataset-level research evidence",
            "biological_inference": "not claimed by this ingestion dashboard",
            "next_action": "Review the modality coverage and validation warnings before enabling downstream models.",
        },
    }


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/status")
def status():
    registry = dataset_registry()
    assets = registry_status()
    return {
        "status": "ready",
        "raw_data": RAW_ROOT.exists(),
        "registered_datasets": len(registry),
        "available_datasets": sum(1 for x in registry if x["available"]),
        "modalities": sorted({x["modality"] for x in registry}),
        "uploaded_assets": assets["count"],
    }


@app.get("/api/datasets")
def datasets():
    registry = [validate_dataset(x) for x in dataset_registry()]
    return {"raw_exists": RAW_ROOT.exists(), "datasets": registry}


@app.get("/api/ingestion/assets")
def ingestion_assets():
    return registry_status()


@app.get("/api/hand/ontology")
def hand_ontology():
    return load_hand_ontology()


@app.get("/api/hand/twin")
def hand_twin(subject_id: str = "own_cohort"):
    twin = build_twin(subject_id, load_hand_ontology())
    return twin.snapshot()


@app.post("/api/hand/validate")
def validate_hand(request: HandValidationRequest):
    root = RAW_ROOT / "hand" / "own_cohort" / request.timepoint
    required = ["front", "back", "thumb", "side_left", "side_right"]
    found = {name: next((p for p in root.glob(f"{name}.*") if p.is_file() and p.suffix.lower() in IMAGE_FORMATS and p.stat().st_size > 0), None) for name in required}
    missing = [name for name, path in found.items() if path is None]
    return {
        "subject_id": request.subject_id,
        "session_id": request.session_id,
        "timepoint": request.timepoint,
        "status": "available" if not missing else ("partial" if any(found.values()) else "unavailable"),
        "required_views": required,
        "available_views": [name for name, path in found.items() if path is not None],
        "missing_views": missing,
    }


@app.post("/api/upload/{modality}")
async def upload(
    modality: str,
    file: UploadFile = File(...),
    subject_id: str = Form("own_cohort"),
    timepoint: str = Form("T0"),
    subtype: str | None = Form(None),
    view: str | None = Form(None),
):
    if modality not in {"hand", "video", "images", "wsi", "rna", "metadata"}:
        raise HTTPException(status_code=400, detail="unsupported modality")
    try:
        asset = await ingest_upload(file, subject_id, timepoint, modality, subtype, view)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"status": asset.status, "asset": asset.to_dict()}


@app.get("/api/pipeline")
def pipeline():
    return run_pipeline([])


@app.post("/api/pipeline/validate")
def validate(request: PipelineRequest):
    return run_pipeline(request.datasets)


@app.post("/api/run")
def run(request: PipelineRequest):
    return run_pipeline(request.datasets)


if WEB_ROOT.exists():
    app.mount("/assets", StaticFiles(directory=WEB_ROOT), name="assets")


@app.get("/")
def home():
    return FileResponse(WEB_ROOT / "index.html")
