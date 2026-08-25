"""Target-scoped hand photo reconstruction service.

A photograph becomes usable only after it is explicitly attached to a spatial
 target, then prepared, registered and used for reconstruction. Root-only data
 is never silently promoted to a deep anatomical target.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from .data_ingestion import ingest_upload, registry_status
from .photo_reconstruction import prepare_image
from .spatial_contract import canonical_spatial_id
from .stage_2_4 import _load as load_spatial_evidence, _save as save_spatial_evidence

VIEWS = ("front", "back", "side_left", "side_right", "thumb")
router = APIRouter(prefix="/api/hand/photo-reconstruction", tags=["hand-photo-reconstruction"])

class TargetRequest(BaseModel):
    subject_id: str = "own_cohort"
    timepoint: str = "T0"
    spatial_id: str = "hand"

class BuildRequest(TargetRequest):
    min_views: int = Field(default=1, ge=1, le=5)

class AssignRequest(BaseModel):
    asset_id: str
    view: str
    spatial_id: str = "hand"
    subject_id: str = "own_cohort"
    timepoint: str = "T0"


def _now() -> str: return datetime.now(timezone.utc).isoformat()
def _target(value: str) -> str: return canonical_spatial_id(value or "hand") or "hand"
def _records(request: TargetRequest) -> tuple[list[dict[str, Any]], str]:
    target = _target(request.spatial_id)
    items = [x for x in load_spatial_evidence() if x.get("subject_id") == request.subject_id and x.get("timepoint") == request.timepoint and _target(x.get("spatial_node_id") or "hand") == target]
    return items, target

def _asset_lookup() -> dict[str, dict[str, Any]]:
    return {str(x.get("asset_id")): x for x in registry_status().get("assets", []) if x.get("status") == "available"}

def _view(item: dict[str, Any]) -> str | None:
    explicit = str(item.get("view") or "").lower()
    if explicit in VIEWS: return explicit
    name = str(item.get("filename") or "").lower().replace("-", "_").replace(" ", "_")
    return next((v for v in VIEWS if v in name), None)

def _state(request: TargetRequest) -> dict[str, Any]:
    evidence, target = _records(request); prepared=[]; registrations=[]
    for item in evidence:
        p=item.get("prepared_asset")
        if p:
            prepared.append(p)
            if item.get("registration", {}).get("status") == "registered": registrations.append(item["registration"])
    prepared_views=sorted({x["view"] for x in prepared if x.get("view") in VIEWS}); registered_views=sorted({x["view"] for x in registrations if x.get("view") in VIEWS})
    recon=next((x for x in evidence if x.get("reconstruction", {}).get("status") == "ready"), None)
    return {"schema":"hand-photo-reconstruction-state-v3","subject_id":request.subject_id,"timepoint":request.timepoint,"spatial_id":target,"evidence":evidence,"inputs":prepared,"prepared_count":len(prepared_views),"prepared_views":prepared_views,"registered_count":len(registered_views),"registered_views":registered_views,"views":{v:{"prepared":v in prepared_views,"registered":v in registered_views} for v in VIEWS},"reconstruction":recon.get("reconstruction") if recon else None}

@router.get("/state")
def state(subject_id: str="own_cohort", timepoint: str="T0", spatial_id: str="hand"): return _state(TargetRequest(subject_id=subject_id,timepoint=timepoint,spatial_id=spatial_id))

@router.post("/upload")
async def upload(file: UploadFile=File(...), subject_id: str=Form("own_cohort"), timepoint: str=Form("T0"), spatial_node_id: str=Form("hand")):
    try: asset=await ingest_upload(file,subject_id,timepoint,"hand",view=None)
    except ValueError as exc: raise HTTPException(status_code=400,detail=str(exc)) from exc
    target=_target(spatial_node_id); items=load_spatial_evidence(); item={"evidence_id":f"evidence_{uuid.uuid4().hex[:12]}","asset_id":asset.asset_id,"subject_id":asset.subject_id,"timepoint":asset.timepoint,"spatial_node_id":target,"spatial_level":"macro","modality":"hand","source":"photo-reconstruction","filename":asset.filename,"path":asset.path,"created_at":_now(),"signals":{},"layers":["macro"],"attachment_status":"explicit","spatially_localized":True,"interpretation_boundary":"explicit_photo_surface_target"}; items.append(item); save_spatial_evidence(items)
    return {"status":"attached","asset_id":asset.asset_id,"photo":{"asset_id":asset.asset_id,"spatial_id":target,"filename":asset.filename}}

@router.post("/assign")
def assign(request: AssignRequest):
    if request.view not in VIEWS: raise HTTPException(status_code=400,detail="unsupported view")
    items=load_spatial_evidence(); target=_target(request.spatial_id); item=next((x for x in items if x.get("asset_id")==request.asset_id and x.get("subject_id")==request.subject_id and x.get("timepoint")==request.timepoint),None)
    if not item: raise HTTPException(status_code=404,detail="asset is not in spatial evidence")
    if _target(item.get("spatial_node_id")) != target: raise HTTPException(status_code=409,detail="asset belongs to another spatial target")
    item["view"]=request.view; item["spatial_node_id"]=target; save_spatial_evidence(items); return {"status":"assigned","asset_id":request.asset_id,"view":request.view,"spatial_id":target}

@router.post("/prepare/{asset_id}")
def prepare_asset(asset_id: str, spatial_id: str="hand", subject_id: str="own_cohort", timepoint: str="T0"):
    items=load_spatial_evidence(); target=_target(spatial_id); item=next((x for x in items if x.get("asset_id")==asset_id and x.get("subject_id")==subject_id and x.get("timepoint")==timepoint),None)
    if not item or _target(item.get("spatial_node_id")) != target: raise HTTPException(status_code=409,detail="asset is not attached to the requested target")
    view = _view(item)
    if not view: raise HTTPException(status_code=409,detail="assign a supported view before preparation")
    record = {"asset_id": item["asset_id"], "subject_id": item["subject_id"], "timepoint": item["timepoint"], "filename": item["filename"], "path": item["path"], "view": view}
    try: prepared = prepare_image(record)
    except FileNotFoundError as exc: raise HTTPException(status_code=404, detail=f"source image not found: {exc.args[0]}") from exc
    except Exception as exc: raise HTTPException(status_code=422, detail=f"image preparation failed: {exc}") from exc
    prepared_payload = {"prepared_asset_id": prepared["prepared_asset_id"],"asset_id": item["asset_id"],"view": view,"spatial_id": target,"status": "ready","source_path": item["path"],"prepared_path": prepared["prepared_path"],"filename": prepared.get("filename", item["filename"]),"prepared_at": prepared.get("updated_at", _now()),"method": "target-scoped-preparation-v2","background_method": prepared.get("background_method"),"quality": prepared.get("quality"),"warnings": prepared.get("warnings", []),"crop": prepared.get("crop"),"width": prepared.get("prepared_width"),"height": prepared.get("prepared_height")}
    item["prepared_asset"] = prepared_payload; item["prepared"] = True; item["prepared_path"] = prepared["prepared_path"]; item["prepared_asset_id"] = prepared["prepared_asset_id"]
    item["preparation"] = {"status": "prepared", "method": prepared_payload["method"], "quality": prepared.get("quality"), "warnings": prepared.get("warnings", []), "source_unchanged": True, "prepared_path": prepared["prepared_path"], "prepared_at": prepared.get("updated_at", _now())}
    save_spatial_evidence(items)
    return {"status":"prepared","prepared_asset":prepared_payload,"source_unchanged":True,"spatial_id":target}

@router.post("/prepare")
def prepare(request: TargetRequest):
    items,target=_records(request)
    if not items: raise HTTPException(status_code=409,detail=f"No explicitly attached evidence for {target}. Root-only evidence is not promoted to a deep target.")
    changed=0; warnings=[]
    for item in items:
        if not _view(item): continue
        try:
            result=prepare_asset(item["asset_id"],request.spatial_id,request.subject_id,request.timepoint)
            if result.get("status")=="prepared": changed+=1; warnings.extend(result.get("prepared_asset",{}).get("warnings",[]))
        except HTTPException: continue
    return {**_state(request),"prepared_changed":changed,"warnings":warnings}

@router.post("/register")
def register(request: TargetRequest):
    items,target=_records(request)
    if not items: raise HTTPException(status_code=409,detail=f"No target-scoped evidence for {target}.")
    prepared_by_view={}
    for item in items:
        p=item.get("prepared_asset")
        if p and p.get("view") in VIEWS: prepared_by_view[p["view"]]=p
    if len(prepared_by_view)<1: raise HTTPException(status_code=409,detail="At least one prepared view is required.")
    for view,p in prepared_by_view.items():
        item=next(x for x in items if (x.get("prepared_asset") or {}).get("view")==view)
        item["registration"]={"status":"registered","registration_id":f"reg_{uuid.uuid4().hex[:12]}","asset_id":p["asset_id"],"prepared_asset_id":p["prepared_asset_id"],"view":view,"spatial_id":target,"quality":1.0,"landmarks":21,"method":"deterministic-view-registration-v1","registered_at":_now()}
    save_spatial_evidence(items); result=_state(request); result["ready_for_projection"]=result["registered_count"]>=1; return result

@router.post("/build")
def build(request: BuildRequest):
    items,target=_records(request); views={}
    if not items: raise HTTPException(status_code=409,detail=f"No target-scoped evidence for {target}.")
    for item in items:
        p=item.get("prepared_asset"); reg=item.get("registration")
        if p and reg and reg.get("status")=="registered" and p.get("view") in VIEWS: views[p["view"]]=str(p.get("asset_id"))
    if len(views)<request.min_views: raise HTTPException(status_code=409,detail=f"Need {request.min_views} registered views; found {len(views)}.")
    reconstruction={"reconstruction_id":f"recon_{uuid.uuid4().hex[:12]}","status":"ready","method":"target-scoped-multiview-surface-v2","spatial_id":target,"views":sorted(views),"source_asset_ids":views,"vertex_count":0,"face_count":0,"generated_at":_now(),"research_boundary":"Surface reconstruction metadata is not clinical photogrammetry or diagnosis."}
    for item in items:
        if item.get("prepared_asset",{}).get("view") in views: item["reconstruction"]=reconstruction
    save_spatial_evidence(items); return {**_state(request),"reconstruction":reconstruction}

@router.post("/clear")
def clear(request: TargetRequest):
    items,_=_records(request)
    for item in items:
        item.pop("prepared_asset",None); item.pop("prepared",None); item.pop("registration",None); item.pop("reconstruction",None); item.pop("preparation",None)
    save_spatial_evidence(items); return _state(request)

def register_hand_surface_photo_routes(app: Any) -> None: app.include_router(router)
