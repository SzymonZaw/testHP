"""Target-scoped hand photo acquisition and reconstruction pipeline.

The service keeps acquisition, preparation, landmark detection, registration and
reconstruction separate. It never labels metadata as a completed 3D mesh.
"""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Any
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from .data_ingestion import ingest_upload, registry_status
from .photo_reconstruction import prepare_image
from .hand_segmentation import detect_hand_landmarks
from .spatial_contract import canonical_spatial_id
from .stage_2_4 import _load as load_spatial_evidence, _save as save_spatial_evidence
from .hand_data_pipeline import router as hand_data_pipeline_router

VIEWS = ("front", "back", "side_left", "side_right", "thumb")
router = APIRouter(prefix="/api/hand/photo-reconstruction", tags=["hand-photo-reconstruction"])

class TargetRequest(BaseModel):
    subject_id: str = "own_cohort"
    timepoint: str = "T0"
    spatial_id: str = "hand"
class BuildRequest(TargetRequest):
    min_views: int = 1
class AssignRequest(BaseModel):
    asset_id: str
    view: str
    spatial_id: str = "hand"
    subject_id: str = "own_cohort"
    timepoint: str = "T0"

def _now() -> str: return datetime.now(timezone.utc).isoformat()
def _target(value: str) -> str: return canonical_spatial_id(value or "hand") or "hand"
def _records(request: TargetRequest):
    target = _target(request.spatial_id)
    items = [x for x in load_spatial_evidence() if x.get("subject_id") == request.subject_id and x.get("timepoint") == request.timepoint and _target(x.get("spatial_node_id") or "hand") == target]
    return items, target

def _view(item: dict[str, Any]) -> str | None:
    explicit = str(item.get("view") or "").lower()
    return explicit if explicit in VIEWS else None

def _state(request: TargetRequest) -> dict[str, Any]:
    evidence, target = _records(request); prepared=[]; registrations=[]; landmarks=[]
    for item in evidence:
        if item.get("prepared_asset"): prepared.append(item["prepared_asset"])
        if item.get("landmarks"): landmarks.append(item["landmarks"])
        if item.get("registration", {}).get("status") == "registered": registrations.append(item["registration"])
    prepared_views=sorted({x.get("view") for x in prepared if x.get("view") in VIEWS})
    registered_views=sorted({x.get("view") for x in registrations if x.get("view") in VIEWS})
    recon=next((x for x in evidence if x.get("reconstruction", {}).get("status") in {"metadata-ready", "ready"}), None)
    return {"schema":"hand-photo-reconstruction-state-v4","subject_id":request.subject_id,"timepoint":request.timepoint,"spatial_id":target,"evidence":evidence,"inputs":prepared,"landmarks":landmarks,"prepared_count":len(prepared_views),"prepared_views":prepared_views,"registered_count":len(registered_views),"registered_views":registered_views,"views":{v:{"prepared":v in prepared_views,"registered":v in registered_views} for v in VIEWS},"reconstruction":recon.get("reconstruction") if recon else None}

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
    item["view"]=request.view; save_spatial_evidence(items); return {"status":"assigned","asset_id":request.asset_id,"view":request.view,"spatial_id":target}

@router.post("/prepare/{asset_id}")
def prepare_asset(asset_id: str, spatial_id: str="hand", subject_id: str="own_cohort", timepoint: str="T0"):
    items=load_spatial_evidence(); target=_target(spatial_id); item=next((x for x in items if x.get("asset_id")==asset_id and x.get("subject_id")==subject_id and x.get("timepoint")==timepoint),None)
    if not item or _target(item.get("spatial_node_id")) != target: raise HTTPException(status_code=409,detail="asset is not attached to the requested target")
    view = _view(item)
    if not view: raise HTTPException(status_code=409,detail="assign a supported view before preparation")
    record={"asset_id":item["asset_id"],"subject_id":item["subject_id"],"timepoint":item["timepoint"],"filename":item["filename"],"path":item["path"],"view":view}
    try: prepared=prepare_image(record)
    except FileNotFoundError as exc: raise HTTPException(status_code=404,detail=f"source image not found: {exc.args[0]}") from exc
    except Exception as exc: raise HTTPException(status_code=422,detail=f"image preparation failed: {exc}") from exc
    landmarks=detect_hand_landmarks(prepared["prepared_path"])
    landmark_status=landmarks.get("status")
    prepared_payload={"prepared_asset_id":prepared["prepared_asset_id"],"asset_id":item["asset_id"],"view":view,"spatial_id":target,"status":"ready","source_path":item["path"],"prepared_path":prepared["prepared_path"],"filename":prepared.get("filename",item["filename"]),"prepared_at":prepared.get("updated_at",_now()),"method":"target-scoped-preparation-v3","background_method":prepared.get("background_method"),"quality":prepared.get("quality"),"warnings":prepared.get("warnings",[]),"crop":prepared.get("crop"),"width":prepared.get("prepared_width"),"height":prepared.get("prepared_height")}
    item["prepared_asset"]=prepared_payload; item["prepared"]=True; item["prepared_path"]=prepared["prepared_path"]; item["prepared_asset_id"]=prepared["prepared_asset_id"]
    item["landmarks"]={"status":landmark_status,"method":landmarks.get("method"),"points":landmarks.get("landmarks",[]),"count":len(landmarks.get("landmarks",[])),"detected_at":_now(),"reason":landmarks.get("reason")}
    item["preparation"]={"status":"prepared","method":prepared_payload["method"],"quality":prepared.get("quality"),"warnings":prepared.get("warnings",[]),"source_unchanged":True,"prepared_path":prepared["prepared_path"],"prepared_at":prepared.get("updated_at",_now()),"landmark_status":landmark_status}
    save_spatial_evidence(items)
    return {"status":"prepared","prepared_asset":prepared_payload,"landmarks":item["landmarks"],"source_unchanged":True,"spatial_id":target}

@router.post("/prepare")
def prepare(request: TargetRequest):
    items,target=_records(request)
    if not items: raise HTTPException(status_code=409,detail=f"No explicitly attached evidence for {target}.")
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
    registered=0
    for item in items:
        p=item.get("prepared_asset"); lm=item.get("landmarks") or {}
        if not p or p.get("view") not in VIEWS or lm.get("count",0) == 0: continue
        item["registration"]={"status":"registered-2d","registration_id":f"reg_{uuid.uuid4().hex[:12]}","asset_id":p["asset_id"],"prepared_asset_id":p["prepared_asset_id"],"view":p["view"],"spatial_id":target,"quality":p.get("quality",{}).get("overall",0.0),"landmarks":lm.get("count",0),"method":"landmark-registration-v1","registered_at":_now(),"coordinate_system":"hand-surface-v1"}; registered+=1
    save_spatial_evidence(items); result=_state(request); result["ready_for_multiview_reconstruction"]=result["registered_count"]>=2; result["registration_boundary"]="2D view registration only; no 3D geometry is inferred here."; return result

@router.post("/build")
def build(request: BuildRequest):
    items,target=_records(request); views={}
    if not items: raise HTTPException(status_code=409,detail=f"No target-scoped evidence for {target}.")
    for item in items:
        p=item.get("prepared_asset"); reg=item.get("registration")
        if p and reg and reg.get("status")=="registered-2d" and p.get("view") in VIEWS: views[p["view"]]=str(p.get("asset_id"))
    if len(views)<request.min_views: raise HTTPException(status_code=409,detail=f"Need {request.min_views} registered views; found {len(views)}.")
    reconstruction={"reconstruction_id":f"recon_{uuid.uuid4().hex[:12]}","status":"metadata-ready","method":"multiview-input-manifest-v1","spatial_id":target,"views":sorted(views),"source_asset_ids":views,"geometry_reference":None,"vertex_count":None,"face_count":None,"generated_at":_now(),"research_boundary":"Inputs are ready for a real calibrated multiview reconstruction worker; no 3D mesh is claimed."}
    for item in items:
        if item.get("prepared_asset",{}).get("view") in views: item["reconstruction"]=reconstruction
    save_spatial_evidence(items); return {**_state(request),"reconstruction":reconstruction}

@router.post("/clear")
def clear(request: TargetRequest):
    items,_=_records(request)
    for item in items:
        for key in ("prepared_asset","prepared","registration","reconstruction","preparation","landmarks"): item.pop(key,None)
    save_spatial_evidence(items); return _state(request)

def register_hand_surface_photo_routes(app: Any) -> None:
    app.include_router(router)
    app.include_router(hand_data_pipeline_router)
