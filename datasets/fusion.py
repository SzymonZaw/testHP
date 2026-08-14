"""Multimodal fusion of normalized observations.

Fusion combines the actual observations produced by dataset adapters. It keeps
provenance at modality/dataset level and never invents subject-level links.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from statistics import mean
from typing import Iterable

from datasets.normalization import NormalizedDataset
from integration.observation_to_twin import Observation


@dataclass(frozen=True)
class FusionResult:
    observations: tuple[Observation, ...]
    modalities: tuple[str, ...]
    datasets: tuple[str, ...]
    linked_subjects: int
    warnings: tuple[str, ...] = ()


def fuse(normalized: Iterable[NormalizedDataset]) -> FusionResult:
    sources = [item for item in normalized if item.valid]
    if not sources:
        return FusionResult((), (), (), 0, ("no valid normalized datasets",))

    by_modality: dict[str, list[NormalizedDataset]] = defaultdict(list)
    for item in sources:
        by_modality[item.modality].append(item)

    # Preserve the real normalized measurements. Dataset-qualified feature names
    # prevent unrelated datasets from silently overwriting one another.
    fused: list[Observation] = []
    for item in sources:
        fused.extend(item.observations)

    for modality, items in sorted(by_modality.items()):
        counts = [float(item.files) for item in items]
        sizes = [float(item.bytes) for item in items]
        fused.extend([
            Observation(f"fusion.{modality}.dataset_count", float(len(items)), 1.0, modality),
            Observation(f"fusion.{modality}.file_count_total", sum(counts), 1.0, modality),
            Observation(f"fusion.{modality}.byte_count_total", sum(sizes), 1.0, modality),
            Observation(f"fusion.{modality}.mean_files_per_dataset", mean(counts), 1.0, modality),
        ])

    modalities = tuple(sorted(by_modality))
    datasets = tuple(item.dataset for item in sources)
    warnings = (
        "Fusion is dataset-level: no patient/sample linkage is inferred without an explicit shared identifier.",
    )
    return FusionResult(tuple(fused), modalities, datasets, 0, warnings)
