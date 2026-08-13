# rna_pipeline.py

"""
RNA Pipeline

Pipeline odpowiedzialny za przygotowanie danych transcriptomicznych.

Obsługiwane źródła:
    - GSE130973
    - GSE281449
    - GSE226189
    - spatial_skin_atlas
    - TCGA-SKCM

Główne zadania:
    1. wczytanie macierzy ekspresji,
    2. standaryzacja orientacji danych,
    3. kontrola jakości,
    4. filtrowanie genów/komórek,
    5. normalizacja,
    6. log-transformacja,
    7. opcjonalna selekcja highly variable genes,
    8. PCA,
    9. przygotowanie embeddingu RNA,
    10. zapis wyników do data/processed/rna/.

Pipeline nie wykonuje właściwego modelowania biologicznego.
Za modelowanie RNA odpowiada scanpy_model.py.
Za integrację z innymi modalnościami odpowiada multimodal_pipeline.py.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import json
import warnings

import numpy as np
import pandas as pd


# ============================================================
# OPTIONAL DEPENDENCIES
# ============================================================

try:
    import scanpy as sc

    SCANPY_AVAILABLE = True

except ImportError:
    sc = None
    SCANPY_AVAILABLE = False


try:
    import anndata as ad

    ANNDATA_AVAILABLE = True

except ImportError:
    ad = None
    ANNDATA_AVAILABLE = False


# ============================================================
# CONFIGURATION
# ============================================================

@dataclass
class RNAConfig:
    """
    Configuration for RNA preprocessing.
    """

    # Minimum quality thresholds.
    min_genes_per_cell: int = 200
    max_genes_per_cell: Optional[int] = None

    min_cells_per_gene: int = 3

    # Mitochondrial filtering.
    max_mito_percent: Optional[float] = 20.0

    # Ribosomal / hemoglobin filtering is optional.
    calculate_ribo: bool = True
    calculate_hb: bool = False

    # Normalization.
    target_sum: float = 1e4
    log_transform: bool = True

    # Highly variable genes.
    select_hvg: bool = True
    n_top_genes: int = 2000

    # PCA.
    run_pca: bool = True
    n_pcs: int = 50

    # Embedding.
    embedding_dim: int = 512

    # Random seed.
    random_state: int = 42

    # Sparse matrix preference.
    use_sparse: bool = True

    # Numerical stability.
    eps: float = 1e-8


# ============================================================
# RESULT CONTAINERS
# ============================================================

@dataclass
class RNAQCReport:
    """
    Quality-control summary.
    """

    n_cells_before: int = 0
    n_cells_after: int = 0

    n_genes_before: int = 0
    n_genes_after: int = 0

    median_genes_per_cell: float = 0.0
    median_counts_per_cell: float = 0.0

    median_mito_percent: Optional[float] = None

    filtered_cells: int = 0
    filtered_genes: int = 0

    warnings: List[str] = field(
        default_factory=list
    )


@dataclass
class RNAEmbedding:
    """
    RNA representation prepared for downstream fusion.
    """

    sample_id: str

    embedding: np.ndarray

    n_cells: int
    n_genes: int

    n_hvg: int

    explained_variance: Optional[np.ndarray] = None

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )


@dataclass
class RNAPipelineResult:
    """
    Complete output of RNA pipeline.
    """

    sample_id: str

    adata: Optional[Any]

    embedding: Optional[np.ndarray]

    qc: RNAQCReport

    genes: List[str]

    hvg_genes: List[str]

    pca: Optional[np.ndarray]

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def _require_scanpy() -> None:
    """
    Ensure Scanpy is available.
    """

    if not SCANPY_AVAILABLE:

        raise ImportError(
            "Scanpy is required for this operation. "
            "Install it with: pip install scanpy"
        )


def _to_dense(
    matrix: Any,
) -> np.ndarray:
    """
    Convert sparse/dense matrix to numpy.
    """

    if hasattr(matrix, "toarray"):
        return matrix.toarray()

    return np.asarray(matrix)


def _safe_float(
    value: Any,
) -> Optional[float]:
    """
    Convert value to float safely.
    """

    if value is None:
        return None

    try:
        return float(value)

    except Exception:
        return None


def _standardize_gene_names(
    genes: Sequence[str],
) -> List[str]:
    """
    Standardize gene names.

    This function intentionally does not aggressively
    modify gene symbols.
    """

    result = []

    for gene in genes:

        gene = str(gene).strip()

        if not gene:
            gene = "UNKNOWN"

        result.append(gene)

    return result


def _make_unique_names(
    names: Sequence[str],
) -> List[str]:
    """
    Make duplicated names unique.
    """

    counts: Dict[str, int] = {}

    result = []

    for name in names:

        name = str(name)

        if name not in counts:

            counts[name] = 0
            result.append(name)

        else:

            counts[name] += 1

            result.append(
                f"{name}-{counts[name]}"
            )

    return result


# ============================================================
# RNA PIPELINE
# ============================================================

class RNAPipeline:
    """
    Main RNA preprocessing pipeline.
    """

    def __init__(
        self,
        config: Optional[RNAConfig] = None,
    ):

        self.config = (
            config
            or RNAConfig()
        )

    # --------------------------------------------------------
    # LOAD CSV / TSV
    # --------------------------------------------------------

    def load_table(
        self,
        path: str | Path,
        sep: Optional[str] = None,
        index_col: int = 0,
    ) -> pd.DataFrame:
        """
        Load expression matrix from CSV/TSV.

        Expected structure:

                cell_1  cell_2  cell_3
        GeneA      ...
        GeneB      ...
        GeneC      ...

        or:

                GeneA GeneB GeneC
        cell_1
        cell_2
        cell_3

        Orientation is handled later.
        """

        path = Path(path)

        if not path.exists():

            raise FileNotFoundError(
                f"RNA file not found: {path}"
            )

        if sep is None:

            if path.suffix.lower() == ".csv":
                sep = ","

            else:
                sep = "\t"

        return pd.read_csv(
            path,
            sep=sep,
            index_col=index_col,
        )

    # --------------------------------------------------------
    # ORIENTATION
    # --------------------------------------------------------

    def orient_expression_matrix(
        self,
        expression: pd.DataFrame,
        genes_as_rows: bool = True,
    ) -> pd.DataFrame:
        """
        Ensure:

            rows    = cells/samples
            columns = genes

        If genes_as_rows=True, transpose the input.
        """

        if not isinstance(
            expression,
            pd.DataFrame,
        ):

            raise TypeError(
                "expression must be pandas.DataFrame"
            )

        if genes_as_rows:

            expression = expression.T

        expression.index = (
            expression.index.astype(str)
        )

        expression.columns = (
            expression.columns.astype(str)
        )

        expression.columns = (
            _standardize_gene_names(
                expression.columns
            )
        )

        expression.columns = (
            _make_unique_names(
                expression.columns
            )
        )

        return expression

    # --------------------------------------------------------
    # DATAFRAME -> ANNDATA
    # --------------------------------------------------------

    def dataframe_to_anndata(
        self,
        expression: pd.DataFrame,
        sample_id: str = "sample",
    ):
        """
        Convert expression matrix into AnnData.

        Expected:

            rows    = cells
            columns = genes
        """

        _require_scanpy()

        expression = expression.copy()

        expression = expression.apply(
            pd.to_numeric,
            errors="coerce",
        )

        expression = expression.fillna(
            0.0
        )

        expression = expression.clip(
            lower=0.0
        )

        adata = sc.AnnData(
            expression.astype(
                np.float32
            )
        )

        adata.obs_names = (
            expression.index.astype(str)
        )

        adata.var_names = (
            expression.columns.astype(str)
        )

        adata.obs[
            "dataset"
        ] = sample_id

        adata.var[
            "gene_symbol"
        ] = adata.var_names

        return adata

    # --------------------------------------------------------
    # LOAD H5AD
    # --------------------------------------------------------

    def load_h5ad(
        self,
        path: str | Path,
    ):
        """
        Load AnnData .h5ad file.
        """

        _require_scanpy()

        path = Path(path)

        if not path.exists():

            raise FileNotFoundError(
                f"AnnData file not found: {path}"
            )

        return sc.read_h5ad(
            path
        )

    # --------------------------------------------------------
    # QC METRICS
    # --------------------------------------------------------

    def calculate_qc_metrics(
        self,
        adata,
    ) -> RNAQCReport:
        """
        Calculate basic RNA QC metrics.
        """

        _require_scanpy()

        report = RNAQCReport()

        report.n_cells_before = (
            adata.n_obs
        )

        report.n_genes_before = (
            adata.n_vars
        )

        # ----------------------------------------------------
        # Mitochondrial genes
        # ----------------------------------------------------

        gene_names = (
            adata.var_names.astype(str)
        )

        mito_mask = np.array(
            [
                gene.upper().startswith("MT-")
                or gene.upper().startswith("MT.")
                for gene in gene_names
            ]
        )

        adata.var[
            "mt"
        ] = mito_mask

        # ----------------------------------------------------
        # Ribosomal genes
        # ----------------------------------------------------

        if self.config.calculate_ribo:

            ribo_mask = np.array(
                [
                    gene.upper().startswith(
                        ("RPS", "RPL")
                    )
                    for gene in gene_names
                ]
            )

            adata.var[
                "ribo"
            ] = ribo_mask

        # ----------------------------------------------------
        # Hemoglobin genes
        # ----------------------------------------------------

        if self.config.calculate_hb:

            hb_mask = np.array(
                [
                    gene.upper().startswith(
                        (
                            "HBA",
                            "HBB",
                        )
                    )
                    for gene in gene_names
                ]
            )

            adata.var[
                "hb"
            ] = hb_mask

        # ----------------------------------------------------
        # Scanpy QC
        # ----------------------------------------------------

        sc.pp.calculate_qc_metrics(
            adata,
            qc_vars=[
                "mt"
            ],
            inplace=True,
        )

        report.median_genes_per_cell = float(
            np.median(
                adata.obs[
                    "n_genes_by_counts"
                ].values
            )
        )

        report.median_counts_per_cell = float(
            np.median(
                adata.obs[
                    "total_counts"
                ].values
            )
        )

        if (
            "pct_counts_mt"
            in adata.obs.columns
        ):

            report.median_mito_percent = float(
                np.median(
                    adata.obs[
                        "pct_counts_mt"
                    ].values
                )
            )

        return report

    # --------------------------------------------------------
    # FILTER GENES
    # --------------------------------------------------------

    def filter_genes(
        self,
        adata,
    ):
        """
        Remove genes expressed in too few cells.
        """

        _require_scanpy()

        before = adata.n_vars

        sc.pp.filter_genes(
            adata,
            min_cells=self.config.min_cells_per_gene,
        )

        removed = (
            before - adata.n_vars
        )

        return adata, removed

    # --------------------------------------------------------
    # FILTER CELLS
    # --------------------------------------------------------

    def filter_cells(
        self,
        adata,
    ):
        """
        Filter cells based on QC.
        """

        _require_scanpy()

        before = adata.n_obs

        sc.pp.filter_cells(
            adata,
            min_genes=self.config.min_genes_per_cell,
        )

        if (
            self.config.max_genes_per_cell
            is not None
        ):

            mask = (
                adata.obs[
                    "n_genes_by_counts"
                ]
                <= self.config.max_genes_per_cell
            )

            adata._inplace_subset_obs(
                mask
            )

        if (
            self.config.max_mito_percent
            is not None
            and "pct_counts_mt"
            in adata.obs.columns
        ):

            mask = (
                adata.obs[
                    "pct_counts_mt"
                ]
                <= self.config.max_mito_percent
            )

            adata._inplace_subset_obs(
                mask
            )

        removed = (
            before - adata.n_obs
        )

        return adata, removed

    # --------------------------------------------------------
    # NORMALIZATION
    # --------------------------------------------------------

    def normalize(
        self,
        adata,
    ):
        """
        Normalize counts per cell.
        """

        _require_scanpy()

        sc.pp.normalize_total(
            adata,
            target_sum=self.config.target_sum,
        )

        if self.config.log_transform:

            sc.pp.log1p(
                adata
            )

        return adata

    # --------------------------------------------------------
    # HIGHLY VARIABLE GENES
    # --------------------------------------------------------

    def select_hvg(
        self,
        adata,
    ):
        """
        Select highly variable genes.
        """

        _require_scanpy()

        if not self.config.select_hvg:

            adata.var[
                "highly_variable"
            ] = True

            return adata

        n_genes = adata.n_vars

        n_top = min(
            self.config.n_top_genes,
            n_genes,
        )

        if n_top < 1:

            raise ValueError(
                "No genes available for HVG selection."
            )

        sc.pp.highly_variable_genes(
            adata,
            n_top_genes=n_top,
            flavor="seurat",
        )

        adata = adata[
            :,
            adata.var[
                "highly_variable"
            ].values,
        ].copy()

        return adata

    # --------------------------------------------------------
    # PCA
    # --------------------------------------------------------

    def run_pca(
        self,
        adata,
    ) -> Tuple[Any, Optional[np.ndarray]]:
        """
        Run PCA and return:
            AnnData
            explained variance ratio
        """

        _require_scanpy()

        if not self.config.run_pca:

            return adata, None

        max_pcs = min(
            self.config.n_pcs,
            adata.n_obs - 1,
            adata.n_vars - 1,
        )

        if max_pcs < 1:

            warnings.warn(
                "Not enough dimensions for PCA."
            )

            return adata, None

        sc.tl.pca(
            adata,
            n_comps=max_pcs,
            random_state=self.config.random_state,
        )

        variance = (
            adata.uns[
                "pca"
            ][
                "variance_ratio"
            ]
        )

        return (
            adata,
            np.asarray(
                variance,
                dtype=np.float32,
            ),
        )

    # --------------------------------------------------------
    # PCA EMBEDDING
    # --------------------------------------------------------

    def build_embedding(
        self,
        adata,
    ) -> np.ndarray:
        """
        Convert PCA / expression data into a single
        sample-level RNA embedding.

        For single-cell data:

            cells x PCA dimensions

        are averaged over cells.

        For bulk data:

            the expression vector is directly represented.

        The final vector is adjusted to embedding_dim.
        """

        if self.config.run_pca and "X_pca" in adata.obsm:

            matrix = np.asarray(
                adata.obsm[
                    "X_pca"
                ],
                dtype=np.float32,
            )

        else:

            matrix = _to_dense(
                adata.X
            ).astype(
                np.float32
            )

        if matrix.ndim == 1:

            embedding = matrix

        else:

            embedding = np.nanmean(
                matrix,
                axis=0,
            )

        embedding = np.nan_to_num(
            embedding,
            nan=0.0,
            posinf=0.0,
            neginf=0.0,
        )

        # ----------------------------------------------------
        # L2 normalization
        # ----------------------------------------------------

        norm = np.linalg.norm(
            embedding
        )

        if norm > self.config.eps:

            embedding = (
                embedding / norm
            )

        # ----------------------------------------------------
        # Fixed embedding dimension
        # ----------------------------------------------------

        target = (
            self.config.embedding_dim
        )

        if embedding.shape[0] < target:

            padded = np.zeros(
                target,
                dtype=np.float32,
            )

            padded[
                : embedding.shape[0]
            ] = embedding

            embedding = padded

        elif embedding.shape[0] > target:

            embedding = (
                embedding[:target]
            )

        return embedding.astype(
            np.float32
        )

    # --------------------------------------------------------
    # COMPLETE PREPROCESSING
    # --------------------------------------------------------

    def preprocess(
        self,
        adata,
    ) -> Tuple[
        Any,
        RNAQCReport,
        Optional[np.ndarray],
    ]:
        """
        Execute complete preprocessing.
        """

        if adata is None:

            raise ValueError(
                "adata cannot be None."
            )

        qc = self.calculate_qc_metrics(
            adata
        )

        # ----------------------------------------------------
        # Filter genes
        # ----------------------------------------------------

        adata, removed_genes = (
            self.filter_genes(
                adata
            )
        )

        # ----------------------------------------------------
        # Recalculate QC
        # ----------------------------------------------------

        self.calculate_qc_metrics(
            adata
        )

        # ----------------------------------------------------
        # Filter cells
        # ----------------------------------------------------

        adata, removed_cells = (
            self.filter_cells(
                adata
            )
        )

        # ----------------------------------------------------
        # Final QC
        # ----------------------------------------------------

        final_qc = (
            self.calculate_qc_metrics(
                adata
            )
        )

        final_qc.filtered_genes = (
            removed_genes
        )

        final_qc.filtered_cells = (
            removed_cells
        )

        final_qc.n_cells_after = (
            adata.n_obs
        )

        final_qc.n_genes_after = (
            adata.n_vars
        )

        # ----------------------------------------------------
        # Normalize
        # ----------------------------------------------------

        adata = self.normalize(
            adata
        )

        # ----------------------------------------------------
        # HVG
        # ----------------------------------------------------

        adata = self.select_hvg(
            adata
        )

        # ----------------------------------------------------
        # PCA
        # ----------------------------------------------------

        adata, variance = self.run_pca(
            adata
        )

        return (
            adata,
            final_qc,
            variance,
        )

    # --------------------------------------------------------
    # FULL PIPELINE
    # --------------------------------------------------------

    def run(
        self,
        adata,
        sample_id: str,
        metadata: Optional[
            Dict[str, Any]
        ] = None,
    ) -> RNAPipelineResult:
        """
        Run complete RNA pipeline.
        """

        adata, qc, variance = (
            self.preprocess(
                adata
            )
        )

        embedding = (
            self.build_embedding(
                adata
            )
        )

        genes = [
            str(gene)
            for gene
            in adata.var_names
        ]

        if (
            "highly_variable"
            in adata.var.columns
        ):

            hvg_genes = [
                str(gene)
                for gene
                in adata.var_names[
                    adata.var[
                        "highly_variable"
                    ].values
                ]
            ]

        else:

            hvg_genes = genes.copy()

        pca = None

        if (
            "X_pca"
            in adata.obsm
        ):

            pca = np.asarray(
                adata.obsm[
                    "X_pca"
                ],
                dtype=np.float32,
            )

        result = RNAPipelineResult(
            sample_id=sample_id,
            adata=adata,
            embedding=embedding,
            qc=qc,
            genes=genes,
            hvg_genes=hvg_genes,
            pca=pca,
            metadata=metadata or {},
        )

        return result

    # --------------------------------------------------------
    # FILE-BASED PIPELINE
    # --------------------------------------------------------

    def run_from_table(
        self,
        path: str | Path,
        sample_id: str,
        genes_as_rows: bool = True,
        metadata: Optional[
            Dict[str, Any]
        ] = None,
    ) -> RNAPipelineResult:
        """
        Run pipeline directly from CSV/TSV.
        """

        expression = self.load_table(
            path
        )

        expression = (
            self.orient_expression_matrix(
                expression,
                genes_as_rows=genes_as_rows,
            )
        )

        adata = (
            self.dataframe_to_anndata(
                expression,
                sample_id=sample_id,
            )
        )

        return self.run(
            adata,
            sample_id=sample_id,
            metadata=metadata,
        )

    # --------------------------------------------------------
    # H5AD PIPELINE
    # --------------------------------------------------------

    def run_from_h5ad(
        self,
        path: str | Path,
        sample_id: str,
        metadata: Optional[
            Dict[str, Any]
        ] = None,
    ) -> RNAPipelineResult:
        """
        Run pipeline from .h5ad.
        """

        adata = self.load_h5ad(
            path
        )

        return self.run(
            adata,
            sample_id=sample_id,
            metadata=metadata,
        )

    # --------------------------------------------------------
    # SAVE PROCESSED DATA
    # --------------------------------------------------------

    def save_result(
        self,
        result: RNAPipelineResult,
        output_dir: str | Path,
    ) -> Dict[str, Path]:
        """
        Save processed RNA data.

        Output:

            sample.h5ad
            sample_embedding.npy
            sample_pca.npy
            sample_qc.json
        """

        output_dir = Path(
            output_dir
        )

        output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        paths: Dict[str, Path] = {}

        # ----------------------------------------------------
        # AnnData
        # ----------------------------------------------------

        if (
            result.adata is not None
            and ANNDATA_AVAILABLE
        ):

            h5ad_path = (
                output_dir
                / f"{result.sample_id}.h5ad"
            )

            result.adata.write_h5ad(
                h5ad_path
            )

            paths[
                "h5ad"
            ] = h5ad_path

        # ----------------------------------------------------
        # Embedding
        # ----------------------------------------------------

        if result.embedding is not None:

            embedding_path = (
                output_dir
                / f"{result.sample_id}_embedding.npy"
            )

            np.save(
                embedding_path,
                result.embedding,
            )

            paths[
                "embedding"
            ] = embedding_path

        # ----------------------------------------------------
        # PCA
        # ----------------------------------------------------

        if result.pca is not None:

            pca_path = (
                output_dir
                / f"{result.sample_id}_pca.npy"
            )

            np.save(
                pca_path,
                result.pca,
            )

            paths[
                "pca"
            ] = pca_path

        # ----------------------------------------------------
        # QC
        # ----------------------------------------------------

        qc_path = (
            output_dir
            / f"{result.sample_id}_qc.json"
        )

        qc_data = {
            "n_cells_before":
                result.qc.n_cells_before,

            "n_cells_after":
                result.qc.n_cells_after,

            "n_genes_before":
                result.qc.n_genes_before,

            "n_genes_after":
                result.qc.n_genes_after,

            "median_genes_per_cell":
                result.qc.median_genes_per_cell,

            "median_counts_per_cell":
                result.qc.median_counts_per_cell,

            "median_mito_percent":
                result.qc.median_mito_percent,

            "filtered_cells":
                result.qc.filtered_cells,

            "filtered_genes":
                result.qc.filtered_genes,

            "n_hvg":
                len(result.hvg_genes),

            "metadata":
                result.metadata,
        }

        with open(
            qc_path,
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                qc_data,
                file,
                indent=2,
                ensure_ascii=False,
            )

        paths[
            "qc"
        ] = qc_path

        return paths


# ============================================================
# DATASET-SPECIFIC HELPERS
# ============================================================

def detect_rna_dataset(
    path: str | Path,
) -> str:
    """
    Identify one of the project's RNA datasets
    from a file/path name.
    """

    path_string = str(
        path
    ).lower()

    if "gse130973" in path_string:
        return "GSE130973"

    if "gse281449" in path_string:
        return "GSE281449"

    if "gse226189" in path_string:
        return "GSE226189"

    if "spatial_skin_atlas" in path_string:
        return "spatial_skin_atlas"

    if "tcga-skcm" in path_string:
        return "TCGA-SKCM"

    return "unknown"


def get_dataset_metadata(
    dataset_name: str,
) -> Dict[str, Any]:
    """
    Return metadata describing the expected dataset.
    """

    metadata = {
        "GSE130973": {
            "type": "GEO",
            "modality": "RNA",
        },

        "GSE281449": {
            "type": "GEO",
            "modality": "RNA",
        },

        "GSE226189": {
            "type": "GEO",
            "modality": "RNA",
        },

        "spatial_skin_atlas": {
            "type": "spatial_transcriptomics",
            "modality": "RNA",
        },

        "TCGA-SKCM": {
            "type": "TCGA",
            "modality": "RNA",
        },
    }

    return metadata.get(
        dataset_name,
        {
            "type": "unknown",
            "modality": "RNA",
        },
    )


# ============================================================
# DEMONSTRATION
# ============================================================

def demo() -> None:
    """
    Demonstration using synthetic RNA data.

    This creates a small fake expression matrix,
    so no external dataset is required.
    """

    print("=" * 70)
    print("RNA Pipeline")
    print("=" * 70)

    # --------------------------------------------------------
    # Configuration
    # --------------------------------------------------------

    config = RNAConfig(
        min_genes_per_cell=5,
        min_cells_per_gene=2,
        max_mito_percent=50.0,
        select_hvg=True,
        n_top_genes=20,
        n_pcs=10,
        embedding_dim=512,
        random_state=42,
    )

    pipeline = RNAPipeline(
        config=config
    )

    # --------------------------------------------------------
    # Synthetic expression matrix
    #
    # rows    = genes
    # columns = cells
    # --------------------------------------------------------

    genes = [
        "COL1A1",
        "COL1A2",
        "KRT14",
        "KRT5",
        "KRT10",
        "TP53",
        "B2M",
        "MMP1",
        "MMP9",
        "MT-CO1",
        "MT-CO2",
        "RPLP0",
        "RPS18",
        "VIM",
        "ACTB",
        "GAPDH",
        "FN1",
        "EPCAM",
        "CD3D",
        "CD68",
        "TYR",
        "SOX10",
        "MLANA",
        "PMEL",
        "MITF",
    ]

    cells = [
        f"cell_{i:03d}"
        for i in range(30)
    ]

    rng = np.random.default_rng(
        config.random_state
    )

    matrix = rng.poisson(
        lam=5,
        size=(
            len(genes),
            len(cells),
        ),
    ).astype(
        np.float32
    )

    expression = pd.DataFrame(
        matrix,
        index=genes,
        columns=cells,
    )

    # --------------------------------------------------------
    # Convert orientation
    # --------------------------------------------------------

    expression = (
        pipeline.orient_expression_matrix(
            expression,
            genes_as_rows=True,
        )
    )

    # --------------------------------------------------------
    # AnnData
    # --------------------------------------------------------

    if not SCANPY_AVAILABLE:

        print(
            "\nScanpy is not installed."
        )

        print(
            "Install with:"
        )

        print(
            "pip install scanpy"
        )

        return

    adata = (
        pipeline.dataframe_to_anndata(
            expression,
            sample_id="demo_skin",
        )
    )

    # --------------------------------------------------------
    # Run
    # --------------------------------------------------------

    result = pipeline.run(
        adata,
        sample_id="demo_skin",
        metadata={
            "dataset": "synthetic",
            "tissue": "skin",
            "timepoint": "T0",
        },
    )

    # --------------------------------------------------------
    # Output
    # --------------------------------------------------------

    print(
        "\nDataset:",
        result.sample_id,
    )

    print(
        "\nCells before:",
        result.qc.n_cells_before,
    )

    print(
        "Cells after:",
        result.qc.n_cells_after,
    )

    print(
        "\nGenes before:",
        result.qc.n_genes_before,
    )

    print(
        "Genes after:",
        result.qc.n_genes_after,
    )

    print(
        "\nHVG genes:",
        result.hvg_genes[:10],
    )

    print(
        "\nEmbedding shape:",
        result.embedding.shape,
    )

    if result.pca is not None:

        print(
            "PCA matrix shape:",
            result.pca.shape,
        )

        print(
            "PCA components:",
            result.pca.shape[1],
        )

    if result.qc.median_mito_percent is not None:

        print(
            "\nMedian mitochondrial percentage:",
            f"{result.qc.median_mito_percent:.2f}%",
        )

    print(
        "\nRNA pipeline ready."
    )

    print("=" * 70)


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    demo()