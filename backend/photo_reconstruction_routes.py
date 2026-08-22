from __future__ import annotations

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

from .photo_reconstruction import assign_view, file_for, prepare_by_id, register_prepared, state, upload_photo

router = APIRouter(prefix="/api/hand/photo-reconstruction", tags=["photo-reconstruction"])


class ViewAssignment(BaseModel):
    asset_id: str
    view: str


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
