from __future__ import annotations

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from .photo_reconstruction import assign_view, file_for, prepare_by_id, register_prepared, state, upload_photo
from .reconstruction_orchestrator import clear, get_result, run

router = APIRouter(prefix="/api/hand/photo-reconstruction", tags=["photo-reconstruction"])


class ViewAssignment(BaseModel):
    asset_id: str
    view: str


class BuildRequest(BaseModel):
    subject_id: str = "own_cohort"
    timepoint: str = "T0"
    resolution: int = Field(default=24, ge=8, le=64)


@router.get("/state")
def photo_reconstruction_state(subject_id: str = "own_cohort", timepoint: str = "T0"):
    return state(subject_id, timepoint)


@router.post("/upload")
async def photo_reconstruction_upload(file: UploadFile = File(...), subject_id: str = Form("own_cohort"), timepoint: str = Form("T0"), view: str | None = Form(None)):
    try:
        return await upload_photo(file, subject_id, timepoint, view)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/assign")
def photo_reconstruction_assign(request: ViewAssignment):
    try:
        return assign_view(request.asset_id, request.view)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="photo asset not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/prepare/{asset_id}")
def photo_reconstruction_prepare(asset_id: str):
    try:
        # Preparation is idempotent: if the server already has a prepared
        # result, return that persisted record instead of generating another
        # prepared asset. This also makes the endpoint safe when the UI has a
        # stale local snapshot.
        current = state("own_cohort", "T0")
        existing = next((item for item in current.get("inputs", []) if item.get("asset_id") == asset_id), None)
        if existing and existing.get("prepared") is True and existing.get("prepared_asset_id"):
            return existing
        return prepare_by_id(asset_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="photo asset not found") from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="source photo not found") from exc
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"photo preparation failed: {exc}") from exc


@router.post("/register")
def photo_reconstruction_register(subject_id: str = "own_cohort", timepoint: str = "T0"):
    try:
        return register_prepared(subject_id, timepoint)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"registration failed: {exc}") from exc


@router.post("/build")
def photo_reconstruction_build(request: BuildRequest):
    result = run(request.subject_id, request.timepoint, request.resolution)
    if result.get("status") == "blocked":
        return result
    return {"status": "published", "reconstruction": result}


@router.get("/result")
def photo_reconstruction_result(subject_id: str = "own_cohort", timepoint: str = "T0"):
    result = get_result(subject_id, timepoint)
    if result is None:
        raise HTTPException(status_code=404, detail="no reconstruction exists for this subject and timepoint")
    return result


@router.delete("/result")
def photo_reconstruction_clear(subject_id: str = "own_cohort", timepoint: str = "T0"):
    return {"status": "cleared", "deleted": clear(subject_id, timepoint)}


@router.get("/file/source/{asset_id}")
def photo_reconstruction_source(asset_id: str):
    try:
        return FileResponse(file_for(asset_id, prepared=False))
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="source photo not found") from exc


@router.get("/file/prepared/{prepared_asset_id}")
def photo_reconstruction_prepared(prepared_asset_id: str):
    try:
        return FileResponse(file_for(prepared_asset_id, prepared=True), media_type="image/png")
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="prepared photo not found") from exc
