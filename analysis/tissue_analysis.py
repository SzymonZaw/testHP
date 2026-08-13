"""
Tissue Analysis
===============

Analysis of tissue-level features produced by image/WSI pipelines.

This module is intentionally model-agnostic. It analyzes:
- segmentation masks,
- tissue regions,
- embeddings,
- intensity statistics,
- spatial organization.

The output can later be consumed by:
- aging_model.py
- abnormality_model.py
- pathology_model.py
- fusion_model.py
- risk_model.py
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np


@dataclass
class TissueAnalysisResult:
    """Container for tissue-level analytical features."""

    tissue_area: float
    occupied_area: float
    occupancy_ratio: float

    mean_intensity: float
    std_intensity: float
    min_intensity: float
    max_intensity: float

    region_count: int
    mean_region_area: float
    largest_region_area: float

    heterogeneity_score: float
    spatial_complexity_score: float

    embedding_mean: Optional[List[float]] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class TissueAnalyzer:
    """
    Analyze tissue images and segmentation masks.

    Parameters
    ----------
    pixel_size_um:
        Physical size of one pixel in micrometers.
        If unknown, leave as None.
    """

    def __init__(self, pixel_size_um: Optional[float] = None):
        if pixel_size_um is not None and pixel_size_um <= 0:
            raise ValueError("pixel_size_um must be positive.")

        self.pixel_size_um = pixel_size_um

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_image(image: np.ndarray) -> np.ndarray:
        image = np.asarray(image)

        if image.size == 0:
            raise ValueError("Image is empty.")

        if image.ndim not in (2, 3):
            raise ValueError(
                "Image must have shape (H, W) or (H, W, C)."
            )

        return image.astype(np.float32)

    @staticmethod
    def _validate_mask(mask: np.ndarray) -> np.ndarray:
        mask = np.asarray(mask)

        if mask.size == 0:
            raise ValueError("Mask is empty.")

        if mask.ndim != 2:
            raise ValueError("Mask must have shape (H, W).")

        return mask

    # ------------------------------------------------------------------
    # Basic image statistics
    # ------------------------------------------------------------------

    @staticmethod
    def _grayscale(image: np.ndarray) -> np.ndarray:
        if image.ndim == 2:
            return image

        if image.shape[-1] == 1:
            return image[..., 0]

        # Standard luminance approximation.
        if image.shape[-1] >= 3:
            return (
                0.299 * image[..., 0]
                + 0.587 * image[..., 1]
                + 0.114 * image[..., 2]
            )

        return image.mean(axis=-1)

    def intensity_statistics(
        self,
        image: np.ndarray,
        mask: Optional[np.ndarray] = None,
    ) -> Dict[str, float]:
        image = self._validate_image(image)
        gray = self._grayscale(image)

        if mask is not None:
            mask = self._validate_mask(mask)

            if mask.shape != gray.shape:
                raise ValueError(
                    "Mask and image dimensions do not match."
                )

            values = gray[mask > 0]
        else:
            values = gray.ravel()

        if values.size == 0:
            return {
                "mean_intensity": 0.0,
                "std_intensity": 0.0,
                "min_intensity": 0.0,
                "max_intensity": 0.0,
            }

        return {
            "mean_intensity": float(np.mean(values)),
            "std_intensity": float(np.std(values)),
            "min_intensity": float(np.min(values)),
            "max_intensity": float(np.max(values)),
        }

    # ------------------------------------------------------------------
    # Region analysis
    # ------------------------------------------------------------------

    @staticmethod
    def _connected_components(mask: np.ndarray) -> List[int]:
        """
        Simple connected-component implementation using 4-connectivity.

        This avoids requiring scipy/skimage for the basic analysis layer.
        """

        binary = mask > 0
        height, width = binary.shape

        visited = np.zeros_like(binary, dtype=bool)
        areas: List[int] = []

        for y in range(height):
            for x in range(width):
                if not binary[y, x] or visited[y, x]:
                    continue

                stack = [(y, x)]
                visited[y, x] = True
                area = 0

                while stack:
                    cy, cx = stack.pop()
                    area += 1

                    neighbors = (
                        (cy - 1, cx),
                        (cy + 1, cx),
                        (cy, cx - 1),
                        (cy, cx + 1),
                    )

                    for ny, nx in neighbors:
                        if (
                            0 <= ny < height
                            and 0 <= nx < width
                            and binary[ny, nx]
                            and not visited[ny, nx]
                        ):
                            visited[ny, nx] = True
                            stack.append((ny, nx))

                areas.append(area)

        return areas

    def region_statistics(
        self,
        mask: np.ndarray,
    ) -> Dict[str, float]:
        mask = self._validate_mask(mask)

        tissue_area = float(mask.size)
        occupied_area = float(np.count_nonzero(mask))

        occupancy_ratio = (
            occupied_area / tissue_area
            if tissue_area > 0
            else 0.0
        )

        regions = self._connected_components(mask)

        if regions:
            mean_region_area = float(np.mean(regions))
            largest_region_area = float(np.max(regions))
        else:
            mean_region_area = 0.0
            largest_region_area = 0.0

        return {
            "tissue_area": tissue_area,
            "occupied_area": occupied_area,
            "occupancy_ratio": occupancy_ratio,
            "region_count": len(regions),
            "mean_region_area": mean_region_area,
            "largest_region_area": largest_region_area,
        }

    # ------------------------------------------------------------------
    # Heterogeneity
    # ------------------------------------------------------------------

    @staticmethod
    def heterogeneity_score(
        image: np.ndarray,
        mask: Optional[np.ndarray] = None,
        grid_size: int = 4,
    ) -> float:
        """
        Estimate spatial heterogeneity from intensity variation
        between image regions.

        Higher values indicate greater spatial variation.
        """

        if grid_size < 1:
            raise ValueError("grid_size must be >= 1.")

        image = np.asarray(image, dtype=np.float32)

        if image.ndim == 3:
            image = image.mean(axis=-1)

        if mask is not None:
            mask = np.asarray(mask)

            if mask.shape != image.shape:
                raise ValueError(
                    "Mask and image dimensions do not match."
                )

        h, w = image.shape

        region_means: List[float] = []

        for gy in range(grid_size):
            y0 = gy * h // grid_size
            y1 = (gy + 1) * h // grid_size

            for gx in range(grid_size):
                x0 = gx * w // grid_size
                x1 = (gx + 1) * w // grid_size

                patch = image[y0:y1, x0:x1]

                if mask is not None:
                    patch_mask = mask[y0:y1, x0:x1] > 0
                    values = patch[patch_mask]
                else:
                    values = patch.ravel()

                if values.size:
                    region_means.append(float(np.mean(values)))

        if len(region_means) < 2:
            return 0.0

        mean_value = np.mean(region_means)
        denominator = abs(mean_value) + 1e-8

        score = np.std(region_means) / denominator

        return float(score)

    # ------------------------------------------------------------------
    # Spatial complexity
    # ------------------------------------------------------------------

    @staticmethod
    def spatial_complexity(mask: np.ndarray) -> float:
        """
        Estimate boundary complexity using transitions between
        neighboring mask pixels.
        """

        mask = np.asarray(mask) > 0

        if mask.ndim != 2:
            raise ValueError("Mask must be 2-dimensional.")

        horizontal = np.sum(mask[:, 1:] != mask[:, :-1])
        vertical = np.sum(mask[1:, :] != mask[:-1, :])

        transitions = horizontal + vertical

        area = np.count_nonzero(mask)

        if area == 0:
            return 0.0

        return float(transitions / area)

    # ------------------------------------------------------------------
    # Embeddings
    # ------------------------------------------------------------------

    @staticmethod
    def summarize_embedding(
        embedding: Optional[np.ndarray],
    ) -> Optional[List[float]]:
        if embedding is None:
            return None

        embedding = np.asarray(embedding, dtype=np.float32)

        if embedding.ndim == 1:
            return embedding.tolist()

        if embedding.ndim == 2:
            return embedding.mean(axis=0).tolist()

        raise ValueError(
            "Embedding must have shape (D,) or (N, D)."
        )

    # ------------------------------------------------------------------
    # Complete analysis
    # ------------------------------------------------------------------

    def analyze(
        self,
        image: np.ndarray,
        mask: Optional[np.ndarray] = None,
        embedding: Optional[np.ndarray] = None,
    ) -> TissueAnalysisResult:

        image = self._validate_image(image)

        if mask is None:
            mask = np.ones(
                image.shape[:2],
                dtype=np.uint8,
            )

        mask = self._validate_mask(mask)

        intensity = self.intensity_statistics(
            image,
            mask,
        )

        regions = self.region_statistics(mask)

        heterogeneity = self.heterogeneity_score(
            image,
            mask,
        )

        complexity = self.spatial_complexity(mask)

        embedding_summary = self.summarize_embedding(
            embedding
        )

        return TissueAnalysisResult(
            tissue_area=regions["tissue_area"],
            occupied_area=regions["occupied_area"],
            occupancy_ratio=regions["occupancy_ratio"],
            mean_intensity=intensity["mean_intensity"],
            std_intensity=intensity["std_intensity"],
            min_intensity=intensity["min_intensity"],
            max_intensity=intensity["max_intensity"],
            region_count=int(regions["region_count"]),
            mean_region_area=regions["mean_region_area"],
            largest_region_area=regions["largest_region_area"],
            heterogeneity_score=heterogeneity,
            spatial_complexity_score=complexity,
            embedding_mean=embedding_summary,
        )


def analyze_tissue(
    image: np.ndarray,
    mask: Optional[np.ndarray] = None,
    embedding: Optional[np.ndarray] = None,
) -> Dict[str, Any]:
    """Convenience function."""

    analyzer = TissueAnalyzer()

    return analyzer.analyze(
        image=image,
        mask=mask,
        embedding=embedding,
    ).to_dict()


if __name__ == "__main__":
    print("Tissue Analysis")

    rng = np.random.default_rng(42)

    image = rng.random((256, 256))
    mask = np.zeros((256, 256), dtype=np.uint8)

    mask[40:180, 40:180] = 1
    mask[200:230, 200:240] = 1

    embedding = rng.normal(size=(4, 768))

    analyzer = TissueAnalyzer()

    result = analyzer.analyze(
        image=image,
        mask=mask,
        embedding=embedding,
    )

    for key, value in result.to_dict().items():
        if isinstance(value, list):
            print(
                f"{key}: "
                f"[{value[0]:.4f}, ...]"
                if value
                else f"{key}: []"
            )
        elif isinstance(value, float):
            print(f"{key}: {value:.4f}")
        else:
            print(f"{key}: {value}")

    print("\nModel-independent tissue analysis ready.")