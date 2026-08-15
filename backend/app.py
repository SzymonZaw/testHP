from __future__ import annotations

import csv
import gzip
import json
import math
import struct
from pathlib import Path
from statistics import mean, pstdev
from typing import Any

import yaml
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .hand_longitudinal import (
    HandObservation,
    build_hand_snapshot,
    compare_numeric_observations,
    make_observation,
    rank_zones_by_change,
)

ROOT = Path(__file__).resolve().parents[1]
RAW_ROOT = ROOT / "data" / "raw"
CONFIG_PATH = ROOT / "configs" / "datasets.yaml"
WEB_ROOT = ROOT / "web"
LONGITUDINAL_PATH = ROOT / "data" / "longitudinal" / "hand_observations.jsonl"

IMAGE_FORMATS = {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff", ".bmp"}
WSI_FORMATS = {".dcm", ".svs", ".ndpi", ".mrxs", ".tif", ".tiff"}
RNA_FORMATS = {".gz", ".mtx", ".tsv", ".csv", ".txt", ".h5", ".h5ad", ".tar"}

app = FastAPI(title="Human Pathology Platform", version="0.7.0")


class PipelineRequest(BaseModel):
    datasets: list[str] = []


class HandObservationRequest(BaseModel):
    subject_id: str
    session_id: str
    timepoint: str
    hand_id: str
    laterality: str = "unknown"
    zone: str
    observation_type: str
    metric: str
    value: float | int | str | None
    unit: str | None = None
    source_file: str | None = None
    confidence: float | None = None
    notes: str | None = None


class HandComparisonRequest(BaseModel):
    baseline: list[HandObservationRequest]
    current: list[HandObservationRequest]


def load_config() -> dict[str, Any]:
    if not CONFIG_PATH.exists():
        return {}
    with CONFIG_PATH.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def iter_files(path: Path):
    if not path.exists():
        return []
    return [p for p in path.rglob("*") if p.is_file()]


def image_dimensions(path: Path) -> tuple[int, int] | None:
    try:
        with path.open("rb") as handle:
            data = handle.read(2_000_000)
        if data.startswith(b"\x89PNG\r\n\x1a\n") and len(data) >= 24:
            return struct.unpack(">II", data[16:24])
        if data[:3] == b"\xff\xd8\xff":
            i = 2
            while i + 9 < len(data):
                if data[i] != 0xFF:
                    i += 1
                    continue
                marker = data[i + 1]
                i += 2
                if marker in {0xD8, 0xD9}:
                    continue
                if i + 2 > len(data):
                    break
                length = struct.unpack(">H", data[i:i + 2])[0]
                if marker in list(range(0xC0, 0xC4)) + list(range(0xC5, 0xC8)) + list(range(0xC9, 0xCC)) + list(range(0xCD, 0xD0)):
                    if i + 7 <= len(data):
                        h, w = struct.unpack(">HH", data[i + 3:i + 7])
                        return w, h
                    break
                i += max(length, 2)
        if path.suffix.lower() in {".tif", ".tiff"} and len(data) >= 16:
            order = "<" if data[:2] == b"II" else ">" if data[:2] == b"MM" else None
            if order and struct.unpack(order + "H", data[2:4])[0] == 42:
                offset = struct.unpack(order + "I", data[4:8])[0]
                if offset + 2 <= len(data):
                    count = struct.unpack(order + "H", data[offset:offset + 2])[0]
                    pos = offset + 2
                    width = height = None
                    for _ in range(min(count, 256)):
                        if pos + 12 > len(data):
                            break
                        tag, typ, n = struct.unpack(order + "HHI", data[pos:pos + 8])
                        raw = data[pos + 8:pos + 12]
                        if typ == 3 and n == 1:
                            value = struct.unpack(order + "H", raw[:2])[0]
                        elif typ == 4 and n == 1:
                            value = struct.unpack(order + "I", raw)[0]
                        else:
                            value = None
                        if tag == 256:
                            width = value
                        elif tag == 257:
                            height = value
                        pos += 12
                    if width and height:
                        return int(width), int(height)
    except (OSError, ValueError, struct.error):
        return None
    return None


def image_content_stats(path: Path) -> dict[str, Any]:
    try:
        from PIL import Image, ImageStat
        with Image.open(path) as image:
            image = image.convert("RGB")
            stat = ImageStat.Stat(image)
            return {
                "width": image.width,
                "height": image.height,
                "pixels": image.width * image.height,
                "mean_rgb": [round(float(x), 4) for x in stat.mean],
                "std_rgb": [round(float(x), 4) for x in stat.stddev],
            }
    except Exception:
        return {}


def text_preview(path: Path, limit: int = 20000) -> str:
    try:
        if path.suffix.lower() == ".gz":
            with gzip.open(path, "rt", encoding="utf-8", errors="replace") as handle:
                return handle.read(limit)
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            return handle.read(limit)
    except (OSError, EOFError, gzip.BadGzipFile, UnicodeError):
        return ""


def tabular_stats(path: Path) -> dict[str, Any]:
    if path.suffix.lower() not in {".csv", ".tsv", ".txt", ".gz"}:
        return {}
    lines = [line for line in text_preview(path).splitlines() if line.strip()]
    if not lines:
        return {}
    delimiter = "\t" if "\t" in lines[0] else "," if "," in lines[0] else None
    if not delimiter:
        return {"sample_rows": len(lines), "numeric_values": 0}
    try:
        rows = list(csv.reader(lines[:5000], delimiter=delimiter))
    except csv.Error:
        return {"sample_rows": len(lines), "numeric_values": 0}
    numeric: list[float] = []
    for row in rows[1:]:
        for value in row:
            try:
                number = float(value)
            except (TypeError, ValueError):
                continue
            if math.isfinite(number):
                numeric.append(number)
    result: dict[str, Any] = {
        "sample_rows": max(0, len(rows) - 1),
        "columns": max((len(row) for row in rows), default=0),
        "delimiter": "tab" if delimiter == "\t" else "comma",
        "numeric_values": len(numeric),
    }
    if numeric:
        result.update({
            "numeric_mean": round(mean(numeric), 6),
            "numeric_std": round(pstdev(numeric), 6) if len(numeric) > 1 else 0.0,
            "numeric_min": round(min(numeric), 6),
            "numeric_max": round(max(numeric), 6),
        })
    return result


def json_annotation_stats(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            data = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return {"json_valid": False}

    def count_nodes(value: Any) -> int:
        if isinstance(value, dict):
            return 1 + sum(count_nodes(v) for v in value.values())
        if isinstance(value, list):
            return sum(count_nodes(v) for v in value[:10000])
        return 1

    return {"json_valid": True, "json_nodes": count_nodes(data), "root_type": type(data).__name__}


def wsi_stats(path: Path) -> dict[str, Any]:
    if path.suffix.lower() != ".dcm":
        return {}
    try:
        import pydicom
        ds = pydicom.dcmread(path, stop_before_pixels=True, force=True)
        result: dict[str, Any] = {}
        rows = getattr(ds, "Rows", None)
        columns = getattr(ds, "Columns", None)
        if rows and columns:
            result.update({"rows": int(rows), "columns": int(columns), "pixels": int(rows) * int(columns)})
        spacing = getattr(ds, "PixelSpacing", None)
        if spacing and len(spacing) >= 2:
            result["pixel_spacing_mm"] = [float(spacing[0]), float(spacing[1])]
        return result
    except Exception:
        return {}


def analyze_dataset(modality: str, files: list[Path]) -> dict[str, Any]:
    result: dict[str, Any] = {"observations": []}
    if modality in {"image", "hand"}:
        image_files = [p for p in files if p.suffix.lower() in IMAGE_FORMATS]
        dimensions = [(p, image_dimensions(p)) for p in image_files]
        dimensions = [(p, d) for p, d in dimensions if d]
        if dimensions:
            widths = [d[0] for _, d in dimensions]
            heights = [d[1] for _, d in dimensions]
            result["image_dimensions"] = {"measured": len(dimensions), "min_width": min(widths), "max_width": max(widths), "min_height": min(heights), "max_height": max(heights)}
            result["observations"].append(f"Measured dimensions for {len(dimensions)} image file(s); width range {min(widths)}–{max(widths)} px and height range {min(heights)}–{max(heights)} px.")
        content = [image_content_stats(p) for p in image_files]
        content = [x for x in content if x]
        if content:
            mean_rgb = [round(mean(x["mean_rgb"][i] for x in content), 4) for i in range(3)]
            brightness = round(mean(sum(x["mean_rgb"]) / 3 for x in content), 4)
            result["raster_statistics"] = {"files": len(content), "mean_rgb": mean_rgb, "mean_brightness": brightness, "mean_pixels": round(mean(x["pixels"] for x in content), 2)}
            result["observations"].append(f"Computed raster statistics for {len(content)} readable image file(s); mean RGB={mean_rgb} and mean brightness={brightness:.4f}/255.")
        if modality == "hand":
            json_files = [p for p in files if p.suffix.lower() == ".json"]
            stats = [json_annotation_stats(p) for p in json_files]
            valid_json = [s for s in stats if s.get("json_valid")]
            nodes = sum(s.get("json_nodes", 0) for s in valid_json)
            result["annotations"] = {"files": len(json_files), "valid_json": len(valid_json), "nodes": nodes}
            if valid_json:
                result["observations"].append(f"Parsed {len(valid_json)} JSON annotation file(s) containing {nodes} structured nodes.")
    elif modality == "rna":
        supported = [p for p in files if p.suffix.lower() in RNA_FORMATS]
        tabular = [s for s in (tabular_stats(p) for p in supported) if s]
        result["tabular_files"] = len(tabular)
        result["sample_rows"] = sum(s.get("sample_rows", 0) for s in tabular)
        result["numeric_values"] = sum(s.get("numeric_values", 0) for s in tabular)
        result["max_columns"] = max((s.get("columns", 0) for s in tabular), default=0)
        result["binary_files"] = sum(1 for p in supported if p.suffix.lower() in {".h5", ".h5ad", ".mtx", ".tar"})
        if tabular:
            result["observations"].append(f"Parsed {len(tabular)} text/tabular file(s); counted {result['sample_rows']} data rows and {result['numeric_values']} finite numeric values in the inspected content.")
            numeric_stats = [s for s in tabular if "numeric_mean" in s]
            if numeric_stats:
                values = [v for s in numeric_stats for v in (s["numeric_min"], s["numeric_max"])]
                result["numeric_summary"] = {"files_with_numeric_data": len(numeric_stats), "observed_min": min(values), "observed_max": max(values)}
                result["observations"].append(f"Observed numeric values range from {result['numeric_summary']['observed_min']} to {result['numeric_summary']['observed_max']} in the inspected tabular content.")
        if result["binary_files"] and not tabular:
            result["observations"].append("Binary RNA files are present, but no expression values are reported because the current lightweight reader does not parse their internal matrix structure.")
    elif modality == "wsi":
        supported = [p for p in files if p.suffix.lower() in WSI_FORMATS]
        sizes = [p.stat().st_size for p in supported]
        result["total_mb"] = round(sum(sizes) / 1024**2, 2)
        result["formats"] = sorted({p.suffix.lower().lstrip(".") for p in supported})
        dicom = [x for x in (wsi_stats(p) for p in supported if p.suffix.lower() == ".dcm") if x]
        if supported:
            result["observations"].append(f"Found {len(supported)} pathology file(s) across {', '.join(result['formats'])} format(s), totaling {result['total_mb']} MB.")
        if dicom:
            result["dicom_metadata"] = dicom
            result["observations"].append(f"Read metadata from {len(dicom)} DICOM file(s) without loading pixel data.")
    return result


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
            if modality == "image": formats |= IMAGE_FORMATS
            elif modality == "wsi": formats |= WSI_FORMATS
            elif modality == "rna": formats |= RNA_FORMATS
            supported = [p for p in files if p.suffix.lower() in {x.lower() for x in formats}]
            empty = [p for p in supported if p.stat().st_size == 0]
            registry.append({"name": name, "modality": modality, "task": spec.get("task") or spec.get("source_type") or "research dataset", "path": path_value, "exists": path.exists(), "enabled": enabled, "files": len(files), "supported_files": len(supported), "bytes": sum(p.stat().st_size for p in files), "empty_files": len(empty), "available": bool(supported), "reason": spec.get("reason"), "analysis": analyze_dataset(modality, files)})
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


def build_findings(datasets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for dataset in datasets:
        if not dataset["available"]:
            continue
        for observation in dataset.get("analysis", {}).get("observations", []):
            findings.append({"dataset": dataset["name"], "modality": dataset["modality"], "type": "measured", "text": observation})
    return findings


def run_pipeline(selected: list[str]) -> dict[str, Any]:
    registry = dataset_registry()
    by_name = {x["name"]: x for x in registry}
    chosen = selected or list(by_name)
    missing = [name for name in chosen if name not in by_name]
    validations = {name: validate_dataset(by_name[name]) for name in chosen if name in by_name}
    usable_items = [x for x in validations.values() if x["available"] and x["supported_files"] > 0]
    modalities = sorted({x["modality"] for x in usable_items})
    total_files = sum(x["supported_files"] for x in usable_items)
    total_bytes = sum(x["bytes"] for x in usable_items)
    warnings = [w for item in validations.values() for w in item["warnings"]]
    steps = [
        {"id": "input", "name": "Input", "purpose": "Identify selected research datasets", "status": "ok" if not missing else "warning"},
        {"id": "ingestion", "name": "Ingestion", "purpose": "Read available files from data/raw", "status": "ok" if usable_items else "warning"},
        {"id": "validation", "name": "Validation", "purpose": "Check files, formats and empty inputs", "status": "ok" if not warnings and not missing else "warning"},
        {"id": "normalization", "name": "Normalization", "purpose": "Convert sources into common observations", "status": "ok" if usable_items else "warning"},
        {"id": "fusion", "name": "Multimodal fusion", "purpose": "Aggregate dataset-level evidence without inventing subject links", "status": "ok" if usable_items else "warning"},
        {"id": "results", "name": "Research view", "purpose": "Present measured evidence, coverage and limitations", "status": "ok" if usable_items else "warning"},
    ]
    return {"status": "ready" if usable_items and not missing else "warning", "selected": chosen, "missing": missing, "datasets": list(validations.values()), "steps": steps, "summary": {"datasets": len(usable_items), "files": total_files, "bytes": total_bytes, "modalities": modalities, "linked_subjects": 0}, "warnings": warnings + (["Subject-level links are not inferred without a shared identifier."] if usable_items else []), "results": {"evidence_level": "dataset-level measured evidence", "biological_inference": "Measured input characteristics are available; biological conclusions are not inferred.", "next_action": "Review the measured observations below. A biological result is shown only after a validated modality-specific analysis is implemented and executed.", "findings": build_findings(usable_items), "biological_results": []}}


def request_to_observation(request: HandObservationRequest) -> HandObservation:
    return make_observation(**request.model_dump())


def read_hand_observations() -> list[HandObservation]:
    if not LONGITUDINAL_PATH.exists():
        return []
    observations: list[HandObservation] = []
    with LONGITUDINAL_PATH.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                observations.append(HandObservation(**json.loads(line)))
            except (TypeError, ValueError, json.JSONDecodeError):
                continue
    return observations


def persist_hand_observation(observation: HandObservation) -> None:
    LONGITUDINAL_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LONGITUDINAL_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(observation.to_dict(), ensure_ascii=False) + "\n")


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/status")
def status():
    registry = dataset_registry()
    return {"status": "ready", "raw_data": RAW_ROOT.exists(), "registered_datasets": len(registry), "available_datasets": sum(1 for x in registry if x["available"]), "modalities": sorted({x["modality"] for x in registry})}


@app.get("/api/datasets")
def datasets():
    return {"raw_exists": RAW_ROOT.exists(), "datasets": [validate_dataset(x) for x in dataset_registry()]}


@app.get("/api/pipeline")
def pipeline():
    return run_pipeline([])


@app.post("/api/pipeline/validate")
def validate(request: PipelineRequest):
    return run_pipeline(request.datasets)


@app.post("/api/run")
def run(request: PipelineRequest):
    return run_pipeline(request.datasets)


@app.post("/api/hand/observations")
def add_hand_observation(request: HandObservationRequest):
    observation = request_to_observation(request)
    persist_hand_observation(observation)
    return {"status": "recorded", "observation": observation.to_dict(), "evidence_boundary": "observation only; no diagnosis inferred"}


@app.get("/api/hand/subjects/{subject_id}")
def hand_subject(subject_id: str):
    observations = [x for x in read_hand_observations() if x.subject_id == subject_id]
    if not observations:
        raise HTTPException(status_code=404, detail="No longitudinal hand observations for this subject")
    grouped: dict[tuple[str, str], list[HandObservation]] = {}
    for observation in observations:
        grouped.setdefault((observation.session_id, observation.timepoint), []).append(observation)
    timepoints = [
        build_hand_snapshot(subject_id, session_id, timepoint, items)
        for (session_id, timepoint), items in sorted(grouped.items(), key=lambda item: item[0][1])
    ]
    return {"subject_id": subject_id, "timepoints": timepoints, "evidence_boundary": "observations only; no diagnosis inferred"}


@app.post("/api/hand/compare")
def compare_hand(request: HandComparisonRequest):
    baseline = [request_to_observation(x) for x in request.baseline]
    current = [request_to_observation(x) for x in request.current]
    changes = compare_numeric_observations(baseline, current)
    return {"changes": changes, "priority_zones": rank_zones_by_change(changes), "evidence_boundary": "measured change only; interpretation and diagnosis are separate layers"}


@app.get("/api/hand/schema")
def hand_schema():
    return {"subject": ["subject_id", "session_id", "timepoint"], "hand": ["hand_id", "laterality"], "zones": ["wrist", "palm", "thumb", "index", "middle", "ring", "little"], "observation_types": ["geometry", "landmark_quality", "image_quality", "appearance", "motion", "depth", "microstructure", "cellular", "molecular"], "evidence_levels": ["observed", "observed_change"], "interpretation": None}


if WEB_ROOT.exists():
    app.mount("/assets", StaticFiles(directory=WEB_ROOT), name="assets")


@app.get("/")
def home():
    return FileResponse(WEB_ROOT / "index.html")
