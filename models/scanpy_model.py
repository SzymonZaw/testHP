"""
scanpy_model.py

Scanpy-based analysis utilities for single-cell and spatial transcriptomics.

Responsibilities
----------------
- Load AnnData files
- Basic dataset inspection
- Quality-control metrics
- Filtering cells and genes
- Normalization and log transformation
- Highly variable gene selection
- Scaling
- PCA
- Nearest-neighbor graph
- UMAP
- Leiden clustering
- Differential expression
- Cell-type marker analysis
- Saving/loading AnnData objects

This module is intentionally focused on reusable analysis operations.
Dataset-specific paths and experiment configuration should be handled
outside this file, e.g. in datasets/ and pipeline/.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Union

import numpy as np
import pandas as pd

try:
    import scanpy as sc
    import anndata as ad
except ImportError as exc:
    raise ImportError(
        "Scanpy/AnnData are required for scanpy_model.py. "
        "Install them with: pip install scanpy anndata"
    ) from exc


logger = logging.getLogger(__name__)


PathLike = Union[str, Path]


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

@dataclass
class ScanpyConfig:
    """
    Configuration for a standard Scanpy workflow.
    """

    min_genes_per_cell: int = 200
    max_genes_per_cell: Optional[int] = None

    min_cells_per_gene: int = 3

    max_mito_percent: float = 20.0

    target_sum: float = 1e4

    n_top_genes: int = 2000

    n_pcs: int = 50
    n_neighbors: int = 15

    resolution: float = 0.5

    random_state: int = 42

    scale_max_value: float = 10.0


# ---------------------------------------------------------------------------
# Main model class
# ---------------------------------------------------------------------------

class ScanpyModel:
    """
    Reusable wrapper around Scanpy operations.

    Parameters
    ----------
    config:
        ScanpyConfig instance controlling preprocessing and analysis.
    """

    def __init__(
        self,
        config: Optional[ScanpyConfig] = None,
    ) -> None:

        self.config = config or ScanpyConfig()

        self.adata: Optional[ad.AnnData] = None

        logger.info("Initialized ScanpyModel.")

    # ------------------------------------------------------------------
    # Loading / saving
    # ------------------------------------------------------------------

    def load(
        self,
        path: PathLike,
        backed: Optional[str] = None,
    ) -> ad.AnnData:
        """
        Load an AnnData dataset.

        Supported formats:
        - .h5ad
        - .h5
        - .h5ad backed mode

        Parameters
        ----------
        path:
            Path to AnnData file.

        backed:
            Optional AnnData backed mode:
            "r" or "r+".

        Returns
        -------
        AnnData
        """

        path = Path(path)

        if not path.exists():
            raise FileNotFoundError(f"AnnData file not found: {path}")

        logger.info("Loading AnnData from %s", path)

        self.adata = sc.read_h5ad(
            filename=path,
            backed=backed,
        )

        logger.info(
            "Loaded dataset: %d cells x %d genes",
            self.adata.n_obs,
            self.adata.n_vars,
        )

        return self.adata

    def save(
        self,
        path: PathLike,
        overwrite: bool = True,
    ) -> None:
        """
        Save current AnnData object.
        """

        self._require_adata()

        path = Path(path)

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        if path.exists() and not overwrite:
            raise FileExistsError(
                f"File already exists: {path}"
            )

        logger.info("Saving AnnData to %s", path)

        self.adata.write_h5ad(path)

    # ------------------------------------------------------------------
    # Dataset inspection
    # ------------------------------------------------------------------

    def summary(self) -> dict:
        """
        Return basic dataset statistics.
        """

        self._require_adata()

        summary = {
            "n_cells": int(self.adata.n_obs),
            "n_genes": int(self.adata.n_vars),
            "obs_columns": list(self.adata.obs.columns),
            "var_columns": list(self.adata.var.columns),
            "layers": list(self.adata.layers.keys()),
            "obsm": list(self.adata.obsm.keys()),
            "uns": list(self.adata.uns.keys()),
        }

        return summary

    def print_summary(self) -> None:
        """
        Print a human-readable dataset summary.
        """

        summary = self.summary()

        print("\n===== AnnData Summary =====")
        print(f"Cells:       {summary['n_cells']}")
        print(f"Genes:       {summary['n_genes']}")
        print(f"obs columns: {summary['obs_columns']}")
        print(f"var columns: {summary['var_columns']}")
        print(f"layers:      {summary['layers']}")
        print(f"obsm:        {summary['obsm']}")
        print("===========================\n")

    # ------------------------------------------------------------------
    # Quality control
    # ------------------------------------------------------------------

    def calculate_qc_metrics(
        self,
        mitochondrial_prefix: str = "MT-",
        ribosomal_prefixes: Sequence[str] = ("RPS", "RPL"),
    ) -> ad.AnnData:
        """
        Calculate standard single-cell QC metrics.

        Adds:
        - total_counts
        - n_genes_by_counts
        - pct_counts_mt
        - pct_counts_ribo

        Parameters
        ----------
        mitochondrial_prefix:
            Prefix used to identify mitochondrial genes.

        ribosomal_prefixes:
            Prefixes used to identify ribosomal genes.
        """

        self._require_adata()

        adata = self.adata

        gene_names = adata.var_names.astype(str)

        adata.var["mt"] = gene_names.str.upper().str.startswith(
            mitochondrial_prefix.upper()
        )

        ribo_mask = np.zeros(
            len(gene_names),
            dtype=bool,
        )

        upper_names = gene_names.str.upper()

        for prefix in ribosomal_prefixes:
            ribo_mask |= upper_names.str.startswith(
                prefix.upper()
            )

        adata.var["ribo"] = ribo_mask

        sc.pp.calculate_qc_metrics(
            adata,
            qc_vars=["mt", "ribo"],
            inplace=True,
            log1p=False,
        )

        logger.info("Calculated QC metrics.")

        return adata

    def qc_report(self) -> pd.DataFrame:
        """
        Return a compact QC report.
        """

        self._require_adata()

        required_columns = [
            "total_counts",
            "n_genes_by_counts",
        ]

        optional_columns = [
            "pct_counts_mt",
            "pct_counts_ribo",
        ]

        columns = [
            column
            for column in required_columns + optional_columns
            if column in self.adata.obs.columns
        ]

        return self.adata.obs[columns].describe()

    # ------------------------------------------------------------------
    # Filtering
    # ------------------------------------------------------------------

    def filter_cells(
        self,
        min_genes: Optional[int] = None,
        max_genes: Optional[int] = None,
        min_counts: Optional[int] = None,
        max_counts: Optional[int] = None,
        max_mito_percent: Optional[float] = None,
    ) -> ad.AnnData:
        """
        Filter cells based on QC metrics.
        """

        self._require_adata()

        adata = self.adata

        min_genes = (
            self.config.min_genes_per_cell
            if min_genes is None
            else min_genes
        )

        max_genes = (
            self.config.max_genes_per_cell
            if max_genes is None
            else max_genes
        )

        max_mito_percent = (
            self.config.max_mito_percent
            if max_mito_percent is None
            else max_mito_percent
        )

        mask = np.ones(
            adata.n_obs,
            dtype=bool,
        )

        if min_genes is not None:
            if "n_genes_by_counts" not in adata.obs:
                raise RuntimeError(
                    "Run calculate_qc_metrics() first."
                )

            mask &= (
                adata.obs["n_genes_by_counts"]
                >= min_genes
            )

        if max_genes is not None:
            if "n_genes_by_counts" not in adata.obs:
                raise RuntimeError(
                    "Run calculate_qc_metrics() first."
                )

            mask &= (
                adata.obs["n_genes_by_counts"]
                <= max_genes
            )

        if min_counts is not None:
            if "total_counts" not in adata.obs:
                raise RuntimeError(
                    "Run calculate_qc_metrics() first."
                )

            mask &= (
                adata.obs["total_counts"]
                >= min_counts
            )

        if max_counts is not None:
            if "total_counts" not in adata.obs:
                raise RuntimeError(
                    "Run calculate_qc_metrics() first."
                )

            mask &= (
                adata.obs["total_counts"]
                <= max_counts
            )

        if max_mito_percent is not None:
            if "pct_counts_mt" not in adata.obs:
                raise RuntimeError(
                    "Run calculate_qc_metrics() first."
                )

            mask &= (
                adata.obs["pct_counts_mt"]
                <= max_mito_percent
            )

        before = adata.n_obs

        self.adata = adata[mask].copy()

        after = self.adata.n_obs

        logger.info(
            "Filtered cells: %d -> %d",
            before,
            after,
        )

        return self.adata

    def filter_genes(
        self,
        min_cells: Optional[int] = None,
    ) -> ad.AnnData:
        """
        Remove genes expressed in fewer than min_cells cells.
        """

        self._require_adata()

        min_cells = (
            self.config.min_cells_per_gene
            if min_cells is None
            else min_cells
        )

        before = self.adata.n_vars

        sc.pp.filter_genes(
            self.adata,
            min_cells=min_cells,
        )

        self.adata = self.adata.copy()

        after = self.adata.n_vars

        logger.info(
            "Filtered genes: %d -> %d",
            before,
            after,
        )

        return self.adata

    # ------------------------------------------------------------------
    # Normalization
    # ------------------------------------------------------------------

    def normalize(
        self,
        target_sum: Optional[float] = None,
        log1p: bool = True,
        store_raw: bool = True,
    ) -> ad.AnnData:
        """
        Normalize counts per cell and optionally log-transform.

        The original expression matrix is optionally stored in
        adata.raw before transformation.
        """

        self._require_adata()

        target_sum = (
            self.config.target_sum
            if target_sum is None
            else target_sum
        )

        if store_raw:
            self.adata.raw = self.adata.copy()

        sc.pp.normalize_total(
            self.adata,
            target_sum=target_sum,
        )

        if log1p:
            sc.pp.log1p(self.adata)

        logger.info(
            "Normalization completed. target_sum=%s",
            target_sum,
        )

        return self.adata

    # ------------------------------------------------------------------
    # Highly variable genes
    # ------------------------------------------------------------------

    def select_highly_variable_genes(
        self,
        n_top_genes: Optional[int] = None,
        flavor: str = "seurat_v3",
    ) -> ad.AnnData:
        """
        Select highly variable genes.

        Parameters
        ----------
        n_top_genes:
            Number of HVGs.

        flavor:
            Scanpy HVG method.

        Notes
        -----
        seurat_v3 may require the scikit-misc package depending on
        the Scanpy version.
        """

        self._require_adata()

        n_top_genes = (
            self.config.n_top_genes
            if n_top_genes is None
            else n_top_genes
        )

        logger.info(
            "Selecting %d highly variable genes.",
            n_top_genes,
        )

        sc.pp.highly_variable_genes(
            self.adata,
            n_top_genes=n_top_genes,
            flavor=flavor,
        )

        return self.adata

    # ------------------------------------------------------------------
    # Scaling
    # ------------------------------------------------------------------

    def scale(
        self,
        max_value: Optional[float] = None,
    ) -> ad.AnnData:
        """
        Scale expression values.
        """

        self._require_adata()

        max_value = (
            self.config.scale_max_value
            if max_value is None
            else max_value
        )

        sc.pp.scale(
            self.adata,
            max_value=max_value,
        )

        logger.info(
            "Expression scaling completed."
        )

        return self.adata

    # ------------------------------------------------------------------
    # PCA
    # ------------------------------------------------------------------

    def pca(
        self,
        n_comps: Optional[int] = None,
    ) -> ad.AnnData:
        """
        Perform PCA.
        """

        self._require_adata()

        n_comps = (
            self.config.n_pcs
            if n_comps is None
            else n_comps
        )

        logger.info(
            "Running PCA with %d components.",
            n_comps,
        )

        sc.tl.pca(
            self.adata,
            n_comps=n_comps,
            random_state=self.config.random_state,
        )

        return self.adata

    # ------------------------------------------------------------------
    # Neighborhood graph
    # ------------------------------------------------------------------

    def compute_neighbors(
        self,
        n_neighbors: Optional[int] = None,
        n_pcs: Optional[int] = None,
    ) -> ad.AnnData:
        """
        Compute nearest-neighbor graph.
        """

        self._require_adata()

        n_neighbors = (
            self.config.n_neighbors
            if n_neighbors is None
            else n_neighbors
        )

        n_pcs = (
            self.config.n_pcs
            if n_pcs is None
            else n_pcs
        )

        logger.info(
            "Computing neighbors: n_neighbors=%d, n_pcs=%d",
            n_neighbors,
            n_pcs,
        )

        sc.pp.neighbors(
            self.adata,
            n_neighbors=n_neighbors,
            n_pcs=n_pcs,
        )

        return self.adata

    # ------------------------------------------------------------------
    # UMAP
    # ------------------------------------------------------------------

    def umap(self) -> ad.AnnData:
        """
        Compute UMAP embedding.
        """

        self._require_adata()

        logger.info("Computing UMAP.")

        sc.tl.umap(
            self.adata,
            random_state=self.config.random_state,
        )

        return self.adata

    # ------------------------------------------------------------------
    # Clustering
    # ------------------------------------------------------------------

    def leiden(
        self,
        resolution: Optional[float] = None,
        key_added: str = "leiden",
    ) -> ad.AnnData:
        """
        Perform Leiden clustering.

        Requires:
        - neighbor graph
        - leidenalg package
        """

        self._require_adata()

        resolution = (
            self.config.resolution
            if resolution is None
            else resolution
        )

        logger.info(
            "Running Leiden clustering. resolution=%s",
            resolution,
        )

        sc.tl.leiden(
            self.adata,
            resolution=resolution,
            key_added=key_added,
            random_state=self.config.random_state,
        )

        return self.adata

    # ------------------------------------------------------------------
    # Differential expression
    # ------------------------------------------------------------------

    def rank_genes_groups(
        self,
        groupby: str,
        method: str = "wilcoxon",
        n_genes: int = 50,
        key_added: str = "rank_genes_groups",
    ) -> ad.AnnData:
        """
        Identify genes enriched in each group.

        Parameters
        ----------
        groupby:
            obs column, e.g. "cell_type" or "leiden".

        method:
            Common options:
            - wilcoxon
            - t-test
            - logreg
        """

        self._require_adata()

        if groupby not in self.adata.obs.columns:
            raise KeyError(
                f"Column '{groupby}' not found in adata.obs."
            )

        logger.info(
            "Running differential expression grouped by '%s'.",
            groupby,
        )

        sc.tl.rank_genes_groups(
            self.adata,
            groupby=groupby,
            method=method,
            n_genes=n_genes,
            key_added=key_added,
        )

        return self.adata

    def get_ranked_genes(
        self,
        group: Optional[str] = None,
        key: str = "rank_genes_groups",
        n_genes: int = 20,
    ) -> pd.DataFrame:
        """
        Convert rank_genes_groups results into a DataFrame.
        """

        self._require_adata()

        if key not in self.adata.uns:
            raise KeyError(
                f"'{key}' not found in adata.uns. "
                "Run rank_genes_groups() first."
            )

        result = self.adata.uns[key]

        names = result["names"]

        if group is not None:
            if group not in names.dtype.names:
                raise KeyError(
                    f"Group '{group}' not found."
                )

            values = names[group][:n_genes]

            output = pd.DataFrame(
                {
                    "gene": values,
                }
            )

            if "scores" in result:
                output["score"] = result["scores"][
                    group
                ][:n_genes]

            if "pvals" in result:
                output["pval"] = result["pvals"][
                    group
                ][:n_genes]

            if "pvals_adj" in result:
                output["pval_adj"] = result[
                    "pvals_adj"
                ][group][:n_genes]

            return output

        records = []

        for current_group in names.dtype.names:

            genes = names[current_group][:n_genes]

            for index, gene in enumerate(genes):

                record = {
                    "group": current_group,
                    "gene": gene,
                }

                if "scores" in result:
                    record["score"] = result[
                        "scores"
                    ][current_group][index]

                if "pvals" in result:
                    record["pval"] = result[
                        "pvals"
                    ][current_group][index]

                if "pvals_adj" in result:
                    record["pval_adj"] = result[
                        "pvals_adj"
                    ][current_group][index]

                records.append(record)

        return pd.DataFrame(records)

    # ------------------------------------------------------------------
    # Marker genes
    # ------------------------------------------------------------------

    def score_cell_type(
        self,
        cell_type: str,
        marker_genes: Sequence[str],
        score_name: Optional[str] = None,
    ) -> ad.AnnData:
        """
        Score cells based on a marker-gene set.

        Example
        -------
        marker_genes = [
            "KRT14",
            "KRT5",
            "KRT17",
        ]
        """

        self._require_adata()

        score_name = (
            score_name
            or f"{cell_type}_score"
        )

        available_genes = [
            gene
            for gene in marker_genes
            if gene in self.adata.var_names
        ]

        if not available_genes:
            raise ValueError(
                f"None of the marker genes for '{cell_type}' "
                "were found in the dataset."
            )

        logger.info(
            "Scoring cell type '%s' using %d markers.",
            cell_type,
            len(available_genes),
        )

        sc.tl.score_genes(
            self.adata,
            gene_list=available_genes,
            score_name=score_name,
        )

        return self.adata

    def assign_cell_type_by_markers(
        self,
        marker_sets: dict[str, Sequence[str]],
        score_suffix: str = "_score",
        label_key: str = "predicted_cell_type",
    ) -> ad.AnnData:
        """
        Assign a cell type based on the highest marker score.

        Parameters
        ----------
        marker_sets:
            Dictionary such as:

            {
                "keratinocyte": ["KRT14", "KRT5"],
                "fibroblast": ["COL1A1", "COL1A2"],
                "melanocyte": ["MLANA", "PMEL"],
            }

        Returns
        -------
        AnnData
        """

        self._require_adata()

        score_columns = []

        for cell_type, markers in marker_sets.items():

            score_name = (
                f"{cell_type}{score_suffix}"
            )

            self.score_cell_type(
                cell_type=cell_type,
                marker_genes=markers,
                score_name=score_name,
            )

            score_columns.append(score_name)

        scores = self.adata.obs[
            score_columns
        ]

        best_indices = scores.values.argmax(
            axis=1
        )

        labels = [
            scores.columns[index].replace(
                score_suffix,
                "",
            )
            for index in best_indices
        ]

        self.adata.obs[label_key] = pd.Categorical(
            labels
        )

        logger.info(
            "Assigned cell types using marker scores."
        )

        return self.adata

    # ------------------------------------------------------------------
    # Batch correction / integration
    # ------------------------------------------------------------------

    def integrate_by_batch(
        self,
        batch_key: str,
    ) -> ad.AnnData:
        """
        Lightweight batch-aware preprocessing.

        This method stores batch information and prepares the dataset
        for downstream integration.

        It intentionally does NOT force a particular integration method
        such as Harmony, scVI or BBKNN.
        """

        self._require_adata()

        if batch_key not in self.adata.obs.columns:
            raise KeyError(
                f"Batch key '{batch_key}' not found."
            )

        batches = self.adata.obs[
            batch_key
        ].astype("category")

        self.adata.obs[
            "_scanpy_batch"
        ] = batches

        logger.info(
            "Registered batch variable '%s'.",
            batch_key,
        )

        return self.adata

    # ------------------------------------------------------------------
    # Standard pipeline
    # ------------------------------------------------------------------

    def run_standard_pipeline(
        self,
        calculate_qc: bool = True,
        filter_cells: bool = True,
        filter_genes: bool = True,
        normalize: bool = True,
        highly_variable: bool = True,
        scale: bool = True,
        pca: bool = True,
        neighbors: bool = True,
        umap: bool = True,
        leiden: bool = True,
    ) -> ad.AnnData:
        """
        Run a complete standard Scanpy workflow.

        Typical workflow:

        QC
          ↓
        filtering
          ↓
        normalization
          ↓
        HVG selection
          ↓
        scaling
          ↓
        PCA
          ↓
        neighbors
          ↓
        UMAP
          ↓
        Leiden
        """

        self._require_adata()

        logger.info(
            "Starting standard Scanpy pipeline."
        )

        if calculate_qc:
            self.calculate_qc_metrics()

        if filter_cells:
            self.filter_cells()

        if filter_genes:
            self.filter_genes()

        if normalize:
            self.normalize()

        if highly_variable:
            self.select_highly_variable_genes()

            # Keep only HVGs for dimensionality reduction.
            if "highly_variable" in self.adata.var:

                self.adata = self.adata[
                    :,
                    self.adata.var[
                        "highly_variable"
                    ],
                ].copy()

        if scale:
            self.scale()

        if pca:
            self.pca()

        if neighbors:
            self.compute_neighbors()

        if umap:
            self.umap()

        if leiden:
            self.leiden()

        logger.info(
            "Standard Scanpy pipeline completed."
        )

        return self.adata

    # ------------------------------------------------------------------
    # Visualization
    # ------------------------------------------------------------------

    def plot_qc(
        self,
        output_path: Optional[PathLike] = None,
    ) -> None:
        """
        Generate basic QC plots.
        """

        self._require_adata()

        if output_path is not None:
            output_path = Path(output_path)
            output_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

        sc.pl.violin(
            self.adata,
            [
                "n_genes_by_counts",
                "total_counts",
                "pct_counts_mt",
            ],
            multi_panel=True,
            show=output_path is None,
            save=None if output_path is None else "_qc.png",
        )

    def plot_umap(
        self,
        color: Optional[
            Union[str, Sequence[str]]
        ] = None,
        output_path: Optional[PathLike] = None,
        show: bool = True,
    ) -> None:
        """
        Plot UMAP.
        """

        self._require_adata()

        if "X_umap" not in self.adata.obsm:
            raise RuntimeError(
                "UMAP has not been computed. "
                "Run umap() first."
            )

        sc.pl.umap(
            self.adata,
            color=color,
            show=show if output_path is None else False,
        )

        if output_path is not None:
            import matplotlib.pyplot as plt

            output_path = Path(output_path)
            output_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            plt.savefig(
                output_path,
                dpi=300,
                bbox_inches="tight",
            )

            plt.close()

    # ------------------------------------------------------------------
    # Spatial transcriptomics helpers
    # ------------------------------------------------------------------

    def get_spatial_coordinates(
        self,
    ) -> Optional[np.ndarray]:
        """
        Return spatial coordinates if present.

        Checks:
        - adata.obsm["spatial"]
        """

        self._require_adata()

        if "spatial" not in self.adata.obsm:
            logger.warning(
                "No 'spatial' coordinates found in adata.obsm."
            )
            return None

        return np.asarray(
            self.adata.obsm["spatial"]
        )

    def has_spatial_data(self) -> bool:
        """
        Check whether spatial coordinates are available.
        """

        self._require_adata()

        return "spatial" in self.adata.obsm

    def plot_spatial(
        self,
        color: Optional[
            Union[str, Sequence[str]]
        ] = None,
        output_path: Optional[PathLike] = None,
        show: bool = True,
    ) -> None:
        """
        Plot spatial transcriptomics data.
        """

        self._require_adata()

        if not self.has_spatial_data():
            raise RuntimeError(
                "No spatial coordinates found."
            )

        sc.pl.spatial(
            self.adata,
            color=color,
            show=show if output_path is None else False,
        )

        if output_path is not None:
            import matplotlib.pyplot as plt

            output_path = Path(output_path)
            output_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            plt.savefig(
                output_path,
                dpi=300,
                bbox_inches="tight",
            )

            plt.close()

    # ------------------------------------------------------------------
    # Gene expression utilities
    # ------------------------------------------------------------------

    def expression_matrix(
        self,
        genes: Optional[Sequence[str]] = None,
        layer: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Return expression matrix as pandas DataFrame.

        Parameters
        ----------
        genes:
            Optional list of genes.

        layer:
            Optional AnnData layer.
        """

        self._require_adata()

        adata = self.adata

        if genes is not None:
            genes = [
                gene
                for gene in genes
                if gene in adata.var_names
            ]

            if not genes:
                raise ValueError(
                    "None of the requested genes exist."
                )

            adata = adata[:, genes]

        if layer is not None:
            matrix = adata.layers[layer]

        else:
            matrix = adata.X

        if hasattr(matrix, "toarray"):
            matrix = matrix.toarray()

        return pd.DataFrame(
            matrix,
            index=adata.obs_names,
            columns=adata.var_names,
        )

    def gene_expression(
        self,
        gene: str,
    ) -> pd.Series:
        """
        Return expression of one gene.
        """

        self._require_adata()

        if gene not in self.adata.var_names:
            raise KeyError(
                f"Gene '{gene}' not found."
            )

        values = self.adata[:, gene].X

        if hasattr(values, "toarray"):
            values = values.toarray()

        values = np.asarray(values).reshape(-1)

        return pd.Series(
            values,
            index=self.adata.obs_names,
            name=gene,
        )

    # ------------------------------------------------------------------
    # Subsetting
    # ------------------------------------------------------------------

    def subset(
        self,
        condition: Union[
            pd.Series,
            np.ndarray,
            Sequence[bool],
        ],
    ) -> ad.AnnData:
        """
        Return a filtered AnnData object.

        Does not modify the current dataset.
        """

        self._require_adata()

        condition = np.asarray(
            condition,
            dtype=bool,
        )

        if len(condition) != self.adata.n_obs:
            raise ValueError(
                "Condition length does not match number of cells."
            )

        return self.adata[
            condition
        ].copy()

    def subset_by_obs(
        self,
        column: str,
        values: Union[
            str,
            Iterable[str],
        ],
    ) -> ad.AnnData:
        """
        Subset cells based on an obs column.
        """

        self._require_adata()

        if column not in self.adata.obs.columns:
            raise KeyError(
                f"Column '{column}' not found in adata.obs."
            )

        if isinstance(values, str):
            values = [values]

        values = set(values)

        mask = self.adata.obs[
            column
        ].isin(values)

        return self.adata[
            mask
        ].copy()

    # ------------------------------------------------------------------
    # Metadata utilities
    # ------------------------------------------------------------------

    def add_metadata(
        self,
        metadata: pd.DataFrame,
        index_column: Optional[str] = None,
    ) -> ad.AnnData:
        """
        Merge external metadata into adata.obs.

        The metadata index must correspond to cell/barcode IDs unless
        index_column is supplied.
        """

        self._require_adata()

        metadata = metadata.copy()

        if index_column is not None:
            if index_column not in metadata.columns:
                raise KeyError(
                    f"Column '{index_column}' not found."
                )

            metadata = metadata.set_index(
                index_column
            )

        if not metadata.index.is_unique:
            raise ValueError(
                "Metadata index must be unique."
            )

        common = self.adata.obs_names.intersection(
            metadata.index
        )

        if len(common) == 0:
            raise ValueError(
                "No matching cell/barcode IDs found."
            )

        self.adata.obs = self.adata.obs.join(
            metadata,
            how="left",
        )

        logger.info(
            "Added metadata for %d cells.",
            len(common),
        )

        return self.adata

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate(self) -> dict:
        """
        Validate basic AnnData structure.
        """

        self._require_adata()

        report = {
            "valid": True,
            "n_obs": self.adata.n_obs,
            "n_vars": self.adata.n_vars,
            "has_X": self.adata.X is not None,
            "has_obs": self.adata.obs is not None,
            "has_var": self.adata.var is not None,
            "has_spatial": "spatial"
            in self.adata.obsm,
            "has_pca": "X_pca"
            in self.adata.obsm,
            "has_umap": "X_umap"
            in self.adata.obsm,
            "has_neighbors": (
                "connectivities"
                in self.adata.obsp
            ),
        }

        return report

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _require_adata(self) -> None:
        """
        Ensure that an AnnData object is loaded.
        """

        if self.adata is None:
            raise RuntimeError(
                "No AnnData dataset loaded. "
                "Call load() or assign self.adata first."
            )


# ---------------------------------------------------------------------------
# Convenience functions
# ---------------------------------------------------------------------------

def load_anndata(
    path: PathLike,
) -> ad.AnnData:
    """
    Convenience function for loading AnnData.
    """

    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(
            f"File not found: {path}"
        )

    return sc.read_h5ad(path)


def save_anndata(
    adata: ad.AnnData,
    path: PathLike,
) -> None:
    """
    Convenience function for saving AnnData.
    """

    path = Path(path)

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    adata.write_h5ad(path)


def create_model(
    config: Optional[ScanpyConfig] = None,
) -> ScanpyModel:
    """
    Factory function used by the rest of the project.
    """

    return ScanpyModel(
        config=config
    )


# ---------------------------------------------------------------------------
# Example
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    logging.basicConfig(
        level=logging.INFO,
        format=(
            "%(asctime)s | "
            "%(levelname)s | "
            "%(name)s | "
            "%(message)s"
        ),
    )

    # Example usage:
    #
    # model = ScanpyModel()
    #
    # model.load(
    #     "data/raw/rna/GSE130973/data.h5ad"
    # )
    #
    # model.print_summary()
    #
    # model.run_standard_pipeline()
    #
    # model.plot_umap(
    #     color=["leiden"],
    #     output_path="outputs/rna_analysis/umap.png",
    # )
    #
    # model.save(
    #     "data/processed/rna/GSE130973_processed.h5ad"
    # )

    logger.info(
        "scanpy_model.py loaded successfully."
    )