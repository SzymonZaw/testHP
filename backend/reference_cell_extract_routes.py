from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query

ROOT = Path(__file__).resolve().parents[1]
EXTRACT_PATH = ROOT / "data" / "reference" / "human-skin-spatial-census" / "cells_preview.json"
SOURCE_ID = "human-skin-spatial-census"

router = APIRouter(prefix="/api/reference/tissue", tags=["reference-cell-extract"])


def _read_extract() -> dict[str, Any]:
    if not EXTRACT_PATH.is_file():
        raise HTTPException(
            status_code=404,
            detail="local cell extract not found; run extract_reference_tissue_preview.py first",
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


@router.get("/{source_id}/cells/local-preview")
def local_cell_preview(
    source_id: str,
    limit: int = Query(default=100, ge=1, le=1000),
) -> dict[str, Any]:
    if source_id != SOURCE_ID:
        raise HTTPException(status_code=404, detail="local cell extract not available for this source")

    payload = _read_extract()
    cells = payload["cells"][:limit]
    return {
        "sourceId": SOURCE_ID,
        "status": "bounded_local_cell_preview",
        "requestedLimit": limit,
        "returnedCount": len(cells),
        "cells": cells,
        "coordinateScope": payload.get("coordinateScope", "sample_local"),
        "registrationStatus": payload.get("registrationStatus", "unregistered_to_hand"),
        "transform": payload.get("transform"),
        "dataLoaded": True,
        "matrixLoaded": False,
        "localExtract": True,
        "sourceFile": payload.get("sourceFile"),
        "sampleId": payload.get("sampleId"),
        "anatomicSite": payload.get("anatomicSite"),
        "sourceCellCount": payload.get("sourceCellCount"),
        "note": "Real cells from a locally materialized bounded H5AD extract. Coordinates remain in dataset/sample-local space and are not projected onto NIH hand geometry.",
    }


@router.get("/{source_id}/cells/local-preview/status")
def local_cell_preview_status(source_id: str) -> dict[str, Any]:
    if source_id != SOURCE_ID:
        raise HTTPException(status_code=404, detail="local cell extract not available for this source")
    if not EXTRACT_PATH.is_file():
        return {
            "sourceId": SOURCE_ID,
            "available": False,
            "status": "not_materialized",
            "path": str(EXTRACT_PATH.relative_to(ROOT)),
        }
    payload = _read_extract()
    return {
        "sourceId": SOURCE_ID,
        "available": True,
        "status": "materialized",
        "path": str(EXTRACT_PATH.relative_to(ROOT)),
        "returnedCount": len(payload.get("cells", [])),
        "anatomicSite": payload.get("anatomicSite"),
        "sampleId": payload.get("sampleId"),
        "sourceFile": payload.get("sourceFile"),
    }


def register_reference_cell_extract_routes(app: Any) -> None:
    app.include_router(router)
