from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def make_provenance(*, asset_id: str | None, source: str, method: str, confidence: float | None = None, parameters: dict[str, Any] | None = None) -> dict[str, Any]:
    record: dict[str, Any] = {
        "asset_id": asset_id,
        "source": source,
        "method": method,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "parameters": parameters or {},
    }
    if confidence is not None:
        record["confidence"] = max(0.0, min(1.0, float(confidence)))
    return record


def attach_provenance(observation: dict[str, Any], provenance: dict[str, Any]) -> dict[str, Any]:
    result = dict(observation)
    result["provenance"] = provenance
    return result
