# visualization/digital_twin_visualization.py

from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

import numpy as np
import matplotlib.pyplot as plt

from visualization.visualization import VisualizationBase


class DigitalTwinVisualizer(VisualizationBase):
    """
    Wizualizacja Digital Twin.

    Pokazuje:
    - stan tkanek,
    - stan komórek,
    - wiek biologiczny,
    - ryzyko,
    - stan czasowy,
    - zmiany stanu.
    """

    def plot_state(
        self,
        state: dict[str, float],
        filename: str | Path = "digital_twin_state.png",
        title: str = "Digital twin state",
    ):

        labels = list(state.keys())
        values = list(state.values())

        fig, ax = self.create_figure()

        ax.bar(
            labels,
            values,
        )

        ax.set_title(title)
        ax.set_ylabel("State value")

        ax.tick_params(
            axis="x",
            rotation=45,
        )

        self.clean_axes(ax)

        return self.save_figure(
            fig,
            filename,
        )

    def plot_radar(
        self,
        state: dict[str, float],
        filename: str | Path = "digital_twin_radar.png",
        title: str = "Digital twin profile",
    ):

        labels = list(state.keys())

        values = np.asarray(
            list(state.values()),
            dtype=float,
        )

        values = np.clip(
            values,
            0,
            1,
        )

        n = len(labels)

        if n < 3:
            raise ValueError(
                "Radar chart requires at least 3 dimensions."
            )

        angles = np.linspace(
            0,
            2 * np.pi,
            n,
            endpoint=False,
        )

        values = np.concatenate(
            [values, [values[0]]]
        )

        angles = np.concatenate(
            [angles, [angles[0]]]
        )

        fig = plt.figure(
            figsize=(8, 8)
        )

        ax = fig.add_subplot(
            111,
            polar=True,
        )

        ax.plot(
            angles,
            values,
        )

        ax.fill(
            angles,
            values,
            alpha=0.2,
        )

        ax.set_xticks(
            angles[:-1]
        )

        ax.set_xticklabels(
            labels
        )

        ax.set_ylim(0, 1)

        ax.set_title(title)

        return self.save_figure(
            fig,
            filename,
        )

    def plot_state_history(
        self,
        history: dict[str, Sequence[float]],
        filename: str | Path = "digital_twin_history.png",
        title: str = "Digital twin state history",
    ):

        fig, ax = self.create_figure()

        for name, values in history.items():

            values = np.asarray(
                values,
                dtype=float,
            )

            ax.plot(
                values,
                marker="o",
                label=name,
            )

        ax.set_title(title)
        ax.set_xlabel("Timepoint")
        ax.set_ylabel("State value")

        ax.legend()

        self.clean_axes(ax)

        return self.save_figure(
            fig,
            filename,
        )

    def plot_twin_summary(
        self,
        twin_state: dict[str, Any],
        filename: str | Path = "digital_twin_summary.png",
    ):

        numeric_state = {}

        for key, value in twin_state.items():

            if isinstance(
                value,
                (int, float, np.integer, np.floating),
            ):
                numeric_state[key] = float(
                    value
                )

        return self.plot_state(
            numeric_state,
            filename=filename,
            title="Digital Twin summary",
        )


if __name__ == "__main__":

    visualizer = DigitalTwinVisualizer(
        output_dir="outputs/digital_twin"
    )

    state = {
        "Tissue": 0.81,
        "Cells": 0.72,
        "RNA": 0.66,
        "Biological age": 0.59,
        "Risk": 0.31,
    }

    visualizer.plot_state(
        state
    )

    visualizer.plot_radar(
        state
    )

    visualizer.plot_state_history(
        {
            "Tissue": [0.82, 0.80, 0.78, 0.76],
            "RNA": [0.74, 0.71, 0.68, 0.66],
            "Risk": [0.22, 0.27, 0.31, 0.36],
        }
    )

    print(
        "Digital Twin visualization test completed."
    )