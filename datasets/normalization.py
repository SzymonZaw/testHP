"""Common normalization layer between dataset adapters and analysis code."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from datasets.adapters import AdapterResult, adapter_for
from datasets.dataset_registry import DatasetInfo
from datasets.validation import ValidationResult, validate_dataset
from integration.observation_to_twin import Observation


@dataclass(frozen=True)
class NormalizedDataset:
    dataset: str
    modality: str
    source_path: str
    observations: tuple[Observation, ...]
    files: int
    bytes: int
    valid: bool
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset": self.dataset,
            "modality": self.modality,
            "source_path": self.source_path,
            "files": self.files,
            "bytes": self.bytes,
            "valid": self.valid,
            "warnings": list(self.warnings),
            "errors": list(self.errors),
            "observations": [asdict(item) for item in self.observations],
        }


def normalize_dataset(dataset: DatasetInfo) -> NormalizedDataset:
    validation: ValidationResult = validate_dataset(dataset)
    if not validation.valid:
        return NormalizedDataset(
            dataset.name,
            dataset.modality,
            str(dataset.path),
            (),
            validation.files,
            validation.bytes,
            False,
            validation.warnings,
            validation.errors,
        )

    adapter = adapter_for(dataset.name, Path(dataset.path), dataset.modality)
    result: AdapterResult = adapter.load()
    observations = list(result.observations)
    # Every normalized dataset exposes the same structural contract.
    observations.extend([
        Observation(f"dataset.{dataset.name}.file_count", float(result.files), 1.0, dataset.modality),
        Observation(f"dataset.{dataset.name}.byte_count", float(result.bytes), 1.0, dataset.modality),
    ])
    return NormalizedDataset(
        dataset.name,
        dataset.modality,
        str(dataset.path),
        tuple(observations),
        result.files,
        result.bytes,
        True,
        tuple(dict.fromkeys((*validation.warnings, *result.warnings))),
        (),
    )


def normalize_registry(datasets: list[DatasetInfo]) -> dict[str, NormalizedDataset]:
    return {dataset.name: normalize_dataset(dataset) for dataset in datasets}
