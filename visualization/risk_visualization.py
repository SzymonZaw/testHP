# visualization/risk_visualization.py

from __future__ import annotations

from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

from visualization.visualization import VisualizationBase


class RiskVisualizer(VisualizationBase):
    """
    Wizualizacja wyników risk_model.py oraz risk_analysis.py.
    """

    def plot_risk_score(
        self,
        score: float,
        filename: str | Path = "risk_score.png",
        title: str = "Risk score",
    ):

        score = float(
            np.clip(score, 0.0, 1.0)
        )

        fig, ax = self.create_figure(
            figsize=(8, 2.5)
        )

        ax.barh(
            ["Risk"],
            [score],
        )

        ax.set_xlim(0, 1)
        ax.set_xlabel("Probability / score")
        ax.set_title(title)

        self.clean_axes(ax)

        return self.save_figure(
            fig,
            filename,
        )

    def plot_risk_factors(
        self,
        factors: dict[str, float],
        filename: str | Path = "risk_factors.png",
        title: str = "Risk factors",
    ):

        names = list(
            factors.keys()
        )

        values = list(
            factors.values()
        )

        fig, ax = self.create_figure()

        ax.barh(
            names,
            values,
        )

        ax.set_xlabel("Contribution")
        ax.set_title(title)

        self.clean_axes(ax)

        return self.save_figure(
            fig,
            filename,
        )

    def plot_risk_probabilities(
        self,
        probabilities: dict[str, float],
        filename: str | Path = "risk_probabilities.png",
        title: str = "Risk probabilities",
    ):

        names = list(
            probabilities.keys()
        )

        values = list(
            probabilities.values()
        )

        values = np.clip(
            values,
            0,
            1,
        )

        fig, ax = self.create_figure()

        ax.bar(
            names,
            values,
        )

        ax.set_ylim(0, 1)
        ax.set_ylabel("Probability")
        ax.set_title(title)

        ax.tick_params(
            axis="x",
            rotation=45,
        )

        self.clean_axes(ax)

        return self.save_figure(
            fig,
            filename,
        )

    def plot_risk_matrix(
        self,
        matrix: np.ndarray,
        filename: str | Path = "risk_matrix.png",
        title: str = "Risk matrix",
    ):

        matrix = np.asarray(
            matrix,
            dtype=float,
        )

        fig, ax = self.create_figure()

        image = ax.imshow(
            matrix,
            cmap="magma",
            aspect="auto",
        )

        ax.set_title(title)
        ax.set_xlabel("Risk dimension")
        ax.set_ylabel("Patient / sample")

        fig.colorbar(
            image,
            ax=ax,
        )

        return self.save_figure(
            fig,
            filename,
        )


if __name__ == "__main__":

    visualizer = RiskVisualizer(
        output_dir="outputs/risk"
    )

    visualizer.plot_risk_score(
        0.42
    )

    visualizer.plot_risk_factors(
        {
            "Morphology": 0.32,
            "RNA": 0.51,
            "Age": 0.73,
            "Longitudinal": 0.41,
        }
    )

    visualizer.plot_risk_probabilities(
        {
            "Low": 0.25,
            "Medium": 0.50,
            "High": 0.25,
        }
    )

    print("Risk visualization test completed.")