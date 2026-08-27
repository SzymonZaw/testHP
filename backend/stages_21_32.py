"""Stages 21-32: inference, longitudinal modelling, validation and governance.

Research-only contracts. These stages never turn missing evidence into a
clinical conclusion. Every derived result carries evidence, uncertainty and
provenance metadata.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(tags=["digital-twin-stages-21-32"])
SCHEMA = "testhp.hand_pipeline.v1"

STAGES = [
    {"id": 21, "name": "Biological age", "basis": "inference", "requires": ["geometry", "anatomy", "tissue", "cell", "omics", "longitudinal"], "output": ["estimate", "uncertainty", "evidence"]},
    {"id": 22, "name": "Aging trajectory", "basis": "longitudinal_inference", "requires": ["timepoints"], "output": ["direction", "rate", "uncertainty", "evidence"]},
    {"id": 23, "name": "Disease trajectory", "basis": "longitudinal_inference", "requires": ["validated_observations", "timepoints"], "output": ["trajectory", "uncertainty", "evidence"]},
    {"id": 24, "name": "Unified Digital Twin", "basis": "integration", "requires": ["surface", "anatomy", "tissue", "cells", "molecules", "state"], "output": ["unified_view", "lineage"]},
    {"id": 25, "name": "Cross-scale navigation", "basis": "navigation", "requires": ["unified_digital_twin"], "output": ["macro_to_molecular", "molecular_to_macro"]},
    {"id": 26, "name": "State estimation", "basis": "inference", "requires": ["observations"], "output": ["state", "confidence", "evidence"]},
    {"id": 27, "name": "Uncertainty", "basis": "uncertainty", "requires": ["derived_results"], "output": ["confidence", "uncertainty", "evidence"]},
    {"id": 28, "name": "What-if simulation", "basis": "predictive_research", "requires": ["validated_predictive_model"], "output": ["hypothesis", "predicted_trajectory", "uncertainty"]},
    {"id": 29, "name": "Risk assessment", "basis": "validated_inference", "requires": ["validated_risk_model"], "output": ["risk_estimate", "uncertainty", "evidence"]},
    {"id": 30, "name": "Intervention support", "basis": "decision_support", "requires": ["validated_models", "evidence"], "output": ["problem_region", "mechanisms", "evidence", "options_for_review"]},
    {"id": 31, "name": "Scientific validation", "basis": "validation", "requires": ["reference_data", "ground_truth"], "output": ["accuracy", "generalization", "bias", "reproducibility", "uncertainty_calibration"]},
    {"id": 32, "name": "Clinical / regulatory", "basis": "governance", "requires": ["validated_system"], "output": ["privacy", "security", "consent", "governance", "traceability", "auditability", "regulatory_classification"]},
]

class Evidence(BaseModel):
    source: str
    modality: str | None = None
    dataset_id: str | None = None
    timepoint: str | None = None
    spatial_node_id: str | None = None
    quality: float | None = Field(default=None, ge=0, le=1)
    confidence: float | None = Field(default=None, ge=0, le=1)

class DerivedResult(BaseModel):
    subject_id: str
    timepoint: str | None = None
    estimate: float | None = None
    unit: str | None = None
    uncertainty: dict[str, Any] = Field(default_factory=dict)
    evidence: list[Evidence] = Field(default_factory=list)
    status: str = "research_only"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class TrajectoryRequest(BaseModel):
    subject_id: str
    observations: list[DerivedResult] = Field(default_factory=list)


def stage_catalog() -> dict[str, Any]:
    return {"schema": SCHEMA, "stages": STAGES}


def _evidence_status(evidence: list[Evidence]) -> str:
    return "evidence_backed" if evidence else "insufficient_evidence"


def build_biological_age(result: DerivedResult) -> dict[str, Any]:
    """Package an externally/model-derived estimate without inventing one."""
    return {**result.model_dump(), "stage": 21, "status": _evidence_status(result.evidence) if result.estimate is not None else "not_established"}


def build_trajectory(request: TrajectoryRequest) -> dict[str, Any]:
    ordered = [x for x in request.observations if x.timepoint]
    return {
        "schema": SCHEMA,
        "stage": 22,
        "subject_id": request.subject_id,
        "timepoints": [x.timepoint for x in ordered],
        "observations": [x.model_dump() for x in ordered],
        "status": "research_only" if len(ordered) >= 2 else "insufficient_timepoints",
        "uncertainty": {"reason": "trajectory requires repeated observations"},
    }


def build_unified_twin(subject_id: str, records: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "stage": 24,
        "subject_id": subject_id,
        "scales": ["surface", "anatomy", "tissue", "cell", "molecular"],
        "records": records,
        "coordinate_system": "HAND_COORDINATE_SYSTEM",
        "requires_lineage": True,
        "status": "research_only",
    }


@router.get("/api/hand/stages-21-32")
def get_stages_21_32() -> dict[str, Any]:
    return stage_catalog()


@router.post("/api/hand/biological-age")
def biological_age(payload: DerivedResult) -> dict[str, Any]:
    return build_biological_age(payload)


@router.post("/api/hand/aging-trajectory")
def aging_trajectory(payload: TrajectoryRequest) -> dict[str, Any]:
    return build_trajectory(payload)


@router.post("/api/hand/unified-twin")
def unified_twin(payload: dict[str, Any]) -> dict[str, Any]:
    return build_unified_twin(str(payload.get("subject_id") or ""), list(payload.get("records") or []))
