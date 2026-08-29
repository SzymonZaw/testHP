"""End-user upload endpoint: validate, plan, and execute available analyses."""

from __future__ import annotations

import json
import re
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from core.input_validation import validate_user_input_package
from core.user_capabilities import build_user_analysis_plan
from backend.macro_analysis import analyze_image
from backend.video_analysis import inspect_video
from pipeline.wsi_pipeline import analyze_wsi

ROOT = Path(__file__).resolve().parents[1]
USER_UPLOAD_ROOT = ROOT / "data" / "user_uploads"
USER_UPLOAD_INDEX = USER_UPLOAD_ROOT / "index.json"
SAFE = re.compile(r"[^A-Za-z0-9._-]+")

router = APIRouter(prefix="/api/user-upload", tags=["user-upload"])

MODALITY_KIND = {
    "hand": "hand_images",
    "images": "hand_images",
    "video": "hand_video",
    "wsi": "tissue_wsi",
    "metadata": "clinical_context",
}

ALLOWED_EXTENSIONS = {
    "hand": {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff", ".bmp"},
    "images": {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff", ".bmp"},
    "video": {".mp4", ".mov", ".m4v", ".avi", ".mkv"},
    "wsi": {".dcm", ".svs", ".ndpi", ".mrxs", ".tif", ".tiff", ".ome.tif", ".ome.tiff"},
    "rna": {".csv", ".tsv", ".txt", ".mtx", ".gz", ".h5", ".h5ad", ".tar"},
    "metadata": {".json", ".yaml", ".yml", ".csv", ".tsv"},
}


@dataclass
class UserUploadAsset:
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
    source: str = "user"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _safe(value: str, fallback: str) -> str:
    cleaned = SAFE.sub("_", value.strip()).strip("._")
    return cleaned or fallback


def _extension(filename: str) -> str:
    lower = filename.lower()
    if lower.endswith(".ome.tiff"):
        return ".ome.tiff"
    if lower.endswith(".ome.tif"):
        return ".ome.tif"
    return Path(lower).suffix


def _rna_kind(subtype: str | None) -> str:
    value = (subtype or "").lower()
    return "single_cell_rna" if any(x in value for x in ("single", "scrna", "sc_rna")) else "bulk_rna"


def _kind(modality: str, subtype: str | None) -> str:
    if modality == "rna":
        return _rna_kind(subtype)
    try:
        return MODALITY_KIND[modality]
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=f"unsupported upload modality: {modality}") from exc


def _load_index() -> list[dict[str, Any]]:
    if not USER_UPLOAD_INDEX.exists():
        return []
    try:
        return json.loads(USER_UPLOAD_INDEX.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []


def _save_index(items: list[dict[str, Any]]) -> None:
    USER_UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
    tmp = USER_UPLOAD_INDEX.with_suffix(".tmp")
    tmp.write_text(json.dumps(items, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(USER_UPLOAD_INDEX)


async def _store_upload(
    file: UploadFile,
    subject_id: str,
    timepoint: str,
    modality: str,
    subtype: str | None,
    view: str | None,
) -> UserUploadAsset:
    if modality not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"unsupported upload modality: {modality}")
    filename = _safe(file.filename or "upload.bin", "upload.bin")
    if _extension(filename) not in ALLOWED_EXTENSIONS[modality]:
        raise HTTPException(status_code=400, detail=f"unsupported file extension for modality {modality}")

    subject = _safe(subject_id, "user_subject")
    tp = _safe(timepoint, "T0")
    asset_id = f"user_asset_{uuid.uuid4().hex[:12]}"
    target_dir = USER_UPLOAD_ROOT / subject / tp
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{asset_id}_{filename}"
    content = await file.read()
    target.write_bytes(content)

    asset = UserUploadAsset(
        asset_id,
        subject,
        tp,
        modality,
        subtype,
        view,
        target.relative_to(ROOT).as_posix(),
        filename,
        len(content),
        "available" if content else "unavailable",
        datetime.now(timezone.utc).isoformat(),
    )
    index = _load_index()
    index.append(asset.to_dict())
    _save_index(index)
    return asset


def _package(asset: UserUploadAsset, laterality: str, kind: str) -> dict[str, Any]:
    return {
        "schema_version": "user_input_v1",
        "subject": {"subject_id": asset.subject_id},
        "acquisition": {
            "timepoint_id": asset.timepoint,
            "acquisition_time": asset.created_at,
            "laterality": laterality,
        },
        "inputs": [{
            "input_id": asset.asset_id,
            "kind": kind,
            "uri": f"upload://{asset.asset_id}",
            "format": "application/octet-stream",
            "provenance": {"source_type": "user"},
            "metadata": {
                "filename": asset.filename,
                "size_bytes": asset.size_bytes,
                "modality": asset.modality,
                "subtype": asset.subtype,
                "view": asset.view,
            },
        }],
    }


def _execute_available_analysis(asset: UserUploadAsset) -> dict[str, Any]:
    """Run only analyses that are implemented and directly match the upload."""
    if asset.status != "available":
        return {"status": "skipped", "reason": "upload is empty or unavailable"}

    path = ROOT / asset.path
    if not path.is_file():
        return {"status": "skipped", "reason": "uploaded file is no longer available"}

    try:
        if asset.modality in {"hand", "images"}:
            result = analyze_image(path)
            return {
                "status": "completed",
                "analysis_id": "macro_image_analysis",
                "analysis_level": "macro",
                "biological_inference": "not_established",
                "result": result,
            }

        if asset.modality == "video":
            result = inspect_video(path)
            return {
                "status": "completed",
                "analysis_id": "hand_video_inspection",
                "analysis_level": "macro",
                "biological_inference": "not_established",
                "result": result,
            }

        if asset.modality == "wsi":
            result = analyze_wsi(path)
            return {
                "status": "completed",
                "analysis_id": "wsi_spatial_cell_morphology",
                "analysis_level": "cell_and_tissue_spatial",
                "biological_inference": "not_established",
                "result": result,
            }

        return {
            "status": "not_implemented",
            "analysis_id": None,
            "analysis_level": None,
            "biological_inference": "not_established",
            "reason": f"No executable end-user adapter is registered yet for {asset.modality}.",
        }
    except Exception as exc:
        return {
            "status": "failed",
            "analysis_id": None,
            "analysis_level": None,
            "biological_inference": "not_established",
            "reason": f"analysis failed: {type(exc).__name__}: {exc}",
        }


@router.post("/analyze")
async def upload_and_analyze(
    file: UploadFile = File(...),
    modality: str = Form(...),
    subject_id: str = Form("user_subject"),
    timepoint: str = Form("T0"),
    subtype: str | None = Form(None),
    view: str | None = Form(None),
    laterality: str = Form("unknown"),
) -> dict[str, Any]:
    """Upload one user object, validate it, plan capabilities, then execute available analysis."""
    if laterality not in {"left", "right", "bilateral", "unknown"}:
        raise HTTPException(status_code=400, detail="laterality must be left, right, bilateral, or unknown")

    asset = await _store_upload(file, subject_id, timepoint, modality, subtype, view)
    package = _package(asset, laterality, _kind(modality, subtype))
    report = validate_user_input_package(package)
    plan = build_user_analysis_plan(report)
    execution = _execute_available_analysis(asset) if report.valid else {
        "status": "skipped",
        "reason": "input package failed validation",
    }

    return {
        "status": "ready" if report.valid and execution["status"] in {"completed", "not_implemented"} else "invalid",
        "asset": asset.to_dict(),
        "user_input_package": package,
        "validation": {
            "valid": report.valid,
            "evidence_status": report.evidence_status.value,
            "available_modalities": list(report.available_modalities),
            "missing_modalities": list(report.missing_modalities),
            "issues": [{"path": x.path, "message": x.message} for x in report.issues],
        },
        "analysis_plan": plan,
        "execution": execution,
        "policy": {
            "training_data_used_as_user_input": False,
            "research_data_raw_registry_used_for_user_package": False,
            "missing_data_fabricated": False,
            "biological_diagnosis_claimed": False,
            "unsupported_biological_age_claimed": False,
        },
    }
