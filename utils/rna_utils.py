# utils/rna_utils.py

from __future__ import annotations

from typing import Iterable, Optional

import numpy as np


def log1p_transform(
    matrix: np.ndarray,
) -> np.ndarray:
    """
    Apply log(1 + x) transformation.
    """

    matrix = np.asarray(
        matrix,
        dtype=np.float32,
    )

    if np.any(matrix < 0):
        raise ValueError(
            "RNA expression matrix cannot contain negative values."
        )

    return np.log1p(matrix)


def normalize_counts(
    matrix: np.ndarray,
    target_sum: float = 1e4,
) -> np.ndarray:
    """
    Normalize each sample/cell to a common library size.

    Matrix shape:
        samples/cells x genes
    """

    matrix = np.asarray(
        matrix,
        dtype=np.float32,
    )

    if np.any(matrix < 0):
        raise ValueError(
            "RNA count matrix cannot contain negative values."
        )

    library_sizes = matrix.sum(axis=1, keepdims=True)

    library_sizes = np.where(
        library_sizes == 0,
        1.0,
        library_sizes,
    )

    normalized = (
        matrix
        / library_sizes
        * target_sum
    )

    return normalized


def zscore(
    matrix: np.ndarray,
    axis: int = 0,
) -> np.ndarray:
    """
    Standardize expression values.

    Default:
        gene-wise normalization.
    """

    matrix = np.asarray(
        matrix,
        dtype=np.float32,
    )

    mean = np.mean(
        matrix,
        axis=axis,
        keepdims=True,
    )

    std = np.std(
        matrix,
        axis=axis,
        keepdims=True,
    )

    std = np.where(
        std == 0,
        1.0,
        std,
    )

    return (matrix - mean) / std


def select_genes(
    matrix: np.ndarray,
    gene_names: Iterable[str],
    selected_genes: Iterable[str],
) -> tuple[np.ndarray, list[str]]:
    """
    Select specified genes from expression matrix.
    """

    gene_names = list(gene_names)
    selected_genes = list(selected_genes)

    index = {
        gene: i
        for i, gene in enumerate(gene_names)
    }

    indices = []
    found_genes = []

    for gene in selected_genes:
        if gene in index:
            indices.append(index[gene])
            found_genes.append(gene)

    if not indices:
        raise ValueError(
            "None of the selected genes were found."
        )

    return (
        matrix[:, indices],
        found_genes,
    )


def filter_genes_by_expression(
    matrix: np.ndarray,
    gene_names: Iterable[str],
    min_cells: int = 3,
) -> tuple[np.ndarray, list[str]]:
    """
    Keep genes expressed above zero in at least min_cells.
    """

    matrix = np.asarray(
        matrix,
        dtype=np.float32,
    )

    gene_names = list(gene_names)

    expressed_cells = np.sum(
        matrix > 0,
        axis=0,
    )

    mask = expressed_cells >= min_cells

    return (
        matrix[:, mask],
        [
            gene
            for gene, keep in zip(
                gene_names,
                mask,
            )
            if keep
        ],
    )


def highly_variable_genes(
    matrix: np.ndarray,
    gene_names: Iterable[str],
    n_genes: int = 2000,
) -> tuple[np.ndarray, list[str]]:
    """
    Simple variance-based highly variable gene selection.

    This is intentionally lightweight.
    For production scRNA-seq analysis,
    Scanpy's highly_variable_genes should
    normally be preferred.
    """

    matrix = np.asarray(
        matrix,
        dtype=np.float32,
    )

    gene_names = list(gene_names)

    if n_genes >= matrix.shape[1]:
        return matrix, gene_names

    variances = np.var(
        matrix,
        axis=0,
    )

    indices = np.argsort(
        variances
    )[-n_genes:]

    indices = np.sort(indices)

    return (
        matrix[:, indices],
        [
            gene_names[i]
            for i in indices
        ],
    )


def matrix_statistics(
    matrix: np.ndarray,
) -> dict:
    """
    Calculate basic RNA matrix statistics.
    """

    matrix = np.asarray(matrix)

    return {
        "n_samples": int(matrix.shape[0]),
        "n_genes": int(matrix.shape[1]),
        "min": float(np.min(matrix)),
        "max": float(np.max(matrix)),
        "mean": float(np.mean(matrix)),
        "median": float(np.median(matrix)),
        "nonzero_fraction": float(
            np.mean(matrix > 0)
        ),
    }


def check_rna_matrix(
    matrix: np.ndarray,
) -> None:
    """
    Validate an RNA expression/count matrix.
    """

    matrix = np.asarray(matrix)

    if matrix.ndim != 2:
        raise ValueError(
            "RNA matrix must be 2-dimensional."
        )

    if not np.isfinite(matrix).all():
        raise ValueError(
            "RNA matrix contains NaN or infinite values."
        )

    if np.any(matrix < 0):
        raise ValueError(
            "RNA matrix contains negative values."
        )