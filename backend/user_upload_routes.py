"""End-user upload endpoint that turns uploaded evidence into user_input_v1.

This is deliberately separate from the research-dataset registry. The endpoint
stores the uploaded object, creates the canonical user package metadata, and
returns a capability plan. It does not treat absent modalities as negative
findings and does not manufacture biological results.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from core.input_validation import validate_user_input_package
from core.user_capabilities import build_user_analysis_plan
from .data_ingestion import ingest_upload

router = APIRouter(prefix="/api/user-upload", tags=["user-upload"])


MODALITY_KIND = {
    "hand": "hand_images",
    "images": "hand_images",
    "video": "hand_video",
    "wsi": "tissue_wsi",
    "metadata": "clinical_context",
}


def _rna_kind(subtype: str | None) -> str:
    value = (subtype or "").lower()
    if "single" in value or "scrna" in value or "sc_rna" in value:
        return "single_cell_rna"
    return "bulk_rna"


def _kind(modality: str, subtype: str | None) -> str:
    if modality == "rna":
        return _rna_kind(subtype)
    try:
        return MODALITY_KIND[modality]
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=f"unsupported upload modality: {modality}") from exc


def _package(asset: Any, acquisition_time: str, laterality: str, kind: str) -> dict[str, Any]:
    return {
        "schema_version": "user_input_v1",
        "subject": {"subject_id": asset.subject_id},
        "acquisition": {
            "timepoint_id": asset.timepoint,
            "acquisition_time": acquisition_time,
            "laterality": laterality,
        },
        "inputs": [
            {
                "input_id": asset.asset_id,
                "kind": kind,
                "uri": f"upload://{asset.asset_id}",
                "format": "application/octet-stream",
                "provenance": {"source_type": "user"},
                "metadata": {
                    "filename": asset.filename,
                    "size_bytes": asset.size_bytes,
                    "stored_path": asset.path,
                },
            }
        ],
    }


@router.post("/analyze")
async def upload_and_plan(
    file: UploadFile = File(...),
    modality: str = Form(...),
    subject_id: str = Form("user_subject"),
    timepoint: str = Form("T0"),
    subtype: str | None = Form(None),
    view: str | None = Form(None),
    laterality: str = Form("unknown"),
) -> dict[str, Any]:
    """Upload one user object and immediately return its evidence/capability plan."""
    if laterality not in {"left", "right", "bilateral", "unknown"}:
        raise HTTPException(status_code=400, detail="laterality must be left, right, bilateral, or unknown")

    try:
        asset = await ingest_upload(file, subject_id, timepoint, modality, subtype, view)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    package = _package(asset, datetime.now(timezone.utc).isoformat(), laterality, _kind(modality, subtype))
    report = validate_user_input_package(package)
    plan = build_user_analysis_plan(report)

    return {
        "status": "ready" if report.valid else "invalid",
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
        "policy": {
            "training_data_used_as_user_input": False,
            "raw_research_registry_used_for_capability_resolution": False,
            "missing_data_fabricated": False,
            "biological_diagnosis_claimed": False,
        },
    }
