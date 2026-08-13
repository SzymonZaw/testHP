# visualization/tissue_visualization.py

from __future__ import annotations

from pathlib import Path
from typing import Optional

import numpy as np
import matplotlib.pyplot as plt

from visualization.visualization import VisualizationBase


class TissueVisualizer(VisualizationBase):
    """
    Wizualizacja danych tkankowych.

    Obsługuje:
    - obrazy tkanek,
    - maski segmentacyjne,
    - overlay obrazu i maski,
    - mapy intensywności,
    - bounding boxy.
    """

    def plot_image(
        self,
        image: np.ndarray,
        filename: str | Path = "tissue.png",
        title: str = "Tissue image",
        cmap: Optional[str] = None,
    ):

        image = np.asarray(image)

        fig, ax = self.create_figure()

        if image.ndim == 2:
            ax.imshow(image, cmap=cmap or "gray")
        else:
            ax.imshow(image)

        ax.set_title(title)
        ax.axis("off")

        return self.save_figure(fig, filename)

    def plot_mask(
        self,
        mask: np.ndarray,
        filename: str | Path = "segmentation.png",
        title: str = "Tissue segmentation",
    ):

        mask = np.asarray(mask)

        fig, ax = self.create_figure()

        ax.imshow(mask, cmap="viridis")
        ax.set_title(title)
        ax.axis("off")

        return self.save_figure(fig, filename)

    def plot_overlay(
        self,
        image: np.ndarray,
        mask: np.ndarray,
        filename: str | Path = "overlay.png",
        alpha: float = 0.45,
        title: str = "Tissue segmentation overlay",
    ):

        image = np.asarray(image)
        mask = np.asarray(mask)

        fig, ax = self.create_figure()

        if image.ndim == 2:
            ax.imshow(image, cmap="gray")
        else:
            ax.imshow(image)

        ax.imshow(
            mask,
            cmap="viridis",
            alpha=alpha,
        )

        ax.set_title(title)
        ax.axis("off")

        return self.save_figure(fig, filename)

    def plot_heatmap(
        self,
        heatmap: np.ndarray,
        filename: str | Path = "tissue_heatmap.png",
        title: str = "Tissue heatmap",
    ):

        heatmap = np.asarray(heatmap)

        fig, ax = self.create_figure()

        image = ax.imshow(
            heatmap,
            cmap="magma",
        )

        ax.set_title(title)
        ax.axis("off")

        fig.colorbar(image, ax=ax)

        return self.save_figure(fig, filename)

    def plot_bounding_boxes(
        self,
        image: np.ndarray,
        boxes: list,
        filename: str | Path = "tissue_boxes.png",
        title: str = "Detected tissue regions",
    ):

        from matplotlib.patches import Rectangle

        fig, ax = self.create_figure()

        if image.ndim == 2:
            ax.imshow(image, cmap="gray")
        else:
            ax.imshow(image)

        for box in boxes:
            if len(box) != 4:
                continue

            x1, y1, x2, y2 = box

            rectangle = Rectangle(
                (x1, y1),
                x2 - x1,
                y2 - y1,
                fill=False,
                linewidth=2,
            )

            ax.add_patch(rectangle)

        ax.set_title(title)
        ax.axis("off")

        return self.save_figure(fig, filename)


if __name__ == "__main__":

    visualizer = TissueVisualizer(
        output_dir="outputs/tissue_visualization"
    )

    image = np.random.rand(256, 256)
    mask = np.random.randint(0, 3, (256, 256))

    visualizer.plot_image(
        image,
        "example_image.png",
    )

    visualizer.plot_mask(
        mask,
        "example_mask.png",
    )

    visualizer.plot_overlay(
        image,
        mask,
        "example_overlay.png",
    )

    print("Tissue visualization test completed.")