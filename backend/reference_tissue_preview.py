from __future__ import annotations

import csv
import io
import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import fsspec
import h5py
from fastapi import APIRouter, HTTPException, Query

ZENODO_API = "https://zenodo.org/api/records/16795569"
MERFISH_H5AD = "merfish.integrated_annotated.h5ad"
MAX_PREVIEW_BYTES = 64 * 1024
MAX_PREVIEW_ROWS = 12
MAX_H5AD_METADATA_KEYS = 200
USER_AGENT = "testHP-reference-tissue-preview/1.0"

router = APIRouter(tags=["reference-tissue-preview"])


def _json_get(url: str) -> dict[str, Any]:
    request = Request(url, headers={"Accept": "application/json", "User-Agent": USER_AGENT})
    try:
        with urlopen(request, timeout=15) as response:
            payload = response.read(512 * 1024)
    except (HTTPError, URLError, TimeoutError) as exc:
        raise HTTPException(status_code=502, detail=f"reference source metadata unavailable: {exc}") from exc
    try:
        return json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=502, detail="reference source returned invalid JSON") from exc


def _files(record: dict[str, Any]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for item in record.get("files") or []:
        links = item.get("links") or {}
        result.append(
            {
                "key": item.get("key"),
                "size": item.get("size"),
                "checksum": item.get("checksum"),
                "contentType": item.get("mimetype") or item.get("content_type"),
                "downloadUrl": links.get("self") or links.get("content"),
            }
        )
    return result


def _candidate_files(record: dict[str, Any]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for item in _files(record):
        name = str(item.get("key") or "").lower()
        content_type = str(item.get("contentType") or "").lower()
        if name.endswith((".csv", ".tsv", ".txt", ".json")) or content_type.startswith("text/") or "json" in content_type:
            candidates.append(item)
    return sorted(candidates, key=lambda x: (x.get("size") or 0, x.get("key") or ""))


def _range_get(url: str, byte_limit: int) -> bytes:
    end = max(0, byte_limit - 1)
    request = Request(
        url,
        headers={
            "Accept": "text/plain, text/csv, application/json, */*",
            "Range": f"bytes=0-{end}",
            "User-Agent": USER_AGENT,
        },
    )
    try:
        with urlopen(request, timeout=20) as response:
            return response.read(byte_limit)
    except (HTTPError, URLError, TimeoutError) as exc:
        raise HTTPException(status_code=502, detail=f"reference data preview unavailable: {exc}") from exc


def _parse_text_sample(raw: bytes, file_name: str) -> dict[str, Any]:
    text = raw.decode("utf-8", errors="replace")
    truncated = len(raw) >= MAX_PREVIEW_BYTES
    lines = text.splitlines()
    if not lines:
        return {"format": "text", "columns": [], "rows": [], "truncated": truncated}

    delimiter = "\t" if "\t" in lines[0] else "," if "," in lines[0] else None
    if delimiter:
        reader = csv.DictReader(io.StringIO("\n".join(lines)))
        rows = []
        for row in reader:
            rows.append(dict(row))
            if len(rows) >= MAX_PREVIEW_ROWS:
                break
        return {
            "format": "tsv" if delimiter == "\t" else "csv",
            "file": file_name,
            "columns": reader.fieldnames or [],
            "rows": rows,
            "truncated": truncated or len(rows) >= MAX_PREVIEW_ROWS,
        }

    return {
        "format": "text",
        "file": file_name,
        "columns": [],
        "rows": [{"value": line[:2000]} for line in lines[:MAX_PREVIEW_ROWS]],
        "truncated": truncated or len(lines) > MAX_PREVIEW_ROWS,
    }


def _file_details(item: dict[str, Any]) -> dict[str, Any]:
    key = str(item.get("key") or "")
    suffix = key.rsplit(".", 1)[-1].lower() if "." in key else ""
    size = item.get("size")
    return {
        **item,
        "extension": f".{suffix}" if suffix else None,
        "formatHint": {
            "csv": "table_text",
            "tsv": "table_text",
            "txt": "text",
            "json": "json_text",
            "zip": "archive",
            "gz": "compressed",
            "h5ad": "anndata_hdf5",
            "h5": "hdf5",
            "yml": "yaml_text",
        }.get(suffix, "binary_or_unknown"),
        "previewableByBoundedTextRoute": suffix in {"csv", "tsv", "txt", "json"},
        "sizeBytes": int(size) if isinstance(size, (int, float)) else size,
    }


def _find_merfish_file(record: dict[str, Any]) -> dict[str, Any] | None:
    return next((item for item in _files(record) if item.get("key") == MERFISH_H5AD), None)


def _h5ad_schema(remote_url: str) -> dict[str, Any]:
    """Inspect H5AD structure through HTTP range reads without loading X/data matrices."""
    try:
        with fsspec.open(
            remote_url,
            mode="rb",
            block_size=64 * 1024,
            headers={"User-Agent": USER_AGENT, "Accept-Encoding": "identity"},
        ) as remote:
            with h5py.File(remote, "r") as handle:
                top_level = list(handle.keys())[:MAX_H5AD_METADATA_KEYS]
                obs = handle.get("obs")
                var = handle.get("var")
                obsm = handle.get("obsm")
                uns = handle.get("uns")

                def keys(group: Any) -> list[str]:
                    return list(group.keys())[:MAX_H5AD_METADATA_KEYS] if group is not None else []

                return {
                    "hdf5": True,
                    "anndataEncodingType": handle.attrs.get("encoding-type"),
                    "anndataEncodingVersion": handle.attrs.get("encoding-version"),
                    "topLevelKeys": top_level,
                    "obsKeys": keys(obs),
                    "varKeys": keys(var),
                    "obsmKeys": keys(obsm),
                    "unsKeys": keys(uns),
                    "obsShape": tuple(obs.attrs.get("_index", [])) if False else None,
                }
    except (OSError, ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=502, detail=f"H5AD metadata inspection failed: {exc}") from exc


@router.get("/api/reference/tissue/human-skin-spatial-census/files")
def list_reference_files() -> dict[str, Any]:
    record = _json_get(ZENODO_API)
    files = [_file_details(item) for item in _files(record)]
    candidates = [item for item in files if item.get("previewableByBoundedTextRoute")]
    return {
        "sourceId": "human-skin-spatial-census",
        "zenodoRecord": record.get("id"),
        "doi": record.get("doi"),
        "files": files,
        "previewCandidates": candidates,
        "previewCandidateCount": len(candidates),
        "maxPreviewBytes": MAX_PREVIEW_BYTES,
    }


@router.get("/api/reference/tissue/human-skin-spatial-census/preview")
def preview_reference_file(
    file_name: str | None = Query(default=None),
    max_bytes: int = Query(default=MAX_PREVIEW_BYTES, ge=1024, le=MAX_PREVIEW_BYTES),
) -> dict[str, Any]:
    record = _json_get(ZENODO_API)
    candidates = _candidate_files(record)
    if not candidates:
        return {
            "sourceId": "human-skin-spatial-census",
            "status": "no_small_text_preview_candidate",
            "previewRows": [],
            "spatialCoordinates": [],
            "tissueIds": [],
            "note": "The published processed dataset is available on Zenodo, but no directly previewable text-table file was found in the record metadata. Large/binary files are not downloaded automatically.",
        }

    selected = next((x for x in candidates if x.get("key") == file_name), None) if file_name else candidates[0]
    if selected is None:
        raise HTTPException(status_code=404, detail="requested reference preview file not found or is not a text preview candidate")
    url = selected.get("downloadUrl")
    if not url:
        raise HTTPException(status_code=502, detail="reference preview file has no download URL")

    raw = _range_get(str(url), max_bytes)
    parsed = _parse_text_sample(raw, str(selected.get("key") or ""))
    return {
        "sourceId": "human-skin-spatial-census",
        "status": "bounded_preview",
        "file": selected,
        "bytesRead": len(raw),
        "previewRows": parsed.get("rows", []),
        "columns": parsed.get("columns", []),
        "format": parsed.get("format"),
        "truncated": parsed.get("truncated", False),
        "coordinateScope": "sample_local",
        "registrationStatus": "unregistered_to_hand",
        "transform": None,
        "tissueIds": [],
        "spatialCoordinates": [],
        "note": "This is a bounded source-data preview. Records remain in the dataset's native/sample-local coordinate space; no projection onto the NIH hand template is performed.",
    }


@router.get("/api/reference/tissue/human-skin-spatial-census/schema")
def inspect_reference_h5ad_schema() -> dict[str, Any]:
    record = _json_get(ZENODO_API)
    selected = _find_merfish_file(record)
    if not selected:
        raise HTTPException(status_code=404, detail=f"reference file {MERFISH_H5AD} not found")
    url = selected.get("downloadUrl")
    if not url:
        raise HTTPException(status_code=502, detail="reference H5AD has no download URL")
    schema = _h5ad_schema(str(url))
    return {
        "sourceId": "human-skin-spatial-census",
        "status": "bounded_h5ad_schema",
        "file": selected,
        "schema": schema,
        "matrixLoaded": False,
        "dataLoaded": False,
        "coordinateScope": "sample_local",
        "registrationStatus": "unregistered_to_hand",
        "transform": None,
        "note": "Only AnnData/HDF5 group metadata is inspected through HTTP range reads. Expression matrices and full cell tables are not loaded.",
    }


def register_reference_tissue_preview(app: Any) -> None:
    app.include_router(router)
