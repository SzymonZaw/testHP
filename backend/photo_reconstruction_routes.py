from __future__ import annotations

import ssl
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import certifi
import truststore
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, Field

# Install Windows/system certificate-store backed SSL globally before any NIH
# reference requests are created. This is required in local Windows venvs where
# Python's OpenSSL CA bundle does not include the issuer trusted by the browser.
truststore.inject_into_ssl()

from .photo_reconstruction import assign_view, prepare_by_id, register_prepared, state, upload_photo
from .photo_reconstruction_file_resolver import resolve_photo_file
from .reconstruction_orchestrator import clear, get_result, run

router = APIRouter(prefix="/api/hand/photo-reconstruction", tags=["photo-reconstruction"])
REFERENCE_HAND_GLB_URL = "https://3d.nih.gov/api/submissions/23310/runs/c054b0b1-404c-4f43-b6a7-ddff98215e52/output-files/511811"

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
    try:
        result = run(request.subject_id, request.timepoint, request.resolution)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"reconstruction build failed: {exc}") from exc
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
        return FileResponse(resolve_photo_file(asset_id, prepared=False))
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="source photo not found") from exc

@router.get("/file/prepared/{prepared_asset_id}")
def photo_reconstruction_prepared(prepared_asset_id: str):
    try:
        return FileResponse(resolve_photo_file(prepared_asset_id, prepared=True), media_type="image/png")
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="prepared photo not found") from exc

@router.get("/reference-glb")
def reference_hand_glb():
    request = Request(REFERENCE_HAND_GLB_URL, headers={"Accept": "model/gltf-binary, application/octet-stream, */*", "User-Agent": "testHP-reference-hand/1.0"})
    contexts = [
        truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT),
        ssl.create_default_context(),
        ssl.create_default_context(cafile=certifi.where()),
    ]
    last_ssl_error: Exception | None = None
    try:
        for context in contexts:
            try:
                with urlopen(request, timeout=60, context=context) as upstream:
                    body = upstream.read()
                if not body:
                    raise HTTPException(status_code=502, detail="NIH reference asset returned an empty response")
                # NIH currently returns text/plain for this binary endpoint.
                # Validate the GLB signature and always expose the correct MIME type.
                if body[:4] != b"glTF":
                    raise HTTPException(status_code=502, detail="NIH reference asset is not a valid GLB (missing glTF magic)")
                return Response(content=body, media_type="model/gltf-binary", headers={"Cache-Control": "public, max-age=3600", "X-Content-Type-Options": "nosniff"})
            except HTTPException:
                raise
            except (ssl.SSLError, URLError) as exc:
                reason = getattr(exc, "reason", exc)
                if isinstance(reason, ssl.SSLError) or isinstance(exc, ssl.SSLError):
                    last_ssl_error = exc
                    continue
                raise
        raise last_ssl_error or URLError("TLS certificate verification failed")
    except HTTPException:
        raise
    except HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"NIH reference asset returned HTTP {exc.code}") from exc
    except (URLError, TimeoutError, ssl.SSLError, OSError) as exc:
        raise HTTPException(status_code=502, detail=f"NIH reference asset unavailable: {exc}") from exc
