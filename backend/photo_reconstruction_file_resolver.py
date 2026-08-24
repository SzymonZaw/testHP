from __future__ import annotations

from pathlib import Path
from typing import Any

from .data_ingestion import ROOT, registry_status, safe_component
from .photo_reconstruction import PHOTO_ROOT, _load_manifest


def _safe_candidate(path: Path) -> Path | None:
    try:
        candidate = path.resolve()
        candidate.relative_to(ROOT.resolve())
    except (OSError, ValueError):
        return None
    return candidate if candidate.is_file() else None


def _prepared_fallback(prepared_asset_id: str) -> Path | None:
    pattern = f"{safe_component(prepared_asset_id, 'prepared')}_*.png"
    for candidate in PHOTO_ROOT.rglob(pattern):
        resolved = _safe_candidate(candidate)
        if resolved:
            return resolved
    return None


def _source_fallback(asset_id: str) -> Path | None:
    for asset in registry_status().get("assets", []):
        if asset.get("asset_id") != asset_id:
            continue
        path = asset.get("path")
        if path:
            resolved = _safe_candidate(ROOT / str(path))
            if resolved:
                return resolved
    return None


def resolve_photo_file(identifier: str, *, prepared: bool = False) -> Path:
    """Resolve persisted photo storage, tolerating stale/moved manifest paths."""
    for item in _load_manifest():
        key = item.get("prepared_asset_id") if prepared else item.get("asset_id")
        if key != identifier:
            continue
        path = item.get("prepared_path") if prepared else item.get("path")
        if path:
            resolved = _safe_candidate(ROOT / str(path))
            if resolved:
                return resolved
        break

    fallback = _prepared_fallback(identifier) if prepared else _source_fallback(identifier)
    if fallback:
        return fallback
    raise FileNotFoundError(identifier)
