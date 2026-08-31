from __future__ import annotations

import csv
import io
import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from fastapi import APIRouter, HTTPException, Query

ZENODO_API = "https://zenodo.org/api/records/16795569"
MERFISH_H5AD = "merfish.integrated_annotated.h5ad"
HDF5_MAGIC = b"\x89HDF\r\n\x1a\n"
MAX_PREVIEW_BYTES = 64 * 1024
MAX_PREVIEW_ROWS = 12
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


def _head_range_get(url: str, byte_limit: int = 64) -> dict[str, Any]:
    end = max(0, byte_limit - 1)
    request = Request(
        url,
        headers={
            "Accept": "application/octet-stream, */*",
            "Range": f"bytes=0-{end}",
            "User-Agent": USER_AGENT,
        },
    )
    try:
        with urlopen(request, timeout=20) as response:
            raw = response.read(byte_limit)
            return {
                "bytes": raw,
                "status": getattr(response, "status", None),
                "contentRange": response.headers.get("Content-Range"),
                "contentLength": response.headers.get("Content-Length"),
                "acceptRanges": response.headers.get("Accept-Ranges"),
            }
    except (HTTPError, URLError, TimeoutError) as exc:
        return {"bytes": b"", "error": str(exc)}


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


def _h5ad_schema_probe(remote_url: str) -> dict[str, Any]:
    """Safely probe the remote H5AD header without random-access HDF5 reads."""
    probe = _head_range_get(remote_url, 64)
    raw = probe.get("bytes", b"")
    if probe.get("error"):
        return {
            "hdf5": False,
            "probeStatus": "remote_probe_failed",
            "error": probe["error"],
            "topLevelKeys": None,
            "obsKeys": None,
            "varKeys": None,
            "obsmKeys": None,
            "unsKeys": None,
            "randomAccessInspection": False,
        }
    if raw[:8] != HDF5_MAGIC:
        return {
            "hdf5": False,
            "probeStatus": "invalid_hdf5_magic",
            "magicHex": raw[:8].hex(" "),
            "topLevelKeys": None,
            "obsKeys": None,
            "varKeys": None,
            "obsmKeys": None,
            "unsKeys": None,
            "randomAccessInspection": False,
        }
    return {
        "hdf5": True,
        "probeStatus": "hdf5_container_confirmed",
        "magicHex": raw[:8].hex(" "),
        "contentRange": probe.get("contentRange"),
        "acceptRanges": probe.get("acceptRanges"),
        "contentLength": probe.get("contentLength"),
        "topLevelKeys": None,
        "obsKeys": None,
        "varKeys": None,
        "obsmKeys": None,
        "unsKeys": None,
        "randomAccessInspection": False,
        "note": "The remote file is confirmed as HDF5, but no random-access AnnData groups are read from the public file URL. This avoids downloading the multi-gigabyte H5AD.",
    }


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
    schema = _h5ad_schema_probe(str(url))
    return {
        "sourceId": "human-skin-spatial-census",
        "status": "bounded_h5ad_schema_probe",
        "file": selected,
        "schema": schema,
        "matrixLoaded": False,
        "dataLoaded": False,
        "coordinateScope": "sample_local",
        "registrationStatus": "unregistered_to_hand",
        "transform": None,
        "note": "Only the HDF5 file signature and transport headers are probed. No expression matrix, AnnData groups, or full cell table are loaded.",
    }


class _RangeHTTPReader(io.RawIOBase):
    """Seekable HTTP Range reader with a strict aggregate byte budget."""

    def __init__(self, url: str, size: int, block_size: int = 64 * 1024, max_total_bytes: int = 4 * 1024 * 1024):
        super().__init__()
        self.url = url
        self.size = int(size)
        self.block_size = int(block_size)
        self.max_total_bytes = int(max_total_bytes)
        self.position = 0
        self.total_fetched = 0
        self.range_requests = 0
        self.cache: dict[int, bytes] = {}

    def readable(self) -> bool:
        return True

    def seekable(self) -> bool:
        return True

    def tell(self) -> int:
        return self.position

    def seek(self, offset: int, whence: int = io.SEEK_SET) -> int:
        if whence == io.SEEK_SET:
            new_position = offset
        elif whence == io.SEEK_CUR:
            new_position = self.position + offset
        elif whence == io.SEEK_END:
            new_position = self.size + offset
        else:
            raise ValueError("unsupported seek mode")
        if new_position < 0:
            raise ValueError("negative seek position")
        self.position = new_position
        return self.position

    def _fetch_block(self, start: int) -> bytes:
        if start in self.cache:
            return self.cache[start]
        if self.total_fetched >= self.max_total_bytes:
            raise OSError("bounded random-access byte budget exceeded")
        length = min(self.block_size, self.size - start, self.max_total_bytes - self.total_fetched)
        if length <= 0:
            return b""
        request = Request(
            self.url,
            headers={
                "Accept": "application/octet-stream, */*",
                "Range": f"bytes={start}-{start + length - 1}",
                "User-Agent": USER_AGENT,
            },
        )
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
        self.total_fetched += len(payload)
        self.range_requests += 1
        return payload

    def read(self, size: int = -1) -> bytes:
        if self.position >= self.size:
            return b""
        if size is None or size < 0:
            size = self.size - self.position
        end_position = min(self.size, self.position + size)
        chunks: list[bytes] = []
        cursor = self.position
        while cursor < end_position:
            block_start = (cursor // self.block_size) * self.block_size
            block = self._fetch_block(block_start)
            if not block:
                break
            start_in_block = cursor - block_start
            take = min(len(block) - start_in_block, end_position - cursor)
            chunks.append(block[start_in_block:start_in_block + take])
            cursor += take
        self.position = cursor
        return b"".join(chunks)

    def readinto(self, buffer: bytearray) -> int:
        data = self.read(len(buffer))
        buffer[:len(data)] = data
        return len(data)


@router.get("/api/reference/tissue/human-skin-spatial-census/schema/random-access")
def inspect_reference_h5ad_random_access(
    block_size: int = Query(default=64 * 1024, ge=4096, le=256 * 1024),
    max_total_bytes: int = Query(default=4 * 1024 * 1024, ge=128 * 1024, le=4 * 1024 * 1024),
) -> dict[str, Any]:
    """Attempt real HDF5 metadata access using bounded HTTP Range reads."""
    record = _json_get(ZENODO_API)
    selected = _find_merfish_file(record)
    if not selected:
        raise HTTPException(status_code=404, detail=f"reference file {MERFISH_H5AD} not found")
    url = selected.get("downloadUrl")
    size = selected.get("size")
    if not url or not isinstance(size, (int, float)):
        raise HTTPException(status_code=502, detail="reference H5AD metadata is incomplete")

    reader = _RangeHTTPReader(str(url), int(size), block_size=block_size, max_total_bytes=max_total_bytes)
    try:
        with h5py.File(reader, "r") as handle:
            top_level = list(handle.keys())[:64]
            obs = handle.get("obs")
            var = handle.get("var")
            obsm = handle.get("obsm")
            uns = handle.get("uns")

            def keys(group: Any) -> list[str]:
                return list(group.keys())[:128] if group is not None else []

            schema = {
                "hdf5": True,
                "probeStatus": "random_access_metadata_read",
                "anndataEncodingType": handle.attrs.get("encoding-type"),
                "anndataEncodingVersion": handle.attrs.get("encoding-version"),
                "topLevelKeys": top_level,
                "obsKeys": keys(obs),
                "varKeys": keys(var),
                "obsmKeys": keys(obsm),
                "unsKeys": keys(uns),
                "randomAccessInspection": True,
            }
        return {
            "sourceId": "human-skin-spatial-census",
            "status": "bounded_h5ad_random_access",
            "file": selected,
            "schema": schema,
            "matrixLoaded": False,
            "dataLoaded": False,
            "bytesFetched": reader.total_fetched,
            "rangeRequests": reader.range_requests,
            "blockSize": reader.block_size,
            "maxTotalBytes": reader.max_total_bytes,
            "coordinateScope": "sample_local",
            "registrationStatus": "unregistered_to_hand",
            "transform": None,
            "note": "AnnData/HDF5 metadata was inspected using bounded HTTP Range reads. No expression matrix or full cell table was loaded.",
        }
    except (OSError, ValueError, RuntimeError) as exc:
        return {
            "sourceId": "human-skin-spatial-census",
            "status": "bounded_h5ad_random_access_failed",
            "file": selected,
            "schema": None,
            "matrixLoaded": False,
            "dataLoaded": False,
            "bytesFetched": reader.total_fetched,
            "rangeRequests": reader.range_requests,
            "blockSize": reader.block_size,
            "maxTotalBytes": reader.max_total_bytes,
            "coordinateScope": "sample_local",
            "registrationStatus": "unregistered_to_hand",
            "transform": None,
            "error": str(exc),
            "note": "The bounded Range reader could not satisfy the HDF5 metadata access pattern without exceeding its byte budget. No full H5AD download was attempted.",
        }


def register_reference_tissue_preview(app: Any) -> None:
    app.include_router(router)
