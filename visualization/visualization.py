# visualization/visualization.py

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, Optional, Sequence

import json
import numpy as np
import matplotlib.pyplot as plt


class VisualizationBase:
    """
    Bazowa klasa dla wszystkich modułów wizualizacyjnych.

    Odpowiada za:
    - zarządzanie katalogiem outputs,
    - zapis wykresów,
    - zapis JSON,
    - wspólne funkcje pomocnicze.
    """

    def __init__(
        self,
        output_dir: str | Path = "outputs",
        show: bool = False,
    ):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.show = show

    def ensure_dir(self, directory: str | Path) -> Path:
        path = Path(directory)

        if not path.is_absolute():
            path = self.output_dir / path

        path.mkdir(parents=True, exist_ok=True)
        return path

    def save_figure(
        self,
        fig: plt.Figure,
        filename: str | Path,
        dpi: int = 200,
        close: bool = True,
    ) -> Path:

        path = Path(filename)

        if not path.is_absolute():
            path = self.output_dir / path

        path.parent.mkdir(parents=True, exist_ok=True)

        fig.savefig(
            path,
            dpi=dpi,
            bbox_inches="tight",
        )

        if self.show:
            plt.show()

        if close:
            plt.close(fig)

        return path

    def save_json(
        self,
        data: Dict[str, Any],
        filename: str | Path,
    ) -> Path:

        path = Path(filename)

        if not path.is_absolute():
            path = self.output_dir / path

        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(
                data,
                f,
                indent=2,
                ensure_ascii=False,
                default=self._json_default,
            )

        return path

    @staticmethod
    def _json_default(value: Any):
        if isinstance(value, np.ndarray):
            return value.tolist()

        if isinstance(value, np.integer):
            return int(value)

        if isinstance(value, np.floating):
            return float(value)

        if isinstance(value, Path):
            return str(value)

        raise TypeError(
            f"Object of type {type(value).__name__} "
            "is not JSON serializable"
        )

    @staticmethod
    def to_numpy(data: Any) -> np.ndarray:
        if isinstance(data, np.ndarray):
            return data

        return np.asarray(data)

    @staticmethod
    def normalize(values: Sequence[float]) -> np.ndarray:
        values = np.asarray(values, dtype=float)

        if values.size == 0:
            return values

        minimum = np.min(values)
        maximum = np.max(values)

        if maximum - minimum == 0:
            return np.zeros_like(values)

        return (values - minimum) / (maximum - minimum)

    @staticmethod
    def create_figure(
        figsize: tuple[int, int] = (10, 6),
    ):
        return plt.subplots(figsize=figsize)

    @staticmethod
    def add_value_labels(
        ax,
        values: Iterable[float],
        fmt: str = "{:.2f}",
    ):
        for index, value in enumerate(values):
            ax.text(
                index,
                value,
                fmt.format(value),
                ha="center",
                va="bottom",
            )

    @staticmethod
    def clean_axes(ax):
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

    def create_summary_plot(
        self,
        values: Dict[str, float],
        title: str,
        filename: str | Path,
    ) -> Path:

        labels = list(values.keys())
        data = list(values.values())

        fig, ax = self.create_figure()

        ax.bar(labels, data)
        ax.set_title(title)
        ax.set_ylabel("Value")

        ax.tick_params(axis="x", rotation=45)

        self.clean_axes(ax)

        return self.save_figure(fig, filename)


if __name__ == "__main__":
    visualization = VisualizationBase(
        output_dir="outputs/visualization_test"
    )

    result = visualization.create_summary_plot(
        {
            "tissue": 0.82,
            "cells": 0.76,
            "rna": 0.91,
        },
        title="Example summary",
        filename="summary.png",
    )

    print(f"Saved: {result}")