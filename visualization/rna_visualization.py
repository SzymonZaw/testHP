# visualization/rna_visualization.py

from __future__ import annotations

from pathlib import Path
from typing import Sequence

import numpy as np
import matplotlib.pyplot as plt

from visualization.visualization import VisualizationBase


class RNAVisualizer(VisualizationBase):
    """
    Wizualizacja danych RNA / transcriptomics.

    Obsługuje:
    - PCA,
    - UMAP,
    - ekspresję genów,
    - heatmapy,
    - rozkłady ekspresji.
    """

    def plot_embedding(
        self,
        embedding: np.ndarray,
        labels: Sequence | None = None,
        filename: str | Path = "rna_embedding.png",
        title: str = "RNA embedding",
    ):

        embedding = np.asarray(embedding)

        if embedding.ndim != 2 or embedding.shape[1] < 2:
            raise ValueError(
                "embedding must have shape (N, >=2)"
            )

        fig, ax = self.create_figure()

        if labels is None:
            ax.scatter(
                embedding[:, 0],
                embedding[:, 1],
                s=10,
            )
        else:
            labels = np.asarray(labels)

            for label in np.unique(labels):
                mask = labels == label

                ax.scatter(
                    embedding[mask, 0],
                    embedding[mask, 1],
                    s=12,
                    label=str(label),
                )

            ax.legend()

        ax.set_title(title)
        ax.set_xlabel("Component 1")
        ax.set_ylabel("Component 2")

        self.clean_axes(ax)

        return self.save_figure(
            fig,
            filename,
        )

    def plot_gene_expression(
        self,
        expression: Sequence[float],
        gene_name: str,
        filename: str | Path = "gene_expression.png",
    ):

        expression = np.asarray(
            expression,
            dtype=float,
        )

        fig, ax = self.create_figure()

        ax.hist(
            expression,
            bins=30,
        )

        ax.set_title(
            f"Expression: {gene_name}"
        )

        ax.set_xlabel("Expression")
        ax.set_ylabel("Cells")

        self.clean_axes(ax)

        return self.save_figure(
            fig,
            filename,
        )

    def plot_expression_heatmap(
        self,
        expression_matrix: np.ndarray,
        gene_names: Sequence[str] | None = None,
        filename: str | Path = "rna_heatmap.png",
        title: str = "RNA expression heatmap",
    ):

        matrix = np.asarray(
            expression_matrix,
            dtype=float,
        )

        fig, ax = self.create_figure(
            figsize=(12, 8)
        )

        image = ax.imshow(
            matrix,
            aspect="auto",
            cmap="viridis",
        )

        ax.set_title(title)
        ax.set_xlabel("Genes")
        ax.set_ylabel("Samples / cells")

        if gene_names is not None:
            gene_names = list(gene_names)

            if len(gene_names) <= 30:
                ax.set_xticks(
                    np.arange(len(gene_names))
                )
                ax.set_xticklabels(
                    gene_names,
                    rotation=90,
                )

        fig.colorbar(
            image,
            ax=ax,
            label="Expression",
        )

        return self.save_figure(
            fig,
            filename,
        )

    def plot_gene_scores(
        self,
        gene_scores: dict[str, float],
        filename: str | Path = "gene_scores.png",
        title: str = "Gene scores",
    ):

        genes = list(gene_scores.keys())
        values = list(gene_scores.values())

        fig, ax = self.create_figure()

        ax.bar(
            genes,
            values,
        )

        ax.set_title(title)
        ax.set_ylabel("Score")

        ax.tick_params(
            axis="x",
            rotation=90,
        )

        self.clean_axes(ax)

        return self.save_figure(
            fig,
            filename,
        )


if __name__ == "__main__":

    visualizer = RNAVisualizer(
        output_dir="outputs/rna_visualization"
    )

    embedding = np.random.randn(
        300,
        2,
    )

    labels = np.random.randint(
        0,
        4,
        300,
    )

    visualizer.plot_embedding(
        embedding,
        labels,
    )

    expression = np.random.gamma(
        2,
        2,
        300,
    )

    visualizer.plot_gene_expression(
        expression,
        "ExampleGene",
    )

    print("RNA visualization test completed.")