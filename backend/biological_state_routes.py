"""API for evidence-backed research biological state summaries."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from core.anatomy import AnatomicalLocation
from core.biological_state_aggregation import BiologicalStateAggregator
from core.evidence import Evidence
from core.observation import Observation
from core.spatial_scope import build_parent_map, canonical_parent_id, split_spatial_scope
from .observation_registry import list_observations, update_observation

router = APIRouter(tags=["biological-state"])

_DIMENSIONS = ("biological_age", "structural_functional_state", "damage", "pathology")
_LEVELS = ("macro", "tissue", "cellular", "molecular")


class BiologicalStateUpdateRequest(BaseModel):
    observation_id: str
    author: str = "local-user"
    interpretations: dict[str, Any] = Field(default_factory=dict)


def _location_parent(payload: dict[str, Any], spatial_id: str) -> str | None:
    return str(payload["parent_id"]) if payload.get("parent_id") else canonical_parent_id(spatial_id)


def _parse_observations(items: list[dict[str, Any]]) -> tuple[list[Observation], list[AnatomicalLocation]]:
    observations: list[Observation] = []
    locations: dict[str, AnatomicalLocation] = {}
    for item in items:
        spatial_id = str(item.get("spatial_id") or "hand")
        location = AnatomicalLocation(
            id=spatial_id,
            name=str(item.get("location_name") or spatial_id.rsplit("/", 1)[-1]),
            level=str(item.get("location_level") or "site"),
            parent_id=_location_parent(item, spatial_id),
        )
        observations.append(Observation(
            id=str(item["id"]), subject_id=str(item["subject_id"]), timepoint_id=str(item["timepoint"]),
            name=str(item["name"]), value=item.get("value"),
            observed_at=datetime.fromisoformat(str(item["observed_at"]).replace("Z", "+00:00")),
            anatomical_location=location, source_measurement_ids=list(item.get("source_measurement_ids") or []),
            metadata={"validated_interpretations": item.get("validated_interpretations") or {}, "biological_level": item.get("biological_level", "unspecified")},
            biological_level=str(item.get("biological_level") or "unspecified"), modality=str(item.get("modality") or "unknown"),
            status=str(item.get("status") or "active"), version=int(item.get("version") or 1),
        ))
        locations[spatial_id] = location

    pending = list(locations.values())
    while pending:
        location = pending.pop()
        if not location.parent_id or location.parent_id in locations:
            continue
        parent_id = location.parent_id
        parent = AnatomicalLocation(
            id=parent_id, name=parent_id.rsplit("/", 1)[-1].replace("_", " ").title(),
            level="site" if "/" not in parent_id else "anatomical_region", parent_id=canonical_parent_id(parent_id),
        )
        locations[parent.id] = parent
        pending.append(parent)
    return observations, list(locations.values())


def _evidence(items: list[dict[str, Any]]) -> list[Evidence]:
    result: list[Evidence] = []
    for item in items:
        evidence_id = item.get("evidence_id")
        if not evidence_id:
            continue
        confidence = item.get("evidence_confidence")
        result.append(Evidence(
            id=str(evidence_id), subject_id=str(item["subject_id"]), observation_id=str(item["id"]),
            evidence_type=str(item.get("evidence_type") or "source"), interpretation_boundary="observation_only",
            provenance={"source": item.get("source", "manual-entry")}, confidence=float(confidence) if confidence is not None else None,
        ))
    return result


def _confidence_payload(value: float | None) -> dict[str, Any]:
    if value is None: return {"value": None, "label": "Nieustalona", "status": "unknown"}
    return {"value": round(value, 4), "label": f"{value:.2f}", "status": "reported"}


def _state_payload(state: Any, editable: list[dict[str, Any]] | None = None, observation_count: int = 0) -> dict[str, Any]:
    return {"subject_id": state.subject_id, "timepoint": state.timepoint_id, "evidence_ids": list(state.evidence_ids), "evidence_count": state.evidence_count, "observation_count": observation_count, "data_count": observation_count, "availability": state.availability, "confidence": _confidence_payload(state.confidence), "interpretations": {d: state.interpretation(d) for d in _DIMENSIONS if state.interpretation(d) is not None}, "editable_observations": editable or []}


def _build_state(subject_id: str, timepoint: str, spatial_id: str | None, include_descendants: bool):
    items = list_observations(subject_id=subject_id, timepoint=timepoint)
    observations, locations = _parse_observations(items)
    evidence = _evidence(items)
    aggregator = BiologicalStateAggregator(observations, evidence, locations)
    if spatial_id is None:
        scoped_observations = [observation for observation in observations if observation.subject_id == subject_id and observation.timepoint_id == timepoint]
        scoped_evidence = tuple(evidence)
        state = aggregator.build_state(subject_id, timepoint)
    else:
        direct_items, descendant_items = split_spatial_scope(items, spatial_id, include_descendants=include_descendants)
        scoped_items = direct_items + descendant_items
        scoped_ids = {str(item["id"]) for item in scoped_items}
        scoped_observations = [observation for observation in observations if observation.id in scoped_ids]
        scoped_evidence = tuple(item for item in evidence if item.observation_id in scoped_ids)
        state = aggregator.build_state(subject_id, timepoint)
        state.observations = scoped_observations
        state.evidence_ids = tuple(item.id for item in scoped_evidence)
        state.evidence_count = len(scoped_evidence)
        state.availability = "observed" if scoped_observations else "insufficient_evidence"
        state.confidence = aggregator._confidence(scoped_evidence)
        state.interpretations = aggregator._interpretations(scoped_observations, scoped_evidence)
    evidence_by_observation = {e.observation_id: e.id for e in evidence}
    editable = [{"id": item.id, "name": item.name, "spatial_id": item.anatomical_location.id if item.anatomical_location else None, "evidence_id": evidence_by_observation.get(item.id), "validated_interpretations": dict(item.metadata.get("validated_interpretations") or {})} for item in scoped_observations if item.id in evidence_by_observation]
    return state, editable, scoped_evidence, scoped_observations, items


@router.get("/api/biological-state")
def biological_state(subject_id: str = "own_cohort", timepoint: str = "T0", spatial_id: str | None = None, include_descendants: bool = True):
    state, editable, scoped_evidence, scoped_observations, all_items = _build_state(subject_id, timepoint, spatial_id, include_descendants)
    direct_evidence = tuple(item for item in scoped_evidence if spatial_id is None or next((o for o in scoped_observations if o.id == item.observation_id and o.anatomical_location and o.anatomical_location.id == spatial_id), None) is not None)
    direct_ids = {item.id for item in direct_evidence}
    descendant_evidence = tuple(item for item in scoped_evidence if item.id not in direct_ids)
    if spatial_id is None:
        direct_observations = list(scoped_observations)
        descendant_observations: list[Observation] = []
    else:
        direct_items, descendant_items = split_spatial_scope(all_items, spatial_id, include_descendants=include_descendants)
        direct_ids_observations = {str(item["id"]) for item in direct_items}
        descendant_ids_observations = {str(item["id"]) for item in descendant_items}
        direct_observations = [o for o in scoped_observations if o.id in direct_ids_observations]
        descendant_observations = [o for o in scoped_observations if o.id in descendant_ids_observations]

    by_location: dict[str, dict[str, Any]] = {}
    by_level = {level: 0 for level in _LEVELS}
    direct_by_level = {level: 0 for level in _LEVELS}
    descendant_by_level = {level: 0 for level in _LEVELS}
    for observation in scoped_observations:
        level = str(observation.biological_level or observation.metadata.get("biological_level") or "").lower()
        if level in by_level:
            by_level[level] += 1
        location = observation.anatomical_location
        if not location: continue
        entry = by_location.setdefault(location.id, {"spatial_id": location.id, "name": location.name, "count": 0, "by_level": {item: 0 for item in _LEVELS}})
        entry["count"] += 1
        if level in _LEVELS:
            entry["by_level"][level] += 1
    for observation in direct_observations:
        level = str(observation.biological_level or observation.metadata.get("biological_level") or "").lower()
        if level in direct_by_level: direct_by_level[level] += 1
    for observation in descendant_observations:
        level = str(observation.biological_level or observation.metadata.get("biological_level") or "").lower()
        if level in descendant_by_level: descendant_by_level[level] += 1

    return {"state": _state_payload(state, editable, len(scoped_observations)), "summary": {
        "scope": spatial_id, "include_descendants": include_descendants, "observations": len(scoped_observations), "observation_count": len(scoped_observations), "data_count": len(scoped_observations),
        "explicit_evidence": state.evidence_count, "direct_evidence": len(direct_evidence), "descendant_evidence": len(descendant_evidence),
        "direct_observations": len(direct_observations), "descendant_observations": len(descendant_observations),
        "by_level": by_level, "direct_by_level": direct_by_level, "descendant_by_level": descendant_by_level,
        "by_location": sorted(by_location.values(), key=lambda item: item["spatial_id"]),
        "interpretation_source": "validated_interpretations only", "dimensions": _DIMENSIONS,
        "scope_definition": "spatial_id exact match plus recursive descendants; biological_level is a separate dimension",
    }}


@router.patch("/api/biological-state")
def update_biological_state(request: BiologicalStateUpdateRequest):
    unknown = set(request.interpretations) - set(_DIMENSIONS)
    if unknown: raise HTTPException(status_code=400, detail=f"Unsupported interpretation dimension(s): {', '.join(sorted(unknown))}")
    cleaned = {key: value for key, value in request.interpretations.items() if value is not None and str(value).strip()}
    try: item = update_observation(request.observation_id, {"validated_interpretations": cleaned, "author": request.author})
    except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc
    if item is None: raise HTTPException(status_code=404, detail="observation not found")
    if not item.get("evidence_id"): raise HTTPException(status_code=400, detail="An explicit evidence-backed observation is required")
    return {"status": "updated", "observation": item}
