from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

from .data_foundation import Acquisition, DataObject, Hand, Provenance, Quality, SpatialReference, Timepoint, Uncertainty
from .data_ingestion import DataAsset

ROOT = Path(__file__).resolve().parents[1]
FOUNDATION_ROOT = ROOT / "data" / "registry"
FOUNDATION_PATH = FOUNDATION_ROOT / "data_objects.json"


def _stable_hand_id(subject_id: str, laterality: str = "unknown") -> str:
    value = uuid.uuid5(uuid.NAMESPACE_URL, f"testhp:hand:{subject_id}:{laterality}")
    return f"hand_{value.hex[:12]}"


def _load_foundation_registry() -> list[dict[str, Any]]:
    if not FOUNDATION_PATH.exists():
        return []
    try:
        value = json.loads(FOUNDATION_PATH.read_text(encoding="utf-8"))
        return value if isinstance(value, list) else []
    except (OSError, json.JSONDecodeError):
        return []


def _save_foundation_registry(items: list[dict[str, Any]]) -> None:
    FOUNDATION_ROOT.mkdir(parents=True, exist_ok=True)
    temporary = FOUNDATION_PATH.with_suffix(".tmp")
    temporary.write_text(json.dumps(items, indent=2, ensure_ascii=False), encoding="utf-8")
    temporary.replace(FOUNDATION_PATH)


def canonicalize_asset(asset: DataAsset) -> DataObject:
    """Map a legacy DataAsset into the Phase-A canonical data model."""
    acquisition_id = f"acq_{uuid.uuid5(uuid.NAMESPACE_URL, f'testhp:acq:{asset.asset_id}').hex[:12]}"
    acquisition = Acquisition(
        acquisition_id=acquisition_id,
        subject_id=asset.subject_id,
        timepoint_id=asset.timepoint,
        source_type=asset.source,
        modality=asset.modality,
        acquired_at=asset.created_at,
        protocol="upload",
    )
    timepoint = Timepoint(timepoint_id=asset.timepoint, subject_id=asset.subject_id, acquired_at=asset.created_at)
    hand = Hand(hand_id=_stable_hand_id(asset.subject_id), subject_id=asset.subject_id, laterality="unknown")
    data_type = "image" if asset.modality in {"hand", "images", "wsi"} else asset.modality
    obj = DataObject(
        data_id=asset.asset_id,
        data_type=data_type,
        subject_id=asset.subject_id,
        timepoint_id=timepoint.timepoint_id,
        acquisition_id=acquisition.acquisition_id,
        source_class="observed",
        modality=asset.modality,
        status=asset.status,
        quality=Quality(status="unknown"),
        uncertainty=Uncertainty(kind="not_assessed"),
        provenance=Provenance(
            method="upload",
            method_version="1",
            processing_timestamp=asset.created_at,
            validation_status="not_validated",
            pipeline_id="ingestion",
            parameters={"filename": asset.filename, "view": asset.view, "subtype": asset.subtype},
        ),
        spatial_reference=SpatialReference(
            frame_id=f"hand-frame:{asset.subject_id}:{asset.timepoint}",
            registration_status="unregistered",
            anatomical_target="hand" if asset.modality == "hand" else None,
        ),
        metadata={
            "path": asset.path,
            "filename": asset.filename,
            "size_bytes": asset.size_bytes,
            "hand_id": hand.hand_id,
            "acquisition": acquisition.__dict__,
            "timepoint": timepoint.__dict__,
        },
    )
    obj.validate()
    return obj


def register_canonical_asset(asset: DataAsset) -> DataObject:
    obj = canonicalize_asset(asset)
    registry = _load_foundation_registry()
    by_id = {item.get("data_id"): item for item in registry}
    by_id[obj.data_id] = obj.to_dict()
    _save_foundation_registry(list(by_id.values()))
    return obj


def canonical_registry_status() -> dict[str, Any]:
    items = _load_foundation_registry()
    return {"schema": "testhp.digital_twin.data_foundation.v1", "count": len(items), "data_objects": items}
