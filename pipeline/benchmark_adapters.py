"""Adapters for public nuclei benchmarks.

Benchmark data stay outside the repository. This module only reads a
user-configured local benchmark path and normalizes common PanNuke arrays.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

import numpy as np


@dataclass(frozen=True)
class BenchmarkSample:
    sample_id: str
    image_path: Path
    instances: np.ndarray
    labels: np.ndarray | None = None


def load_pannuke_npz(path: str | Path, sample_id: str | None = None) -> BenchmarkSample:
    """Load one PanNuke-style NPZ sample containing img/inst_map/type_map."""
    path = Path(path)
    data = np.load(path, allow_pickle=False)
    if "img" not in data or "inst_map" not in data:
        raise ValueError("PanNuke sample must contain img and inst_map arrays")
    return BenchmarkSample(
        sample_id or path.stem,
        path,
        data["inst_map"],
        data["type_map"] if "type_map" in data else None,
    )


def load_instance_masks(inst_map: np.ndarray) -> list[np.ndarray]:
    """Convert an instance-id map into binary masks."""
    if inst_map.ndim != 2:
        raise ValueError("inst_map must be a 2D array")
    return [(inst_map == i) for i in np.unique(inst_map) if i != 0]


def labels_from_type_map(inst_map: np.ndarray, type_map: np.ndarray) -> dict[int, int]:
    """Assign each instance its majority semantic class."""
    if inst_map.shape != type_map.shape:
        raise ValueError("inst_map and type_map must have the same shape")
    result: dict[int, int] = {}
    for instance_id in np.unique(inst_map):
        if instance_id == 0:
            continue
        values = type_map[inst_map == instance_id]
        values = values[values != 0]
        if values.size:
            result[int(instance_id)] = int(np.bincount(values.astype(int)).argmax())
    return result


def validate_sample(sample: BenchmarkSample) -> Mapping[str, object]:
    """Return deterministic structural QC for a benchmark sample."""
    nonzero = sample.instances[sample.instances != 0]
    return {
        "sample_id": sample.sample_id,
        "image_exists": sample.image_path.exists(),
        "instance_shape": list(sample.instances.shape),
        "instance_count": int(np.unique(nonzero).size),
        "has_labels": sample.labels is not None,
    }
