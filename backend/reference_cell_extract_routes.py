from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query

ROOT = Path(__file__).resolve().parents[1]
EXTRACT_PATH = ROOT / "data" / "reference" / "human-skin-spatial-census" / "cells_preview.json"
SOURCE_ID = "human-skin-spatial-census"

router = APIRouter(prefix="/api/reference/tissue", tags=["reference-cell-extract"])


def _extract_signature() -> tuple[int, int]:
    try:
        stat = EXTRACT_PATH.stat()
    except OSError:
        return (0, 0)
    return (stat.st_mtime_ns, stat.st_size)


@lru_cache(maxsize=2)
def _read_extract_cached(signature: tuple[int, int]) -> dict[str, Any]:
    if not signature[1]:
        raise HTTPException(
            status_code=404,
            detail="local cell extract not found; run scripts/build_merfish_local_preview.py first",
        )
    try:
        payload = json.loads(EXTRACT_PATH.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=500, detail=f"local cell extract invalid: {exc}") from exc
    if not isinstance(payload, dict):
        raise HTTPException(status_code=500, detail="local cell extract must contain a JSON object")
    cells = payload.get("cells")
    if not isinstance(cells, list):
        raise HTTPException(status_code=500, detail="local cell extract has no cells array")
    return payload


def _read_extract() -> dict[str, Any]:
    return _read_extract_cached(_extract_signature())


def _filter_cells(payload: dict[str, Any], region: str | None, limit: int) -> list[dict[str, Any]]:
    cells = payload["cells"]
    normalized = (region or "").strip().lower()
    if not normalized:
        return cells[:limit]
    filtered = []
    for cell in cells:
        searchable = " ".join(
            str(cell.get(key, "")) for key in ("anatomicSite", "regionName")
        ).lower()
        if normalized in searchable:
            filtered.append(cell)
            if len(filtered) >= limit:
                break
    return filtered


@router.get("/{source_id}/cells/local-preview")
def local_cell_preview(
    source_id: str,
    region: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
) -> dict[str, Any]:
    if source_id != SOURCE_ID:
        raise HTTPException(status_code=404, detail="local cell extract not available for this source")

    payload = _read_extract()
    cells = _filter_cells(payload, region, limit)
    return {
        "sourceId": SOURCE_ID,
        "status": "bounded_local_cell_preview" if cells else "bounded_local_cell_preview_empty",
        "region": region.strip().lower() if region else None,
        "requestedLimit": limit,
        "returnedCount": len(cells),
        "cells": cells,
        "coordinateScope": payload.get("coordinateScope", "sample_local"),
        "registrationStatus": payload.get("registrationStatus", "unregistered_to_hand"),
        "transform": payload.get("transform"),
        "dataLoaded": True,
        "matrixLoaded": False,
        "localExtract": True,
        "sourceFile": payload.get("sourceFile") or payload.get("sourceDataset"),
        "sampleId": payload.get("sampleId"),
        "anatomicSite": payload.get("anatomicSite"),
        "sourceCellCount": payload.get("sourceCellCount"),
        "note": "Real cells from a locally materialized bounded H5AD extract. Coordinates remain in dataset/sample-local space and are not projected onto NIH hand geometry.",
    }


@router.get("/{source_id}/cells/local-preview/status")
def local_cell_preview_status(source_id: str) -> dict[str, Any]:
    if source_id != SOURCE_ID:
        raise HTTPException(status_code=404, detail="local cell extract not available for this source")
    signature = _extract_signature()
    if not signature[1]:
        return {
            "sourceId": SOURCE_ID,
            "available": False,
            "status": "not_materialized",
            "path": str(EXTRACT_PATH.relative_to(ROOT)),
            "sizeBytes": 0,
        }
    payload = _read_extract_cached(signature)
    return {
        "sourceId": SOURCE_ID,
        "available": True,
        "status": "materialized",
        "path": str(EXTRACT_PATH.relative_to(ROOT)),
        "sizeBytes": signature[1],
        "returnedCount": len(payload.get("cells", [])),
        "anatomicSite": payload.get("anatomicSite"),
        "sampleId": payload.get("sampleId"),
        "sourceFile": payload.get("sourceFile") or payload.get("sourceDataset"),
    }


def register_reference_cell_extract_routes(app: Any) -> None:
    app.include_router(router)
