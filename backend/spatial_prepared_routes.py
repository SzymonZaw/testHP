"""Canonical writer for prepared Digital Twin surface evidence."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from .data_ingestion import ingest_upload
from .stage_2_4 import REGISTRY_PATH, _load, _save, _safe_node

router = APIRouter(tags=["digital-twin-spatial-prepared"])
ROOT = Path(__file__).resolve().parents[1]
ALIASES = {
    "hand/palm/thenar-eminence": "hand/palm/thenar",
    "hand/palm/hypothenar-eminence": "hand/palm/hypothenar",
    "hand/palm/central-palm-eminence": "hand/palm/central-palm",
}
LEVEL_BY_DEPTH = {1: "macro", 2: "macro", 3: "tissue", 4: "cellular", 5: "cell"}


def canonical_spatial_id(value: str) -> str:
    raw = _safe_node(value or "hand")
    return ALIASES.get(raw, raw)


def level_for_target(target: str) -> str:
    return LEVEL_BY_DEPTH.get(len([p for p in target.split("/") if p]), "cell")


@router.post("/api/spatial/prepared")
async def register_prepared_surface(
    file: UploadFile = File(...),
    subject_id: str = Form("own_cohort"),
    timepoint: str = Form("T0"),
    spatial_node_id: str = Form("hand"),
    spatial_level: str | None = Form(None),
    source_evidence_id: str | None = Form(None),
):
    target = canonical_spatial_id(spatial_node_id)
    level = spatial_level or level_for_target(target)
    if level not in {"macro", "tissue", "cellular", "cell"}:
        raise HTTPException(status_code=400, detail="unsupported spatial level")
    try:
        asset = await ingest_upload(file, subject_id, timepoint, "hand")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    items = _load()
    item = {
        "evidence_id": f"prepared_{uuid.uuid4().hex[:12]}",
        "asset_id": asset.asset_id,
        "subject_id": asset.subject_id,
        "timepoint": asset.timepoint,
        "spatial_node_id": target,
        "spatial_level": level,
        "modality": "hand",
        "resolution": None,
        "source": "prepared_surface",
        "filename": asset.filename,
        "path": asset.path,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "signals": {},
        "layers": [level],
        "attachment_status": "explicit_prepared",
        "spatially_localized": True,
        "prepared": True,
        "prepared_asset_id": asset.asset_id,
        "source_evidence_id": source_evidence_id,
        "interpretation_boundary": "prepared_surface_observation_no_anatomical_inference",
    }
    items.append(item)
    _save(items)
    return {"status": "registered", "evidence": item}
