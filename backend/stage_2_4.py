"""Stages 2-4: spatial evidence, current biological state and hierarchy.

Research-only implementation. The spatial registry is the canonical backend
source for evidence visible to the Digital Twin. Registered ingestion assets
without an explicit spatial attachment are represented at the owning root
node (hand) and remain clearly marked as registered rather than spatially
localized. Missing deeper evidence stays missing.
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

from .data_ingestion import ingest_upload, registry_status, safe_component
from .spatial_contract import canonical_spatial_id

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

def _load_raw() -> list[dict[str, Any]]:
    if not REGISTRY_PATH.exists(): return []
    try: return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError): return []

def _save(items: list[dict[str, Any]]) -> None:
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = REGISTRY_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(items, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(REGISTRY_PATH)

def _now() -> str: return datetime.now(timezone.utc).isoformat()

def _sync_registered_assets(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Mirror ingestion assets into the canonical spatial registry.

    An ingestion asset has a valid subject/timepoint but no spatial annotation.
    Such an asset is attached only to the root anatomical target. It must not
    be projected into Palm/Thenar/etc. without an explicit user attachment.
    """
    try:
        assets = registry_status().get("assets", [])
    except Exception:
        return items
    by_asset = {str(i.get("asset_id")): i for i in items if i.get("asset_id")}
    changed = False
    for asset in assets:
        if asset.get("status") not in {"available", "ready"}: continue
        asset_id = str(asset.get("asset_id") or "")
        if not asset_id or asset_id in by_asset: continue
        modality = str(asset.get("modality") or "").lower()
        if modality != "hand": continue
        item = {
            "evidence_id": f"registered_{asset_id}",
            "asset_id": asset_id,
            "subject_id": asset.get("subject_id") or "own_cohort",
            "timepoint": asset.get("timepoint") or "T0",
            "spatial_node_id": "hand",
            "spatial_level": "macro",
            "modality": "hand",
            "resolution": asset.get("resolution"),
            "source": "ingestion_registry",
            "filename": asset.get("filename"),
            "path": asset.get("path"),
            "created_at": asset.get("created_at") or _now(),
            "signals": {},
            "layers": ["macro"],
            "attachment_status": "registered_root",
            "spatially_localized": False,
            "interpretation_boundary": "registered_asset_not_spatially_localized",
        }
        items.append(item)
        by_asset[asset_id] = item
        changed = True
    if changed: _save(items)
    return items

def _load() -> list[dict[str, Any]]:
    return _sync_registered_assets(_load_raw())

def _safe_node(node_id: str) -> str:
    canonical = canonical_spatial_id(node_id)
    parts = [safe_component(part, "node") for part in canonical.split("/") if part]
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

def _node_match_debug(item: dict[str, Any], node_id: str | None) -> dict[str, Any]:
    """Explain the exact spatial filter decision for one canonical record."""
    actual = item.get("spatial_node_id")
    matched = node_id is None or actual == node_id
    if node_id is None:
        reason = "no spatial_node_id filter requested"
    elif actual == node_id:
        reason = "EXACT_SPATIAL_ID_MATCH"
    elif actual == "hand" and str(node_id).startswith("hand/"):
        reason = "ROOT_ONLY_REGISTERED_ASSET_NOT_DEEP_ATTACHED"
    elif actual is None:
        reason = "MISSING_SPATIAL_NODE_ID"
    else:
        reason = "SPATIAL_ID_MISMATCH"
    return {
        "evidence_id": item.get("evidence_id"),
        "asset_id": item.get("asset_id"),
        "expected_spatial_node_id": node_id,
        "actual_spatial_node_id": actual,
        "matched": matched,
        "reason": reason,
        "attachment_status": item.get("attachment_status"),
        "spatially_localized": item.get("spatially_localized"),
        "source": item.get("source"),
        "filename": item.get("filename"),
    }

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
    return {layer: {"evidence_items": sum(1 for i in items if layer in (i.get("layers") or [])), "observed": any(layer in (i.get("layers") or []) for i in items)} for layer in SIGNAL_LAYERS.keys()}

def _direct_state(items: list[dict[str, Any]], node_id: str | None = None) -> dict[str, Any]:
    selected = [i for i in items if _node_matches(i, node_id)]; signal_summary = _signal_summary(selected)
    return {"evidence_count": len(selected), "signals": signal_summary, "biological_age": _age_summary(signal_summary), "coverage": _coverage(selected), "interpretation_boundary": "research_signals_only", "insufficient_evidence": not bool(signal_summary), "registered_evidence_count": len(selected), "localized_evidence_count": sum(1 for i in selected if i.get("spatially_localized", True))}

def _node_path(node_id: str) -> list[str]:
    parts = [p for p in node_id.split("/") if p]
    if parts and parts[0] != "hand": parts.insert(0, "hand")
    return ["/".join(parts[:i]) for i in range(1, len(parts) + 1)] or ["hand"]

def _aggregate(items: list[dict[str, Any]], root_node_id: str) -> dict[str, Any]:
    path = _node_path(root_node_id); nodes: list[dict[str, Any]] = []
    for node in path:
        descendants = [i for i in items if i.get("spatial_node_id") == node or str(i.get("spatial_node_id", "")).startswith(node + "/")]
        summary = _signal_summary(descendants)
        localized = sum(1 for i in descendants if i.get("spatially_localized", True))
        nodes.append({"node_id": node, "evidence_count": len(descendants), "signals": summary, "biological_age": _age_summary(summary), "coverage": _coverage(descendants), "status": "observed" if descendants else "insufficient_evidence", "registered_evidence_count": len(descendants), "localized_evidence_count": localized})
    return {"root_node_id": root_node_id, "nodes": nodes, "interpretation_boundary": "hierarchical_research_summary"}

@router.post("/api/spatial/attach")
async def attach_evidence(file: UploadFile = File(...), subject_id: str = Form("own_cohort"), timepoint: str = Form("T0"), spatial_node_id: str = Form("hand"), spatial_level: str = Form("macro"), modality: str = Form("hand"), resolution: str | None = Form(None), source: str | None = Form(None), signals_json: str | None = Form(None)):
    level = _validate_level(spatial_level)
    if modality not in {"hand", "images", "wsi", "rna", "metadata"}: raise HTTPException(status_code=400, detail="unsupported evidence modality")
    try: signals = _clean_signals(json.loads(signals_json)) if signals_json else {}
    except (json.JSONDecodeError, TypeError): raise HTTPException(status_code=400, detail="signals_json must be a JSON object")
    try: asset = await ingest_upload(file, subject_id, timepoint, modality)
    except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc
    items = _load()
    existing = next((i for i in items if i.get("asset_id") == asset.asset_id), None)
    item = existing or {"evidence_id": f"evidence_{uuid.uuid4().hex[:12]}", "asset_id": asset.asset_id}
    item.update({"subject_id": asset.subject_id, "timepoint": asset.timepoint, "spatial_node_id": _safe_node(spatial_node_id), "spatial_level": level, "modality": modality, "resolution": resolution, "source": source or "upload", "filename": asset.filename, "path": asset.path, "created_at": item.get("created_at") or _now(), "signals": signals, "layers": sorted({x for key in signals for x in [_layer_for_signal(key)] if x} or {level}), "attachment_status": "explicit", "spatially_localized": True, "interpretation_boundary": "explicitly_attached_evidence"})
    if existing is None: items.append(item)
    _save(items)
    return {"status": "attached", "evidence": item, "state": _direct_state(items, item["spatial_node_id"])}

@router.delete("/api/spatial/evidence")
def delete_evidence(evidence_id: str | None = None, asset_id: str | None = None):
    """Remove an explicit spatial attachment from the canonical registry.

    Ingestion assets remain available at their owning root; only the explicit
    spatial evidence link is removed. This prevents a UI-only delete from
    being resurrected by the canonical registry after refresh.
    """
    if not evidence_id and not asset_id:
        raise HTTPException(status_code=400, detail="evidence_id or asset_id is required")
    items = _load_raw()
    removed: list[dict[str, Any]] = []
    kept: list[dict[str, Any]] = []
    for item in items:
        matches_evidence = bool(evidence_id and item.get("evidence_id") == evidence_id and item.get("attachment_status") == "explicit")
        matches_asset = bool(asset_id and item.get("asset_id") == asset_id and item.get("attachment_status") == "explicit")
        if matches_evidence or matches_asset:
            removed.append(item)
        else:
            kept.append(item)
    if not removed:
        raise HTTPException(status_code=404, detail="explicit spatial evidence not found")
    _save(kept)
    return {
        "status": "deleted",
        "deleted_count": len(removed),
        "deleted": [
            {"evidence_id": item.get("evidence_id"), "asset_id": item.get("asset_id"), "filename": item.get("filename")}
            for item in removed
        ],
    }

@router.get("/api/spatial/registry")
def spatial_registry(subject_id: str = "own_cohort", timepoint: str = "T0", spatial_node_id: str | None = None, debug: bool = False):
    all_items = _load()
    requested_node = canonical_spatial_id(spatial_node_id) if spatial_node_id else None
    scoped = [i for i in all_items if _matches(i, subject_id, timepoint)]
    items = [i for i in scoped if _node_matches(i, requested_node)]
    response: dict[str, Any] = {"subject_id": subject_id, "timepoint": timepoint, "items": items, "count": len(items), "canonical": True, "spatial_node_id": requested_node}
    if debug:
        response["debug"] = {
            "filter": {"subject_id": subject_id, "timepoint": timepoint, "spatial_node_id": requested_node},
            "scoped_count": len(scoped),
            "returned_count": len(items),
            "rejected_count": len(scoped) - len(items),
            "decisions": [_node_match_debug(item, requested_node) for item in scoped],
        }
    return response

@router.get("/api/spatial/state")
def current_state(subject_id: str = "own_cohort", timepoint: str = "T0", spatial_node_id: str | None = None):
    requested_node = canonical_spatial_id(spatial_node_id) if spatial_node_id else None
    items = [i for i in _load() if _matches(i, subject_id, timepoint)]
    return {"subject_id": subject_id, "timepoint": timepoint, "spatial_node_id": requested_node, **_direct_state(items, requested_node)}

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
