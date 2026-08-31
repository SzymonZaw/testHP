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
MAX_RANDOM_ACCESS_TOTAL_BYTES = 512 * 1024
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
            {"key": item.get("key"), "size": item.get("size"), "checksum": item.get("checksum"), "contentType": item.get("mimetype") or item.get("content_type"), "downloadUrl": links.get("self") or links.get("content")}
        )
    return result


def _file_details(item: dict[str, Any]) -> dict[str, Any]:
    key = str(item.get("key") or "")
    suffix = key.rsplit(".", 1)[-1].lower() if "." in key else ""
    size = item.get("size")
    return {
        **item,
        "extension": f".{suffix}" if suffix else None,
        "formatHint": {"csv":"table_text","tsv":"table_text","txt":"text","json":"json_text","zip":"archive","gz":"compressed","h5ad":"anndata_hdf5","h5":"hdf5","yml":"yaml_text"}.get(suffix, "binary_or_unknown"),
        "previewableByBoundedTextRoute": suffix in {"csv","tsv","txt","json"},
        "sizeBytes": int(size) if isinstance(size, (int, float)) else size,
    }


def _candidate_files(record: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for item in _files(record):
        key = str(item.get("key") or "").lower()
        ctype = str(item.get("contentType") or "").lower()
        if key.endswith((".csv", ".tsv", ".txt", ".json")) or ctype.startswith("text/") or "json" in ctype:
            out.append(item)
    return sorted(out, key=lambda x: (x.get("size") or 0, x.get("key") or ""))


def _find_merfish_file(record: dict[str, Any]) -> dict[str, Any] | None:
    return next((item for item in _files(record) if item.get("key") == MERFISH_H5AD), None)


def _range_get(url: str, byte_limit: int, start: int = 0) -> dict[str, Any]:
    end = start + byte_limit - 1
    request = Request(url, headers={"Accept":"application/octet-stream, */*","Range":f"bytes={start}-{end}","User-Agent":USER_AGENT})
    try:
        with urlopen(request, timeout=20) as response:
            raw = response.read(byte_limit)
            return {"bytes":raw,"status":getattr(response,"status",None),"contentRange":response.headers.get("Content-Range"),"contentLength":response.headers.get("Content-Length"),"acceptRanges":response.headers.get("Accept-Ranges")}
    except (HTTPError, URLError, TimeoutError) as exc:
        return {"bytes":b"","error":str(exc)}


def _parse_text_sample(raw: bytes, file_name: str) -> dict[str, Any]:
    text = raw.decode("utf-8", errors="replace")
    lines = text.splitlines()
    if not lines:
        return {"format":"text","columns":[],"rows":[],"truncated":len(raw)>=MAX_PREVIEW_BYTES}
    delimiter = "\t" if "\t" in lines[0] else "," if "," in lines[0] else None
    if delimiter:
        reader = csv.DictReader(io.StringIO("\n".join(lines)))
        rows=[]
        for row in reader:
            rows.append(dict(row))
            if len(rows)>=MAX_PREVIEW_ROWS: break
        return {"format":"tsv" if delimiter=="\t" else "csv","file":file_name,"columns":reader.fieldnames or [],"rows":rows,"truncated":len(raw)>=MAX_PREVIEW_BYTES or len(rows)>=MAX_PREVIEW_ROWS}
    return {"format":"text","file":file_name,"columns":[],"rows":[{"value":line[:2000]} for line in lines[:MAX_PREVIEW_ROWS]],"truncated":len(raw)>=MAX_PREVIEW_BYTES or len(lines)>MAX_PREVIEW_ROWS}


@router.get("/api/reference/tissue/human-skin-spatial-census/files")
def list_reference_files() -> dict[str, Any]:
    record=_json_get(ZENODO_API)
    files=[_file_details(item) for item in _files(record)]
    candidates=[item for item in files if item.get("previewableByBoundedTextRoute")]
    return {"sourceId":"human-skin-spatial-census","zenodoRecord":record.get("id"),"doi":record.get("doi"),"files":files,"previewCandidates":candidates,"previewCandidateCount":len(candidates),"maxPreviewBytes":MAX_PREVIEW_BYTES}


@router.get("/api/reference/tissue/human-skin-spatial-census/preview")
def preview_reference_file(file_name: str | None=Query(default=None), max_bytes: int=Query(default=MAX_PREVIEW_BYTES, ge=1024, le=MAX_PREVIEW_BYTES)) -> dict[str, Any]:
    record=_json_get(ZENODO_API)
    candidates=_candidate_files(record)
    if not candidates:
        return {"sourceId":"human-skin-spatial-census","status":"no_small_text_preview_candidate","previewRows":[],"spatialCoordinates":[],"tissueIds":[],"note":"The published processed dataset is available on Zenodo, but no directly previewable text-table file was found in the record metadata. Large/binary files are not downloaded automatically."}
    selected=next((x for x in candidates if x.get("key")==file_name),None) if file_name else candidates[0]
    if selected is None: raise HTTPException(status_code=404,detail="requested reference preview file not found or is not a text preview candidate")
    url=selected.get("downloadUrl")
    if not url: raise HTTPException(status_code=502,detail="reference preview file has no download URL")
    info=_range_get(str(url),max_bytes)
    if info.get("error"): raise HTTPException(status_code=502,detail=f"reference data preview unavailable: {info['error']}")
    parsed=_parse_text_sample(info.get("bytes",b""),str(selected.get("key") or ""))
    return {"sourceId":"human-skin-spatial-census","status":"bounded_preview","file":selected,"bytesRead":len(info.get("bytes",b"")),"previewRows":parsed.get("rows",[]),"columns":parsed.get("columns",[]),"format":parsed.get("format"),"truncated":parsed.get("truncated",False),"coordinateScope":"sample_local","registrationStatus":"unregistered_to_hand","transform":None,"tissueIds":[],"spatialCoordinates":[],"note":"This is a bounded source-data preview. Records remain in the dataset's native/sample-local coordinate space; no projection onto the NIH hand template is performed."}


@router.get("/api/reference/tissue/human-skin-spatial-census/schema")
def inspect_reference_h5ad_schema() -> dict[str, Any]:
    record=_json_get(ZENODO_API)
    selected=_find_merfish_file(record)
    if not selected: raise HTTPException(status_code=404,detail=f"reference file {MERFISH_H5AD} not found")
    url=selected.get("downloadUrl")
    if not url: raise HTTPException(status_code=502,detail="reference H5AD has no download URL")
    probe=_range_get(str(url),64)
    raw=probe.get("bytes",b"")
    if probe.get("error"):
        schema={"hdf5":False,"probeStatus":"remote_probe_failed","error":probe["error"],"randomAccessInspection":False}
    elif raw[:8]!=HDF5_MAGIC:
        schema={"hdf5":False,"probeStatus":"invalid_hdf5_magic","magicHex":raw[:8].hex(" "),"randomAccessInspection":False}
    else:
        schema={"hdf5":True,"probeStatus":"hdf5_container_confirmed","magicHex":raw[:8].hex(" "),"contentRange":probe.get("contentRange"),"acceptRanges":probe.get("acceptRanges"),"contentLength":probe.get("contentLength"),"topLevelKeys":None,"obsKeys":None,"varKeys":None,"obsmKeys":None,"unsKeys":None,"randomAccessInspection":False,"note":"The remote file is confirmed as HDF5, but AnnData groups are not read from the public file URL."}
    return {"sourceId":"human-skin-spatial-census","status":"bounded_h5ad_schema_probe","file":selected,"schema":schema,"matrixLoaded":False,"dataLoaded":False,"coordinateScope":"sample_local","registrationStatus":"unregistered_to_hand","transform":None,"note":"Only the HDF5 signature and transport headers are probed."}


@router.get("/api/reference/tissue/human-skin-spatial-census/schema/random-access")
def inspect_reference_h5ad_random_access(
    block_size:int=Query(default=64*1024,ge=4096,le=256*1024),
    max_total_bytes:int=Query(default=128*1024,ge=64*1024,le=MAX_RANDOM_ACCESS_TOTAL_BYTES),
) -> dict[str, Any]:
    record=_json_get(ZENODO_API)
    selected=_find_merfish_file(record)
    if not selected: raise HTTPException(status_code=404,detail=f"reference file {MERFISH_H5AD} not found")
    url=selected.get("downloadUrl"); size=selected.get("size")
    if not url or not isinstance(size,(int,float)): raise HTTPException(status_code=502,detail="reference H5AD metadata is incomplete")
    size=int(size); block=min(int(block_size),int(max_total_bytes)); offsets=[0,max(0,size//2),max(0,size-block)]
    ranges=[]; total=0; successful=0; errors=[]; seen=set()
    for start in offsets:
        if start in seen or total>=max_total_bytes: continue
        seen.add(start); budget=min(block,size-start,int(max_total_bytes)-total)
        if budget<=0: continue
        info=_range_get(str(url),int(budget),start=start)
        if info.get("error"): errors.append(str(info["error"])); continue
        raw=info.get("bytes",b""); cr=str(info.get("contentRange") or ""); honored=cr.startswith(f"bytes {start}-")
        ranges.append({"start":start,"requested":int(budget),"received":len(raw),"contentRange":cr,"rangeHonored":honored})
        total+=len(raw)
        if len(raw)==budget and honored: successful+=1
    status="bounded_h5ad_random_access_transport_confirmed" if successful and successful==len(ranges) else "bounded_h5ad_random_access_transport_partial"
    return {"sourceId":"human-skin-spatial-census","status":status,"file":selected,"schema":None,"matrixLoaded":False,"dataLoaded":False,"bytesFetched":total,"rangeRequests":len(ranges),"blockSize":block,"maxTotalBytes":max_total_bytes,"successfulRanges":successful,"ranges":ranges,"errors":errors,"coordinateScope":"sample_local","registrationStatus":"unregistered_to_hand","transform":None,"note":"This verifies bounded HTTP Range access at multiple file offsets. It does not open or parse HDF5/AnnData groups and never downloads the full H5AD."}


def register_reference_tissue_preview(app: Any) -> None:
    app.include_router(router)
