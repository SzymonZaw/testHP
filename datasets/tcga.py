"""
tcga.py

Dataset adapter for The Cancer Genome Atlas (TCGA).

Primary project use
-------------------
TCGA-SKCM (Skin Cutaneous Melanoma)

Responsibilities
----------------
- Locate locally downloaded TCGA datasets
- Discover TCGA files
- Identify data modalities
- Identify TCGA project / cancer type
- Calculate dataset statistics
- Validate the local dataset
- Export a reproducible file inventory

This module does NOT:
- download data from GDC
- perform RNA preprocessing
- perform pathology analysis
- train models
- modify raw files

Expected project structure
--------------------------

data/
└── raw/
    ├── rna/
    │   └── TCGA-SKCM/
    │
    └── wsi/
        └── melanoma/
            └── TCGA-SKCM/

The same TCGA project may therefore be represented in two
different modalities:

    RNA:
        data/raw/rna/TCGA-SKCM/

    WSI:
        data/raw/wsi/melanoma/TCGA-SKCM/
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional
import json
import logging


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# TCGA metadata
# ---------------------------------------------------------------------------

@dataclass
class TCGAMetadata:
    """
    Metadata describing a TCGA project.
    """

    project_id: str = "TCGA-SKCM"

    disease_name: str = "Skin Cutaneous Melanoma"

    program: str = "TCGA"

    organism: str = "Homo sapiens"

    source: str = "NCI Genomic Data Commons"

    description: str = (
        "The Cancer Genome Atlas Skin Cutaneous Melanoma "
        "project containing genomic, transcriptomic, clinical "
        "and pathology-related data."
    )

    modalities: List[str] = field(
        default_factory=lambda: [
            "rna",
            "wsi",
            "clinical",
            "genomic",
        ]
    )

    notes: str = (
        "Exact files, sample counts and modalities depend on "
        "the downloaded GDC release and selected data types."
    )


# ---------------------------------------------------------------------------
# TCGA file record
# ---------------------------------------------------------------------------

@dataclass
class TCGAFile:
    """
    Represents one local TCGA file.
    """

    path: Path
    project_id: str
    modality: str
    data_category: str
    data_type: str
    extension: str
    size_bytes: int

    @property
    def name(self) -> str:
        return self.path.name

    @property
    def size_mb(self) -> float:
        return self.size_bytes / (1024 ** 2)

    @property
    def size_gb(self) -> float:
        return self.size_bytes / (1024 ** 3)

    def to_dict(self) -> Dict[str, object]:
        return {
            "path": str(self.path),
            "name": self.name,
            "project_id": self.project_id,
            "modality": self.modality,
            "data_category": self.data_category,
            "data_type": self.data_type,
            "extension": self.extension,
            "size_bytes": self.size_bytes,
            "size_mb": round(self.size_mb, 3),
            "size_gb": round(self.size_gb, 4),
        }


# ---------------------------------------------------------------------------
# TCGA dataset adapter
# ---------------------------------------------------------------------------

class TCGA:
    """
    Local adapter for TCGA datasets.

    By default the class is configured for TCGA-SKCM.

    Examples
    --------
    tcga = TCGA()

    tcga.print_summary()

    rna_files = tcga.list_rna_files()

    wsi_files = tcga.list_wsi_files()

    clinical_files = tcga.list_clinical_files()

    tcga.validate()
    """

    DEFAULT_RNA_PATH = Path(
        "data",
        "raw",
        "rna",
        "TCGA-SKCM",
    )

    DEFAULT_WSI_PATH = Path(
        "data",
        "raw",
        "wsi",
        "melanoma",
        "TCGA-SKCM",
    )

    RNA_EXTENSIONS = {
        ".tsv",
        ".csv",
        ".txt",
        ".gz",
        ".h5",
        ".h5ad",
        ".mtx",
        ".loom",
        ".zip",
    }

    WSI_EXTENSIONS = {
        ".svs",
        ".ndpi",
        ".mrxs",
        ".scn",
        ".tif",
        ".tiff",
    }

    CLINICAL_EXTENSIONS = {
        ".json",
        ".xml",
        ".tsv",
        ".csv",
        ".txt",
    }

    GENOMIC_EXTENSIONS = {
        ".maf",
        ".vcf",
        ".vcf.gz",
        ".bed",
        ".bedpe",
        ".seg",
        ".tsv",
        ".txt",
        ".gz",
    }

    def __init__(
        self,
        project_id: str = "TCGA-SKCM",
        rna_root: Optional[str | Path] = None,
        wsi_root: Optional[str | Path] = None,
    ) -> None:
        """
        Parameters
        ----------
        project_id:
            TCGA project identifier.

        rna_root:
            Location of TCGA RNA data.

        wsi_root:
            Location of TCGA pathology/WSI data.
        """

        self.metadata = TCGAMetadata(
            project_id=project_id
        )

        self.project_id = project_id

        self.rna_root = (
            Path(rna_root)
            if rna_root is not None
            else self.DEFAULT_RNA_PATH
        )

        self.wsi_root = (
            Path(wsi_root)
            if wsi_root is not None
            else self.DEFAULT_WSI_PATH
        )

        logger.debug(
            "Initialized TCGA adapter: %s",
            self.project_id,
        )

    # -----------------------------------------------------------------------
    # Paths
    # -----------------------------------------------------------------------

    @property
    def rna_exists(self) -> bool:
        """
        Check whether RNA dataset exists.
        """

        return (
            self.rna_root.exists()
            and self.rna_root.is_dir()
        )

    @property
    def wsi_exists(self) -> bool:
        """
        Check whether WSI dataset exists.
        """

        return (
            self.wsi_root.exists()
            and self.wsi_root.is_dir()
        )

    # -----------------------------------------------------------------------
    # File classification
    # -----------------------------------------------------------------------

    def _classify_rna_file(
        self,
        path: Path,
    ) -> tuple[str, str]:
        """
        Classify an RNA-related TCGA file.

        Returns
        -------
        modality, data_type
        """

        name = path.name.lower()

        if any(
            keyword in name
            for keyword in (
                "star",
                "counts",
                "gene",
                "expression",
                "transcript",
                "rna",
            )
        ):
            return "rna", "transcriptome"

        if "clinical" in name:
            return "clinical", "clinical"

        if "biospecimen" in name:
            return "clinical", "biospecimen"

        if any(
            keyword in name
            for keyword in (
                "maf",
                "mutation",
                "variant",
                "somatic",
            )
        ):
            return "genomic", "mutation"

        if any(
            suffix in "".join(path.suffixes).lower()
            for suffix in (
                ".h5",
                ".h5ad",
                ".mtx",
                ".tsv",
                ".csv",
                ".txt",
                ".gz",
            )
        ):
            return "rna", "transcriptome"

        return "other", "unknown"

    def _classify_wsi_file(
        self,
        path: Path,
    ) -> tuple[str, str]:
        """
        Classify a pathology / WSI file.
        """

        suffix = "".join(
            path.suffixes
        ).lower()

        if suffix.endswith(
            tuple(
                self.WSI_EXTENSIONS
            )
        ):
            return "wsi", "whole_slide_image"

        if suffix.endswith(
            (
                ".json",
                ".xml",
                ".tsv",
                ".csv",
                ".txt",
            )
        ):
            return "metadata", "pathology_metadata"

        return "other", "unknown"

    # -----------------------------------------------------------------------
    # File discovery
    # -----------------------------------------------------------------------

    def _discover_directory(
        self,
        root: Path,
        modality_source: str,
    ) -> List[TCGAFile]:
        """
        Discover files in a specific TCGA directory.
        """

        if not root.exists():
            return []

        if not root.is_dir():
            return []

        records: List[TCGAFile] = []

        for path in root.rglob("*"):

            if not path.is_file():
                continue

            if modality_source == "rna":
                modality, data_type = (
                    self._classify_rna_file(path)
                )
            else:
                modality, data_type = (
                    self._classify_wsi_file(path)
                )

            extension = "".join(
                path.suffixes
            )

            try:
                size_bytes = path.stat().st_size
            except OSError:
                size_bytes = 0

            data_category = self._infer_data_category(
                path,
                modality,
            )

            records.append(
                TCGAFile(
                    path=path,
                    project_id=self.project_id,
                    modality=modality,
                    data_category=data_category,
                    data_type=data_type,
                    extension=extension,
                    size_bytes=size_bytes,
                )
            )

        records.sort(
            key=lambda item: str(item.path)
        )

        return records

    # -----------------------------------------------------------------------
    # Data category inference
    # -----------------------------------------------------------------------

    @staticmethod
    def _infer_data_category(
        path: Path,
        modality: str,
    ) -> str:
        """
        Infer broad GDC-like data category.
        """

        name = path.name.lower()

        if modality == "wsi":
            return "biospecimen/pathology"

        if modality == "clinical":
            return "clinical"

        if modality == "genomic":
            return "simple nucleotide variation"

        if modality == "rna":
            return "transcriptome profiling"

        if "clinical" in name:
            return "clinical"

        if "mutation" in name:
            return "simple nucleotide variation"

        return "unknown"

    # -----------------------------------------------------------------------
    # Public listing
    # -----------------------------------------------------------------------

    def list_files(
        self,
        modality: Optional[str] = None,
    ) -> List[TCGAFile]:
        """
        List all TCGA files.

        Parameters
        ----------
        modality:
            Optional filter:

            "rna"
            "wsi"
            "clinical"
            "genomic"
        """

        files = []

        files.extend(
            self._discover_directory(
                self.rna_root,
                "rna",
            )
        )

        files.extend(
            self._discover_directory(
                self.wsi_root,
                "wsi",
            )
        )

        if modality is None:
            return files

        modality = modality.lower()

        return [
            file
            for file in files
            if file.modality.lower() == modality
        ]

    # -----------------------------------------------------------------------
    # Convenience methods
    # -----------------------------------------------------------------------

    def list_rna_files(self) -> List[TCGAFile]:
        """
        Return transcriptomic files.
        """

        return self.list_files(
            modality="rna"
        )

    def list_wsi_files(self) -> List[TCGAFile]:
        """
        Return whole-slide pathology images.
        """

        return self.list_files(
            modality="wsi"
        )

    def list_clinical_files(self) -> List[TCGAFile]:
        """
        Return clinical files.
        """

        return self.list_files(
            modality="clinical"
        )

    def list_genomic_files(self) -> List[TCGAFile]:
        """
        Return genomic / mutation files.
        """

        return self.list_files(
            modality="genomic"
        )

    # -----------------------------------------------------------------------
    # Statistics
    # -----------------------------------------------------------------------

    def total_files(self) -> int:
        """
        Return total number of files.
        """

        return len(
            self.list_files()
        )

    def total_size_bytes(self) -> int:
        """
        Return total dataset size.
        """

        return sum(
            file.size_bytes
            for file in self.list_files()
        )

    def total_size_gb(self) -> float:
        """
        Return total dataset size in GB.
        """

        return (
            self.total_size_bytes()
            / (1024 ** 3)
        )

    def statistics(
        self,
    ) -> Dict[str, Dict[str, float]]:
        """
        Calculate statistics by modality.
        """

        result: Dict[
            str,
            Dict[str, float]
        ] = {}

        for file in self.list_files():

            modality = file.modality

            if modality not in result:
                result[modality] = {
                    "files": 0,
                    "size_bytes": 0,
                }

            result[modality]["files"] += 1
            result[modality]["size_bytes"] += (
                file.size_bytes
            )

        for modality in result:

            result[modality]["size_gb"] = (
                result[modality]["size_bytes"]
                / (1024 ** 3)
            )

        return result

    # -----------------------------------------------------------------------
    # Validation
    # -----------------------------------------------------------------------

    def validate(self) -> Dict[str, object]:
        """
        Validate local TCGA dataset structure.
        """

        warnings: List[str] = []

        if not self.rna_exists:
            warnings.append(
                "RNA directory does not exist."
            )

        if not self.wsi_exists:
            warnings.append(
                "WSI directory does not exist."
            )

        files = self.list_files()

        if not files:
            warnings.append(
                "No TCGA files were detected."
            )

        return {
            "project_id": self.project_id,
            "valid": len(files) > 0,
            "rna_exists": self.rna_exists,
            "wsi_exists": self.wsi_exists,
            "rna_path": str(
                self.rna_root.resolve()
            ),
            "wsi_path": str(
                self.wsi_root.resolve()
            ),
            "file_count": len(files),
            "size_gb": round(
                sum(
                    file.size_bytes
                    for file in files
                ) / (1024 ** 3),
                4,
            ),
            "warnings": warnings,
        }

    # -----------------------------------------------------------------------
    # Sample identification
    # -----------------------------------------------------------------------

    def find_sample(
        self,
        sample_id: str,
    ) -> List[TCGAFile]:
        """
        Find all files containing a given TCGA sample identifier.

        Example
        -------
        tcga.find_sample("TCGA-DK-A6AV")
        """

        sample_id = sample_id.lower()

        return [
            file
            for file in self.list_files()
            if sample_id in file.name.lower()
            or sample_id in str(
                file.path
            ).lower()
        ]

    # -----------------------------------------------------------------------
    # Extension filtering
    # -----------------------------------------------------------------------

    def find_by_extension(
        self,
        extension: str,
    ) -> List[TCGAFile]:
        """
        Find files by extension.

        Example
        -------
        tcga.find_by_extension(".svs")
        """

        extension = extension.lower()

        if not extension.startswith("."):
            extension = "." + extension

        return [
            file
            for file in self.list_files()
            if extension in file.extension.lower()
        ]

    # -----------------------------------------------------------------------
    # Inventory
    # -----------------------------------------------------------------------

    def inventory(self) -> Dict[str, object]:
        """
        Create complete dataset inventory.
        """

        files = self.list_files()

        return {
            "metadata": self.metadata.__dict__,
            "paths": {
                "rna": str(
                    self.rna_root.resolve()
                ),
                "wsi": str(
                    self.wsi_root.resolve()
                ),
            },
            "statistics": self.statistics(),
            "validation": self.validate(),
            "files": [
                file.to_dict()
                for file in files
            ],
        }

    def export_inventory(
        self,
        output_path: str | Path,
    ) -> Path:
        """
        Export dataset inventory as JSON.
        """

        output_path = Path(
            output_path
        )

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        inventory = self.inventory()

        with output_path.open(
            "w",
            encoding="utf-8",
        ) as handle:

            json.dump(
                inventory,
                handle,
                indent=2,
                ensure_ascii=False,
            )

        logger.info(
            "TCGA inventory written to %s",
            output_path,
        )

        return output_path

    # -----------------------------------------------------------------------
    # Summary
    # -----------------------------------------------------------------------

    def summary(self) -> Dict[str, object]:
        """
        Return concise dataset summary.
        """

        validation = self.validate()

        return {
            "project_id": self.project_id,
            "disease": self.metadata.disease_name,
            "rna_path": str(
                self.rna_root
            ),
            "wsi_path": str(
                self.wsi_root
            ),
            "rna_exists": self.rna_exists,
            "wsi_exists": self.wsi_exists,
            "total_files": validation[
                "file_count"
            ],
            "total_size_gb": validation[
                "size_gb"
            ],
            "statistics": self.statistics(),
        }

    def print_summary(self) -> None:
        """
        Print human-readable summary.
        """

        summary = self.summary()

        print("=" * 70)
        print("TCGA DATASET")
        print("=" * 70)

        print(
            f"Project:       {summary['project_id']}"
        )

        print(
            f"Disease:       {summary['disease']}"
        )

        print(
            f"RNA path:      {summary['rna_path']}"
        )

        print(
            f"RNA exists:    {summary['rna_exists']}"
        )

        print(
            f"WSI path:      {summary['wsi_path']}"
        )

        print(
            f"WSI exists:    {summary['wsi_exists']}"
        )

        print(
            f"Total files:   {summary['total_files']}"
        )

        print(
            f"Total size GB: {summary['total_size_gb']}"
        )

        print("\nModalities:")

        statistics = summary["statistics"]

        if not statistics:
            print("  No files detected.")

        else:
            for modality, values in statistics.items():

                print(
                    f"  {modality}: "
                    f"{int(values['files'])} files, "
                    f"{values['size_gb']:.4f} GB"
                )

        print("=" * 70)


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def get_tcga(
    project_id: str = "TCGA-SKCM",
    rna_root: Optional[str | Path] = None,
    wsi_root: Optional[str | Path] = None,
) -> TCGA:
    """
    Factory function for creating a TCGA adapter.
    """

    return TCGA(
        project_id=project_id,
        rna_root=rna_root,
        wsi_root=wsi_root,
    )


# ---------------------------------------------------------------------------
# Standalone execution
# ---------------------------------------------------------------------------

def main() -> None:
    """
    Run a local TCGA dataset diagnostic.
    """

    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s | %(message)s",
    )

    tcga = TCGA(
        project_id="TCGA-SKCM"
    )

    tcga.print_summary()

    print("\nValidation:")

    print(
        json.dumps(
            tcga.validate(),
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()