from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from datasets.dataset_registry import DatasetInfo, create_default_registry
from integration.observation_to_twin import Observation, ObservationToTwinPipeline
from organism.digital_twin import DigitalBiologicalTwin


def _scan(path: Path) -> tuple[int, int]:
    files = 0
    total_bytes = 0
    if path.is_file():
        return 1, path.stat().st_size
    if not path.exists():
        return 0, 0
    for item in path.rglob("*"):
        if item.is_file():
            files += 1
            total_bytes += item.stat().st_size
    return files, total_bytes


def _dataset_observations(dataset: DatasetInfo) -> list[Observation]:
    """Create observations from facts about the ingested source, never fake biology.

    The current repository does not yet expose source-specific model loaders for every
    modality. These measurements therefore represent ingestion/quality facts only.
    They are useful for testing the real observation -> twin path without pretending
    that a file count is a biological measurement.
    """
    files, total_bytes = _scan(dataset.path)
    return [
        Observation(
            feature=f"dataset.{dataset.name}.file_count",
            value=float(files),
            quality_score=1.0 if files else 0.0,
            modality=dataset.modality,
        ),
        Observation(
            feature=f"dataset.{dataset.name}.bytes",
            value=float(total_bytes),
            quality_score=1.0 if total_bytes else 0.0,
            modality=dataset.modality,
        ),
    ]


def run_datasets(dataset_names: list[str] | None = None) -> dict[str, Any]:
    registry = create_default_registry()
    available = {item.name: item for item in registry.all()}
    selected = dataset_names or sorted(available)
    missing = [name for name in selected if name not in available]
    if missing:
        return {
            "status": "blocked",
            "selected": selected,
            "missing": missing,
            "datasets": [],
            "snapshot": None,
        }

    twin = DigitalBiologicalTwin(subject_id="web-demo")
    pipeline = ObservationToTwinPipeline(twin, minimum_quality=0.5)
    all_observations: list[Observation] = []
    dataset_results: list[dict[str, Any]] = []

    for name in selected:
        dataset = available[name]
        observations = _dataset_observations(dataset)
        accepted = [item for item in observations if item.quality_score >= 0.5]
        files, total_bytes = _scan(dataset.path)
        all_observations.extend(observations)
        dataset_results.append({
            "name": name,
            "path": str(dataset.path),
            "modality": dataset.modality,
            "files": files,
            "bytes": total_bytes,
            "observations": len(accepted),
            "status": "ok" if accepted else "empty",
        })

    captured_at = datetime.now(timezone.utc)
    snapshot = pipeline.ingest("web-run-1", all_observations, captured_at)
    return {
        "status": "completed",
        "selected": selected,
        "missing": [],
        "datasets": dataset_results,
        "snapshot": {
            "timepoint_id": snapshot.timepoint_id,
            "captured_at": snapshot.captured_at.isoformat(),
            "observation_count": len(snapshot.state),
            "provenance": list(snapshot.provenance),
            "state": snapshot.state,
        },
        "note": "This is an ingestion smoke run. Biological interpretation is not performed by this endpoint.",
    }
