"""
RNA Analysis
============

Analysis utilities for transcriptomic data.

The module is designed to work with:
- NumPy matrices
- pandas DataFrames
- Scanpy AnnData objects

It provides:
- expression statistics
- library-size statistics
- highly variable gene selection
- gene-level summaries
- simple differential-expression statistics
- PCA-like dimensionality reduction using NumPy SVD

For full single-cell workflows, Scanpy remains the preferred
upstream processing framework.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np


@dataclass
class RNAAnalysisResult:
    n_cells: int
    n_genes: int

    mean_expression: float
    expression_std: float

    mean_library_size: float
    median_library_size: float

    detected_genes_mean: float

    top_variable_genes: List[int]

    pca_shape: Optional[Tuple[int, int]]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class RNAAnalyzer:
    """
    Analyze expression matrices.

    Matrix convention:
        rows = cells/samples
        columns = genes
    """

    def __init__(
        self,
        min_expression: float = 0.0,
    ):
        self.min_expression = min_expression

    # ------------------------------------------------------------------
    # Input handling
    # ------------------------------------------------------------------

    @staticmethod
    def validate_matrix(
        expression: np.ndarray,
    ) -> np.ndarray:

        expression = np.asarray(
            expression,
            dtype=np.float32,
        )

        if expression.ndim != 2:
            raise ValueError(
                "Expression matrix must be 2-dimensional."
            )

        if expression.size == 0:
            raise ValueError(
                "Expression matrix is empty."
            )

        if np.any(~np.isfinite(expression)):
            raise ValueError(
                "Expression matrix contains "
                "non-finite values."
            )

        return expression

    # ------------------------------------------------------------------
    # Basic statistics
    # ------------------------------------------------------------------

    def library_sizes(
        self,
        expression: np.ndarray,
    ) -> np.ndarray:

        expression = self.validate_matrix(
            expression
        )

        return np.sum(
            expression,
            axis=1,
        )

    def detected_genes(
        self,
        expression: np.ndarray,
    ) -> np.ndarray:

        expression = self.validate_matrix(
            expression
        )

        return np.sum(
            expression > self.min_expression,
            axis=1,
        )

    # ------------------------------------------------------------------
    # Gene variability
    # ------------------------------------------------------------------

    def highly_variable_genes(
        self,
        expression: np.ndarray,
        n_top: int = 50,
    ) -> List[int]:

        expression = self.validate_matrix(
            expression
        )

        if n_top <= 0:
            raise ValueError(
                "n_top must be positive."
            )

        n_top = min(
            n_top,
            expression.shape[1],
        )

        variances = np.var(
            expression,
            axis=0,
        )

        indices = np.argsort(
            variances
        )[::-1][:n_top]

        return [
            int(index)
            for index in indices
        ]

    # ------------------------------------------------------------------
    # Gene summary
    # ------------------------------------------------------------------

    def gene_statistics(
        self,
        expression: np.ndarray,
        gene_indices: Optional[
            Sequence[int]
        ] = None,
    ) -> Dict[int, Dict[str, float]]:

        expression = self.validate_matrix(
            expression
        )

        if gene_indices is None:
            gene_indices = range(
                expression.shape[1]
            )

        result = {}

        for gene_index in gene_indices:

            if not (
                0 <= gene_index
                < expression.shape[1]
            ):
                continue

            values = expression[
                :, gene_index
            ]

            result[int(gene_index)] = {
                "mean": float(
                    np.mean(values)
                ),
                "std": float(
                    np.std(values)
                ),
                "median": float(
                    np.median(values)
                ),
                "detection_rate": float(
                    np.mean(
                        values
                        > self.min_expression
                    )
                ),
            }

        return result

    # ------------------------------------------------------------------
    # Differential expression
    # ------------------------------------------------------------------

    @staticmethod
    def differential_expression(
        expression: np.ndarray,
        group_a: Sequence[int],
        group_b: Sequence[int],
    ) -> List[Dict[str, float]]:

        expression = np.asarray(
            expression,
            dtype=np.float32,
        )

        group_a = np.asarray(
            group_a,
            dtype=int,
        )

        group_b = np.asarray(
            group_b,
            dtype=int,
        )

        if len(group_a) == 0 or len(group_b) == 0:
            raise ValueError(
                "Both groups must contain samples."
            )

        results = []

        for gene_index in range(
            expression.shape[1]
        ):

            a = expression[
                group_a,
                gene_index
            ]

            b = expression[
                group_b,
                gene_index
            ]

            mean_a = float(
                np.mean(a)
            )

            mean_b = float(
                np.mean(b)
            )

            pooled_std = float(
                np.sqrt(
                    (
                        np.var(a)
                        + np.var(b)
                    ) / 2.0
                )
            )

            effect = (
                (mean_a - mean_b)
                / (pooled_std + 1e-8)
            )

            results.append(
                {
                    "gene_index": float(
                        gene_index
                    ),
                    "mean_group_a": mean_a,
                    "mean_group_b": mean_b,
                    "effect_size": effect,
                    "absolute_effect": abs(
                        effect
                    ),
                }
            )

        results.sort(
            key=lambda x: x[
                "absolute_effect"
            ],
            reverse=True,
        )

        return results

    # ------------------------------------------------------------------
    # PCA / SVD
    # ------------------------------------------------------------------

    @staticmethod
    def pca(
        expression: np.ndarray,
        n_components: int = 10,
    ) -> Tuple[np.ndarray, np.ndarray]:

        expression = np.asarray(
            expression,
            dtype=np.float32,
        )

        if expression.ndim != 2:
            raise ValueError(
                "Expression matrix must be 2D."
            )

        n_components = min(
            n_components,
            expression.shape[0],
            expression.shape[1],
        )

        centered = (
            expression
            - expression.mean(axis=0)
        )

        u, s, vt = np.linalg.svd(
            centered,
            full_matrices=False,
        )

        components = vt[
            :n_components
        ]

        transformed = (
            u[:, :n_components]
            * s[:n_components]
        )

        return transformed, components

    # ------------------------------------------------------------------
    # Complete analysis
    # ------------------------------------------------------------------

    def analyze(
        self,
        expression: np.ndarray,
        n_top_genes: int = 50,
        n_pca_components: int = 10,
    ) -> RNAAnalysisResult:

        expression = self.validate_matrix(
            expression
        )

        library = self.library_sizes(
            expression
        )

        detected = self.detected_genes(
            expression
        )

        top_genes = self.highly_variable_genes(
            expression,
            n_top=n_top_genes,
        )

        pca_result = None

        if min(expression.shape) >= 2:
            transformed, _ = self.pca(
                expression,
                n_components=n_pca_components,
            )

            pca_result = (
                transformed.shape
            )

        return RNAAnalysisResult(
            n_cells=expression.shape[0],
            n_genes=expression.shape[1],
            mean_expression=float(
                np.mean(expression)
            ),
            expression_std=float(
                np.std(expression)
            ),
            mean_library_size=float(
                np.mean(library)
            ),
            median_library_size=float(
                np.median(library)
            ),
            detected_genes_mean=float(
                np.mean(detected)
            ),
            top_variable_genes=top_genes,
            pca_shape=pca_result,
        )


def analyze_rna(
    expression: np.ndarray,
) -> Dict[str, Any]:

    analyzer = RNAAnalyzer()

    return analyzer.analyze(
        expression
    ).to_dict()


if __name__ == "__main__":
    print("RNA Analysis")

    rng = np.random.default_rng(42)

    expression = rng.poisson(
        lam=2.0,
        size=(100, 500),
    ).astype(np.float32)

    analyzer = RNAAnalyzer()

    result = analyzer.analyze(
        expression,
        n_top_genes=20,
        n_pca_components=10,
    )

    print(
        f"Cells: {result.n_cells}"
    )

    print(
        f"Genes: {result.n_genes}"
    )

    print(
        f"Mean expression: "
        f"{result.mean_expression:.4f}"
    )

    print(
        f"Mean library size: "
        f"{result.mean_library_size:.2f}"
    )

    print(
        f"Mean detected genes: "
        f"{result.detected_genes_mean:.2f}"
    )

    print(
        "Top variable genes:",
        result.top_variable_genes[:10],
    )

    print(
        "PCA shape:",
        result.pca_shape,
    )

    print("\nRNA analysis ready.")