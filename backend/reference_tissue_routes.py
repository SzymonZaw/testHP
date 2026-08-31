from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/api/reference/tissue", tags=["reference-tissue"])
_HAND_REFERENCE = "nih-hand-template-3DPX-017237"
_ZENODO_API = "https://zenodo.org/api/records/16795569"
_ROOT = Path(__file__).resolve().parents[1]
_LOCAL_PREVIEW = _ROOT / "data" / "reference" / "human-skin-spatial-census" / "palm_cells.json"
_NATURE_SUPPLEMENTARY_XLSX = "https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41588-026-02552-8/MediaObjects/41588_2026_2552_MOESM3_ESM.xlsx"
_SOURCES: dict[str, dict[str, Any]] = {
    "human-skin-spatial-census": {
        "id": "human-skin-spatial-census",
        "accessions": ["S-BIAD2376"],
        "label": "Single-cell spatial transcriptomic analysis of human skin anatomy",
        "organism": "Homo sapiens",
        "modality": "spatial_transcriptomics",
        "spatialMethod": "MERFISH",
        "coordinateScope": "sample_local",
        "handReferenceId": _HAND_REFERENCE,
        "registrationStatus": "unregistered_to_hand",
        "registrationReadiness": "anatomical_match_verified_transform_missing",
        "verifiedAnatomicalSites": [
            {"regionId": "palm", "sourceSite": "palm", "approxCellCount": 2600},
            {"regionId": "hand", "sourceSite": "hand", "approxCellCount": 1148},
        ],
        "dataAvailability": {
            "raw": "https://www.ebi.ac.uk/biostudies/bioimages/studies/S-BIAD2376",
            "processed": "https://doi.org/10.5281/zenodo.16795569",
            "publication": "https://doi.org/10.1038/s41588-026-02552-8",
        },
    },
    "geo-skin-spatial-visium": {
        "id": "geo-skin-spatial-visium",
        "accessions": ["GSM8238470"],
        "label": "GEO human skin spatial transcriptomics sample",
        "organism": "Homo sapiens",
        "modality": "spatial_transcriptomics",
        "spatialMethod": "10x Genomics Visium",
        "coordinateScope": "sample_local",
        "handReferenceId": _HAND_REFERENCE,
        "registrationStatus": "unregistered_to_hand",
        "registrationReadiness": "no_verified_hand_registration",
        "verifiedAnatomicalSites": [],
        "dataAvailability": {"geo": "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSM8238470"},
    },
    "hubmap-human-reference-atlas": {
        "id": "hubmap-human-reference-atlas",
        "accessions": [],
        "label": "HuBMAP Human Reference Atlas resources",
        "organism": "Homo sapiens",
        "modality": "multimodal_tissue_reference",
        "spatialMethod": None,
        "coordinateScope": "resource_dependent",
        "handReferenceId": _HAND_REFERENCE,
        "registrationStatus": "unregistered_to_hand",
        "registrationReadiness": "resource_dependent",
        "verifiedAnatomicalSites": [],
        "dataAvailability": {"portal": "https://hubmapconsortium.org/"},
    },
}


def _zenodo_record() -> dict[str, Any]:
    request = Request(_ZENODO_API, headers={"Accept": "application/json", "User-Agent": "testHP-reference-tissue/5.0"})
    try:
        with urlopen(request, timeout=15) as response:
            return json.loads(response.read(512 * 1024).decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, ValueError) as exc:
        raise HTTPException(status_code=502, detail=f"reference source metadata unavailable: {exc}") from exc


@router.get("/sources")
def list_reference_tissue_sources() -> dict[str, Any]:
    return {"handReferenceId": _HAND_REFERENCE, "sources": list(_SOURCES.values())}


@router.get("/{source_id}")
def reference_tissue_manifest(source_id: str) -> dict[str, Any]:
    source = _SOURCES.get(source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="reference tissue source not found")
    local = source_id == "human-skin-spatial-census" and _LOCAL_PREVIEW.is_file()
    return {
        "source": source,
        "dataLoadStatus": "local_extract_available" if local else "manifest_only",
        "tissueIds": [],
        "spatialCoordinates": [],
        "transform": None,
        "localExtractAvailable": local,
        "localExtractPath": str(_LOCAL_PREVIEW.relative_to(_ROOT)) if local else None,
        "supplementaryArtifacts": [
            {
                "id": "nature-supplementary-tables-1-12",
                "type": "xlsx",
                "approxSize": "17.4 MB",
                "purpose": "sample and analytical metadata; not a cell-coordinate replacement",
                "url": _NATURE_SUPPLEMENTARY_XLSX,
            }
        ],
        "note": "Large spatial data are not fetched automatically. A verified transform into the NIH hand-template frame is not established.",
    }


@router.get("/{source_id}/cells/preview")
def reference_tissue_cells_preview(
    source_id: str,
    region: str = Query(default="palm"),
    limit: int = Query(default=25, ge=1, le=100),
) -> dict[str, Any]:
    if source_id not in _SOURCES:
        raise HTTPException(status_code=404, detail="reference tissue source not found")
    if region.lower() not in {"palm", "hand"}:
        raise HTTPException(status_code=400, detail="bounded cell preview supports palm or hand only")
    if source_id == "human-skin-spatial-census" and _LOCAL_PREVIEW.is_file():
        try:
            payload = json.loads(_LOCAL_PREVIEW.read_text(encoding="utf-8"))
            cells = [
                x for x in payload.get("cells", [])
                if region.lower() in str(x.get("anatomicSite", "")).lower()
                or region.lower() in str(x.get("regionName", "")).lower()
            ][:limit]
            return {
                "sourceId": source_id,
                "status": "bounded_local_cell_preview",
                "region": region,
                "requestedLimit": limit,
                "returnedCount": len(cells),
                "cells": cells,
                "coordinateScope": "sample_local",
                "registrationStatus": "unregistered_to_hand",
                "transform": None,
                "matrixLoaded": False,
                "dataLoaded": True,
                "localExtract": True,
                "sourceFile": payload.get("sourceFile"),
                "sourceCellCount": payload.get("sourceCellCount"),
                "note": "Cells are served from a locally materialized bounded extract. Coordinates remain in dataset/sample-local space and are not projected onto NIH hand geometry.",
            }
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            return {
                "sourceId": source_id,
                "status": "local_cell_preview_invalid",
                "region": region,
                "requestedLimit": limit,
                "returnedCount": 0,
                "cells": [],
                "coordinateScope": "sample_local",
                "registrationStatus": "unregistered_to_hand",
                "transform": None,
                "matrixLoaded": False,
                "dataLoaded": False,
                "error": f"{type(exc).__name__}: {exc}",
                "note": "The local extract exists but could not be read safely.",
            }
    try:
        record = _zenodo_record()
        f = next((x for x in record.get("files") or [] if x.get("key") == "merfish.integrated_annotated.h5ad"), None)
        return {
            "sourceId": source_id,
            "status": "bounded_cell_preview_not_materialized",
            "region": region,
            "requestedLimit": limit,
            "returnedCount": 0,
            "cells": [],
            "coordinateScope": "sample_local",
            "registrationStatus": "unregistered_to_hand",
            "transform": None,
            "matrixLoaded": False,
            "dataLoaded": False,
            "remoteFile": {"name": f.get("key"), "size": f.get("size")} if f else None,
            "supplementaryArtifact": {
                "id": "nature-supplementary-tables-1-12",
                "approxSize": "17.4 MB",
                "containsCellSpatialCoordinates": False,
                "url": _NATURE_SUPPLEMENTARY_XLSX,
            },
            "note": "The smaller supplementary workbook is metadata-focused and does not replace obsm/spatial. No full H5AD download or remote cell scan is attempted.",
        }
    except Exception as exc:
        return {
            "sourceId": source_id,
            "status": "bounded_cell_preview_unavailable",
            "region": region,
            "requestedLimit": limit,
            "returnedCount": 0,
            "cells": [],
            "coordinateScope": "sample_local",
            "registrationStatus": "unregistered_to_hand",
            "transform": None,
            "matrixLoaded": False,
            "dataLoaded": False,
            "error": f"{type(exc).__name__}: {exc}",
            "note": "No full H5AD download was attempted.",
        }
