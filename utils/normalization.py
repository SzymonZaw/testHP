# utils/normalization.py

from __future__ import annotations

import numpy as np


def min_max_normalize(
    values,
    min_value: float | None = None,
    max_value: float | None = None,
) -> np.ndarray:
    """
    Min-max normalization to [0, 1].
    """

    values = np.asarray(
        values,
        dtype=np.float32,
    )

    if min_value is None:
        min_value = float(
            np.min(values)
        )

    if max_value is None:
        max_value = float(
            np.max(values)
        )

    if max_value == min_value:
        return np.zeros_like(values)

    return (
        (values - min_value)
        / (max_value - min_value)
    )


def standardize(
    values,
    mean: float | None = None,
    std: float | None = None,
) -> np.ndarray:
    """
    Z-score standardization.
    """

    values = np.asarray(
        values,
        dtype=np.float32,
    )

    if mean is None:
        mean = float(
            np.mean(values)
        )

    if std is None:
        std = float(
            np.std(values)
        )

    if std == 0:
        return np.zeros_like(values)

    return (
        values - mean
    ) / std


def robust_normalize(
    values,
) -> np.ndarray:
    """
    Robust normalization using median and IQR.
    """

    values = np.asarray(
        values,
        dtype=np.float32,
    )

    median = np.median(values)

    q1 = np.percentile(
        values,
        25,
    )

    q3 = np.percentile(
        values,
        75,
    )

    iqr = q3 - q1

    if iqr == 0:
        return np.zeros_like(values)

    return (
        values - median
    ) / iqr


def percentile_normalize(
    values,
) -> np.ndarray:
    """
    Convert values into percentile ranks [0, 1].
    """

    values = np.asarray(
        values,
        dtype=np.float32,
    )

    flat = values.reshape(-1)

    order = np.argsort(
        np.argsort(flat)
    )

    if len(flat) <= 1:
        return np.zeros_like(
            values,
            dtype=np.float32,
        )

    ranks = (
        order
        / (len(flat) - 1)
    )

    return ranks.reshape(
        values.shape
    ).astype(np.float32)


def clip_outliers(
    values,
    lower_percentile: float = 1.0,
    upper_percentile: float = 99.0,
) -> np.ndarray:
    """
    Clip values to percentile boundaries.
    """

    values = np.asarray(
        values,
        dtype=np.float32,
    )

    lower = np.percentile(
        values,
        lower_percentile,
    )

    upper = np.percentile(
        values,
        upper_percentile,
    )

    return np.clip(
        values,
        lower,
        upper,
    )


def normalize_batch(
    batch: np.ndarray,
    method: str = "zscore",
) -> np.ndarray:
    """
    Normalize each sample independently.

    Supported methods:
        - minmax
        - zscore
        - robust
    """

    batch = np.asarray(
        batch,
        dtype=np.float32,
    )

    if batch.ndim < 2:
        raise ValueError(
            "Batch must have at least 2 dimensions."
        )

    normalized = np.zeros_like(
        batch,
        dtype=np.float32,
    )

    for i in range(batch.shape[0]):

        sample = batch[i]

        if method == "minmax":
            normalized[i] = min_max_normalize(
                sample
            )

        elif method == "zscore":
            normalized[i] = standardize(
                sample
            )

        elif method == "robust":
            normalized[i] = robust_normalize(
                sample
            )

        else:
            raise ValueError(
                f"Unknown normalization method: {method}"
            )

    return normalized