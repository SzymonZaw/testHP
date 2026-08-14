from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def build_audit_record(*, run_id: str, result: dict[str, Any]) -> dict[str, Any]:
    """Stage 10: reproducible, provenance-first audit record."""
    return {
        "run_id": run_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": result.get("status"),
        "selected_datasets": result.get("selected", []),
        "stages": result.get("stages", []),
        "fusion": result.get("fusion"),
        "snapshot": {
            "timepoint_id": (result.get("snapshot") or {}).get("timepoint_id"),
            "observation_count": (result.get("snapshot") or {}).get("observation_count", 0),
        },
        "limitations": [
            "Audit metadata records pipeline execution and provenance; it is not a medical record.",
        ],
    }
