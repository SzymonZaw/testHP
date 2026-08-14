from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from datasets.dataset_registry import DatasetRegistry, create_default_registry
from datasets.fusion import fuse
from datasets.normalization import normalize_dataset
from datasets.validation import validate_dataset


@dataclass(frozen=True)
class PipelineStep:
    name: str
    purpose: str
    status: str


def run_pipeline(dataset_names: list[str] | None = None) -> dict[str, Any]:
    """Run stages 1-3 on the data that is actually available.

    Missing datasets are reported rather than becoming fatal dependencies.
    No cross-patient/sample linkage is inferred during fusion.
    """
    registry: DatasetRegistry = create_default_registry()
    available = {dataset.name: dataset for dataset in registry.all()}
    selected = dataset_names or list(available)
    missing = [name for name in selected if name not in available]
    datasets = [available[name] for name in selected if name in available]

    validation = {item.name: validate_dataset(item) for item in datasets}
    normalized = {item.name: normalize_dataset(item) for item in datasets}
    fusion = fuse(normalized.values())

    valid = not missing and all(item.valid for item in normalized.values())
    steps = [
        PipelineStep("ingestion", "Read the files from data/raw through dataset adapters", "ok" if valid else "warning"),
        PipelineStep("validation", "Check existence, non-empty files and supported formats", "ok" if all(v.valid for v in validation.values()) else "warning"),
        PipelineStep("normalization", "Convert heterogeneous sources into the common Observation contract", "ok" if normalized else "warning"),
        PipelineStep("multimodal_fusion", "Aggregate compatible dataset-level observations without inventing subject links", "ok" if fusion.observations else "warning"),
    ]

    return {
        "valid": valid,
        "selected": selected,
        "available": sorted(available),
        "missing": missing,
        "steps": [asdict(step) for step in steps],
        "validation": {
            name: {
                "valid": result.valid,
                "files": result.files,
                "bytes": result.bytes,
                "supported_files": result.supported_files,
                "unsupported_files": result.unsupported_files,
                "warnings": list(result.warnings),
                "errors": list(result.errors),
            }
            for name, result in validation.items()
        },
        "normalized": {name: item.to_dict() for name, item in normalized.items()},
        "fusion": {
            "datasets": list(fusion.datasets),
            "modalities": list(fusion.modalities),
            "linked_subjects": fusion.linked_subjects,
            "warnings": list(fusion.warnings),
            "observations": [asdict(item) for item in fusion.observations],
        },
    }


def build_pipeline(dataset_names: list[str] | None = None) -> dict[str, Any]:
    """Backward-compatible status endpoint plus real execution of stages 1-3."""
    return run_pipeline(dataset_names)
