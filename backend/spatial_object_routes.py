"""Read-only API for canonical SpatialObject records published by reconstruction."""
from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, HTTPException

from .data_ingestion import ROOT

router = APIRouter(prefix="/api/spatial/objects", tags=["spatial-model"])
INDEX = ROOT / "data" / "registry" / "spatial_objects.json"


def _load() -> list[dict[str, Any]]:
    if not INDEX.is_file():
        return []
    try:
        value = json.loads(INDEX.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    return value if isinstance(value, list) else []


@router.get("")
def spatial_objects(subject_id: str | None = None, object_type: str | None = None):
    items = _load()
    if subject_id:
        items = [x for x in items if x.get("subject_id") == subject_id]
    if object_type:
        items = [x for x in items if x.get("object_type") == object_type]
    return {"count": len(items), "objects": items}


@router.get("/{spatial_object_id:path}")
def spatial_object(spatial_object_id: str):
    item = next((x for x in _load() if x.get("spatial_object_id") == spatial_object_id), None)
    if item is None:
        raise HTTPException(status_code=404, detail="spatial object not found")
    return {"object": item}
