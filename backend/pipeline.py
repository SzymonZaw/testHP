from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from datasets.dataset_registry import DatasetRegistry, create_default_registry


@dataclass(frozen=True)
class PipelineStep:
    name: str
    purpose: str
    status: str


def build_pipeline(dataset_names: list[str] | None = None) -> dict[str, Any]:
    registry: DatasetRegistry = create_default_registry()
    available = {dataset.name: dataset for dataset in registry.all()}
    selected = dataset_names or list(available)

    missing = [name for name in selected if name not in available]
    invalid = [name for name in selected if name in available and not available[name].has_data()]

    steps: list[PipelineStep] = [
        PipelineStep("ingestion", "Read datasets from data/raw", "ok" if not missing and not invalid else "blocked"),
        PipelineStep("normalization", "Convert source-specific records into project observations", "planned"),
        PipelineStep("multimodal_fusion", "Combine compatible observations across modalities", "planned"),
        PipelineStep("analysis", "Run the selected biological/pathology analyses", "planned"),
        PipelineStep("evaluation", "Produce quality, uncertainty and evaluation outputs", "planned"),
    ]

    return {
        "valid": not missing and not invalid,
        "selected": selected,
        "available": sorted(available),
        "missing": missing,
        "invalid": invalid,
        "steps": [step.__dict__ for step in steps],
    }
