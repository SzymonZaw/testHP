"""Research-only contracts and registry routes for Digital Twin stages 21-32."""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "data" / "registry" / "hand_data_pipeline.json"
SCHEMA = "testhp.hand_pipeline.v1"
router = APIRouter(tags=["digital-twin-stages-21-32"])
STAGES = [
    {"id":21,"name":"Biological age","basis":"inference","requires":["geometry","anatomy","tissue","cell","omics","longitudinal"],"output":["estimate","uncertainty","evidence"]},
    {"id":22,"name":"Aging trajectory","basis":"longitudinal_inference","requires":["timepoints"],"output":["direction","rate","uncertainty","evidence"]},
    {"id":23,"name":"Disease trajectory","basis":"longitudinal_inference","requires":["validated_observations","timepoints"],"output":["trajectory","uncertainty","evidence"]},
    {"id":24,"name":"Unified Digital Twin","basis":"integration","requires":["surface","anatomy","tissue","cells","molecules","state"],"output":["unified_view","lineage"]},
    {"id":25,"name":"Cross-scale navigation","basis":"navigation","requires":["unified_digital_twin"],"output":["macro_to_molecular","molecular_to_macro"]},
    {"id":26,"name":"State estimation","basis":"inference","requires":["observations"],"output":["state","confidence","evidence"]},
    {"id":27,"name":"Uncertainty","basis":"uncertainty","requires":["derived_results"],"output":["confidence","uncertainty","evidence"]},
    {"id":28,"name":"What-if simulation","basis":"predictive_research","requires":["validated_predictive_model"],"output":["hypothesis","predicted_trajectory","uncertainty"]},
    {"id":29,"name":"Risk assessment","basis":"validated_inference","requires":["validated_risk_model"],"output":["risk_estimate","uncertainty","evidence"]},
    {"id":30,"name":"Intervention support","basis":"decision_support","requires":["validated_models","evidence"],"output":["problem_region","mechanisms","evidence","options_for_review"]},
    {"id":31,"name":"Scientific validation","basis":"validation","requires":["reference_data","ground_truth"],"output":["accuracy","generalization","bias","reproducibility","uncertainty_calibration"]},
    {"id":32,"name":"Clinical / regulatory","basis":"governance","requires":["validated_system"],"output":["privacy","security","consent","governance","traceability","auditability","regulatory_classification"]},
]

class Evidence(BaseModel):
    object_id: str = Field(min_length=1)
    modality: str = Field(min_length=1)
    timepoint: str | None = None
    spatial_node_id: str | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)

class ResultInput(BaseModel):
    subject_id: str = Field(min_length=1)
    hand_id: str = Field(min_length=1)
    timepoint_id: str = Field(min_length=1)
    payload: dict[str, Any] = Field(default_factory=dict)
    evidence: list[Evidence] = Field(default_factory=list)


def _read() -> dict[str, Any]:
    if not REGISTRY_PATH.exists():
        return {"schema": SCHEMA, "subjects": {}, "objects": [], "stage_records": []}
    try:
        data = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {"schema": SCHEMA, "subjects": {}, "objects": [], "stage_records": []}
    except (OSError, json.JSONDecodeError):
        return {"schema": SCHEMA, "subjects": {}, "objects": [], "stage_records": []}


def _write(data: dict[str, Any]) -> None:
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = REGISTRY_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(REGISTRY_PATH)


def _record(stage: int, request: ResultInput, status: str, boundary: str) -> dict[str, Any]:
    evidence_ids = [e.object_id for e in request.evidence]
    record = {"record_id": f"stage{stage}_{uuid.uuid4().hex[:12]}", "stage": stage, "stage_name": STAGES[stage-21]["name"], "status": status, "created_at": datetime.now(timezone.utc).isoformat(), "subject_id": request.subject_id, "hand_id": request.hand_id, "timepoint_id": request.timepoint_id, "evidence_ids": evidence_ids, "payload": request.payload, "interpretation_boundary": boundary}
    data = _read(); data.setdefault("stage_records", []).append(record); _write(data)
    return record


def register_stage_21_32_routes(app: Any) -> None:
    app.include_router(router)


@router.get("/api/hand/stages-21-32")
def stage_catalog() -> dict[str, Any]:
    return {"schema": SCHEMA, "stages": STAGES, "policy": "research_only_until_scientific_and_clinical_validation"}


@router.get("/api/hand/digital-twin-status")
def digital_twin_status(subject_id: str = "own_cohort", hand_id: str = "hand-001", timepoint_id: str = "T0") -> dict[str, Any]:
    records = [r for r in _read().get("stage_records", []) if r.get("subject_id") == subject_id and r.get("hand_id") == hand_id and r.get("timepoint_id") == timepoint_id and 21 <= int(r.get("stage", 0)) <= 32]
    completed = sorted({int(r["stage"]) for r in records})
    return {"schema": SCHEMA, "subject_id": subject_id, "hand_id": hand_id, "timepoint_id": timepoint_id, "completed_stages": completed, "missing_stages": [s["id"] for s in STAGES if s["id"] not in completed], "clinical_ready": False, "interpretation_boundary": "research_only_until_scientific_and_clinical_validation"}


def _register(stage: int, request: ResultInput, *, require_evidence: bool = False, boundary: str) -> dict[str, Any]:
    if require_evidence and not request.evidence:
        raise HTTPException(status_code=422, detail=f"stage {stage} requires linked evidence")
    status = "evidence_backed" if request.evidence else "not_established"
    return _record(stage, request, status, boundary)


@router.post("/api/hand/biological-age")
def biological_age(request: ResultInput): return _register(21, request, require_evidence=True, boundary="research_estimate_not_clinical_age")
@router.post("/api/hand/aging-trajectory")
def aging_trajectory(request: ResultInput): return _register(22, request, require_evidence=True, boundary="requires_repeated_timepoints")
@router.post("/api/hand/disease-trajectory")
def disease_trajectory(request: ResultInput): return _register(23, request, require_evidence=True, boundary="requires_disease_specific_validation")
@router.post("/api/hand/unified-twin")
def unified_twin(request: ResultInput): return _register(24, request, boundary="integrated_evidence_model")
@router.post("/api/hand/cross-scale-navigation")
def cross_scale_navigation(request: ResultInput): return _register(25, request, require_evidence=True, boundary="requires_verified_spatial_lineage")
@router.post("/api/hand/state-estimation")
def state_estimation(request: ResultInput): return _register(26, request, require_evidence=True, boundary="evidence_backed_research_state")
@router.post("/api/hand/uncertainty")
def uncertainty(request: ResultInput): return _register(27, request, boundary="uncertainty_is_required_downstream")
@router.post("/api/hand/what-if")
def what_if(request: ResultInput): return _register(28, request, boundary="requires_validated_predictive_model")
@router.post("/api/hand/risk-assessment")
def risk_assessment(request: ResultInput): return _register(29, request, require_evidence=True, boundary="not_medical_advice_until_validated")
@router.post("/api/hand/intervention-support")
def intervention_support(request: ResultInput): return _register(30, request, require_evidence=True, boundary="human_clinician_decision_required")
@router.post("/api/hand/scientific-validation")
def scientific_validation(request: ResultInput): return _register(31, request, require_evidence=True, boundary="scientific_validation_record")
@router.post("/api/hand/clinical-governance")
def clinical_governance(request: ResultInput): return _register(32, request, boundary="privacy_security_consent_traceability_auditability_required")
