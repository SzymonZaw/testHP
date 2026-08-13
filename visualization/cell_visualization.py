# visualization/cell_visualization.py

from __future__ import annotations

from pathlib import Path
from typing import Sequence

import numpy as np
import matplotlib.pyplot as plt

from visualization.visualization import VisualizationBase


class CellVisualizer(VisualizationBase):
    """
    Wizualizacja danych komórkowych.

    Obsługuje:
    - lokalizacje komórek,
    - mapy komórek,
    - segmentacje,
    - rozkłady cech,
    - morfologię.
    """

    def plot_cell_map(
        self,
        positions: Sequence,
        image_shape: tuple[int, int] | None = None,
        filename: str | Path = "cell_map.png",
        title: str = "Cell map",
    ):

        positions = np.asarray(positions)

        if positions.size == 0:
            raise ValueError("positions cannot be empty.")

        if positions.ndim != 2 or positions.shape[1] < 2:
            raise ValueError(
                "positions must have shape (N, 2)"
            )

        fig, ax = self.create_figure()

        ax.scatter(
            positions[:, 0],
            positions[:, 1],
            s=10,
        )

        if image_shape is not None:
            height, width = image_shape
            ax.set_xlim(0, width)
            ax.set_ylim(height, 0)

        ax.set_title(title)
        ax.set_xlabel("X")
        ax.set_ylabel("Y")

        self.clean_axes(ax)

        return self.save_figure(fig, filename)

    def plot_cell_density(
        self,
        positions: Sequence,
        filename: str | Path = "cell_density.png",
        bins: int = 50,
        title: str = "Cell density",
    ):

        positions = np.asarray(positions)

        fig, ax = self.create_figure()

        density = ax.hist2d(
            positions[:, 0],
            positions[:, 1],
            bins=bins,
        )

        ax.set_title(title)
        ax.set_xlabel("X")
        ax.set_ylabel("Y")

        fig.colorbar(
            density[3],
            ax=ax,
            label="Cell count",
        )

        return self.save_figure(fig, filename)

    def plot_segmentation(
        self,
        segmentation: np.ndarray,
        filename: str | Path = "cell_segmentation.png",
        title: str = "Cell segmentation",
    ):

        fig, ax = self.create_figure()

        ax.imshow(
            segmentation,
            cmap="nipy_spectral",
        )

        ax.set_title(title)
        ax.axis("off")

        return self.save_figure(fig, filename)

    def plot_feature_distribution(
        self,
        values: Sequence[float],
        feature_name: str,
        filename: str | Path = "cell_feature.png",
    ):

        values = np.asarray(values, dtype=float)

        fig, ax = self.create_figure()

        ax.hist(
            values,
            bins=30,
        )

        ax.set_title(
            f"Distribution of {feature_name}"
        )

        ax.set_xlabel(feature_name)
        ax.set_ylabel("Count")

        self.clean_axes(ax)

        return self.save_figure(fig, filename)

    def plot_morphology_features(
        self,
        features: dict[str, Sequence[float]],
        filename: str | Path = "cell_morphology.png",
    ):

        fig, axes = plt.subplots(
            len(features),
            1,
            figsize=(10, 4 * len(features)),
        )

        if len(features) == 1:
            axes = [axes]

        for ax, (name, values) in zip(
            axes,
            features.items(),
        ):

            values = np.asarray(values)

            ax.hist(
                values,
                bins=25,
            )

            ax.set_title(name)
            ax.set_xlabel(name)
            ax.set_ylabel("Count")

            self.clean_axes(ax)

        fig.tight_layout()

        return self.save_figure(
            fig,
            filename,
        )


if __name__ == "__main__":

    visualizer = CellVisualizer(
        output_dir="outputs/cell_visualization"
    )

    positions = np.random.rand(500, 2) * 512

    visualizer.plot_cell_map(
        positions,
        image_shape=(512, 512),
    )

    visualizer.plot_cell_density(
        positions,
    )

    print("Cell visualization test completed.")