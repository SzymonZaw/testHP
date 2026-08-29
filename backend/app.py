from __future__ import annotations

import io
import mimetypes
from pathlib import Path
from typing import Any

import numpy as np
import pydicom
import yaml
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from PIL import Image
from pydantic import BaseModel

from .availability import build_availability
from .data_ingestion import ingest_upload, registry_status, safe_component
from .canonical_ingestion import canonical_registry_status, register_canonical_asset
from .hand_twin_v2 import build_twin
from .hand_zones import assign_feature_to_zone, zone_layout
from .images_layer import scan_skin, validate_skin_dataset
from .longitudinal import compare_observations
from .macro_analysis import analyze_image
from .observation_service import analyze_asset
from .observation_routes import router as observation_router
from .provenance import make_provenance
from .skin_longitudinal import compare_skin_observations
from .skin_ontology import ontology_snapshot
from .video_analysis import analyze_video_directory, inspect_video
from .stage_2_4 import register_stage_routes
from .stages_5_8 import register_stage_5_8_routes
from .hand_surface_photo import register_hand_surface_photo_routes
from .stages_21_32 import register_stage_21_32_routes
from .database_routes import router as database_router
from .user_input_routes import router as user_input_router

ROOT = Path(__file__).resolve().parents[1]
RAW_ROOT = ROOT / "data" / "raw"
CONFIG_PATH = ROOT / "configs" / "datasets.yaml"
HAND_ONTOLOGY_PATH = ROOT / "configs" / "hand_zones.yaml"
WEB_ROOT = ROOT / "web"
DIGITAL_TWIN_ROOT = ROOT / "frontend" / "digital-twin"
IMAGE_FORMATS = {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff", ".bmp"}
WSI_FORMATS = {".dcm", ".svs", ".ndpi", ".mrxs", ".tif", ".tiff"}
RNA_FORMATS = {".gz", ".mtx", ".tsv", ".csv", ".txt", ".h5", ".h5ad", ".tar"}

app = FastAPI(title="Human Pathology Platform", version="0.8.0")
register_stage_routes(app)
register_stage_5_8_routes(app)
register_hand_surface_photo_routes(app)
register_stage_21_32_routes(app)
app.include_router(observation_router)
app.include_router(database_router)
app.include_router(user_input_router)

class PipelineRequest(BaseModel):
    datasets: list[str] = []
class HandValidationRequest(BaseModel):
    subject_id: str
    timepoint: str
    session_id: str = "session-001"
class LongitudinalRequest(BaseModel):
    subject_id: str
    observations: list[dict[str, Any]]
class SkinLongitudinalRequest(BaseModel):
    subject_id: str
    observations: list[dict[str, Any]]

def load_config() -> dict[str, Any]:
    if not CONFIG_PATH.exists(): return {}
    with CONFIG_PATH.open("r", encoding="utf-8") as handle: return yaml.safe_load(handle) or {}

def load_hand_ontology() -> dict[str, Any]:
    if not HAND_ONTOLOGY_PATH.exists(): return {"hand": []}
    with HAND_ONTOLOGY_PATH.open("r", encoding="utf-8") as handle: return yaml.safe_load(handle) or {"hand": []}

def iter_files(path: Path): return [p for p in path.rglob("*") if p.is_file()] if path.exists() else []

def dataset_registry() -> list[dict[str, Any]]:
    cfg = load_config().get("datasets", {})
    registry: list[dict[str, Any]] = []
    for modality, entries in (("image", cfg.get("images", {})), ("wsi", cfg.get("wsi", {})), ("rna", cfg.get("rna", {})), ("hand", cfg.get("hand", {}))):
        for name, spec in entries.items():
            path_value = spec.get("path") or spec.get("root") or spec.get("images")
            if not path_value: continue
            path = ROOT / path_value; files = iter_files(path); enabled = bool(spec.get("enabled", True))
            formats = set(spec.get("formats") or spec.get("image_formats") or [])
            formats |= IMAGE_FORMATS if modality == "image" else set(); formats |= WSI_FORMATS if modality == "wsi" else set(); formats |= RNA_FORMATS if modality == "rna" else set()
            supported = [p for p in files if p.suffix.lower() in {x.lower() for x in formats}]
            empty = [p for p in supported if p.stat().st_size == 0]
            registry.append({"name": name, "modality": modality, "task": spec.get("task") or spec.get("source_type") or "research dataset", "path": path_value, "exists": path.exists(), "enabled": enabled, "files": len(files), "supported_files": len(supported), "bytes": sum(p.stat().st_size for p in files), "empty_files": len(empty), "available": bool(supported), "reason": spec.get("reason")})
    return registry

def validate_dataset(item: dict[str, Any]) -> dict[str, Any]:
    warnings: list[str] = []; errors: list[str] = []
    if not item["exists"]: errors.append("dataset directory is missing")
    if not item["enabled"]: warnings.append(item["reason"] or "dataset is disabled in configuration")
    if item["exists"] and item["supported_files"] == 0: warnings.append("no supported data files are available locally")
    if item["empty_files"]: warnings.append(f"{item['empty_files']} empty file(s) present")
    valid = not errors and (item["supported_files"] > 0 or not item["enabled"])
    return {**item, "valid": valid, "warnings": warnings, "errors": errors}

def run_pipeline(selected: list[str]) -> dict[str, Any]:
    registry = dataset_registry(); by_name = {x["name"]: x for x in registry}; chosen = selected or list(by_name)
    missing = [name for name in chosen if name not in by_name]; validations = {name: validate_dataset(by_name[name]) for name in chosen if name in by_name}; valid_items = [x for x in validations.values() if x["valid"]]
    warnings = [w for item in validations.values() for w in item["warnings"]]
    steps = [{"id":"input","name":"Input","purpose":"Identify selected research datasets","status":"ok" if not missing else "warning"},{"id":"ingestion","name":"Ingestion","purpose":"Read available files from data/raw","status":"ok" if valid_items else "warning"},{"id":"validation","name":"Validation","purpose":"Check files, formats and empty inputs","status":"ok" if all(x["valid"] for x in validations.values()) and validations else "warning"},{"id":"normalization","name":"Normalization","purpose":"Convert sources into common observations","status":"ok" if valid_items else "warning"},{"id":"fusion","name":"Multimodal fusion","purpose":"Aggregate dataset-level evidence without inventing subject links","status":"ok" if valid_items else "warning"},{"id":"results","name":"Research view","purpose":"Present evidence, coverage and limitations","status":"ok" if valid_items else "warning"}]
    return {"status":"ready" if valid_items and not missing else "warning","selected":chosen,"missing":missing,"datasets":list(validations.values()),"steps":steps,"summary":{"datasets":len(valid_items),"files":sum(x["supported_files"] for x in valid_items),"bytes":sum(x["bytes"] for x in valid_items),"modalities":sorted({x["modality"] for x in valid_items}),"linked_subjects":0},"warnings":warnings+(["Subject-level links are not inferred without a shared identifier."] if valid_items else []),"results":{"evidence_level":"dataset-level research evidence","biological_inference":"not claimed by this ingestion dashboard","next_action":"Review the modality coverage and validation warnings before enabling downstream models."}}

@app.get("/api/health")
def health(): return {"status":"ok"}
@app.get("/api/status")
def status():
    registry = dataset_registry(); assets = registry_status(); canonical = canonical_registry_status()
    return {"status":"ready","raw_data":RAW_ROOT.exists(),"registered_datasets":len(registry),"available_datasets":sum(1 for x in registry if x["available"]),"modalities":sorted({x["modality"] for x in registry}),"uploaded_assets":assets["count"],"canonical_data_objects":canonical["count"]}
@app.get("/api/datasets")
def datasets(): return {"raw_exists":RAW_ROOT.exists(),"datasets":[validate_dataset(x) for x in dataset_registry()]}
@app.get("/api/ingestion/assets")
def ingestion_assets(): return registry_status()
@app.get("/api/data-foundation/objects")
def data_foundation_objects(): return canonical_registry_status()
@app.get("/api/availability")
def availability(): return build_availability(registry_status()["assets"])
@app.get("/api/hand/ontology")
def hand_ontology(): return load_hand_ontology()
@app.get("/api/hand/zones")
def hand_zones(width: int = 900, height: int = 600): return {"coordinate_system":"image","zones":zone_layout(width,height)}
@app.get("/api/hand/twin")
def hand_twin(subject_id: str = "own_cohort"): return build_twin(subject_id, load_hand_ontology()).snapshot()

@app.get("/api/hand/analysis")
def hand_analysis(subject_id: str = "own_cohort", timepoint: str = "T0"):
    subject = safe_component(subject_id, "subject"); tp = safe_component(timepoint, "T0")
    assets = [x for x in registry_status()["assets"] if x.get("subject_id") == subject and x.get("timepoint") == tp]
    analyses = []
    for asset in assets:
        item = analyze_asset(asset)
        if asset.get("modality") == "hand" and asset.get("status") == "available":
            image_path = ROOT / asset["path"]
            macro = analyze_image(image_path); features = macro.get("features", {})
            width, height = features.get("width_px", 0), features.get("height_px", 0); view = asset.get("view") or "unknown"
            zone = assign_feature_to_zone(width / 2, height / 2, width, height) if width and height else None
            item = {**item, "macro": macro, "zone_id": zone, "zone_assignment": "view_center_proxy" if zone else "unassigned", "view": view}
        analyses.append(item)
    hand_assets = [x for x in analyses if x.get("modality") == "hand" and x.get("status") == "ready"]
    return {"subject_id":subject_id,"timepoint":timepoint,"analysis_level":"macro_features","biological_inference":"not_established","assets":analyses,"zones": {z["zone_id"]:[a["asset_id"] for a in hand_assets if a.get("zone_id")==z["zone_id"]] for z in zone_layout(900,600)},"coverage":{"macro":100 if hand_assets else 0,"micro":100 if any(x.get("modality")=="wsi" and x.get("status")=="ready" for x in analyses) else 0,"molecular":100 if any(x.get("modality")=="rna" and x.get("status")=="ready" for x in analyses) else 0}}

@app.get("/api/spatial/evidence/{asset_id}")
def spatial_evidence(asset_id: str):
    asset = next((x for x in registry_status()["assets"] if x.get("asset_id") == asset_id), None)
    if not asset or asset.get("status") != "available": raise HTTPException(status_code=404, detail="spatial evidence not found")
    path = ROOT / str(asset.get("path", ""))
    try: path.resolve().relative_to(ROOT.resolve())
    except ValueError: raise HTTPException(status_code=404, detail="invalid evidence path")
    if not path.is_file(): raise HTTPException(status_code=404, detail="evidence file missing")
    media_type = asset.get("media_type") or mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    return FileResponse(path, media_type=media_type, filename=asset.get("filename") or path.name)

@app.get("/api/spatial/preview/{asset_id}")
def spatial_preview(asset_id: str, max_width: int = 1800, max_height: int = 1200):
    asset = next((x for x in registry_status()["assets"] if x.get("asset_id") == asset_id), None)
    if not asset or asset.get("status") != "available": raise HTTPException(status_code=404, detail="spatial evidence not found")
    path = ROOT / str(asset.get("path", ""))
    try: path.resolve().relative_to(ROOT.resolve())
    except ValueError: raise HTTPException(status_code=404, detail="invalid evidence path")
    if not path.is_file(): raise HTTPException(status_code=404, detail="evidence file missing")
    try:
        if asset.get("modality") == "wsi" and path.name.lower().endswith(".dcm"):
            dataset = pydicom.dcmread(str(path), force=True); pixels = dataset.pixel_array.astype(np.float32)
            if pixels.ndim > 2: pixels = pixels[0]
            pixels -= pixels.min(); peak = pixels.max()
            if peak > 0: pixels /= peak
            image = Image.fromarray(np.uint8(pixels * 255), mode="L").convert("RGB")
        else:
            image = Image.open(path); image.seek(0); image = image.convert("RGB")
        image.thumbnail((max(256, min(max_width, 2400)), max(256, min(max_height, 1800))), Image.Resampling.LANCZOS)
        output = io.BytesIO(); image.save(output, format="PNG", optimize=True)
        return Response(content=output.getvalue(), media_type="image/png", headers={"Cache-Control":"no-store", "X-Spatial-Source": asset.get("filename") or path.name})
    except Exception as exc: raise HTTPException(status_code=415, detail=f"preview unavailable for {path.name}: {exc}") from exc

@app.get("/api/hand/evidence/{asset_id}")
def hand_evidence(asset_id: str):
    asset = next((x for x in registry_status()["assets"] if x.get("asset_id") == asset_id), None)
    if not asset or asset.get("modality") != "hand" or asset.get("status") != "available": raise HTTPException(status_code=404,detail="hand evidence not found")
    path = ROOT / asset["path"]
    try: path.resolve().relative_to(ROOT.resolve())
    except ValueError: raise HTTPException(status_code=404, detail="invalid evidence path")
    if not path.is_file(): raise HTTPException(status_code=404, detail="evidence file missing")
    return FileResponse(path)

@app.post("/api/hand/validate")
def validate_hand(request: HandValidationRequest):
    subject=safe_component(request.subject_id,"subject"); root=RAW_ROOT/"hand"/subject/safe_component(request.timepoint,"T0"); required=["front","back","thumb","side_left","side_right"]
    found={name:next((p for p in root.glob(f"{name}.*") if p.is_file() and p.suffix.lower() in IMAGE_FORMATS and p.stat().st_size>0),None) for name in required}; missing=[name for name,path in found.items() if path is None]
    return {"subject_id":request.subject_id,"session_id":request.session_id,"timepoint":request.timepoint,"status":"available" if not missing else ("partial" if any(found.values()) else "unavailable"),"required_views":required,"available_views":[name for name,path in found.items() if path],"missing_views":missing}

@app.post("/api/upload/{modality}")
async def upload(modality: str, file: UploadFile = File(...), subject_id: str = Form("own_cohort"), timepoint: str = Form("T0"), subtype: str | None = Form(None), view: str | None = Form(None)):
    if modality not in {"hand","video","images","wsi","rna","metadata"}: raise HTTPException(status_code=400,detail="unsupported modality")
    try:
        asset=await ingest_upload(file,subject_id,timepoint,modality,subtype,view)
        canonical=register_canonical_asset(asset)
    except ValueError as exc: raise HTTPException(status_code=400,detail=str(exc)) from exc
    analysis=analyze_asset(asset.to_dict())
    return {"status":asset.status,"asset":asset.to_dict(),"canonical_data_object":canonical.to_dict(),"provenance":make_provenance(asset_id=asset.asset_id,source=asset.path,method="upload"),"analysis":analysis}

@app.post("/api/longitudinal/compare")
def longitudinal_compare(request: LongitudinalRequest): return {"subject_id":request.subject_id,"changes":compare_observations(request.subject_id,request.observations)}
@app.get("/api/video/inspect")
def video_inspect(path: str):
    target=ROOT/path
    if not target.is_file(): raise HTTPException(status_code=404,detail="video not found")
    return inspect_video(target)
@app.get("/api/video")
def video_inventory(): return {"videos":analyze_video_directory(RAW_ROOT/"hand"/"media")}
@app.get("/api/skin/longitudinal")
def skin_longitudinal(request: SkinLongitudinalRequest): return {"subject_id":request.subject_id,"changes":compare_skin_observations(request.subject_id,request.observations)}

@app.get("/api/ontology/skin")
def skin_ontology(): return ontology_snapshot()

app.mount("/web", StaticFiles(directory=WEB_ROOT), name="web")
app.mount("/digital-twin", StaticFiles(directory=DIGITAL_TWIN_ROOT, html=True), name="digital-twin")
