"""Lightweight baseline cell segmentation.

This module intentionally provides a deterministic NumPy-only baseline. It is
not a clinical segmentation method and is not intended to replace Cellpose,
StarDist, or a validated microscopy pipeline.
"""

from __future__ import annotations

from collections import deque
from typing import Optional

import numpy as np


def _validate_image(image: np.ndarray) -> np.ndarray:
    image = np.asarray(image)
    if image.ndim != 2:
        raise ValueError("Cell image must have shape (H, W).")
    if image.size == 0:
        raise ValueError("Image is empty.")
    if not np.issubdtype(image.dtype, np.number):
        raise TypeError("Cell image must contain numeric values.")
    return image


def _connected_components(binary: np.ndarray) -> np.ndarray:
    """Label 8-connected foreground components using a simple BFS."""
    height, width = binary.shape
    labels = np.zeros((height, width), dtype=np.int32)
    next_label = 0
    neighbors = (
        (-1, -1), (-1, 0), (-1, 1),
        (0, -1),           (0, 1),
        (1, -1),  (1, 0),  (1, 1),
    )

    for y in range(height):
        for x in range(width):
            if not binary[y, x] or labels[y, x] != 0:
                continue

            next_label += 1
            labels[y, x] = next_label
            queue = deque([(y, x)])

            while queue:
                cy, cx = queue.popleft()
                for dy, dx in neighbors:
                    ny, nx = cy + dy, cx + dx
                    if (
                        0 <= ny < height
                        and 0 <= nx < width
                        and binary[ny, nx]
                        and labels[ny, nx] == 0
                    ):
                        labels[ny, nx] = next_label
                        queue.append((ny, nx))

    return labels


def segment_binary_cells(
    image: np.ndarray,
    threshold: Optional[float] = None,
    min_area: int = 10,
) -> np.ndarray:
    """Create an instance mask from a grayscale image by thresholding.

    The output follows the project convention: 0 is background and each
    positive integer identifies one connected cell-like component.
    """
    image = _validate_image(image)
    if min_area < 1:
        raise ValueError("min_area must be at least 1.")

    finite = image[np.isfinite(image)]
    if finite.size == 0:
        raise ValueError("Image contains no finite values.")

    if threshold is None:
        threshold = float(np.mean(finite))

    binary = np.isfinite(image) & (image > threshold)
    labels = _connected_components(binary)

    if min_area <= 1:
        return labels

    counts = np.bincount(labels.ravel())
    keep = counts >= min_area
    keep[0] = False
    return np.where(keep[labels], labels, 0).astype(np.int32)
