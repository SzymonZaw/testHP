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
from .observation_registry import list_observations, update_observation

router = APIRouter(tags=["biological-state"])

_DIMENSIONS = (
    "biological_age",
    "structural_functional_state",
    "damage",
    "pathology",
)


class BiologicalStateUpdateRequest(BaseModel):
    observation_id: str
    author: str = "local-user"
    interpretations: dict[str, Any] = Field(default_factory=dict)


def _parse_observations(items: list[dict[str, Any]]) -> tuple[list[Observation], list[AnatomicalLocation]]:
    observations: list[Observation] = []
    locations: dict[str, AnatomicalLocation] = {}
    for item in items:
        location = AnatomicalLocation(
            id=str(item.get("spatial_id") or "hand"),
            name=str(item.get("location_name") or item.get("spatial_id") or "hand"),
            level=str(item.get("location_level") or "site"),
            parent_id=item.get("parent_id"),
        )
        domain = Observation(
            id=str(item["id"]),
            subject_id=str(item["subject_id"]),
            timepoint_id=str(item["timepoint"]),
            name=str(item["name"]),
            value=item.get("value"),
            observed_at=datetime.fromisoformat(str(item["observed_at"]).replace("Z", "+00:00")),
            anatomical_location=location,
            source_measurement_ids=list(item.get("source_measurement_ids") or []),
            metadata={
                "validated_interpretations": item.get("validated_interpretations") or {},
                "biological_level": item.get("biological_level", "unspecified"),
            },
            biological_level=str(item.get("biological_level") or "unspecified"),
            modality=str(item.get("modality") or "unknown"),
            status=str(item.get("status") or "active"),
            version=int(item.get("version") or 1),
        )
        observations.append(domain)
        locations[location.id] = location
    return observations, list(locations.values())


def _evidence(items: list[dict[str, Any]]) -> list[Evidence]:
    result: list[Evidence] = []
    for item in items:
        evidence_id = item.get("evidence_id")
        if not evidence_id:
            continue
        confidence = item.get("evidence_confidence")
        result.append(Evidence(
            id=str(evidence_id),
            subject_id=str(item["subject_id"]),
            observation_id=str(item["id"]),
            evidence_type=str(item.get("evidence_type") or "source"),
            interpretation_boundary="observation_only",
            provenance={"source": item.get("source", "manual-entry")},
            confidence=float(confidence) if confidence is not None else None,
        ))
    return result


def _confidence_payload(value: float | None) -> dict[str, Any]:
    if value is None:
        return {"value": None, "label": "Nieustalona", "status": "unknown"}
    return {"value": round(value, 4), "label": f"{value:.2f}", "status": "reported"}


def _state_payload(state: Any, observation_count: int, editable: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    return {
        "subject_id": state.subject_id,
        "timepoint": state.timepoint_id,
        "observation_count": observation_count,
        "evidence_ids": list(state.evidence_ids),
        "evidence_count": state.evidence_count,
        "availability": state.availability,
        "confidence": _confidence_payload(state.confidence),
        "interpretations": {
            dimension: state.interpretation(dimension)
            for dimension in _DIMENSIONS
            if state.interpretation(dimension) is not None
        },
        "editable_observations": editable or [],
    }


def _in_spatial_scope(selected_spatial_id: str, candidate_spatial_id: str, include_descendants: bool) -> bool:
    selected = str(selected_spatial_id or "").strip().strip("/")
    candidate = str(candidate_spatial_id or "").strip().strip("/")
    if not selected or not candidate:
        return False
    if candidate == selected:
        return True
    return include_descendants and candidate.startswith(f"{selected}/")


def _build_state(subject_id: str, timepoint: str, spatial_id: str | None, include_descendants: bool):
    items = list_observations(subject_id=subject_id, timepoint=timepoint)
    observations, locations = _parse_observations(items)
    evidence = _evidence(items)
    aggregator = BiologicalStateAggregator(observations, evidence, locations)

    if spatial_id is None:
        scoped_observations = observations
        scoped_evidence = evidence
    else:
        scoped_observations = [
            observation for observation in observations
            if observation.anatomical_location and _in_spatial_scope(spatial_id, observation.anatomical_location.id, include_descendants)
        ]
        scoped_observation_ids = {observation.id for observation in scoped_observations}
        scoped_evidence = [
            item for item in evidence
            if item.observation_id in scoped_observation_ids
        ]

    state = aggregator.build_state(subject_id, timepoint)
    state.observations = scoped_observations
    state.evidence_ids = tuple(item.id for item in scoped_evidence)
    state.evidence_count = len(state.evidence_ids)
    state.confidence = aggregator._confidence(scoped_evidence)
    state.interpretations = aggregator._interpretations(scoped_observations, scoped_evidence)
    state.availability = "observed" if scoped_observations else "insufficient_evidence"

    editable = [
        {
            "id": item.id,
            "name": item.name,
            "spatial_id": item.anatomical_location.id if item.anatomical_location else None,
            "evidence_id": next((e.id for e in scoped_evidence if e.observation_id == item.id), None),
            "validated_interpretations": dict(item.metadata.get("validated_interpretations") or {}),
        }
        for item in scoped_observations
        if any(e.observation_id == item.id for e in scoped_evidence)
    ]
    return state, len(scoped_observations), editable


@router.get("/api/biological-state")
def biological_state(
    subject_id: str = "own_cohort",
    timepoint: str = "T0",
    spatial_id: str | None = None,
    include_descendants: bool = True,
):
    """Return one canonical research state for a spatial observation scope."""
    state, observation_count, editable = _build_state(subject_id, timepoint, spatial_id, include_descendants)
    return {
        "state": _state_payload(state, observation_count, editable),
        "summary": {
            "scope": spatial_id,
            "include_descendants": include_descendants,
            "observation_count": observation_count,
            "evidence_count": state.evidence_count,
            "interpretation_source": "validated_interpretations only",
            "dimensions": _DIMENSIONS,
        },
    }


@router.patch("/api/biological-state")
def update_biological_state(request: BiologicalStateUpdateRequest):
    unknown = set(request.interpretations) - set(_DIMENSIONS)
    if unknown:
        raise HTTPException(status_code=400, detail=f"Unsupported interpretation dimension(s): {', '.join(sorted(unknown))}")
    cleaned = {key: value for key, value in request.interpretations.items() if value is not None and str(value).strip()}
    try:
        item = update_observation(request.observation_id, {"validated_interpretations": cleaned, "author": request.author})
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if item is None:
        raise HTTPException(status_code=404, detail="observation not found")
    if not item.get("evidence_id"):
        raise HTTPException(status_code=400, detail="An explicit evidence-backed observation is required")
    return {"status": "updated", "observation": item}
