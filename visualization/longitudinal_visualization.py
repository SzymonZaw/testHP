# visualization/longitudinal_visualization.py

from __future__ import annotations

from pathlib import Path
from typing import Sequence

import numpy as np
import matplotlib.pyplot as plt

from visualization.visualization import VisualizationBase


class LongitudinalVisualizer(VisualizationBase):
    """
    Wizualizacja zmian pacjenta w czasie.

    Typowy przebieg:

        T0 -> T1 -> T2 -> T3

    Obsługuje:
    - trajectories,
    - porównanie timepointów,
    - zmianę wieku biologicznego,
    - zmianę ryzyka,
    - zmianę biomarkerów.
    """

    def plot_trajectory(
        self,
        values: Sequence[float],
        timepoints: Sequence[str] | None = None,
        filename: str | Path = "trajectory.png",
        title: str = "Longitudinal trajectory",
        ylabel: str = "Value",
    ):

        values = np.asarray(
            values,
            dtype=float,
        )

        if timepoints is None:
            timepoints = [
                f"T{i}"
                for i in range(len(values))
            ]

        if len(values) != len(timepoints):
            raise ValueError(
                "values and timepoints must have the same length."
            )

        x = np.arange(
            len(timepoints)
        )

        fig, ax = self.create_figure()

        ax.plot(
            x,
            values,
            marker="o",
            linewidth=2,
        )

        ax.set_xticks(x)
        ax.set_xticklabels(timepoints)

        ax.set_title(title)
        ax.set_xlabel("Timepoint")
        ax.set_ylabel(ylabel)

        self.clean_axes(ax)

        return self.save_figure(
            fig,
            filename,
        )

    def plot_multiple_trajectories(
        self,
        trajectories: dict[str, Sequence[float]],
        timepoints: Sequence[str] | None = None,
        filename: str | Path = "multiple_trajectories.png",
        title: str = "Longitudinal trajectories",
    ):

        if not trajectories:
            raise ValueError(
                "trajectories cannot be empty."
            )

        max_length = max(
            len(values)
            for values in trajectories.values()
        )

        if timepoints is None:
            timepoints = [
                f"T{i}"
                for i in range(max_length)
            ]

        x = np.arange(
            len(timepoints)
        )

        fig, ax = self.create_figure()

        for name, values in trajectories.items():

            values = np.asarray(
                values,
                dtype=float,
            )

            if len(values) != len(timepoints):
                raise ValueError(
                    f"Trajectory '{name}' has "
                    f"{len(values)} values, expected "
                    f"{len(timepoints)}."
                )

            ax.plot(
                x,
                values,
                marker="o",
                label=name,
            )

        ax.set_xticks(x)
        ax.set_xticklabels(timepoints)

        ax.set_title(title)
        ax.set_xlabel("Timepoint")
        ax.set_ylabel("Value")

        ax.legend()

        self.clean_axes(ax)

        return self.save_figure(
            fig,
            filename,
        )

    def plot_age_progression(
        self,
        chronological_age: Sequence[float],
        biological_age: Sequence[float],
        timepoints: Sequence[str] | None = None,
        filename: str | Path = "age_progression.png",
    ):

        chronological_age = np.asarray(
            chronological_age,
            dtype=float,
        )

        biological_age = np.asarray(
            biological_age,
            dtype=float,
        )

        if len(chronological_age) != len(
            biological_age
        ):
            raise ValueError(
                "Age arrays must have equal length."
            )

        if timepoints is None:
            timepoints = [
                f"T{i}"
                for i in range(
                    len(chronological_age)
                )
            ]

        x = np.arange(
            len(timepoints)
        )

        fig, ax = self.create_figure()

        ax.plot(
            x,
            chronological_age,
            marker="o",
            label="Chronological age",
        )

        ax.plot(
            x,
            biological_age,
            marker="o",
            label="Biological age",
        )

        ax.set_xticks(x)
        ax.set_xticklabels(timepoints)

        ax.set_title(
            "Age progression"
        )

        ax.set_ylabel("Age")

        ax.legend()

        self.clean_axes(ax)

        return self.save_figure(
            fig,
            filename,
        )

    def plot_risk_progression(
        self,
        risks: Sequence[float],
        timepoints: Sequence[str] | None = None,
        filename: str | Path = "risk_progression.png",
    ):

        return self.plot_trajectory(
            risks,
            timepoints=timepoints,
            filename=filename,
            title="Risk progression",
            ylabel="Risk score",
        )

    def plot_change_heatmap(
        self,
        matrix: np.ndarray,
        feature_names: Sequence[str] | None = None,
        timepoints: Sequence[str] | None = None,
        filename: str | Path = "longitudinal_heatmap.png",
        title: str = "Longitudinal feature changes",
    ):

        matrix = np.asarray(
            matrix,
            dtype=float,
        )

        if matrix.ndim != 2:
            raise ValueError(
                "matrix must be 2-dimensional."
            )

        n_features, n_timepoints = matrix.shape

        fig, ax = self.create_figure(
            figsize=(10, 7)
        )

        image = ax.imshow(
            matrix,
            aspect="auto",
            cmap="viridis",
        )

        if feature_names is not None:
            if len(feature_names) == n_features:
                ax.set_yticks(
                    np.arange(n_features)
                )

                ax.set_yticklabels(
                    feature_names
                )

        if timepoints is not None:
            if len(timepoints) == n_timepoints:
                ax.set_xticks(
                    np.arange(n_timepoints)
                )

                ax.set_xticklabels(
                    timepoints
                )

        ax.set_title(title)
        ax.set_xlabel("Timepoint")
        ax.set_ylabel("Feature")

        fig.colorbar(
            image,
            ax=ax,
        )

        return self.save_figure(
            fig,
            filename,
        )


if __name__ == "__main__":

    visualizer = LongitudinalVisualizer(
        output_dir="outputs/longitudinal"
    )

    timepoints = [
        "T0",
        "T1",
        "T2",
        "T3",
    ]

    visualizer.plot_trajectory(
        [0.42, 0.48, 0.55, 0.61],
        timepoints=timepoints,
        title="Example risk trajectory",
        ylabel="Risk",
    )

    visualizer.plot_multiple_trajectories(
        {
            "Aging": [0.40, 0.45, 0.51, 0.57],
            "Risk": [0.20, 0.27, 0.34, 0.42],
            "Tissue": [0.82, 0.79, 0.76, 0.73],
        },
        timepoints=timepoints,
    )

    visualizer.plot_age_progression(
        chronological_age=[
            45,
            46,
            47,
            48,
        ],
        biological_age=[
            48,
            49,
            51,
            53,
        ],
        timepoints=timepoints,
    )

    visualizer.plot_risk_progression(
        [0.22, 0.29, 0.37, 0.44],
        timepoints=timepoints,
    )

    matrix = np.random.rand(
        6,
        4,
    )

    visualizer.plot_change_heatmap(
        matrix,
        feature_names=[
            "Morphology",
            "Cell density",
            "RNA",
            "Aging",
            "Risk",
            "Pathology",
        ],
        timepoints=timepoints,
    )

    print(
        "Longitudinal visualization test completed."
    )