"""
human_cell_atlas.py

Human Cell Atlas (HCA) dataset interface.

Responsibilities
----------------
- Describe HCA datasets used by the project.
- Register local HCA datasets.
- Discover local files.
- Load common single-cell RNA-seq formats.
- Perform basic validation.
- Provide a unified representation for downstream pipelines.

This module does NOT:
- perform biological interpretation,
- train neural networks,
- calculate biological age,
- perform pathology classification.

Those responsibilities belong to other project modules.

Expected project structure
--------------------------

data/
└── raw/
    └── rna/
        └── human_cell_atlas/
            ├── metadata/
            ├── expression/
            └── raw/

The exact HCA dataset layout may differ between releases.
This module therefore supports flexible local file discovery.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple
import json
import logging

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------
# Optional dependencies
# ---------------------------------------------------------------------

try:
    import anndata as ad

    ANNDATA_AVAILABLE = True
except ImportError:
    ad = None
    ANNDATA_AVAILABLE = False


try:
    import scipy.sparse as sp

    SCIPY_AVAILABLE = True
except ImportError:
    sp = None
    SCIPY_AVAILABLE = False


# ---------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------
# Dataset configuration
# ---------------------------------------------------------------------

@dataclass
class HCADatasetConfig:
    """
    Configuration describing one Human Cell Atlas dataset.
    """

    name: str
    path: Path

    species: Optional[str] = None
    tissue: Optional[str] = None
    organ: Optional[str] = None
    disease: Optional[str] = None

    description: str = ""

    metadata_files: List[str] = field(default_factory=list)
    expression_files: List[str] = field(default_factory=list)

    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to a serializable dictionary.
        """

        return {
            "name": self.name,
            "path": str(self.path),
            "species": self.species,
            "tissue": self.tissue,
            "organ": self.organ,
            "disease": self.disease,
            "description": self.description,
            "metadata_files": self.metadata_files,
            "expression_files": self.expression_files,
            "tags": self.tags,
        }


@dataclass
class HCAData:
    """
    Unified representation of an HCA dataset.

    X
        Expression matrix.

    obs
        Cell-level metadata.

    var
        Gene-level metadata.

    uns
        Additional dataset information.
    """

    X: Any

    obs: pd.DataFrame
    var: pd.DataFrame

    uns: Dict[str, Any] = field(default_factory=dict)

    source_path: Optional[Path] = None

    def n_cells(self) -> int:
        return int(self.obs.shape[0])

    def n_genes(self) -> int:
        return int(self.var.shape[0])

    def shape(self) -> Tuple[int, int]:
        return self.n_cells(), self.n_genes()


# ---------------------------------------------------------------------
# Dataset registry
# ---------------------------------------------------------------------

class HCADatasetRegistry:
    """
    Registry of HCA datasets used by the project.
    """

    def __init__(self) -> None:
        self._datasets: Dict[str, HCADatasetConfig] = {}

    def register(self, dataset: HCADatasetConfig) -> None:
        """
        Register a dataset.
        """

        if dataset.name in self._datasets:
            logger.warning(
                "Replacing already registered HCA dataset: %s",
                dataset.name,
            )

        self._datasets[dataset.name] = dataset

    def get(self, name: str) -> HCADatasetConfig:
        """
        Retrieve dataset configuration by name.
        """

        if name not in self._datasets:
            raise KeyError(
                f"HCA dataset '{name}' is not registered. "
                f"Available datasets: {self.list_names()}"
            )

        return self._datasets[name]

    def list_names(self) -> List[str]:
        """
        Return registered dataset names.
        """

        return sorted(self._datasets.keys())

    def remove(self, name: str) -> None:
        """
        Remove a dataset from the registry.
        """

        if name in self._datasets:
            del self._datasets[name]

    def to_dict(self) -> Dict[str, Dict[str, Any]]:
        """
        Export registry.
        """

        return {
            name: dataset.to_dict()
            for name, dataset in self._datasets.items()
        }


# ---------------------------------------------------------------------
# Main HCA interface
# ---------------------------------------------------------------------

class HumanCellAtlas:
    """
    Main interface for Human Cell Atlas datasets.

    Example
    -------

    hca = HumanCellAtlas(
        root="data/raw/rna/human_cell_atlas"
    )

    datasets = hca.discover_datasets()

    data = hca.load(
        "skin_dataset"
    )
    """

    SUPPORTED_EXTENSIONS = {
        ".h5ad",
        ".csv",
        ".tsv",
        ".txt",
        ".mtx",
        ".h5",
    }

    def __init__(
        self,
        root: str | Path = "data/raw/rna/human_cell_atlas",
    ) -> None:

        self.root = Path(root)

        self.registry = HCADatasetRegistry()

        logger.info(
            "Initialized Human Cell Atlas interface: %s",
            self.root,
        )

    # -----------------------------------------------------------------
    # Directory management
    # -----------------------------------------------------------------

    def create_structure(self) -> None:
        """
        Create recommended HCA directory structure.
        """

        directories = [
            self.root,
            self.root / "metadata",
            self.root / "expression",
            self.root / "raw",
        ]

        for directory in directories:
            directory.mkdir(
                parents=True,
                exist_ok=True,
            )

        logger.info(
            "HCA directory structure created at %s",
            self.root,
        )

    # -----------------------------------------------------------------
    # Dataset discovery
    # -----------------------------------------------------------------

    def discover_files(self) -> List[Path]:
        """
        Discover supported files inside the HCA directory.
        """

        if not self.root.exists():
            logger.warning(
                "HCA root does not exist: %s",
                self.root,
            )
            return []

        files = []

        for path in self.root.rglob("*"):

            if not path.is_file():
                continue

            if path.suffix.lower() in self.SUPPORTED_EXTENSIONS:
                files.append(path)

        return sorted(files)

    def discover_datasets(self) -> Dict[str, List[Path]]:
        """
        Group discovered files by their parent directory.

        This is intentionally flexible because HCA releases can
        have different directory layouts.
        """

        files = self.discover_files()

        datasets: Dict[str, List[Path]] = {}

        for file_path in files:

            relative = file_path.relative_to(self.root)

            if len(relative.parts) <= 1:
                dataset_name = file_path.stem
            else:
                dataset_name = relative.parts[0]

            datasets.setdefault(
                dataset_name,
                [],
            ).append(file_path)

        return datasets

    # -----------------------------------------------------------------
    # Registration
    # -----------------------------------------------------------------

    def register_dataset(
        self,
        name: str,
        path: str | Path,
        *,
        species: Optional[str] = None,
        tissue: Optional[str] = None,
        organ: Optional[str] = None,
        disease: Optional[str] = None,
        description: str = "",
        tags: Optional[Sequence[str]] = None,
    ) -> HCADatasetConfig:
        """
        Register a local HCA dataset.
        """

        dataset_path = Path(path)

        if not dataset_path.is_absolute():
            dataset_path = self.root / dataset_path

        config = HCADatasetConfig(
            name=name,
            path=dataset_path,
            species=species,
            tissue=tissue,
            organ=organ,
            disease=disease,
            description=description,
            tags=list(tags or []),
        )

        self.registry.register(config)

        return config

    # -----------------------------------------------------------------
    # File identification
    # -----------------------------------------------------------------

    @staticmethod
    def _is_metadata_file(path: Path) -> bool:
        """
        Heuristic metadata-file detection.
        """

        name = path.name.lower()

        metadata_keywords = [
            "metadata",
            "obs",
            "cell",
            "sample",
            "annotation",
            "annotations",
        ]

        return any(
            keyword in name
            for keyword in metadata_keywords
        )

    @staticmethod
    def _is_expression_file(path: Path) -> bool:
        """
        Heuristic expression-file detection.
        """

        name = path.name.lower()

        expression_keywords = [
            "expression",
            "matrix",
            "counts",
            "normalized",
            "raw",
        ]

        return any(
            keyword in name
            for keyword in expression_keywords
        )

    def identify_files(
        self,
        dataset_path: str | Path,
    ) -> Dict[str, List[Path]]:
        """
        Identify likely expression and metadata files.
        """

        path = Path(dataset_path)

        if not path.is_absolute():
            path = self.root / path

        if not path.exists():
            raise FileNotFoundError(
                f"HCA dataset path does not exist: {path}"
            )

        files = []

        if path.is_file():
            files = [path]
        else:
            files = [
                p
                for p in path.rglob("*")
                if p.is_file()
            ]

        metadata = []
        expression = []
        other = []

        for file_path in files:

            if file_path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
                continue

            if self._is_metadata_file(file_path):
                metadata.append(file_path)

            elif self._is_expression_file(file_path):
                expression.append(file_path)

            else:
                other.append(file_path)

        return {
            "metadata": sorted(metadata),
            "expression": sorted(expression),
            "other": sorted(other),
        }

    # -----------------------------------------------------------------
    # Generic table loading
    # -----------------------------------------------------------------

    @staticmethod
    def _read_table(
        path: Path,
        *,
        index_col: Optional[int | str] = None,
    ) -> pd.DataFrame:
        """
        Read CSV/TSV/TXT table.
        """

        suffix = path.suffix.lower()

        if suffix == ".csv":

            return pd.read_csv(
                path,
                index_col=index_col,
            )

        if suffix in {".tsv", ".txt"}:

            return pd.read_csv(
                path,
                sep="\t",
                index_col=index_col,
            )

        raise ValueError(
            f"Unsupported table format: {path}"
        )

    # -----------------------------------------------------------------
    # AnnData loading
    # -----------------------------------------------------------------

    def load_h5ad(
        self,
        path: str | Path,
    ) -> HCAData:
        """
        Load an AnnData .h5ad file.

        This is the preferred format for modern single-cell RNA-seq
        workflows.
        """

        if not ANNDATA_AVAILABLE:
            raise ImportError(
                "anndata is required to load .h5ad files. "
                "Install it with: pip install anndata"
            )

        path = Path(path)

        if not path.exists():
            raise FileNotFoundError(path)

        logger.info(
            "Loading HCA AnnData: %s",
            path,
        )

        adata = ad.read_h5ad(path)

        uns = dict(adata.uns)

        uns["source"] = str(path)
        uns["n_cells"] = int(adata.n_obs)
        uns["n_genes"] = int(adata.n_vars)

        return HCAData(
            X=adata.X,
            obs=adata.obs.copy(),
            var=adata.var.copy(),
            uns=uns,
            source_path=path,
        )

    # -----------------------------------------------------------------
    # Matrix Market loading
    # -----------------------------------------------------------------

    def load_matrix_market(
        self,
        matrix_path: str | Path,
        *,
        obs_path: Optional[str | Path] = None,
        var_path: Optional[str | Path] = None,
        transpose: bool = False,
    ) -> HCAData:
        """
        Load a Matrix Market expression matrix.

        Typical 10x / single-cell layout:

            matrix.mtx
            barcodes.tsv
            features.tsv

        Matrix Market files often use:

            genes x cells

        while AnnData convention is:

            cells x genes

        Therefore transpose=True is often appropriate.
        """

        if not SCIPY_AVAILABLE:
            raise ImportError(
                "scipy is required for Matrix Market files."
            )

        matrix_path = Path(matrix_path)

        if not matrix_path.exists():
            raise FileNotFoundError(matrix_path)

        logger.info(
            "Loading Matrix Market file: %s",
            matrix_path,
        )

        matrix = sp.io.mmread(
            matrix_path
        )

        if transpose:
            matrix = matrix.T

        # -------------------------------------------------------------
        # Cell metadata
        # -------------------------------------------------------------

        if obs_path is not None:

            obs = self._read_table(
                Path(obs_path),
                index_col=0,
            )

        else:

            obs = pd.DataFrame(
                index=[
                    f"cell_{i}"
                    for i in range(matrix.shape[0])
                ]
            )

        # -------------------------------------------------------------
        # Gene metadata
        # -------------------------------------------------------------

        if var_path is not None:

            var = self._read_table(
                Path(var_path),
                index_col=0,
            )

        else:

            var = pd.DataFrame(
                index=[
                    f"gene_{i}"
                    for i in range(matrix.shape[1])
                ]
            )

        # -------------------------------------------------------------
        # Validate dimensions
        # -------------------------------------------------------------

        if matrix.shape[0] != len(obs):

            raise ValueError(
                "Number of cells in matrix does not match "
                f"obs metadata: {matrix.shape[0]} vs {len(obs)}"
            )

        if matrix.shape[1] != len(var):

            raise ValueError(
                "Number of genes in matrix does not match "
                f"var metadata: {matrix.shape[1]} vs {len(var)}"
            )

        return HCAData(
            X=matrix,
            obs=obs,
            var=var,
            uns={
                "source": str(matrix_path),
                "format": "matrix_market",
            },
            source_path=matrix_path,
        )

    # -----------------------------------------------------------------
    # CSV / TSV expression loading
    # -----------------------------------------------------------------

    def load_expression_table(
        self,
        path: str | Path,
        *,
        genes_in_rows: bool = True,
    ) -> HCAData:
        """
        Load a simple expression matrix.

        Parameters
        ----------
        path:
            CSV/TSV/TXT expression file.

        genes_in_rows:
            If True, rows correspond to genes and columns to cells.

            If False, rows correspond to cells and columns to genes.
        """

        path = Path(path)

        if not path.exists():
            raise FileNotFoundError(path)

        logger.info(
            "Loading expression table: %s",
            path,
        )

        df = self._read_table(
            path,
            index_col=0,
        )

        if genes_in_rows:

            X = df.to_numpy()

            var = pd.DataFrame(
                index=df.index.astype(str)
            )

            obs = pd.DataFrame(
                index=df.columns.astype(str)
            )

            X = X.T

        else:

            X = df.to_numpy()

            obs = pd.DataFrame(
                index=df.index.astype(str)
            )

            var = pd.DataFrame(
                index=df.columns.astype(str)
            )

        return HCAData(
            X=X,
            obs=obs,
            var=var,
            uns={
                "source": str(path),
                "format": "table",
            },
            source_path=path,
        )

    # -----------------------------------------------------------------
    # Automatic loader
    # -----------------------------------------------------------------

    def load(
        self,
        path_or_name: str | Path,
        **kwargs: Any,
    ) -> HCAData:
        """
        Automatically load an HCA dataset.

        Supports:
            .h5ad
            .csv
            .tsv
            .txt
            .mtx
        """

        # -------------------------------------------------------------
        # Registered dataset
        # -------------------------------------------------------------

        if isinstance(path_or_name, str):

            if path_or_name in self.registry.list_names():

                path = self.registry.get(
                    path_or_name
                ).path

            else:

                path = Path(path_or_name)

        else:

            path = Path(path_or_name)

        # -------------------------------------------------------------
        # Relative path handling
        # -------------------------------------------------------------

        if not path.is_absolute():

            candidate = self.root / path

            if candidate.exists():
                path = candidate

        # -------------------------------------------------------------
        # Directory
        # -------------------------------------------------------------

        if path.is_dir():

            files = self.identify_files(path)

            h5ad_files = [
                p
                for p in (
                    files["expression"]
                    + files["other"]
                )
                if p.suffix.lower() == ".h5ad"
            ]

            if h5ad_files:

                return self.load_h5ad(
                    h5ad_files[0]
                )

            raise ValueError(
                f"Could not automatically determine how to load "
                f"HCA dataset directory: {path}"
            )

        # -------------------------------------------------------------
        # File
        # -------------------------------------------------------------

        suffix = path.suffix.lower()

        if suffix == ".h5ad":

            return self.load_h5ad(
                path
            )

        if suffix == ".mtx":

            return self.load_matrix_market(
                path,
                **kwargs,
            )

        if suffix in {
            ".csv",
            ".tsv",
            ".txt",
        }:

            return self.load_expression_table(
                path,
                **kwargs,
            )

        raise ValueError(
            f"Unsupported HCA file format: {path}"
        )

    # -----------------------------------------------------------------
    # Validation
    # -----------------------------------------------------------------

    @staticmethod
    def validate(
        data: HCAData,
        *,
        require_unique_cell_ids: bool = True,
        require_unique_gene_ids: bool = True,
    ) -> Dict[str, Any]:
        """
        Validate an HCA dataset.

        Returns
        -------
        dict
            Validation report.
        """

        report: Dict[str, Any] = {
            "valid": True,
            "n_cells": data.n_cells(),
            "n_genes": data.n_genes(),
            "shape": data.shape(),
            "issues": [],
        }

        # -------------------------------------------------------------
        # Empty dataset
        # -------------------------------------------------------------

        if data.n_cells() == 0:

            report["valid"] = False
            report["issues"].append(
                "Dataset contains zero cells."
            )

        if data.n_genes() == 0:

            report["valid"] = False
            report["issues"].append(
                "Dataset contains zero genes."
            )

        # -------------------------------------------------------------
        # Dimension consistency
        # -------------------------------------------------------------

        try:

            if data.X.shape != data.shape():

                report["valid"] = False

                report["issues"].append(
                    f"Expression matrix shape {data.X.shape} "
                    f"does not match expected {data.shape()}."
                )

        except AttributeError:

            report["valid"] = False

            report["issues"].append(
                "Expression matrix has no shape attribute."
            )

        # -------------------------------------------------------------
        # Cell IDs
        # -------------------------------------------------------------

        if require_unique_cell_ids:

            if not data.obs.index.is_unique:

                report["valid"] = False

                report["issues"].append(
                    "Cell identifiers are not unique."
                )

        # -------------------------------------------------------------
        # Gene IDs
        # -------------------------------------------------------------

        if require_unique_gene_ids:

            if not data.var.index.is_unique:

                report["valid"] = False

                report["issues"].append(
                    "Gene identifiers are not unique."
                )

        return report

    # -----------------------------------------------------------------
    # Dataset statistics
    # -----------------------------------------------------------------

    @staticmethod
    def statistics(
        data: HCAData,
    ) -> Dict[str, Any]:
        """
        Calculate basic dataset statistics.
        """

        X = data.X

        stats: Dict[str, Any] = {
            "n_cells": data.n_cells(),
            "n_genes": data.n_genes(),
        }

        # -------------------------------------------------------------
        # Sparse matrix
        # -------------------------------------------------------------

        if SCIPY_AVAILABLE and sp.issparse(X):

            stats["nonzero_values"] = int(
                X.nnz
            )

            total_values = (
                X.shape[0]
                * X.shape[1]
            )

            stats["sparsity"] = float(
                1.0
                - (
                    X.nnz
                    / total_values
                )
            )

            stats["density"] = float(
                X.nnz
                / total_values
            )

            return stats

        # -------------------------------------------------------------
        # Dense matrix
        # -------------------------------------------------------------

        array = np.asarray(X)

        stats["nonzero_values"] = int(
            np.count_nonzero(array)
        )

        total_values = array.size

        if total_values > 0:

            stats["sparsity"] = float(
                1.0
                - (
                    np.count_nonzero(array)
                    / total_values
                )
            )

            stats["density"] = float(
                np.count_nonzero(array)
                / total_values
            )

        else:

            stats["sparsity"] = 0.0
            stats["density"] = 0.0

        return stats

    # -----------------------------------------------------------------
    # Metadata helpers
    # -----------------------------------------------------------------

    @staticmethod
    def find_metadata_columns(
        data: HCAData,
        keywords: Sequence[str],
    ) -> List[str]:
        """
        Find metadata columns containing selected keywords.
        """

        columns = []

        normalized_keywords = [
            keyword.lower()
            for keyword in keywords
        ]

        for column in data.obs.columns:

            column_name = str(column).lower()

            if any(
                keyword in column_name
                for keyword in normalized_keywords
            ):
                columns.append(
                    str(column)
                )

        return columns

    def find_cell_type_columns(
        self,
        data: HCAData,
    ) -> List[str]:
        """
        Find likely cell-type annotation columns.
        """

        return self.find_metadata_columns(
            data,
            keywords=[
                "cell_type",
                "celltype",
                "cell type",
                "annotation",
                "cluster",
                "major_type",
                "minor_type",
            ],
        )

    def find_tissue_columns(
        self,
        data: HCAData,
    ) -> List[str]:
        """
        Find likely tissue annotation columns.
        """

        return self.find_metadata_columns(
            data,
            keywords=[
                "tissue",
                "organ",
                "anatomy",
                "site",
                "location",
            ],
        )

    # -----------------------------------------------------------------
    # Filtering
    # -----------------------------------------------------------------

    @staticmethod
    def filter_cells(
        data: HCAData,
        *,
        column: str,
        values: Iterable[Any],
    ) -> HCAData:
        """
        Filter cells based on metadata.

        Example
        -------

        data = hca.filter_cells(
            data,
            column="cell_type",
            values=["fibroblast", "keratinocyte"]
        )
        """

        if column not in data.obs.columns:

            raise KeyError(
                f"Column '{column}' not found in cell metadata."
            )

        values = set(values)

        mask = data.obs[column].isin(
            values
        ).to_numpy()

        X = data.X[mask]

        obs = data.obs.loc[
            mask
        ].copy()

        return HCAData(
            X=X,
            obs=obs,
            var=data.var.copy(),
            uns={
                **data.uns,
                "filtered_by": column,
                "filter_values": list(values),
            },
            source_path=data.source_path,
        )

    # -----------------------------------------------------------------
    # Export
    # -----------------------------------------------------------------

    @staticmethod
    def save_registry(
        registry: HCADatasetRegistry,
        path: str | Path,
    ) -> None:
        """
        Save HCA dataset registry as JSON.
        """

        path = Path(path)

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with path.open(
            "w",
            encoding="utf-8",
        ) as f:

            json.dump(
                registry.to_dict(),
                f,
                indent=2,
                ensure_ascii=False,
            )

        logger.info(
            "HCA registry saved to %s",
            path,
        )

    # -----------------------------------------------------------------
    # Summary
    # -----------------------------------------------------------------

    def summary(
        self,
    ) -> Dict[str, Any]:
        """
        Return a summary of the HCA data available locally.
        """

        files = self.discover_files()

        datasets = self.discover_datasets()

        return {
            "root": str(self.root),
            "root_exists": self.root.exists(),
            "num_files": len(files),
            "num_discovered_datasets": len(datasets),
            "datasets": {
                name: [
                    str(path)
                    for path in paths
                ]
                for name, paths in datasets.items()
            },
            "registered_datasets": (
                self.registry.list_names()
            ),
        }


# ---------------------------------------------------------------------
# Default factory
# ---------------------------------------------------------------------

def create_hca_interface(
    root: str | Path = "data/raw/rna/human_cell_atlas",
) -> HumanCellAtlas:
    """
    Create a configured HCA interface.
    """

    hca = HumanCellAtlas(
        root=root
    )

    return hca


# ---------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------

def main() -> None:
    """
    Simple command-line diagnostic.
    """

    logging.basicConfig(
        level=logging.INFO,
        format=(
            "%(asctime)s | "
            "%(levelname)s | "
            "%(name)s | "
            "%(message)s"
        ),
    )

    hca = create_hca_interface()

    hca.create_structure()

    summary = hca.summary()

    print()
    print("=" * 70)
    print("Human Cell Atlas")
    print("=" * 70)

    print(
        f"Root: {summary['root']}"
    )

    print(
        f"Root exists: {summary['root_exists']}"
    )

    print(
        f"Files discovered: {summary['num_files']}"
    )

    print(
        f"Datasets discovered: "
        f"{summary['num_discovered_datasets']}"
    )

    print()

    if summary["datasets"]:

        print("Datasets:")

        for name, files in summary["datasets"].items():

            print(
                f"  - {name}: "
                f"{len(files)} files"
            )

    else:

        print(
            "No HCA datasets found yet."
        )

    print()
    print("=" * 70)


if __name__ == "__main__":
    main()