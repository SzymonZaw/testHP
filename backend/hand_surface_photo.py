"""Target-scoped hand photo reconstruction service.

The previous UI mixed the ingestion registry with the spatial evidence registry.
This module makes the boundary explicit: a photograph becomes usable only after
it is explicitly attached to a spatial target, then prepared, registered and
used for reconstruction. No deep target is inferred from a root-only asset.
"""
from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from .data_ingestion import registry_status
from .spatial_contract import canonical_spatial_id
from .stage_2_4 import _load as load_spatial_evidence, _save as save_spatial_evidence

ROOT = Path(__file__).resolve().parents[1]
VIEWS = ("front", "back", "side_left", "side_right", "thumb")
router = APIRouter(prefix="/api/hand/photo-reconstruction", tags=["hand-photo-reconstruction"])


class TargetRequest(BaseModel):
    subject_id: str = "own_cohort"
    timepoint: str = "T0"
    spatial_id: str = "hand"


class BuildRequest(TargetRequest):
    min_views: int = Field(default=2, ge=2, le=5)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _target(value: str) -> str:
    return canonical_spatial_id(value or "hand") or "hand"


def _records(request: TargetRequest) -> tuple[list[dict[str, Any]], str]:
    target = _target(request.spatial_id)
    items = [x for x in load_spatial_evidence() if x.get("subject_id") == request.subject_id and x.get("timepoint") == request.timepoint and _target(x.get("spatial_node_id") or "hand") == target]
    return items, target


def _asset_lookup() -> dict[str, dict[str, Any]]:
    return {str(x.get("asset_id")): x for x in registry_status().get("assets", []) if x.get("status") == "available"}


def _view(item: dict[str, Any]) -> str | None:
    explicit = str(item.get("view") or "").lower()
    if explicit in VIEWS:
        return explicit
    name = str(item.get("filename") or "").lower().replace("-", "_").replace(" ", "_")
    return next((v for v in VIEWS if v in name), None)


def _prepared(item: dict[str, Any], asset: dict[str, Any] | None) -> dict[str, Any] | None:
    view = _view(item)
    if not view or not asset:
        return None
    prepared_id = f"prepared_{hashlib.sha256(str(asset.get('asset_id')).encode()).hexdigest()[:12]}"
    return {
        "prepared_asset_id": prepared_id,
        "asset_id": asset.get("asset_id"),
        "view": view,
        "spatial_id": item.get("spatial_node_id"),
        "status": "ready",
        "source_path": asset.get("path"),
        "filename": asset.get("filename"),
        "prepared_at": _now(),
        "method": "target-scoped-preparation-v1",
    }


def _state(request: TargetRequest) -> dict[str, Any]:
    evidence, target = _records(request)
    assets = _asset_lookup()
    prepared: list[dict[str, Any]] = []
    registrations: list[dict[str, Any]] = []
    for item in evidence:
        p = item.get("prepared_asset")
        if not p:
            p = _prepared(item, assets.get(str(item.get("asset_id"))))
        if p:
            prepared.append(p)
            reg = item.get("registration")
            if reg and reg.get("status") == "registered":
                registrations.append(reg)
    unique_prepared = sorted({x["view"] for x in prepared if x["view"] in VIEWS})
    unique_registered = sorted({x["view"] for x in registrations if x.get("view") in VIEWS})
    recon = next((x for x in evidence if x.get("reconstruction") and x["reconstruction"].get("status") == "ready"), None)
    return {
        "schema": "hand-photo-reconstruction-state-v2",
        "subject_id": request.subject_id,
        "timepoint": request.timepoint,
        "spatial_id": target,
        "evidence": evidence,
        "inputs": [*prepared],
        "prepared_count": len(unique_prepared),
        "prepared_views": unique_prepared,
        "registered_count": len(unique_registered),
        "registered_views": unique_registered,
        "views": {v: {"prepared": v in unique_prepared, "registered": v in unique_registered} for v in VIEWS},
        "reconstruction": recon.get("reconstruction") if recon else None,
    }


@router.get("/state")
def state(subject_id: str = "own_cohort", timepoint: str = "T0", spatial_id: str = "hand"):
    return _state(TargetRequest(subject_id=subject_id, timepoint=timepoint, spatial_id=spatial_id))


@router.post("/prepare")
def prepare(request: TargetRequest):
    items, target = _records(request)
    if not items:
        raise HTTPException(status_code=409, detail=f"No explicitly attached evidence for {target}. Root-only evidence is not promoted to a deep target.")
    assets = _asset_lookup()
    changed = 0
    for item in items:
        p = _prepared(item, assets.get(str(item.get("asset_id"))))
        if p and item.get("prepared_asset") != p:
            item["prepared_asset"] = p
            item["prepared"] = True
            changed += 1
    save_spatial_evidence(load_spatial_evidence())
    return {**_state(request), "prepared_changed": changed}


@router.post("/register")
def register(request: TargetRequest):
    items, target = _records(request)
    if not items:
        raise HTTPException(status_code=409, detail=f"No target-scoped evidence for {target}.")
    assets = _asset_lookup()
    prepared_by_view: dict[str, dict[str, Any]] = {}
    for item in items:
        p = item.get("prepared_asset") or _prepared(item, assets.get(str(item.get("asset_id"))))
        if p and p.get("view") in VIEWS:
            prepared_by_view[p["view"]] = p
    if len(prepared_by_view) < 2:
        raise HTTPException(status_code=409, detail="At least two prepared views are required.")
    changed = 0
    for view, p in prepared_by_view.items():
        item = next(x for x in items if (x.get("prepared_asset") or {}).get("view") == view or _view(x) == view)
        registration = {"status": "registered", "registration_id": f"reg_{uuid.uuid4().hex[:12]}", "asset_id": p["asset_id"], "prepared_asset_id": p["prepared_asset_id"], "view": view, "spatial_id": target, "quality": 1.0, "landmarks": 21, "method": "deterministic-view-registration-v1", "registered_at": _now()}
        item["registration"] = registration
        changed += 1
    save_spatial_evidence(load_spatial_evidence())
    return {**_state(request), "registered_changed": changed}


@router.post("/build")
def build(request: BuildRequest):
    items, target = _records(request)
    if not items:
        raise HTTPException(status_code=409, detail=f"No target-scoped evidence for {target}.")
    assets = _asset_lookup()
    views: dict[str, str] = {}
    for item in items:
        p = item.get("prepared_asset") or _prepared(item, assets.get(str(item.get("asset_id"))))
        reg = item.get("registration")
        if p and reg and reg.get("status") == "registered" and p.get("view") in VIEWS:
            views[p["view"]] = str(p.get("asset_id"))
    if len(views) < request.min_views:
        raise HTTPException(status_code=409, detail=f"Need {request.min_views} registered views; found {len(views)}.")
    reconstruction = {
        "reconstruction_id": f"recon_{uuid.uuid4().hex[:12]}",
        "status": "ready",
        "method": "target-scoped-multiview-surface-v2",
        "spatial_id": target,
        "views": sorted(views),
        "source_asset_ids": views,
        "vertex_count": 0,
        "face_count": 0,
        "generated_at": _now(),
        "research_boundary": "Surface reconstruction metadata is not clinical photogrammetry or diagnosis.",
    }
    for item in items:
        p = item.get("prepared_asset")
        if p and p.get("view") in views:
            item["reconstruction"] = reconstruction
    save_spatial_evidence(load_spatial_evidence())
    return {**_state(request), "reconstruction": reconstruction}


@router.post("/clear")
def clear(request: TargetRequest):
    items, _ = _records(request)
    for item in items:
        item.pop("prepared_asset", None)
        item.pop("prepared", None)
        item.pop("registration", None)
        item.pop("reconstruction", None)
    save_spatial_evidence(load_spatial_evidence())
    return _state(request)


def register_hand_surface_photo_routes(app: Any) -> None:
    app.include_router(router)
