"""
Cell Analysis
=============

Analysis of individual cells detected/segmented by Cellpose
or another cell-segmentation pipeline.

Expected mask format:
- 0 = background
- 1..N = individual cell IDs

This module extracts:
- cell count
- area
- centroid
- density
- nearest-neighbour statistics
- size statistics
- spatial distribution
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Tuple

import numpy as np


@dataclass
class CellFeature:
    cell_id: int
    area: float
    centroid_x: float
    centroid_y: float
    bbox_width: int
    bbox_height: int
    compactness: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CellAnalysisResult:
    cell_count: int
    cell_density: float

    mean_area: float
    median_area: float
    std_area: float
    min_area: float
    max_area: float

    mean_compactness: float

    mean_nearest_neighbor_distance: float
    cell_distribution_score: float

    cells: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class CellAnalyzer:
    """Analyze instance-level cell segmentation masks."""

    def __init__(
        self,
        pixel_size_um: Optional[float] = None,
    ):
        if pixel_size_um is not None and pixel_size_um <= 0:
            raise ValueError(
                "pixel_size_um must be positive."
            )

        self.pixel_size_um = pixel_size_um

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def validate_mask(mask: np.ndarray) -> np.ndarray:
        mask = np.asarray(mask)

        if mask.ndim != 2:
            raise ValueError(
                "Cell instance mask must have shape (H, W)."
            )

        if mask.size == 0:
            raise ValueError("Mask is empty.")

        return mask

    @staticmethod
    def _cell_ids(mask: np.ndarray) -> np.ndarray:
        return np.unique(mask[mask > 0])

    @staticmethod
    def _cell_pixels(
        mask: np.ndarray,
        cell_id: int,
    ) -> np.ndarray:
        return np.argwhere(mask == cell_id)

    # ------------------------------------------------------------------
    # Cell features
    # ------------------------------------------------------------------

    def extract_cell_features(
        self,
        mask: np.ndarray,
    ) -> List[CellFeature]:

        mask = self.validate_mask(mask)

        features: List[CellFeature] = []

        for cell_id in self._cell_ids(mask):

            pixels = self._cell_pixels(
                mask,
                int(cell_id),
            )

            if pixels.size == 0:
                continue

            y_coords = pixels[:, 0]
            x_coords = pixels[:, 1]

            area = float(len(pixels))

            min_y = int(y_coords.min())
            max_y = int(y_coords.max())

            min_x = int(x_coords.min())
            max_x = int(x_coords.max())

            width = max_x - min_x + 1
            height = max_y - min_y + 1

            perimeter_estimate = 2.0 * (
                width + height
            )

            compactness = (
                4.0 * np.pi * area
                / (perimeter_estimate ** 2 + 1e-8)
            )

            features.append(
                CellFeature(
                    cell_id=int(cell_id),
                    area=area,
                    centroid_x=float(x_coords.mean()),
                    centroid_y=float(y_coords.mean()),
                    bbox_width=width,
                    bbox_height=height,
                    compactness=float(compactness),
                )
            )

        return features

    # ------------------------------------------------------------------
    # Density
    # ------------------------------------------------------------------

    @staticmethod
    def cell_density(
        cell_count: int,
        image_shape: Tuple[int, int],
    ) -> float:

        height, width = image_shape

        area = height * width

        if area == 0:
            return 0.0

        return float(cell_count / area)

    # ------------------------------------------------------------------
    # Nearest neighbours
    # ------------------------------------------------------------------

    @staticmethod
    def nearest_neighbor_distances(
        centroids: np.ndarray,
    ) -> np.ndarray:

        centroids = np.asarray(
            centroids,
            dtype=np.float32,
        )

        if len(centroids) < 2:
            return np.array([], dtype=np.float32)

        distances = []

        for i in range(len(centroids)):

            diff = centroids - centroids[i]

            dist = np.sqrt(
                np.sum(diff ** 2, axis=1)
            )

            dist[i] = np.inf

            distances.append(
                float(np.min(dist))
            )

        return np.asarray(
            distances,
            dtype=np.float32,
        )

    # ------------------------------------------------------------------
    # Distribution
    # ------------------------------------------------------------------

    @staticmethod
    def distribution_score(
        centroids: np.ndarray,
        image_shape: Tuple[int, int],
        grid_size: int = 4,
    ) -> float:

        if len(centroids) == 0:
            return 0.0

        height, width = image_shape

        grid = np.zeros(
            (grid_size, grid_size),
            dtype=np.float32,
        )

        for x, y in centroids:

            gx = min(
                int(x / width * grid_size),
                grid_size - 1,
            )

            gy = min(
                int(y / height * grid_size),
                grid_size - 1,
            )

            grid[gy, gx] += 1

        if np.mean(grid) == 0:
            return 0.0

        # Coefficient of variation.
        return float(
            np.std(grid) / (np.mean(grid) + 1e-8)
        )

    # ------------------------------------------------------------------
    # Complete analysis
    # ------------------------------------------------------------------

    def analyze(
        self,
        mask: np.ndarray,
    ) -> CellAnalysisResult:

        mask = self.validate_mask(mask)

        features = self.extract_cell_features(mask)

        cell_count = len(features)

        if cell_count == 0:

            return CellAnalysisResult(
                cell_count=0,
                cell_density=0.0,
                mean_area=0.0,
                median_area=0.0,
                std_area=0.0,
                min_area=0.0,
                max_area=0.0,
                mean_compactness=0.0,
                mean_nearest_neighbor_distance=0.0,
                cell_distribution_score=0.0,
                cells=[],
            )

        areas = np.asarray(
            [cell.area for cell in features],
            dtype=np.float32,
        )

        compactness = np.asarray(
            [cell.compactness for cell in features],
            dtype=np.float32,
        )

        centroids = np.asarray(
            [
                [cell.centroid_x, cell.centroid_y]
                for cell in features
            ],
            dtype=np.float32,
        )

        nn_distances = (
            self.nearest_neighbor_distances(
                centroids
            )
        )

        mean_nn = (
            float(np.mean(nn_distances))
            if len(nn_distances)
            else 0.0
        )

        distribution = self.distribution_score(
            centroids,
            mask.shape,
        )

        return CellAnalysisResult(
            cell_count=cell_count,
            cell_density=self.cell_density(
                cell_count,
                mask.shape,
            ),
            mean_area=float(np.mean(areas)),
            median_area=float(np.median(areas)),
            std_area=float(np.std(areas)),
            min_area=float(np.min(areas)),
            max_area=float(np.max(areas)),
            mean_compactness=float(
                np.mean(compactness)
            ),
            mean_nearest_neighbor_distance=mean_nn,
            cell_distribution_score=distribution,
            cells=[
                cell.to_dict()
                for cell in features
            ],
        )


def analyze_cells(
    mask: np.ndarray,
) -> Dict[str, Any]:
    """Convenience function."""

    analyzer = CellAnalyzer()

    return analyzer.analyze(mask).to_dict()


if __name__ == "__main__":
    print("Cell Analysis")

    mask = np.zeros(
        (256, 256),
        dtype=np.int32,
    )

    # Example cells.
    mask[20:40, 20:40] = 1
    mask[60:90, 70:100] = 2
    mask[120:145, 150:175] = 3
    mask[180:220, 50:90] = 4

    analyzer = CellAnalyzer()

    result = analyzer.analyze(mask)

    print(f"Cell count: {result.cell_count}")
    print(f"Cell density: {result.cell_density:.6f}")
    print(f"Mean area: {result.mean_area:.2f}")
    print(f"Median area: {result.median_area:.2f}")
    print(f"Area std: {result.std_area:.2f}")
    print(
        "Mean compactness: "
        f"{result.mean_compactness:.4f}"
    )
    print(
        "Mean nearest-neighbour distance: "
        f"{result.mean_nearest_neighbor_distance:.2f}"
    )
    print(
        "Distribution score: "
        f"{result.cell_distribution_score:.4f}"
    )

    print("\nCell analysis ready.")