"""Non-destructive ingestion of files from data/raw into biological observations."""
from __future__ import annotations

from pathlib import Path
from typing import Any

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".webp"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
TABULAR_EXTENSIONS = {".csv", ".tsv", ".json", ".jsonl"}
TEXT_EXTENSIONS = {".txt", ".md"}


def infer_modality(path: Path) -> str:
    """Infer a conservative modality from file extension and raw path."""
    suffix = path.suffix.lower()
    parts = {p.lower() for p in path.parts}
    if suffix in IMAGE_EXTENSIONS:
        if "wsi" in parts or "microscopy" in parts:
            return "wsi"
        return "image"
    if suffix in VIDEO_EXTENSIONS:
        return "video"
    if "rna" in parts and suffix in TABULAR_EXTENSIONS:
        return "rna"
    if suffix in TABULAR_EXTENSIONS:
        return "tabular"
    if suffix in TEXT_EXTENSIONS:
        return "text"
    return "unknown"


def scan_raw(raw_root: str | Path) -> list[dict[str, Any]]:
    """Scan raw files without changing them.

    The public result is kept as plain dictionaries for backwards compatibility
    with the ingestion API and existing callers.
    """
    root = Path(raw_root)
    if not root.exists():
        return []
    result: list[dict[str, Any]] = []
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        result.append({
            "path": str(path),
            "relative_path": str(path.relative_to(root)),
            "modality": infer_modality(path),
            "size_bytes": path.stat().st_size,
        })
    return result


def artifact_records(raw_root: str | Path) -> list[dict[str, Any]]:
    """Return JSON-serializable artifact records for the observation layer."""
    return scan_raw(raw_root)
