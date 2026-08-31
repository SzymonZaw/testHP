from __future__ import annotations

import io
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import h5py
import numpy as np
from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/api/reference/tissue", tags=["reference-tissue"])

_HAND_REFERENCE = "nih-hand-template-3DPX-017237"
_ZENODO_API = "https://zenodo.org/api/records/16795569"
_MERFISH_H5AD = "merfish.integrated_annotated.h5ad"
_USER_AGENT = "testHP-reference-tissue-cells/1.0"
_MAX_CELL_PREVIEW = 100
_MAX_RANGE_BYTES = 8 * 1024 * 1024
_SOURCES = {
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
            "raw": "https://www.ebi.ac.uk/biostudies/arrayexpress/studies/S-BIAD2376",
            "processed": "https://doi.org/10.5281/zenodo.16795569",
            "interactive": "https://rstudio-connect.hpc.mssm.edu/humanskin-spatialcensus/",
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
        "dataAvailability": {
            "geo": "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSM8238470",
        },
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
    request = Request(_ZENODO_API, headers={"Accept": "application/json", "User-Agent": _USER_AGENT})
    try:
        with urlopen(request, timeout=15) as response:
            return __import__("json").loads(response.read(512 * 1024).decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, ValueError) as exc:
        raise HTTPException(status_code=502, detail=f"reference source metadata unavailable: {exc}") from exc


def _h5ad_url(record: dict[str, Any]) -> str:
    for item in record.get("files") or []:
        if item.get("key") == _MERFISH_H5AD:
            links = item.get("links") or {}
            url = links.get("content") or links.get("self")
            if url:
                return str(url)
    raise HTTPException(status_code=404, detail=f"reference file {_MERFISH_H5AD} not found")


class _RangeReader(io.RawIOBase):
    def __init__(self, url: str, size: int, block_size: int = 64 * 1024, max_bytes: int = _MAX_RANGE_BYTES):
        self.url = url
        self.size = int(size)
        self.block_size = int(block_size)
        self.max_bytes = int(max_bytes)
        self.pos = 0
        self.total = 0
        self.requests = 0
        self.cache: dict[int, bytes] = {}

    def readable(self) -> bool:
        return True

    def seekable(self) -> bool:
        return True

    def tell(self) -> int:
        return self.pos

    def seek(self, offset: int, whence: int = io.SEEK_SET) -> int:
        if whence == io.SEEK_SET:
            target = offset
        elif whence == io.SEEK_CUR:
            target = self.pos + offset
        elif whence == io.SEEK_END:
            target = self.size + offset
        else:
            raise ValueError("unsupported seek mode")
        if target < 0:
            raise ValueError("negative seek position")
        self.pos = target
        return self.pos

    def _fetch(self, start: int) -> bytes:
        if start in self.cache:
            return self.cache[start]
        remaining = self.max_bytes - self.total
        if remaining <= 0:
            raise OSError("bounded H5AD byte budget exceeded")
        length = min(self.block_size, self.size - start, remaining)
        if length <= 0:
            return b""
        request = Request(self.url, headers={"Range": f"bytes={start}-{start + length - 1}", "Accept": "application/octet-stream, */*", "User-Agent": _USER_AGENT})
        try:
            with urlopen(request, timeout=20) as response:
                payload = response.read(length)
                content_range = response.headers.get("Content-Range", "")
        except (HTTPError, URLError, TimeoutError) as exc:
            raise OSError(f"range request failed: {exc}") from exc
        if len(payload) != length:
            raise OSError(f"short range response: requested {length}, received {len(payload)}")
        if content_range and not content_range.startswith(f"bytes {start}-"):
            raise OSError(f"unexpected Content-Range: {content_range}")
        self.cache[start] = payload
        self.total += len(payload)
        self.requests += 1
        return payload

    def read(self, size: int = -1) -> bytes:
        if self.pos >= self.size:
            return b""
        if size is None or size < 0:
            size = self.size - self.pos
        end = min(self.size, self.pos + size)
        chunks: list[bytes] = []
        cursor = self.pos
        while cursor < end:
            block_start = (cursor // self.block_size) * self.block_size
            block = self._fetch(block_start)
            if not block:
                break
            in_block = cursor - block_start
            take = min(len(block) - in_block, end - cursor)
            chunks.append(block[in_block:in_block + take])
            cursor += take
        self.pos = cursor
        return b"".join(chunks)

    def readinto(self, buffer: bytearray) -> int:
        data = self.read(len(buffer))
        buffer[:len(data)] = data
        return len(data)


def _decode_scalar(value: Any) -> Any:
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if isinstance(value, np.generic):
        value = value.item()
    return value


def _read_vector(group: h5py.Group, key: str, indices: list[int], limit: int = 100) -> list[Any]:
    dataset = group[key]
    result: list[Any] = []
    for idx in indices[:limit]:
        value = dataset[idx]
        if isinstance(value, np.ndarray) and value.ndim == 0:
            value = value.item()
        result.append(_decode_scalar(value))
    return result


@router.get("/sources")
def list_reference_tissue_sources() -> dict:
    return {"handReferenceId": _HAND_REFERENCE, "sources": list(_SOURCES.values())}


@router.get("/{source_id}")
def reference_tissue_manifest(source_id: str) -> dict:
    source = _SOURCES.get(source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="reference tissue source not found")
    return {
        "source": source,
        "dataLoadStatus": "manifest_only",
        "tissueIds": [],
        "spatialCoordinates": [],
        "transform": None,
        "note": "Large spatial data are not fetched automatically. A verified transform into the NIH hand-template frame is not established.",
    }


@router.get("/{source_id}/cells/preview")
def reference_tissue_cells_preview(
    source_id: str,
    region: str = Query(default="palm"),
    limit: int = Query(default=25, ge=1, le=_MAX_CELL_PREVIEW),
) -> dict[str, Any]:
    if source_id != "human-skin-spatial-census":
        raise HTTPException(status_code=404, detail="bounded cell preview is not available for this source")
    if region.lower() not in {"palm", "hand"}:
        raise HTTPException(status_code=400, detail="bounded cell preview supports palm or hand only")

    record = _zenodo_record()
    url = _h5ad_url(record)
    selected = next(item for item in record.get("files") or [] if item.get("key") == _MERFISH_H5AD)
    size = selected.get("size")
    if not isinstance(size, (int, float)):
        raise HTTPException(status_code=502, detail="reference H5AD metadata has no numeric size")

    reader = _RangeReader(url, int(size))
    try:
        with h5py.File(reader, "r") as handle:
            obs = handle["obs"]
            obsm = handle["obsm"]
            required = {"cell_id", "cell_barcode", "anatomic_site", "region_name", "sample_id"}
            available = set(obs.keys())
            missing = sorted(required - available)
            if "spatial" not in obsm:
                raise OSError("AnnData obsm/spatial is missing")

            site_values = obs["anatomic_site"][:]
            region_values = obs["region_name"][:]
            site_lower = [_decode_scalar(v).lower() for v in site_values]
            region_lower = [_decode_scalar(v).lower() for v in region_values]
            needle = region.lower()
            indices = [i for i, (site, reg) in enumerate(zip(site_lower, region_lower)) if needle in site or needle in reg][:limit]

            spatial = obsm["spatial"]
            coords = []
            for idx in indices:
                value = np.asarray(spatial[idx]).reshape(-1)
                coords.append([float(value[0]), float(value[1])] if value.size >= 2 else [float(value[0])] if value.size else [])

            cells = []
            fields = {name: _read_vector(obs, name, indices, limit) for name in required if name in available}
            for row_idx, index in enumerate(indices):
                cells.append({
                    "index": int(index),
                    "cellId": fields.get("cell_id", [None] * len(indices))[row_idx],
                    "cellBarcode": fields.get("cell_barcode", [None] * len(indices))[row_idx],
                    "anatomicSite": fields.get("anatomic_site", [None] * len(indices))[row_idx],
                    "regionName": fields.get("region_name", [None] * len(indices))[row_idx],
                    "sampleId": fields.get("sample_id", [None] * len(indices))[row_idx],
                    "spatial": coords[row_idx],
                })

        return {
            "sourceId": source_id,
            "status": "bounded_cell_preview",
            "region": region,
            "requestedLimit": limit,
            "returnedCount": len(cells),
            "cells": cells,
            "missingRequiredObsKeys": missing,
            "coordinateScope": "sample_local",
            "registrationStatus": "unregistered_to_hand",
            "transform": None,
            "bytesFetched": reader.total,
            "rangeRequests": reader.requests,
            "maxBytes": reader.max_bytes,
            "matrixLoaded": False,
            "note": "Only bounded obs fields and obsm/spatial coordinates are read. The expression matrix X is not loaded and coordinates are not projected onto the NIH hand template.",
        }
    except (OSError, ValueError, RuntimeError, KeyError) as exc:
        return {
            "sourceId": source_id,
            "status": "bounded_cell_preview_failed",
            "region": region,
            "requestedLimit": limit,
            "returnedCount": 0,
            "cells": [],
            "coordinateScope": "sample_local",
            "registrationStatus": "unregistered_to_hand",
            "transform": None,
            "bytesFetched": reader.total,
            "rangeRequests": reader.requests,
            "maxBytes": reader.max_bytes,
            "matrixLoaded": False,
            "error": str(exc),
            "note": "The bounded reader could not complete the requested cell preview without exceeding its transfer budget. No full H5AD download was attempted.",
        }
