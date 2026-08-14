from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from datasets.dataset_registry import create_default_registry
from datasets.adapters import adapter_for
from integration.observation_to_twin import ObservationToTwinPipeline
from organism.digital_twin import DigitalBiologicalTwin


def run_datasets(dataset_names: list[str] | None = None) -> dict[str, Any]:
    """Run the real ingestion path using adapters for the selected raw datasets.

    The adapter layer is deliberately conservative: it exposes observations that
    can be verified directly from files (counts, bytes and available annotations).
    No biological interpretation is fabricated at ingestion time.
    """
    registry = create_default_registry()
    available = {item.name: item for item in registry.all()}
    selected = dataset_names or sorted(available)
    missing = [name for name in selected if name not in available]
    invalid = [name for name in selected if name in available and not available[name].has_data()]
    if missing or invalid:
        return {
            "status": "blocked",
            "selected": selected,
            "missing": missing,
            "invalid": invalid,
            "datasets": [],
            "snapshot": None,
        }

    twin = DigitalBiologicalTwin(subject_id="web-demo")
    pipeline = ObservationToTwinPipeline(twin, minimum_quality=0.5)
    all_observations = []
    dataset_results = []

    for name in selected:
        dataset = available[name]
        result = adapter_for(name, dataset.path, dataset.modality).load()
        all_observations.extend(result.observations)
        dataset_results.append({
            "name": result.dataset,
            "path": str(dataset.path),
            "modality": result.modality,
            "files": result.files,
            "bytes": result.bytes,
            "observations": len(result.observations),
            "warnings": list(result.warnings),
            "status": "ok" if result.observations else "empty",
        })

    captured_at = datetime.now(timezone.utc)
    snapshot = pipeline.ingest("web-run-1", all_observations, captured_at)
    return {
        "status": "completed",
        "selected": selected,
        "missing": [],
        "invalid": [],
        "datasets": dataset_results,
        "snapshot": {
            "timepoint_id": snapshot.timepoint_id,
            "captured_at": snapshot.captured_at.isoformat(),
            "observation_count": len(snapshot.state),
            "provenance": list(snapshot.provenance),
            "state": snapshot.state,
        },
        "note": "Ingestion and normalization are active. Biological model inference remains a downstream stage.",
    }
