from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Any

from .data_foundation import Acquisition, DataObject, Hand, Provenance, Quality, SpatialReference, Timepoint, Uncertainty
from .data_ingestion import DataAsset
from .database import connect


def _stable_hand_id(subject_id: str, laterality: str = "unknown") -> str:
    value = uuid.uuid5(uuid.NAMESPACE_URL, f"testhp:hand:{subject_id}:{laterality}")
    return f"hand_{value.hex[:12]}"


def canonicalize_asset(asset: DataAsset) -> DataObject:
    """Map a DataAsset into the canonical data model persisted in PostgreSQL."""
    acquisition_id = f"acq_{uuid.uuid5(uuid.NAMESPACE_URL, f'testhp:acq:{asset.asset_id}').hex[:12]}"
    acquisition = Acquisition(acquisition_id=acquisition_id, subject_id=asset.subject_id, timepoint_id=asset.timepoint, source_type=asset.source, modality=asset.modality, acquired_at=asset.created_at, protocol="upload")
    timepoint = Timepoint(timepoint_id=asset.timepoint, subject_id=asset.subject_id, acquired_at=asset.created_at)
    hand = Hand(hand_id=_stable_hand_id(asset.subject_id), subject_id=asset.subject_id, laterality="unknown")
    obj = DataObject(
        data_id=asset.asset_id,
        data_type="image" if asset.modality in {"hand", "images", "wsi"} else asset.modality,
        subject_id=asset.subject_id,
        timepoint_id=timepoint.timepoint_id,
        acquisition_id=acquisition.acquisition_id,
        source_class="observed",
        modality=asset.modality,
        status=asset.status,
        quality=Quality(status="unknown"),
        uncertainty=Uncertainty(kind="not_assessed"),
        provenance=Provenance(method="upload", method_version="1", processing_timestamp=asset.created_at, validation_status="not_validated", pipeline_id="ingestion", parameters={"filename": asset.filename, "view": asset.view, "subtype": asset.subtype}),
        spatial_reference=SpatialReference(frame_id=f"hand-frame:{asset.subject_id}:{asset.timepoint}", registration_status="unregistered", anatomical_target="hand" if asset.modality == "hand" else None),
        metadata={"path": asset.path, "filename": asset.filename, "size_bytes": asset.size_bytes, "hand_id": hand.hand_id},
    )
    obj.validate()
    return obj


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, default=str)


def register_canonical_asset(asset: DataAsset) -> DataObject:
    """Persist Subject -> Hand -> Timepoint -> Dataset in PostgreSQL."""
    obj = canonicalize_asset(asset)
    acquired_at = datetime.fromisoformat(asset.created_at.replace("Z", "+00:00"))
    hand_id = obj.metadata["hand_id"]
    with connect() as conn:
        conn.execute("INSERT INTO subjects(subject_id) VALUES (%s) ON CONFLICT (subject_id) DO NOTHING", (obj.subject_id,))
        conn.execute("INSERT INTO hands(hand_id, subject_id, laterality) VALUES (%s, %s, 'unknown') ON CONFLICT (hand_id) DO NOTHING", (hand_id, obj.subject_id))
        conn.execute("INSERT INTO timepoints(timepoint_id, subject_id, acquisition_time) VALUES (%s, %s, %s) ON CONFLICT (subject_id, timepoint_id) DO NOTHING", (obj.timepoint_id, obj.subject_id, acquired_at))
        conn.execute(
            """INSERT INTO datasets(dataset_id, subject_id, hand_id, timepoint_id, modality, source, acquisition_time, provenance, quality, metadata)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s::jsonb,%s::jsonb)
               ON CONFLICT (dataset_id) DO UPDATE SET subject_id=EXCLUDED.subject_id, hand_id=EXCLUDED.hand_id,
                 timepoint_id=EXCLUDED.timepoint_id, modality=EXCLUDED.modality, source=EXCLUDED.source,
                 acquisition_time=EXCLUDED.acquisition_time, provenance=EXCLUDED.provenance, quality=EXCLUDED.quality,
                 metadata=EXCLUDED.metadata""",
            (obj.data_id, obj.subject_id, hand_id, obj.timepoint_id, obj.modality, asset.source, acquired_at, _json(obj.provenance.__dict__), _json(obj.quality.__dict__), _json({**obj.metadata, "acquisition_id": obj.acquisition_id, "uncertainty": obj.uncertainty.__dict__, "spatial_reference": obj.spatial_reference.__dict__})),
        )
    return obj


def canonical_registry_status() -> dict[str, Any]:
    """Read the canonical registry from PostgreSQL. Filesystem JSON is not authoritative."""
    try:
        with connect() as conn:
            subjects = conn.execute("SELECT subject_id, created_at, metadata FROM subjects ORDER BY subject_id").fetchall()
            hands = conn.execute("SELECT hand_id, subject_id, laterality, created_at, metadata FROM hands ORDER BY hand_id").fetchall()
            timepoints = conn.execute("SELECT subject_id, timepoint_id, acquisition_time, subject_age_years, created_at, metadata FROM timepoints ORDER BY subject_id, timepoint_id").fetchall()
            datasets = conn.execute("SELECT dataset_id, subject_id, hand_id, timepoint_id, modality, source, acquisition_time, created_at, provenance, quality, confidence, metadata FROM datasets ORDER BY created_at, dataset_id").fetchall()
        return {"schema": "testhp.digital_twin.data_foundation.v1", "storage": "postgresql", "count": len(datasets), "subjects": subjects, "hands": hands, "timepoints": timepoints, "datasets": datasets}
    except Exception as exc:
        return {"schema": "testhp.digital_twin.data_foundation.v1", "storage": "postgresql", "count": 0, "subjects": [], "hands": [], "timepoints": [], "datasets": [], "error": f"{type(exc).__name__}: {exc}"}
