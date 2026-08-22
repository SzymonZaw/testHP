"""Stage 11-14 API: validation, result lifecycle and user-facing diagnostics."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .photo_reconstruction import _load_manifest
from .reconstruction_orchestrator import clear, get_result, run, validate

router = APIRouter(prefix="/api/hand/photo-reconstruction/quality", tags=["photo-reconstruction-quality"])


class ReconstructionRequest(BaseModel):
    subject_id: str
    timepoint: str = "default"
    resolution: int = 24


@router.get("/validate")
def validate_reconstruction(subject_id: str = "default", timepoint: str = "default"):
    return validate(subject_id, timepoint)


@router.get("/state")
def reconstruction_state(subject_id: str = "default", timepoint: str = "default"):
    records = [r for r in _load_manifest() if r.get("subject_id") == subject_id and r.get("timepoint") == timepoint]
    result = get_result(subject_id, timepoint)
    validation = validate(subject_id, timepoint)
    views = {}
    for record in records:
        view = record.get("view")
        if view:
            views[view] = record
    return {
        "schema": "photo-reconstruction-ui-v2",
        "subject_id": subject_id,
        "timepoint": timepoint,
        "views": views,
        "prepared_count": validation["prepared_count"],
        "registered_count": validation["registered_count"],
        "minimum_views": validation["minimum_views"],
        "validation": validation,
        "reconstruction": result,
    }


@router.post("/build")
def build_reconstruction(request: ReconstructionRequest):
    result = run(request.subject_id, request.timepoint, max(12, min(64, request.resolution)))
    if result.get("status") == "blocked":
        raise HTTPException(status_code=400, detail=result["validation"]["message"])
    return result


@router.post("/clear")
def clear_reconstruction(request: ReconstructionRequest):
    return {"cleared": clear(request.subject_id, request.timepoint)}
