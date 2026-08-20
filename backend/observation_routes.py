"""HTTP API for explicit, traceable biological observations."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from .observation_registry import create_observation, get_observation, list_observations, update_observation

router = APIRouter(tags=["biological-observations"])


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
    source_measurement_ids: list[str] | None = None


@router.get("/api/observations")
def observations(
    subject_id: str = "own_cohort",
    timepoint: str | None = None,
    spatial_id: str | None = None,
    biological_level: str | None = None,
    include_archived: bool = False,
):
    items = list_observations(
        subject_id=subject_id,
        timepoint=timepoint,
        spatial_id=spatial_id,
        biological_level=biological_level,
        include_archived=include_archived,
    )
    return {"subject_id": subject_id, "count": len(items), "observations": items}


@router.post("/api/observations", status_code=201)
def create(request: ObservationCreateRequest):
    try:
        item = create_observation(request.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"status": "created", "observation": item}


@router.get("/api/observations/{observation_id}")
def detail(observation_id: str):
    item = get_observation(observation_id)
    if item is None:
        raise HTTPException(status_code=404, detail="observation not found")
    return {"observation": item}


@router.patch("/api/observations/{observation_id}")
def update(observation_id: str, request: ObservationUpdateRequest):
    try:
        item = update_observation(observation_id, request.model_dump(exclude_unset=True))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if item is None:
        raise HTTPException(status_code=404, detail="observation not found")
    return {"status": "updated", "observation": item}
