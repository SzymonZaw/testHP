from __future__ import annotations

from typing import Any

MODALITIES = ("hand", "video", "images", "wsi", "rna", "metadata")


def availability_record(modality: str, status: str = "unavailable", *, reason: str | None = None, asset_id: str | None = None) -> dict[str, Any]:
    if modality not in MODALITIES:
        raise ValueError(f"unsupported modality: {modality}")
    return {
        "modality": modality,
        "status": status if status in {"available", "partial", "unavailable"} else "unavailable",
        "reason": reason,
        "asset_id": asset_id,
    }


def build_availability(records: list[dict[str, Any]]) -> dict[str, Any]:
    by_modality = {m: availability_record(m) for m in MODALITIES}
    for record in records:
        modality = record.get("modality")
        if modality in by_modality:
            current = by_modality[modality]
            current.update({k: v for k, v in record.items() if k in {"status", "reason", "asset_id"}})
            if current["status"] == "unavailable" and record.get("status") == "available":
                current["status"] = "available"
    return {"modalities": list(by_modality.values())}
