from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from datasets.dataset_registry import create_default_registry
from datasets.fusion import fuse
from datasets.normalization import normalize_dataset
from integration.observation_to_twin import ObservationToTwinPipeline
from organism.digital_twin import DigitalBiologicalTwin


def run_datasets(dataset_names: list[str] | None = None) -> dict[str, Any]:
    """Execute ingestion -> validation -> normalization -> fusion -> twin.

    Fusion remains dataset-level unless explicit subject/sample identifiers are
    available. No biological interpretation is fabricated at ingestion time.
    """
    registry = create_default_registry()
    available = {item.name: item for item in registry.all()}
    selected = dataset_names or sorted(available)
    missing = [name for name in selected if name not in available]
    datasets = [available[name] for name in selected if name in available]

    normalized = {item.name: normalize_dataset(item) for item in datasets}
    invalid = [name for name, item in normalized.items() if not item.valid]
    if missing or invalid:
        return {
            "status": "blocked",
            "selected": selected,
            "missing": missing,
            "invalid": invalid,
            "datasets": [],
            "fusion": None,
            "snapshot": None,
        }

    fusion = fuse(normalized.values())
    twin = DigitalBiologicalTwin(subject_id="web-demo")
    pipeline = ObservationToTwinPipeline(twin, minimum_quality=0.5)
    observations = [observation for item in normalized.values() for observation in item.observations]
    observations.extend(fusion.observations)
    snapshot = pipeline.ingest("web-run-1", observations, datetime.now(timezone.utc))

    return {
        "status": "completed",
        "selected": selected,
        "missing": [],
        "invalid": [],
        "datasets": [
            {
                "name": item.dataset,
                "path": item.source_path,
                "modality": item.modality,
                "files": item.files,
                "bytes": item.bytes,
                "observations": len(item.observations),
                "warnings": list(item.warnings),
                "status": "ok",
            }
            for item in normalized.values()
        ],
        "fusion": {
            "datasets": list(fusion.datasets),
            "modalities": list(fusion.modalities),
            "linked_subjects": fusion.linked_subjects,
            "warnings": list(fusion.warnings),
            "observation_count": len(fusion.observations),
        },
        "snapshot": {
            "timepoint_id": snapshot.timepoint_id,
            "captured_at": snapshot.captured_at.isoformat(),
            "observation_count": len(snapshot.state),
            "provenance": list(snapshot.provenance),
            "state": snapshot.state,
        },
    }
