from __future__ import annotations

import json
import struct
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/api/reference/tissue", tags=["reference-tissue"])
_HAND_REFERENCE = "nih-hand-template-3DPX-017237"
_ZENODO_API = "https://zenodo.org/api/records/16795569"
_EXPLORER_URL = "https://rstudio-connect.hpc.mssm.edu/humanskin-spatialcensus/"
_ROOT = Path(__file__).resolve().parents[1]
_LOCAL_PREVIEW = _ROOT / "data" / "reference" / "human-skin-spatial-census" / "cells_preview.json"
_NATURE_SUPPLEMENTARY_XLSX = "https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41588-026-02552-8/MediaObjects/41588_2026_2552_MOESM3_ESM.xlsx"
_SUPPLEMENTARY_ZIP = "supplementary_tables.zip"
_MAX_ARCHIVE_INSPECT_BYTES = 1 * 1024 * 1024
_MAX_ARCHIVE_ENTRIES = 5000
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
            "explorer": _EXPLORER_URL,
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
    request = Request(_ZENODO_API, headers={"Accept": "application/json", "User-Agent": "testHP-reference-tissue/6.1"})
    try:
        with urlopen(request, timeout=15) as response:
            return json.loads(response.read(512 * 1024).decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, ValueError) as exc:
        raise HTTPException(status_code=502, detail=f"reference source metadata unavailable: {exc}") from exc


def _file_metadata(record: dict[str, Any], key: str) -> dict[str, Any]:
    for item in record.get("files") or []:
        if item.get("key") == key:
            return item
    raise HTTPException(status_code=404, detail=f"reference file {key} not found")


def _file_url(item: dict[str, Any]) -> str:
    links = item.get("links") or {}
    url = links.get("content") or links.get("self")
    if not url:
        raise HTTPException(status_code=404, detail=f"reference file {item.get('key')} has no content URL")
    return str(url)


def _range_fetch(url: str, start: int, end: int) -> tuple[bytes, dict[str, str]]:
    request = Request(url, headers={
        "Range": f"bytes={start}-{end}",
        "Accept": "application/octet-stream, */*",
        "User-Agent": "testHP-reference-tissue/6.1",
    })
    try:
        with urlopen(request, timeout=20) as response:
            return response.read(end - start + 1), {
                "content-range": response.headers.get("Content-Range", ""),
                "accept-ranges": response.headers.get("Accept-Ranges", ""),
            }
    except (HTTPError, URLError, TimeoutError) as exc:
        raise HTTPException(status_code=502, detail=f"remote range request failed: {exc}") from exc


def _find_eocd(payload: bytes) -> int:
    return payload.rfind(b"PK\x05\x06")


def _parse_zip_central_directory(payload: bytes, cd_offset: int, cd_size: int) -> list[dict[str, Any]]:
    signature = b"PK\x01\x02"
    end = min(len(payload), cd_offset + cd_size)
    cursor = cd_offset
    entries: list[dict[str, Any]] = []
    while cursor + 46 <= end and len(entries) < _MAX_ARCHIVE_ENTRIES:
        if payload[cursor:cursor + 4] != signature:
            break
        values = struct.unpack("<4s6H3I5H2I", payload[cursor:cursor + 46])
        filename_len, extra_len, comment_len = values[10], values[11], values[12]
        compressed_size, uncompressed_size = values[8], values[9]
        local_offset = values[16]
        name_start = cursor + 46
        name_end = name_start + filename_len
        if name_end + extra_len + comment_len > end:
            break
        entries.append({
            "name": payload[name_start:name_end].decode("utf-8", errors="replace"),
            "compressedSize": compressed_size,
            "uncompressedSize": uncompressed_size,
            "localHeaderOffset": local_offset,
        })
        cursor = name_end + extra_len + comment_len
    return entries


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
        "supplementaryArtifacts": [{
            "id": "nature-supplementary-tables-1-12",
            "type": "xlsx",
            "approxSize": "17.4 MB",
            "purpose": "sample and analytical metadata; not a cell-coordinate replacement",
            "url": _NATURE_SUPPLEMENTARY_XLSX,
        }],
        "officialExplorer": {
            "url": _EXPLORER_URL,
            "type": "rstudio_connect_shiny",
            "accessMode": "interactive_only",
            "programmaticCellApi": "not_documented_publicly",
            "supportsInteractiveSpatialPlots": True,
            "notes": "The published explorer exposes interactive spatial plots and selectors, but no documented public REST endpoint for bounded cell-coordinate retrieval was found.",
        },
        "note": "Large spatial data are not fetched automatically. A verified transform into the NIH hand-template frame is not established.",
    }


@router.get("/{source_id}/explorer")
def reference_tissue_explorer(source_id: str) -> dict[str, Any]:
    if source_id not in _SOURCES:
        raise HTTPException(status_code=404, detail="reference tissue source not found")
    return {
        "sourceId": source_id,
        "status": "interactive_only",
        "url": _EXPLORER_URL if source_id == "human-skin-spatial-census" else None,
        "type": "rstudio_connect_shiny" if source_id == "human-skin-spatial-census" else None,
        "programmaticCellApi": "not_documented_publicly" if source_id == "human-skin-spatial-census" else None,
        "spatialDataSource": "zenodo_processed_merfish",
        "cellCountApprox": 1200000 if source_id == "human-skin-spatial-census" else None,
        "sampleCount": 114 if source_id == "human-skin-spatial-census" else None,
        "anatomicSiteCount": 15 if source_id == "human-skin-spatial-census" else None,
        "coordinateScope": "sample_local",
        "registrationStatus": "unregistered_to_hand",
        "transform": None,
        "note": "Use the explorer for interactive browsing. This API does not scrape session state or claim a hidden REST cell endpoint.",
    }


@router.get("/{source_id}/supplementary/archive-inspect")
def inspect_supplementary_archive(
    source_id: str,
    window_bytes: int = Query(default=262144, ge=65536, le=_MAX_ARCHIVE_INSPECT_BYTES),
) -> dict[str, Any]:
    if source_id != "human-skin-spatial-census":
        raise HTTPException(status_code=404, detail="supplementary archive inspection is not available for this source")
    record = _zenodo_record()
    item = _file_metadata(record, _SUPPLEMENTARY_ZIP)
    size = item.get("size")
    if not isinstance(size, (int, float)) or int(size) <= 0:
        raise HTTPException(status_code=502, detail="supplementary archive metadata has no usable size")
    total_size = int(size)
    window = min(window_bytes, total_size)
    start = total_size - window
    payload, headers = _range_fetch(_file_url(item), start, total_size - 1)
    eocd_rel = _find_eocd(payload)
    if eocd_rel < 0 or eocd_rel + 22 > len(payload):
        return {
            "sourceId": source_id,
            "status": "zip_eocd_not_found_in_bounded_window",
            "archive": {"name": item.get("key"), "size": total_size},
            "bytesFetched": len(payload),
            "rangeStart": start,
            "rangeEnd": total_size - 1,
            "entries": [],
            "note": "The ZIP end-of-central-directory marker was not found in the bounded suffix window. No archive contents were downloaded.",
        }
    eocd = payload[eocd_rel:eocd_rel + 22]
    _, _disk_no, _cd_disk, _entries_disk, entries_total, cd_size, cd_offset, _comment_len = struct.unpack("<4s4H2IH", eocd)
    if entries_total == 0xFFFF or cd_size == 0xFFFFFFFF or cd_offset == 0xFFFFFFFF:
        return {
            "sourceId": source_id,
            "status": "zip64_central_directory_not_supported",
            "archive": {"name": item.get("key"), "size": total_size},
            "bytesFetched": len(payload),
            "rangeStart": start,
            "rangeEnd": total_size - 1,
            "entries": [],
            "note": "The archive uses ZIP64 metadata; bounded inspection stopped without downloading archive contents.",
        }
    cd_abs_start = int(cd_offset)
    cd_abs_end = cd_abs_start + int(cd_size)
    if cd_abs_start < start or cd_abs_end > total_size:
        needed_start = max(0, cd_abs_start)
        needed_end = min(total_size - 1, cd_abs_end - 1)
        if needed_end - needed_start + 1 > _MAX_ARCHIVE_INSPECT_BYTES:
            return {
                "sourceId": source_id,
                "status": "central_directory_exceeds_bounded_window",
                "archive": {"name": item.get("key"), "size": total_size},
                "centralDirectory": {"offset": cd_abs_start, "size": int(cd_size)},
                "bytesFetched": len(payload),
                "rangeStart": start,
                "rangeEnd": total_size - 1,
                "entries": [],
                "note": "The ZIP central directory is larger than the safe inspection window. No archive contents were downloaded.",
            }
        payload, headers = _range_fetch(_file_url(item), needed_start, needed_end)
        start = needed_start
        cd_offset = 0
        cd_size = needed_end - needed_start + 1
    else:
        cd_offset = cd_abs_start - start
    entries = _parse_zip_central_directory(payload, int(cd_offset), int(cd_size))
    return {
        "sourceId": source_id,
        "status": "bounded_zip_central_directory_inspected",
        "archive": {"name": item.get("key"), "size": total_size},
        "centralDirectory": {"offset": cd_abs_start, "size": int(cd_size), "entryCount": int(entries_total), "parsedEntryCount": len(entries)},
        "bytesFetched": len(payload),
        "rangeStart": start,
        "rangeEnd": start + len(payload) - 1,
        "entries": entries,
        "note": "Only ZIP directory metadata were read. No member file contents were downloaded or decompressed.",
        "http": headers,
    }


@router.get("/{source_id}/cells/preview")
def reference_tissue_cells_preview(
    source_id: str,
    region: str = Query(default="palm"),
    limit: int = Query(default=25, ge=1, le=1000),
) -> dict[str, Any]:
    if source_id not in _SOURCES:
        raise HTTPException(status_code=404, detail="reference tissue source not found")
    normalized_region = region.strip().lower()
    if not normalized_region:
        raise HTTPException(status_code=400, detail="region must not be empty")
    if source_id == "human-skin-spatial-census" and _LOCAL_PREVIEW.is_file():
        try:
            payload = json.loads(_LOCAL_PREVIEW.read_text(encoding="utf-8"))
            cells = [
                x for x in payload.get("cells", [])
                if normalized_region in str(x.get("anatomicSite", "")).lower()
                or normalized_region in str(x.get("regionName", "")).lower()
            ][:limit]
            return {
                "sourceId": source_id,
                "status": "bounded_local_cell_preview" if cells else "bounded_local_cell_preview_empty",
                "region": normalized_region,
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
            return {"sourceId": source_id, "status": "local_cell_preview_invalid", "region": normalized_region, "requestedLimit": limit, "returnedCount": 0, "cells": [], "coordinateScope": "sample_local", "registrationStatus": "unregistered_to_hand", "transform": None, "matrixLoaded": False, "dataLoaded": False, "error": f"{type(exc).__name__}: {exc}", "note": "The local extract exists but could not be read safely."}
    if source_id == "human-skin-spatial-census":
        return {
            "sourceId": source_id,
            "status": "bounded_cell_preview_not_materialized",
            "region": normalized_region,
            "requestedLimit": limit,
            "returnedCount": 0,
            "cells": [],
            "coordinateScope": "sample_local",
            "registrationStatus": "unregistered_to_hand",
            "transform": None,
            "matrixLoaded": False,
            "dataLoaded": False,
            "note": "No local bounded extract is available for the requested region. No full H5AD download or remote cell scan is attempted.",
        }
    try:
        record = _zenodo_record()
        f = _file_metadata(record, "merfish.integrated_annotated.h5ad")
        return {"sourceId": source_id, "status": "bounded_cell_preview_not_materialized", "region": normalized_region, "requestedLimit": limit, "returnedCount": 0, "cells": [], "coordinateScope": "sample_local", "registrationStatus": "unregistered_to_hand", "transform": None, "matrixLoaded": False, "dataLoaded": False, "remoteFile": {"name": f.get("key"), "size": f.get("size")}, "supplementaryArtifact": {"id": "nature-supplementary-tables-1-12", "approxSize": "17.4 MB", "containsCellSpatialCoordinates": False, "url": _NATURE_SUPPLEMENTARY_XLSX}, "officialExplorer": {"url": _EXPLORER_URL, "type": "rstudio_connect_shiny", "accessMode": "interactive_only"}, "note": "The smaller supplementary workbook is metadata-focused and does not replace obsm/spatial. No full H5AD download or remote cell scan is attempted."}
    except Exception as exc:
        return {"sourceId": source_id, "status": "bounded_cell_preview_unavailable", "region": normalized_region, "requestedLimit": limit, "returnedCount": 0, "cells": [], "coordinateScope": "sample_local", "registrationStatus": "unregistered_to_hand", "transform": None, "matrixLoaded": False, "dataLoaded": False, "error": f"{type(exc).__name__}: {exc}", "note": "No full H5AD download was attempted."}
