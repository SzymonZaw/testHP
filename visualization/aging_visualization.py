# visualization/aging_visualization.py

from __future__ import annotations

from pathlib import Path
from typing import Sequence

import numpy as np
import matplotlib.pyplot as plt

from visualization.visualization import VisualizationBase


class AgingVisualizer(VisualizationBase):
    """
    Wizualizacja wieku biologicznego.

    Obsługuje:
    - biological age,
    - chronological vs biological age,
    - aging score,
    - komponenty starzenia,
    - profile aging.
    """

    def plot_age_comparison(
        self,
        chronological_age: float,
        biological_age: float,
        filename: str | Path = "age_comparison.png",
    ):

        fig, ax = self.create_figure()

        labels = [
            "Chronological age",
            "Biological age",
        ]

        values = [
            chronological_age,
            biological_age,
        ]

        ax.bar(
            labels,
            values,
        )

        ax.set_ylabel("Age")
        ax.set_title(
            "Chronological vs biological age"
        )

        self.clean_axes(ax)

        return self.save_figure(
            fig,
            filename,
        )

    def plot_aging_score(
        self,
        score: float,
        filename: str | Path = "aging_score.png",
    ):

        fig, ax = self.create_figure(
            figsize=(8, 2.5)
        )

        score = float(
            np.clip(score, 0.0, 1.0)
        )

        ax.barh(
            ["Aging score"],
            [score],
        )

        ax.set_xlim(0, 1)
        ax.set_xlabel("Score")
        ax.set_title("Aging score")

        self.clean_axes(ax)

        return self.save_figure(
            fig,
            filename,
        )

    def plot_aging_components(
        self,
        components: dict[str, float],
        filename: str | Path = "aging_components.png",
    ):

        labels = list(
            components.keys()
        )

        values = list(
            components.values()
        )

        fig, ax = self.create_figure()

        ax.bar(
            labels,
            values,
        )

        ax.set_title(
            "Aging model components"
        )

        ax.set_ylabel("Contribution")

        ax.tick_params(
            axis="x",
            rotation=45,
        )

        self.clean_axes(ax)

        return self.save_figure(
            fig,
            filename,
        )

    def plot_aging_trajectory(
        self,
        ages: Sequence[float],
        timepoints: Sequence[str] | None = None,
        filename: str | Path = "aging_trajectory.png",
    ):

        ages = np.asarray(
            ages,
            dtype=float,
        )

        if timepoints is None:
            x = np.arange(len(ages))
        else:
            x = np.arange(
                len(timepoints)
            )

        fig, ax = self.create_figure()

        ax.plot(
            x,
            ages,
            marker="o",
        )

        if timepoints is not None:
            ax.set_xticks(x)
            ax.set_xticklabels(
                timepoints
            )

        ax.set_title(
            "Biological age trajectory"
        )

        ax.set_ylabel(
            "Biological age"
        )

        self.clean_axes(ax)

        return self.save_figure(
            fig,
            filename,
        )


if __name__ == "__main__":

    visualizer = AgingVisualizer(
        output_dir="outputs/aging"
    )

    visualizer.plot_age_comparison(
        chronological_age=45,
        biological_age=51,
    )

    visualizer.plot_aging_score(
        0.67
    )

    visualizer.plot_aging_components(
        {
            "Morphology": 0.71,
            "RNA": 0.64,
            "Cell": 0.58,
            "Tissue": 0.73,
        }
    )

    print("Aging visualization test completed.")