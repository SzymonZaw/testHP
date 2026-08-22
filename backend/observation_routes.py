"""HTTP API for explicit, traceable biological observations."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from .biological_state_routes import biological_state
from .data_ingestion import registry_status
from .observation_registry import archive_observation, create_observation, get_observation, list_observations, observation_history, restore_observation, update_observation
from .photo_reconstruction_routes import router as photo_reconstruction_router
from .spatial_object_routes import router as spatial_object_router

router = APIRouter(tags=["biological-observations"])
router.include_router(photo_reconstruction_router)
router.include_router(spatial_object_router)


class ObservationCreateRequest(BaseModel):
    subject_id: str = "own_cohort"
    timepoint: str = "T0"
    spatial_id: str
    location_name: str | None = None
    location_level: str = "site"
    parent_id: str | None = None
    biological_level: str
    modality: str = "manual-entry"
    name: str
    value: Any = None
    observed_at: str | None = None
    source: str = "manual-entry"
    notes: str = ""
    evidence_id: str | None = None
    evidence_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    evidence_type: str = "source"
    validated_interpretations: dict[str, Any] = Field(default_factory=dict)
    author: str = "local-user"
    source_measurement_ids: list[str] = Field(default_factory=list)


class ObservationUpdateRequest(BaseModel):
    name: str | None = None
    value: Any = None
    observed_at: str | None = None
    source: str | None = None
    notes: str | None = None
    modality: str | None = None
    biological_level: str | None = None
    evidence_id: str | None = None
    evidence_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    evidence_type: str | None = None
    validated_interpretations: dict[str, Any] | None = None
    author: str | None = None
    source_measurement_ids: list[str] | None = None


class ObservationLifecycleRequest(BaseModel):
    author: str = "local-user"
    reason: str = ""


def _in_spatial_scope(selected_spatial_id: str, candidate_spatial_id: str, include_descendants: bool) -> bool:
    selected = str(selected_spatial_id or "").strip().strip("/")
    candidate = str(candidate_spatial_id or "").strip().strip("/")
    if not selected or not candidate:
        return False
    if candidate == selected:
        return True
    return include_descendants and candidate.startswith(f"{selected}/")


@router.get("/api/spatial/registry")
def spatial_registry(
    subject_id: str = "own_cohort",
    timepoint: str = "T0",
    spatial_node_id: str | None = None,
    debug: bool = False,
):
    assets = [
        dict(item)
        for item in registry_status()["assets"]
        if item.get("subject_id") == subject_id and item.get("timepoint") == timepoint
    ]
    target = str(spatial_node_id or "").strip().strip("/") or None
    decisions: list[dict[str, Any]] = []
    matched: list[dict[str, Any]] = []
    for item in assets:
        actual = str(item.get("spatial_node_id") or item.get("spatial_id") or item.get("target") or "").strip().strip("/") or None
        attachment = item.get("attachment_status") or ("explicit" if item.get("spatial_node_id") else "registered_root")
        localized = item.get("spatially_localized")
        if target is None:
            is_match = True; reason = "NO_TARGET_REQUESTED"
        elif actual == target:
            is_match = True; reason = "EXACT_SPATIAL_NODE_MATCH"
        elif actual and target.startswith(f"{actual}/"):
            is_match = False; reason = "ROOT_OR_ANCESTOR_ATTACHMENT_NOT_DEEP_ATTACHED"
        elif not actual:
            is_match = False; reason = "MISSING_SPATIAL_NODE_ID"
        else:
            is_match = False; reason = "SPATIAL_NODE_ID_MISMATCH"
        decision = {
            "matched": is_match, "reason": reason,
            "evidence_id": item.get("evidence_id") or item.get("asset_id"),
            "asset_id": item.get("asset_id"), "filename": item.get("filename"),
            "actual_spatial_node_id": actual, "expected_spatial_node_id": target,
            "attachment_status": attachment, "spatially_localized": localized,
            "subject_id": item.get("subject_id"), "timepoint": item.get("timepoint"),
            "modality": item.get("modality"), "source": item.get("source"),
            "status": item.get("status"),
            "prepared": bool(item.get("prepared") or item.get("prepared_asset") or item.get("prepared_asset_id")),
        }
        decisions.append(decision)
        if is_match:
            matched.append(item)
    payload: dict[str, Any] = {"subject_id": subject_id, "timepoint": timepoint, "scope": target, "items": matched, "count": len(matched)}
    if debug:
        payload["debug"] = {"scoped_count": len(assets), "target_linked_count": len(matched), "accepted_count": sum(1 for d in decisions if d["matched"]), "rejected_count": sum(1 for d in decisions if not d["matched"]), "target": target, "decisions": decisions}
    return payload


@router.get("/api/observations")
def observations(subject_id: str = "own_cohort", timepoint: str | None = None, spatial_id: str | None = None, biological_level: str | None = None, include_archived: bool = False, include_descendants: bool = False):
    items = list_observations(subject_id=subject_id, timepoint=timepoint, spatial_id=None if include_descendants else spatial_id, biological_level=biological_level, include_archived=include_archived)
    if spatial_id and include_descendants:
        items = [item for item in items if _in_spatial_scope(spatial_id, item.get("spatial_id"), True)]
    return {"subject_id": subject_id, "scope": spatial_id, "include_descendants": include_descendants, "count": len(items), "observations": items}


@router.get("/api/biological-state")
def state(subject_id: str = "own_cohort", timepoint: str = "T0", spatial_id: str | None = None, include_descendants: bool = True):
    return biological_state(subject_id=subject_id, timepoint=timepoint, spatial_id=spatial_id, include_descendants=include_descendants)


@router.post("/api/observations", status_code=201)
def create(request: ObservationCreateRequest):
    try: item = create_observation(request.model_dump())
    except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"status": "created", "observation": item}


@router.get("/api/observations/{observation_id}")
def detail(observation_id: str):
    item = get_observation(observation_id)
    if item is None: raise HTTPException(status_code=404, detail="observation not found")
    return {"observation": item}


@router.get("/api/observations/{observation_id}/history")
def history(observation_id: str):
    items = observation_history(observation_id)
    if items is None: raise HTTPException(status_code=404, detail="observation not found")
    return {"observation_id": observation_id, "history": items}


@router.patch("/api/observations/{observation_id}")
def update(observation_id: str, request: ObservationUpdateRequest):
    try: item = update_observation(observation_id, request.model_dump(exclude_unset=True))
    except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc
    if item is None: raise HTTPException(status_code=404, detail="observation not found")
    return {"status": "updated", "observation": item}


@router.post("/api/observations/{observation_id}/archive")
def archive(observation_id: str, request: ObservationLifecycleRequest):
    item = archive_observation(observation_id, author=request.author, reason=request.reason)
    if item is None: raise HTTPException(status_code=404, detail="observation not found")
    return {"status": "archived", "observation": item}


@router.post("/api/observations/{observation_id}/restore")
def restore(observation_id: str, request: ObservationLifecycleRequest):
    item = restore_observation(observation_id, author=request.author, reason=request.reason)
    if item is None: raise HTTPException(status_code=404, detail="observation not found")
    return {"status": "restored", "observation": item}
