"""Stages 5-8: longitudinal monitoring, prediction, research copilot and human twin.

Research prototype only. Predictions are transparent extrapolations of supplied
research signals; no clinical diagnosis or treatment recommendation is made.
"""
from __future__ import annotations

import json
import math
import statistics
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_PATH = ROOT / "data" / "registry" / "spatial_evidence.json"
HUMAN_PATH = ROOT / "data" / "registry" / "human_twin.json"
router = APIRouter(tags=["digital-twin-stages-5-8"])

AGE_KEYS = {"macro": "macro_age", "tissue": "tissue_age", "cellular": "cell_age", "molecular": "molecular_age"}
BODY_SYSTEMS = {"hand": "hand", "skin": "skin", "face": "face", "eye": "eye", "muscle": "muscle", "brain": "brain", "heart": "heart"}

class LongitudinalStageRequest(BaseModel):
    subject_id: str = "own_cohort"
    node_id: str = "hand"
    observations: list[dict[str, Any]] = Field(default_factory=list)

class PredictionRequest(BaseModel):
    subject_id: str = "own_cohort"
    node_id: str = "hand"
    observations: list[dict[str, Any]] = Field(default_factory=list)
    horizon: int = Field(default=5, ge=1, le=50)

class CopilotRequest(BaseModel):
    subject_id: str = "own_cohort"
    node_id: str = "hand"
    observations: list[dict[str, Any]] = Field(default_factory=list)

class HumanRegisterRequest(BaseModel):
    subject_id: str = "own_cohort"
    systems: list[str] = Field(default_factory=lambda: ["hand"])


def _read(path: Path) -> list[dict[str, Any]] | dict[str, Any]:
    if not path.exists(): return [] if path == EVIDENCE_PATH else {}
    try: return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError): return [] if path == EVIDENCE_PATH else {}


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(path)


def _num(value: Any) -> float | None:
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value)) else None


def _age_from_observation(observation: dict[str, Any]) -> float | None:
    for key in ("biological_age", "age", "overall_age"):
        value = _num(observation.get(key))
        if value is not None: return value
    layers = observation.get("layers") or observation.get("biological_age_layers") or {}
    values = []
    if isinstance(layers, dict):
        for layer, key in AGE_KEYS.items():
            item = layers.get(layer)
            if isinstance(item, dict): item = item.get("value")
            value = _num(item)
            if value is None: value = _num(observation.get(key))
            if value is not None: values.append(value)
    return statistics.fmean(values) if values else None


def _normalize_observations(observations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized = []
    for index, obs in enumerate(observations):
        timepoint = obs.get("timepoint", index)
        age = _age_from_observation(obs)
        if age is not None: normalized.append({"timepoint": timepoint, "age": round(age, 4), "source": obs.get("source", "supplied_research_observation")})
    return normalized


def _slope(values: list[dict[str, Any]]) -> float | None:
    if len(values) < 2: return None
    ys = [x["age"] for x in values]
    xs = list(range(len(ys)))
    mean_x, mean_y = statistics.fmean(xs), statistics.fmean(ys)
    denom = sum((x - mean_x) ** 2 for x in xs)
    return sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys)) / denom if denom else 0.0


def _stored_evidence(subject_id: str, node_id: str) -> list[dict[str, Any]]:
    items = _read(EVIDENCE_PATH)
    if not isinstance(items, list): return []
    return [x for x in items if x.get("subject_id") == subject_id and (x.get("spatial_node_id") == node_id or str(x.get("spatial_node_id", "")).startswith(node_id + "/"))]


def _evidence_observations(subject_id: str, node_id: str) -> list[dict[str, Any]]:
    grouped: dict[str, list[float]] = {}
    for item in _stored_evidence(subject_id, node_id):
        ages = []
        signals = item.get("signals") or {}
        for key in AGE_KEYS.values():
            value = _num(signals.get(key))
            if value is not None: ages.append(value)
        if ages: grouped.setdefault(str(item.get("timepoint", "unknown")), []).append(statistics.fmean(ages))
    return [{"timepoint": tp, "biological_age": round(statistics.fmean(vals), 4), "source": "attached_evidence"} for tp, vals in grouped.items()]


@router.post("/api/longitudinal/stage5")
def stage5(request: LongitudinalStageRequest):
    observations = _normalize_observations(request.observations) or _normalize_observations(_evidence_observations(request.subject_id, request.node_id))
    observations.sort(key=lambda x: str(x["timepoint"]))
    if len(observations) < 2:
        return {"stage": 5, "status": "insufficient_evidence", "subject_id": request.subject_id, "node_id": request.node_id, "observations": observations, "changes": [], "message": "At least two comparable observations are required."}
    slope = _slope(observations)
    changes = []
    for previous, current in zip(observations, observations[1:]):
        delta = round(current["age"] - previous["age"], 4)
        changes.append({"from": previous["timepoint"], "to": current["timepoint"], "delta": delta, "direction": "increased" if delta > 0 else "decreased" if delta < 0 else "stable"})
    return {"stage": 5, "status": "observed", "subject_id": request.subject_id, "node_id": request.node_id, "observations": observations, "changes": changes, "trajectory": {"slope_per_observation": round(slope or 0, 4), "direction": "worsening" if (slope or 0) > 0 else "improving" if (slope or 0) < 0 else "stable"}, "interpretation_boundary": "longitudinal_research_signal"}


@router.post("/api/prediction/stage6")
def stage6(request: PredictionRequest):
    observations = _normalize_observations(request.observations) or _normalize_observations(_evidence_observations(request.subject_id, request.node_id))
    observations.sort(key=lambda x: str(x["timepoint"]))
    if len(observations) < 2:
        return {"stage": 6, "status": "insufficient_evidence", "prediction": None, "message": "At least two timepoints are required for trajectory extrapolation."}
    slope = _slope(observations) or 0.0
    current = observations[-1]["age"]
    predicted = round(current + slope * request.horizon, 2)
    return {"stage": 6, "status": "research_extrapolation", "subject_id": request.subject_id, "node_id": request.node_id, "current": current, "horizon": request.horizon, "prediction": predicted, "annualized_slope_proxy": round(slope, 4), "method": "ordinary_least_squares_on_supplied_observation_sequence", "uncertainty": "not_calibrated", "clinical_use": False}


@router.post("/api/copilot/stage7")
def stage7(request: CopilotRequest):
    evidence = _stored_evidence(request.subject_id, request.node_id)
    observations = _normalize_observations(request.observations) or _normalize_observations(_evidence_observations(request.subject_id, request.node_id))
    signal_counts: dict[str, int] = {}
    for item in evidence:
        for key in (item.get("signals") or {}): signal_counts[key] = signal_counts.get(key, 0) + 1
    findings = []
    if len(observations) >= 2:
        slope = _slope(observations) or 0
        findings.append({"type": "trajectory", "statement": f"Supplied biological-age proxy changed across {len(observations)} observations.", "direction": "increased" if slope > 0 else "decreased" if slope < 0 else "stable", "support": len(observations)})
    if signal_counts:
        top = sorted(signal_counts.items(), key=lambda x: (-x[1], x[0]))[:8]
        findings.append({"type": "evidence_coverage", "statement": "Observed research signals are concentrated in the attached evidence.", "signals": [{"name": k, "evidence_items": v} for k, v in top], "support": sum(signal_counts.values())})
    if not findings:
        findings.append({"type": "coverage_gap", "statement": "No interpretable research signal was supplied for this target.", "support": 0})
    return {"stage": 7, "status": "research_summary", "subject_id": request.subject_id, "node_id": request.node_id, "findings": findings, "evidence_items": len(evidence), "analyzed_observations": len(observations), "summary": " ".join(x["statement"] for x in findings), "limitations": ["This is a research interpretation layer.", "It does not diagnose disease or recommend treatment.", "Statements are limited to supplied evidence and explicit signals."]}


@router.post("/api/human-twin/register")
def register_human(request: HumanRegisterRequest):
    data = _read(HUMAN_PATH)
    if not isinstance(data, dict): data = {}
    systems = [x.strip().lower() for x in request.systems if x.strip().lower() in BODY_SYSTEMS]
    if not systems: raise HTTPException(status_code=400, detail="at least one supported body system is required")
    record = data.get(request.subject_id) or {"subject_id": request.subject_id, "created_at": datetime.now(timezone.utc).isoformat(), "systems": []}
    record["systems"] = sorted(set(record.get("systems", [])) | set(systems))
    record["updated_at"] = datetime.now(timezone.utc).isoformat()
    data[request.subject_id] = record
    _write(HUMAN_PATH, data)
    return {"stage": 8, "status": "registered", "twin": record}


@router.get("/api/human-twin")
def human_twin(subject_id: str = "own_cohort"):
    data = _read(HUMAN_PATH)
    record = data.get(subject_id) if isinstance(data, dict) else None
    if not record: record = {"subject_id": subject_id, "systems": ["hand"], "status": "hand_scope"}
    evidence = _stored_evidence(subject_id, "hand")
    return {"stage": 8, "subject_id": subject_id, "twin": record, "architecture": {"systems": list(BODY_SYSTEMS.values()), "spatial_hierarchy": ["organ", "region", "tissue", "cellular_field", "cell", "molecular"], "status": "research_prototype"}, "evidence": {"hand_items": len(evidence)}, "clinical_use": False}


def register_stage_5_8_routes(app: Any) -> None:
    app.include_router(router)
