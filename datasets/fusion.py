"""Conservative multimodal fusion for normalized dataset observations.

Fusion here is dataset-level unless an explicit subject/sample identifier is
present. It deliberately does not manufacture patient-level links between
independent public datasets.
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

    fused: list[Observation] = []
    for modality, items in sorted(by_modality.items()):
        counts = [float(item.files) for item in items]
        sizes = [float(item.bytes) for item in items]
        fused.append(Observation(f"fusion.{modality}.dataset_count", float(len(items)), 1.0, modality))
        fused.append(Observation(f"fusion.{modality}.file_count_total", sum(counts), 1.0, modality))
        fused.append(Observation(f"fusion.{modality}.byte_count_total", sum(sizes), 1.0, modality))
        fused.append(Observation(f"fusion.{modality}.mean_files_per_dataset", mean(counts), 1.0, modality))

    modalities = tuple(sorted(by_modality))
    datasets = tuple(item.dataset for item in sources)
    warnings = (
        "Fusion is dataset-level: no patient/sample linkage is inferred without an explicit shared identifier.",
    )
    return FusionResult(tuple(fused), modalities, datasets, 0, warnings)
