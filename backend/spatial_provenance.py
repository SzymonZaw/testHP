"""Shared provenance helpers for spatial/reconstruction modules."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_provenance(*, reconstruction_id: str, source_photo_asset_ids: list[str], prepared_photo_asset_ids: list[str], registered_view_ids: list[str], method: str, version: str, quality: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "schema": "spatial-provenance-v1",
        "reconstruction_id": reconstruction_id,
        "source_photo_asset_ids": list(source_photo_asset_ids),
        "prepared_photo_asset_ids": list(prepared_photo_asset_ids),
        "registered_view_ids": list(registered_view_ids),
        "method": method,
        "version": version,
        "quality": dict(quality or {}),
        "created_at": now_iso(),
    }


def lifecycle_transition(current: str, target: str) -> bool:
    allowed = {
        "created": {"prepared", "failed"},
        "prepared": {"registered", "needs_review", "failed"},
        "registered": {"reconstructed", "needs_review", "failed"},
        "needs_review": {"prepared", "registered", "failed"},
        "reconstructed": {"published", "failed"},
        "published": {"failed"},
        "failed": {"prepared", "registered"},
    }
    return target in allowed.get(current, set())
