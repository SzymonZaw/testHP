"""API for evidence-backed research biological state summaries."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from core.anatomy import AnatomicalLocation
from core.biological_state_aggregation import BiologicalStateAggregator
from core.evidence import Evidence
from core.observation import Observation
from .observation_registry import list_observations

router = APIRouter(tags=["biological-state"])


_DIMENSIONS = (
    "biological_age",
    "structural_functional_state",
    "damage",
    "pathology",
)


def _parse_observations(items: list[dict[str, Any]]) -> tuple[list[Observation], list[AnatomicalLocation]]:
    observations: list[Observation] = []
    locations: dict[str, AnatomicalLocation] = {}
    for item in items:
        domain = Observation(
            id=str(item["id"]),
            subject_id=str(item["subject_id"]),
            timepoint_id=str(item["timepoint"]),
            name=str(item["name"]),
            value=item.get("value"),
            observed_at=__import__("datetime").datetime.fromisoformat(str(item["observed_at"]).replace("Z", "+00:00")),
            anatomical_location=AnatomicalLocation(
                id=str(item.get("spatial_id") or "hand"),
                name=str(item.get("location_name") or item.get("spatial_id") or "hand"),
                level=str(item.get("location_level") or "site"),
                parent_id=item.get("parent_id"),
            ),
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
        locations[domain.anatomical_location.id] = domain.anatomical_location
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


def _state_payload(state: Any) -> dict[str, Any]:
    interpretations = {
        dimension: state.interpretation(dimension)
        for dimension in _DIMENSIONS
        if state.interpretation(dimension) is not None
    }
    return {
        "subject_id": state.subject_id,
        "timepoint": state.timepoint_id,
        "evidence_ids": list(state.evidence_ids),
        "evidence_count": state.evidence_count,
        "availability": state.availability,
        "confidence": _confidence_payload(state.confidence),
        "interpretations": interpretations,
    }


@router.get("/api/biological-state")
def biological_state(
    subject_id: str = "own_cohort",
    timepoint: str = "T0",
    spatial_id: str | None = None,
    include_descendants: bool = True,
):
    """Return one canonical, evidence-backed research state for a spatial scope."""
    items = list_observations(subject_id=subject_id, timepoint=timepoint)
    observations, locations = _parse_observations(items)
    evidence = _evidence(items)
    aggregator = BiologicalStateAggregator(observations, evidence, locations)
    state = aggregator.build_state(subject_id, timepoint, location_id=spatial_id)

    scoped_observations = state.observations
    if spatial_id is not None and include_descendants:
        scoped_evidence = aggregator.evidence_for_location(spatial_id, include_descendants=True)
        evidence_ids = {item.id for item in scoped_evidence}
        state.evidence_ids = tuple(item.id for item in scoped_evidence)
        state.evidence_count = len(scoped_evidence)
        state.availability = "observed" if scoped_evidence else "insufficient_evidence"
        state.confidence = aggregator._confidence(scoped_evidence)
        state.interpretations = aggregator._interpretations(scoped_observations, scoped_evidence)

    summary = {
        "scope": spatial_id,
        "include_descendants": include_descendants,
        "observations": len(scoped_observations),
        "explicit_evidence": state.evidence_count,
        "interpretation_source": "validated_interpretations only",
        "dimensions": _DIMENSIONS,
    }
    return {"state": _state_payload(state), "summary": summary}
