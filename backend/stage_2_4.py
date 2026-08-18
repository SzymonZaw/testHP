"""Stages 2-4: spatial evidence, current biological state and hierarchy.

Research-only implementation. Missing evidence stays missing; biological claims
are never inferred from spatial depth alone.
"""
from __future__ import annotations

import json
import math
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from .data_ingestion import ingest_upload, safe_component

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "data" / "registry" / "spatial_evidence.json"
router = APIRouter(tags=["digital-twin-stages-2-4"])
LEVELS = {"macro": 0, "tissue": 1, "cellular": 2, "cell": 3}
SIGNAL_LAYERS = {
    "macro": {"skin_age", "wrinkles", "elasticity", "pigmentation", "macro_age"},
    "tissue": {"fibrosis", "inflammation", "collagen_structure", "tissue_age"},
    "cellular": {"health_score", "stress_score", "senescence_score", "cell_age", "cell_count"},
    "molecular": {"inflammaging", "biomarkers", "gene_signatures", "molecular_age"},
}
AGE_KEYS = {"macro": "macro_age", "tissue": "tissue_age", "cellular": "cell_age", "molecular": "molecular_age"}

class AggregateRequest(BaseModel):
    subject_id: str
    timepoint: str = "T0"
    root_node_id: str = "hand"

def _load() -> list[dict[str, Any]]:
    if not REGISTRY_PATH.exists(): return []
    try: return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError): return []

def _save(items: list[dict[str, Any]]) -> None:
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = REGISTRY_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(items, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(REGISTRY_PATH)

def _now() -> str: return datetime.now(timezone.utc).isoformat()

def _safe_node(node_id: str) -> str:
    parts = [safe_component(part, "node") for part in node_id.split("/") if part]
    return "/".join(parts)[:160] or "hand"

def _validate_level(level: str) -> str:
    value = level.strip().lower()
    if value not in LEVELS: raise HTTPException(status_code=400, detail=f"unsupported spatial level: {level}")
    return value

def _clean_signals(signals: dict[str, Any]) -> dict[str, Any]:
    clean: dict[str, Any] = {}; allowed = set().union(*SIGNAL_LAYERS.values())
    for key, value in signals.items():
        key = str(key).strip().lower()
        if key not in allowed: continue
        if isinstance(value, bool): clean[key] = value
        elif isinstance(value, (int, float)) and math.isfinite(float(value)): clean[key] = float(value)
        elif isinstance(value, (list, dict, str)): clean[key] = value
    return clean

def _layer_for_signal(signal: str) -> str | None:
    for layer, keys in SIGNAL_LAYERS.items():
        if signal in keys: return layer
    return None

def _matches(item: dict[str, Any], subject_id: str, timepoint: str) -> bool:
    return item.get("subject_id") == subject_id and item.get("timepoint") == timepoint

def _node_matches(item: dict[str, Any], node_id: str | None) -> bool:
    return node_id is None or item.get("spatial_node_id") == node_id

def _numeric(values: list[Any]) -> list[float]:
    return [float(v) for v in values if isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(float(v))]

def _mean(values: list[Any]) -> float | None:
    nums = _numeric(values)
    return round(sum(nums) / len(nums), 4) if nums else None

def _signal_summary(items: list[dict[str, Any]]) -> dict[str, Any]:
    values: dict[str, list[Any]] = {}
    for item in items:
        for key, value in (item.get("signals") or {}).items(): values.setdefault(key, []).append(value)
    summary: dict[str, Any] = {}
    for key, vals in values.items():
        if all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in vals): summary[key] = {"value": _mean(vals), "n": len(vals), "status": "observed"}
        else: summary[key] = {"value": vals[-1], "n": len(vals), "status": "observed"}
    return summary

def _age_summary(summary: dict[str, Any]) -> dict[str, Any]:
    layers: dict[str, Any] = {}
    for layer, key in AGE_KEYS.items():
        value = summary.get(key, {}).get("value")
        layers[layer] = {"value": value, "source": "explicit_signal" if value is not None else None, "status": "research_proxy" if value is not None else "not_established"}
    values = [x["value"] for x in layers.values() if x["value"] is not None]
    return {"overall": round(sum(values) / len(values), 2) if values else None, "layers": layers, "status": "research_proxy" if values else "not_established"}

def _coverage(items: list[dict[str, Any]]) -> dict[str, Any]:
    return {layer: {"evidence_items": sum(1 for i in items if layer in (i.get("layers") or [])), "observed": any(layer in (i.get("layers") or []) for i in items)} for layer in (*SIGNAL_LAYERS.keys(), "molecular")}

def _direct_state(items: list[dict[str, Any]], node_id: str | None = None) -> dict[str, Any]:
    selected = [i for i in items if _node_matches(i, node_id)]; signal_summary = _signal_summary(selected)
    return {"evidence_count": len(selected), "signals": signal_summary, "biological_age": _age_summary(signal_summary), "coverage": _coverage(selected), "interpretation_boundary": "research_signals_only", "insufficient_evidence": not bool(signal_summary)}

def _node_path(node_id: str) -> list[str]:
    parts = [p for p in node_id.split("/") if p]
    if parts and parts[0] != "hand": parts.insert(0, "hand")
    return ["/".join(parts[:i]) for i in range(1, len(parts) + 1)] or ["hand"]

def _aggregate(items: list[dict[str, Any]], root_node_id: str) -> dict[str, Any]:
    path = _node_path(root_node_id); nodes: list[dict[str, Any]] = []
    for node in path:
        descendants = [i for i in items if i.get("spatial_node_id") == node or str(i.get("spatial_node_id", "")).startswith(node + "/")]
        summary = _signal_summary(descendants)
        nodes.append({"node_id": node, "evidence_count": len(descendants), "signals": summary, "biological_age": _age_summary(summary), "coverage": _coverage(descendants), "status": "observed" if descendants else "insufficient_evidence"})
    return {"root_node_id": root_node_id, "nodes": nodes, "interpretation_boundary": "hierarchical_research_summary"}

@router.post("/api/spatial/attach")
async def attach_evidence(file: UploadFile = File(...), subject_id: str = Form("own_cohort"), timepoint: str = Form("T0"), spatial_node_id: str = Form("hand"), spatial_level: str = Form("macro"), modality: str = Form("hand"), resolution: str | None = Form(None), source: str | None = Form(None), signals_json: str | None = Form(None)):
    level = _validate_level(spatial_level)
    if modality not in {"hand", "images", "wsi", "rna", "metadata"}: raise HTTPException(status_code=400, detail="unsupported evidence modality")
    try: signals = _clean_signals(json.loads(signals_json)) if signals_json else {}
    except (json.JSONDecodeError, TypeError): raise HTTPException(status_code=400, detail="signals_json must be a JSON object")
    try: asset = await ingest_upload(file, subject_id, timepoint, modality)
    except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc
    item = {"evidence_id": f"evidence_{uuid.uuid4().hex[:12]}", "asset_id": asset.asset_id, "subject_id": asset.subject_id, "timepoint": asset.timepoint, "spatial_node_id": _safe_node(spatial_node_id), "spatial_level": level, "modality": modality, "resolution": resolution, "source": source or "upload", "filename": asset.filename, "path": asset.path, "created_at": _now(), "signals": signals, "layers": sorted({x for key in signals for x in [_layer_for_signal(key)] if x}), "interpretation_boundary": "explicitly_attached_evidence"}
    items = _load(); items.append(item); _save(items)
    return {"status": "attached", "evidence": item, "state": _direct_state(items, item["spatial_node_id"])}

@router.get("/api/spatial/registry")
def spatial_registry(subject_id: str = "own_cohort", timepoint: str = "T0", spatial_node_id: str | None = None):
    items = [i for i in _load() if _matches(i, subject_id, timepoint) and _node_matches(i, spatial_node_id)]
    return {"subject_id": subject_id, "timepoint": timepoint, "items": items, "count": len(items)}

@router.get("/api/spatial/state")
def current_state(subject_id: str = "own_cohort", timepoint: str = "T0", spatial_node_id: str | None = None):
    items = [i for i in _load() if _matches(i, subject_id, timepoint)]
    return {"subject_id": subject_id, "timepoint": timepoint, "spatial_node_id": spatial_node_id, **_direct_state(items, spatial_node_id)}

@router.post("/api/spatial/summary")
def hierarchical_summary(request: AggregateRequest):
    items = [i for i in _load() if _matches(i, request.subject_id, request.timepoint)]
    return {"subject_id": request.subject_id, "timepoint": request.timepoint, **_aggregate(items, _safe_node(request.root_node_id))}

@router.get("/api/spatial/tree")
def spatial_tree(subject_id: str = "own_cohort", timepoint: str = "T0"):
    items = [i for i in _load() if _matches(i, subject_id, timepoint)]
    nodes: dict[str, dict[str, Any]] = {"hand": {"node_id": "hand", "level": "macro", "evidence_count": 0}}
    for item in items:
        node = item["spatial_node_id"]; parts = _node_path(node)
        for index, part in enumerate(parts):
            level = "macro" if index == 0 else ("tissue" if index == 1 else ("cellular" if index == 2 else "cell"))
            nodes.setdefault(part, {"node_id": part, "level": level, "evidence_count": 0})
        nodes[node]["evidence_count"] += 1
    return {"subject_id": subject_id, "timepoint": timepoint, "nodes": list(nodes.values())}

def register_stage_routes(app: Any) -> None: app.include_router(router)
