"""Utilities for transcriptomic analysis of OSKM/Yamanaka-factor reprogramming.

This module intentionally stays research-level: it prepares expression data,
computes compact QC/state summaries and compares timepoints without claiming
that a cell has been reprogrammed or that a biological state is clinically valid.

Supported inputs:
- AnnData objects/files for single-cell RNA-seq
- 2D NumPy arrays for bulk expression matrices

For single-cell work, Scanpy is the preferred upstream framework.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Iterable, Mapping, Sequence

import numpy as np


YAMANAKA_FACTORS = ("POU5F1", "SOX2", "KLF4", "MYC")
DEFAULT_PLURIPOTENCY_MARKERS = (
    "NANOG", "LIN28A", "DPPA4", "DPPA5", "ESRRB", "ZFP42"
)
DEFAULT_FIBROBLAST_MARKERS = ("COL1A1", "COL1A2", "DCN", "LUM", "VIM")


@dataclass(frozen=True)
class ReprogrammingSummary:
    n_observations: int
    n_features: int
    mean_library_size: float
    median_library_size: float
    mean_detected_features: float
    factor_coverage: dict[str, bool]
    pluripotency_marker_coverage: dict[str, bool]
    fibroblast_marker_coverage: dict[str, bool]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _matrix_and_names(expression: Any) -> tuple[np.ndarray, list[str]]:
    """Extract a dense matrix and feature names from NumPy or AnnData-like input."""
    if hasattr(expression, "X") and hasattr(expression, "var_names"):
        matrix = expression.X
        names = [str(x) for x in expression.var_names]
        if hasattr(matrix, "toarray"):
            matrix = matrix.toarray()
        return np.asarray(matrix, dtype=np.float32), names

    matrix = np.asarray(expression, dtype=np.float32)
    if matrix.ndim != 2:
        raise ValueError("Expression matrix must be 2-dimensional.")
    return matrix, [str(i) for i in range(matrix.shape[1])]


def validate_expression(expression: Any) -> tuple[np.ndarray, list[str]]:
    """Validate expression values and return rows=observations, columns=features."""
    matrix, names = _matrix_and_names(expression)
    if matrix.size == 0:
        raise ValueError("Expression matrix is empty.")
    if not np.all(np.isfinite(matrix)):
        raise ValueError("Expression matrix contains non-finite values.")
    if np.any(matrix < 0):
        raise ValueError("Expression matrix contains negative expression values.")
    return matrix, names


def _coverage(feature_names: Sequence[str], markers: Iterable[str]) -> dict[str, bool]:
    available = {str(name).upper() for name in feature_names}
    return {marker: marker.upper() in available for marker in markers}


def summarize_reprogramming(
    expression: Any,
    *,
    pluripotency_markers: Iterable[str] = DEFAULT_PLURIPOTENCY_MARKERS,
    fibroblast_markers: Iterable[str] = DEFAULT_FIBROBLAST_MARKERS,
) -> ReprogrammingSummary:
    """Return dataset-level QC and marker availability, without biological inference."""
    matrix, names = validate_expression(expression)
    library = matrix.sum(axis=1)
    detected = (matrix > 0).sum(axis=1)
    return ReprogrammingSummary(
        n_observations=int(matrix.shape[0]),
        n_features=int(matrix.shape[1]),
        mean_library_size=float(library.mean()),
        median_library_size=float(np.median(library)),
        mean_detected_features=float(detected.mean()),
        factor_coverage=_coverage(names, YAMANAKA_FACTORS),
        pluripotency_marker_coverage=_coverage(names, pluripotency_markers),
        fibroblast_marker_coverage=_coverage(names, fibroblast_markers),
    )


def marker_score(
    expression: Any,
    markers: Iterable[str],
) -> np.ndarray:
    """Compute a simple per-observation mean expression over available markers.

    This is a feature-engineering primitive, not a validated pluripotency score.
    Missing markers are ignored; an error is raised if none of the requested
    markers is present.
    """
    matrix, names = validate_expression(expression)
    index = {name.upper(): i for i, name in enumerate(names)}
    selected = [index[m.upper()] for m in markers if m.upper() in index]
    if not selected:
        raise ValueError("None of the requested markers are present in the expression data.")
    return matrix[:, selected].mean(axis=1)


def timepoint_effect(
    expression: Any,
    group_a: Sequence[int],
    group_b: Sequence[int],
) -> dict[str, np.ndarray]:
    """Compare two groups using per-feature mean difference and standardized effect."""
    matrix, names = validate_expression(expression)
    a = matrix[np.asarray(group_a, dtype=int)]
    b = matrix[np.asarray(group_b, dtype=int)]
    if len(a) == 0 or len(b) == 0:
        raise ValueError("Both groups must contain observations.")
    mean_a = a.mean(axis=0)
    mean_b = b.mean(axis=0)
    pooled = np.sqrt((a.var(axis=0) + b.var(axis=0)) / 2.0)
    effect = (mean_a - mean_b) / (pooled + 1e-8)
    return {
        "feature_names": np.asarray(names, dtype=object),
        "mean_group_a": mean_a,
        "mean_group_b": mean_b,
        "mean_difference": mean_a - mean_b,
        "standardized_effect": effect,
    }
