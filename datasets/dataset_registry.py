"""
Dataset Registry
================

Central registry for all datasets used in the doctoral project.

Responsibilities
----------------
- Define a common representation of datasets.
- Register datasets used by the project.
- Provide dataset lookup by name.
- Validate dataset paths.
- Expose metadata needed by pipelines and training code.

This module does NOT:
- download datasets,
- preprocess images,
- process RNA,
- run model inference,
- train models.

Those responsibilities belong to pipeline/, models/, and training/.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


# ---------------------------------------------------------------------------
# Dataset description
# ---------------------------------------------------------------------------

@dataclass
class DatasetInfo:
    """
    Metadata describing one dataset.

    Parameters
    ----------
    name:
        Unique internal dataset name.

    path:
        Local filesystem path containing the dataset.

    modality:
        Main modality, e.g.:
        - image
        - wsi
        - rna
        - hand
        - multimodal

    description:
        Human-readable description.

    source:
        Original source of the dataset.

    url:
        Optional URL of the original dataset.

    task:
        Main intended task.

    license:
        Optional license/access information.

    tags:
        Additional searchable labels.

    optional:
        Whether the dataset is optional for the project.
    """

    name: str
    path: Path
    modality: str

    description: str = ""
    source: str = ""
    url: Optional[str] = None
    task: Optional[str] = None
    license: Optional[str] = None

    tags: List[str] = field(default_factory=list)

    optional: bool = False

    def exists(self) -> bool:
        """Return True if the dataset path exists."""
        return self.path.exists()

    def is_directory(self) -> bool:
        """Return True if the dataset path is a directory."""
        return self.path.is_dir()

    def validate(self) -> Dict[str, object]:
        """
        Validate the dataset location.

        Returns
        -------
        dict
            Validation report.
        """

        return {
            "name": self.name,
            "path": str(self.path),
            "exists": self.exists(),
            "is_directory": self.is_directory(),
            "valid": self.exists(),
        }

    def summary(self) -> str:
        """Return a compact human-readable description."""

        return (
            f"{self.name} | "
            f"modality={self.modality} | "
            f"path={self.path}"
        )


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

class DatasetRegistry:
    """
    Central registry containing all datasets used by the project.
    """

    def __init__(self) -> None:
        self._datasets: Dict[str, DatasetInfo] = {}

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(self, dataset: DatasetInfo) -> None:
        """
        Register a dataset.

        Raises
        ------
        ValueError
            If a dataset with the same name already exists.
        """

        if dataset.name in self._datasets:
            raise ValueError(
                f"Dataset '{dataset.name}' is already registered."
            )

        self._datasets[dataset.name] = dataset

    # ------------------------------------------------------------------
    # Lookup
    # ------------------------------------------------------------------

    def get(self, name: str) -> DatasetInfo:
        """
        Get dataset by name.

        Raises
        ------
        KeyError
            If dataset is not registered.
        """

        if name not in self._datasets:
            raise KeyError(
                f"Dataset '{name}' is not registered."
            )

        return self._datasets[name]

    def exists(self, name: str) -> bool:
        """Return True if dataset name exists in registry."""
        return name in self._datasets

    # ------------------------------------------------------------------
    # Collections
    # ------------------------------------------------------------------

    def all(self) -> List[DatasetInfo]:
        """Return all registered datasets."""
        return list(self._datasets.values())

    def names(self) -> List[str]:
        """Return names of all registered datasets."""
        return list(self._datasets.keys())

    def by_modality(self, modality: str) -> List[DatasetInfo]:
        """
        Return all datasets belonging to a modality.
        """

        modality = modality.lower()

        return [
            dataset
            for dataset in self._datasets.values()
            if dataset.modality.lower() == modality
        ]

    def by_tag(self, tag: str) -> List[DatasetInfo]:
        """Return all datasets containing a specific tag."""

        tag = tag.lower()

        return [
            dataset
            for dataset in self._datasets.values()
            if tag in [t.lower() for t in dataset.tags]
        ]

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate_all(self) -> Dict[str, Dict[str, object]]:
        """
        Validate all registered datasets.

        Returns
        -------
        dict
            Mapping dataset name -> validation report.
        """

        return {
            dataset.name: dataset.validate()
            for dataset in self._datasets.values()
        }

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------

    def summary(self) -> str:
        """Return a formatted registry summary."""

        lines = [
            "Dataset Registry",
            "=" * 80,
        ]

        for dataset in self._datasets.values():
            status = "OK" if dataset.exists() else "MISSING"

            lines.append(
                f"[{status}] "
                f"{dataset.name:<25} "
                f"{dataset.modality:<12} "
                f"{dataset.path}"
            )

        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------------------

def get_project_root() -> Path:
    """
    Determine project root.

    Expected structure:

        Doktorat_Kod/
        ├── datasets/
        ├── data/
        ├── models/
        └── ...

    This file is located in:

        Doktorat_Kod/datasets/dataset_registry.py
    """

    return Path(__file__).resolve().parents[1]


def get_raw_data_root() -> Path:
    """Return data/raw directory."""
    return get_project_root() / "data" / "raw"


# ---------------------------------------------------------------------------
# Default registry
# ---------------------------------------------------------------------------

def create_default_registry() -> DatasetRegistry:
    """
    Create registry containing the project's currently planned datasets.

    Missing datasets are allowed. They will simply be reported as MISSING
    until the corresponding data are downloaded.
    """

    raw = get_raw_data_root()

    registry = DatasetRegistry()

    # ================================================================
    # IMAGE DATASETS
    # ================================================================

    registry.register(
        DatasetInfo(
            name="skin_lesions_dataset",
            path=raw / "images" / "normal_skin" / "skin_lesions_dataset",
            modality="image",
            description=(
                "Skin lesion image dataset used for image-level "
                "analysis and lesion classification."
            ),
            source="Skin lesion dataset",
            task="skin lesion analysis",
            tags=[
                "skin",
                "lesion",
                "dermatology",
                "image",
            ],
        )
    )

    registry.register(
        DatasetInfo(
            name="ISIC",
            path=raw / "images" / "lesions" / "ISIC",
            modality="image",
            description=(
                "ISIC dermatology image collection."
            ),
            source="ISIC Archive",
            url="https://www.isic-archive.com/",
            task="lesion analysis",
            tags=[
                "skin",
                "lesion",
                "dermatology",
                "image",
                "melanoma",
            ],
        )
    )

    # ================================================================
    # WSI DATASETS
    # ================================================================

    registry.register(
        DatasetInfo(
            name="spatial_skin_atlas_wsi",
            path=raw / "wsi" / "normal" / "spatial_skin_atlas",
            modality="wsi",
            description=(
                "Spatial skin atlas histology / spatial tissue data "
                "used for tissue-level analysis."
            ),
            source="Spatial Skin Atlas",
            task="skin tissue analysis",
            tags=[
                "skin",
                "wsi",
                "histology",
                "spatial",
            ],
        )
    )

    registry.register(
        DatasetInfo(
            name="TCGA-SKCM-WIS",
            path=raw / "wsi" / "melanoma" / "TCGA-SKCM",
            modality="wsi",
            description=(
                "TCGA Skin Cutaneous Melanoma pathology slide data."
            ),
            source="Genomic Data Commons / TCGA",
            url="https://portal.gdc.cancer.gov/",
            task="melanoma pathology",
            tags=[
                "tcga",
                "skcm",
                "melanoma",
                "wsi",
                "pathology",
            ],
        )
    )

    # ================================================================
    # RNA DATASETS
    # ================================================================

    registry.register(
        DatasetInfo(
            name="GSE130973",
            path=raw / "rna" / "GSE130973",
            modality="rna",
            description="GEO RNA dataset GSE130973.",
            source="NCBI GEO",
            url="https://www.ncbi.nlm.nih.gov/geo/",
            task="skin transcriptomics",
            tags=[
                "geo",
                "rna",
                "transcriptomics",
                "skin",
            ],
        )
    )

    registry.register(
        DatasetInfo(
            name="GSE281449",
            path=raw / "rna" / "GSE281449",
            modality="rna",
            description="GEO RNA dataset GSE281449.",
            source="NCBI GEO",
            url="https://www.ncbi.nlm.nih.gov/geo/",
            task="skin transcriptomics",
            tags=[
                "geo",
                "rna",
                "transcriptomics",
                "skin",
            ],
        )
    )

    registry.register(
        DatasetInfo(
            name="GSE226189",
            path=raw / "rna" / "GSE226189",
            modality="rna",
            description="GEO RNA dataset GSE226189.",
            source="NCBI GEO",
            url="https://www.ncbi.nlm.nih.gov/geo/",
            task="skin transcriptomics",
            tags=[
                "geo",
                "rna",
                "transcriptomics",
                "skin",
            ],
        )
    )

    registry.register(
        DatasetInfo(
            name="spatial_skin_atlas_rna",
            path=raw / "rna" / "spatial_skin_atlas",
            modality="rna",
            description=(
                "Spatial transcriptomics data associated with "
                "the skin atlas."
            ),
            source="Spatial Skin Atlas",
            task="spatial transcriptomics",
            tags=[
                "spatial",
                "rna",
                "transcriptomics",
                "skin",
            ],
        )
    )

    registry.register(
        DatasetInfo(
            name="TCGA-SKCM-RNA",
            path=raw / "rna" / "TCGA-SKCM",
            modality="rna",
            description=(
                "TCGA Skin Cutaneous Melanoma transcriptomic data."
            ),
            source="Genomic Data Commons / TCGA",
            url="https://portal.gdc.cancer.gov/",
            task="melanoma transcriptomics",
            tags=[
                "tcga",
                "skcm",
                "melanoma",
                "rna",
                "transcriptomics",
            ],
        )
    )

    # ================================================================
    # HAND DATASETS
    # ================================================================

    registry.register(
        DatasetInfo(
            name="InterHand2.6M",
            path=raw / "hand" / "InterHand2.6M",
            modality="hand",
            description=(
                "Large-scale hand pose and hand-object interaction "
                "dataset."
            ),
            source="InterHand2.6M",
            task="3D hand pose estimation",
            tags=[
                "hand",
                "pose",
                "3d",
                "mano",
            ],
        )
    )

    registry.register(
        DatasetInfo(
            name="media",
            path=raw / "hand" / "media",
            modality="hand",
            description=(
                "MediaPipe-related hand input data and samples."
            ),
            source="Project / MediaPipe",
            task="hand landmark detection",
            tags=[
                "hand",
                "mediapipe",
                "landmarks",
            ],
        )
    )

    registry.register(
        DatasetInfo(
            name="own_cohort",
            path=raw / "hand" / "own_cohort",
            modality="hand",
            description=(
                "Own cohort data collected for the doctoral project."
            ),
            source="Own cohort",
            task="project-specific hand analysis",
            tags=[
                "hand",
                "own-data",
                "cohort",
            ],
            optional=True,
        )
    )

    return registry


# ---------------------------------------------------------------------------
# Convenience functions
# ---------------------------------------------------------------------------

def get_default_registry() -> DatasetRegistry:
    """
    Return a fully initialized project dataset registry.
    """

    return create_default_registry()


def validate_datasets() -> Dict[str, Dict[str, object]]:
    """
    Validate all datasets in the default registry.
    """

    registry = get_default_registry()

    return registry.validate_all()


def print_dataset_summary() -> None:
    """Print registry summary to the terminal."""

    registry = get_default_registry()

    print(registry.summary())


# ---------------------------------------------------------------------------
# Command-line execution
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print_dataset_summary()