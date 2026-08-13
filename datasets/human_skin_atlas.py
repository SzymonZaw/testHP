"""
human_skin_atlas.py

Dataset adapter for Human Skin Atlas data.

Responsibilities
----------------
- Locate Human Skin Atlas data stored under data/raw/
- Discover available files
- Classify files by modality
- Provide metadata about the dataset
- Validate the local dataset structure
- Expose a simple API for pipeline/ and analysis/ modules

This module does NOT:
- preprocess images
- normalize RNA data
- perform clustering
- train models
- modify raw files
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence
import json
import logging


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Dataset metadata
# ---------------------------------------------------------------------------

@dataclass
class HumanSkinAtlasMetadata:
    """
    Basic metadata describing the Human Skin Atlas dataset.
    """

    name: str = "Human Skin Atlas"
    dataset_id: str = "human_skin_atlas"

    description: str = (
        "Human skin atlas data containing molecular, cellular and/or "
        "spatial information from human skin samples."
    )

    modalities: List[str] = field(
        default_factory=lambda: [
            "rna",
            "spatial",
            "wsi",
        ]
    )

    supported_types: List[str] = field(
        default_factory=lambda: [
            "RNA",
            "single-cell RNA",
            "spatial transcriptomics",
            "whole-slide imaging",
            "histology",
        ]
    )

    source: str = "Human Skin Atlas"

    license: str = "Check original dataset license"

    notes: str = (
        "Metadata is intentionally conservative. Exact modalities and "
        "sample counts depend on the locally downloaded release."
    )


# ---------------------------------------------------------------------------
# File record
# ---------------------------------------------------------------------------

@dataclass
class DatasetFile:
    """
    Represents one file belonging to the dataset.
    """

    path: Path
    modality: str
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
            "modality": self.modality,
            "extension": self.extension,
            "size_bytes": self.size_bytes,
            "size_mb": round(self.size_mb, 3),
            "size_gb": round(self.size_gb, 4),
        }


# ---------------------------------------------------------------------------
# Dataset class
# ---------------------------------------------------------------------------

class HumanSkinAtlas:
    """
    Local dataset interface for Human Skin Atlas.

    Expected location
    -----------------
    data/raw/rna/spatial_skin_atlas/

    Example
    -------
    atlas = HumanSkinAtlas()

    print(atlas.summary())

    files = atlas.list_files()

    rna_files = atlas.list_files(modality="rna")

    atlas.validate()
    """

    DEFAULT_RELATIVE_PATH = Path(
        "data",
        "raw",
        "rna",
        "spatial_skin_atlas",
    )

    # File extensions commonly encountered in transcriptomic /
    # spatial-transcriptomic datasets.
    RNA_EXTENSIONS = {
        ".h5",
        ".h5ad",
        ".loom",
        ".mtx",
        ".tsv",
        ".csv",
        ".txt",
        ".gz",
        ".zip",
        ".tar",
        ".tar.gz",
    }

    IMAGE_EXTENSIONS = {
        ".png",
        ".jpg",
        ".jpeg",
        ".tif",
        ".tiff",
        ".svs",
        ".ndpi",
        ".mrxs",
        ".scn",
    }

    SPATIAL_EXTENSIONS = {
        ".h5ad",
        ".h5",
        ".mtx",
        ".tsv",
        ".csv",
        ".json",
        ".gz",
        ".zip",
    }

    METADATA_EXTENSIONS = {
        ".json",
        ".yaml",
        ".yml",
        ".csv",
        ".tsv",
        ".txt",
    }

    def __init__(
        self,
        root: Optional[str | Path] = None,
    ) -> None:
        """
        Parameters
        ----------
        root:
            Path to the Human Skin Atlas dataset.

            If None, the default project location is used:
            data/raw/rna/spatial_skin_atlas/
        """

        if root is None:
            self.root = self.DEFAULT_RELATIVE_PATH
        else:
            self.root = Path(root)

        self.metadata = HumanSkinAtlasMetadata()

        logger.debug(
            "Initialized HumanSkinAtlas with root: %s",
            self.root,
        )

    # -----------------------------------------------------------------------
    # Basic properties
    # -----------------------------------------------------------------------

    @property
    def exists(self) -> bool:
        """
        Return True if dataset directory exists.
        """
        return self.root.exists() and self.root.is_dir()

    @property
    def absolute_path(self) -> Path:
        """
        Return absolute dataset path.
        """
        return self.root.resolve()

    # -----------------------------------------------------------------------
    # File classification
    # -----------------------------------------------------------------------

    def _classify_file(self, path: Path) -> str:
        """
        Classify a file into a broad modality category.

        Classification is intentionally heuristic.
        """

        name = path.name.lower()
        suffixes = [suffix.lower() for suffix in path.suffixes]

        # Explicit naming conventions first.
        if any(
            keyword in name
            for keyword in (
                "spatial",
                "visium",
                "spot",
                "coordinate",
                "tissue_positions",
            )
        ):
            return "spatial"

        if any(
            keyword in name
            for keyword in (
                "rna",
                "transcript",
                "expression",
                "matrix",
                "gene",
                "feature",
            )
        ):
            return "rna"

        if any(
            keyword in name
            for keyword in (
                "metadata",
                "meta",
                "annotation",
                "clinical",
                "sample",
            )
        ):
            return "metadata"

        # Extension-based classification.
        if any(
            suffix in self.IMAGE_EXTENSIONS
            for suffix in suffixes
        ):
            return "wsi/image"

        if any(
            suffix in self.SPATIAL_EXTENSIONS
            for suffix in suffixes
        ):
            return "spatial/rna"

        if any(
            suffix in self.RNA_EXTENSIONS
            for suffix in suffixes
        ):
            return "rna"

        if any(
            suffix in self.METADATA_EXTENSIONS
            for suffix in suffixes
        ):
            return "metadata"

        return "other"

    # -----------------------------------------------------------------------
    # File discovery
    # -----------------------------------------------------------------------

    def list_files(
        self,
        modality: Optional[str] = None,
        recursive: bool = True,
    ) -> List[DatasetFile]:
        """
        Discover files in the dataset.

        Parameters
        ----------
        modality:
            Optional modality filter.

            Examples:
                "rna"
                "spatial"
                "metadata"
                "wsi/image"

        recursive:
            Search recursively through subdirectories.

        Returns
        -------
        List[DatasetFile]
        """

        if not self.exists:
            logger.warning(
                "Human Skin Atlas directory does not exist: %s",
                self.root,
            )
            return []

        pattern = "**/*" if recursive else "*"

        records: List[DatasetFile] = []

        for path in self.root.glob(pattern):

            if not path.is_file():
                continue

            classification = self._classify_file(path)

            if modality is not None:
                if modality.lower() not in classification.lower():
                    continue

            try:
                size = path.stat().st_size
            except OSError:
                size = 0

            records.append(
                DatasetFile(
                    path=path,
                    modality=classification,
                    extension="".join(path.suffixes),
                    size_bytes=size,
                )
            )

        records.sort(key=lambda x: str(x.path))

        return records

    # -----------------------------------------------------------------------
    # Modality-specific helpers
    # -----------------------------------------------------------------------

    def list_rna_files(self) -> List[DatasetFile]:
        """
        Return RNA-related files.
        """
        return self.list_files(modality="rna")

    def list_spatial_files(self) -> List[DatasetFile]:
        """
        Return spatial-transcriptomics-related files.
        """
        return self.list_files(modality="spatial")

    def list_metadata_files(self) -> List[DatasetFile]:
        """
        Return metadata and annotation files.
        """
        return self.list_files(modality="metadata")

    def list_images(self) -> List[DatasetFile]:
        """
        Return image/WSI files.
        """
        return self.list_files(modality="wsi/image")

    # -----------------------------------------------------------------------
    # Dataset statistics
    # -----------------------------------------------------------------------

    def total_files(self) -> int:
        """
        Return total number of discovered files.
        """
        return len(self.list_files())

    def total_size_bytes(self) -> int:
        """
        Return total size of discovered files in bytes.
        """
        return sum(
            item.size_bytes
            for item in self.list_files()
        )

    def total_size_gb(self) -> float:
        """
        Return total dataset size in GB.
        """
        return self.total_size_bytes() / (1024 ** 3)

    def modality_statistics(self) -> Dict[str, Dict[str, float]]:
        """
        Calculate file count and total size for each modality.
        """

        statistics: Dict[str, Dict[str, float]] = {}

        for record in self.list_files():

            modality = record.modality

            if modality not in statistics:
                statistics[modality] = {
                    "files": 0,
                    "size_bytes": 0,
                }

            statistics[modality]["files"] += 1
            statistics[modality]["size_bytes"] += record.size_bytes

        for modality in statistics:
            statistics[modality]["size_gb"] = (
                statistics[modality]["size_bytes"]
                / (1024 ** 3)
            )

        return statistics

    # -----------------------------------------------------------------------
    # Dataset validation
    # -----------------------------------------------------------------------

    def validate(self) -> Dict[str, object]:
        """
        Validate the local dataset.

        This function checks whether the directory exists and whether
        files have been discovered.

        It does not attempt to validate biological correctness.
        """

        result = {
            "dataset": self.metadata.dataset_id,
            "root": str(self.absolute_path),
            "exists": self.exists,
            "valid": False,
            "file_count": 0,
            "size_gb": 0.0,
            "warnings": [],
        }

        if not self.exists:
            result["warnings"].append(
                "Dataset directory does not exist."
            )
            return result

        files = self.list_files()

        result["file_count"] = len(files)
        result["size_gb"] = round(
            sum(file.size_bytes for file in files)
            / (1024 ** 3),
            4,
        )

        if not files:
            result["warnings"].append(
                "Dataset directory exists but contains no files."
            )
            return result

        result["valid"] = True

        return result

    # -----------------------------------------------------------------------
    # Summary
    # -----------------------------------------------------------------------

    def summary(self) -> Dict[str, object]:
        """
        Return a structured dataset summary.
        """

        validation = self.validate()

        return {
            "name": self.metadata.name,
            "dataset_id": self.metadata.dataset_id,
            "root": str(self.absolute_path),
            "exists": self.exists,
            "valid": validation["valid"],
            "total_files": self.total_files(),
            "total_size_gb": round(
                self.total_size_gb(),
                4,
            ),
            "modalities": self.modality_statistics(),
            "supported_types": self.metadata.supported_types,
            "source": self.metadata.source,
        }

    # -----------------------------------------------------------------------
    # JSON export
    # -----------------------------------------------------------------------

    def export_inventory(
        self,
        output_path: str | Path,
    ) -> Path:
        """
        Export a complete dataset inventory to JSON.

        Useful for reproducibility and dataset documentation.
        """

        output_path = Path(output_path)

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        inventory = {
            "dataset": self.metadata.__dict__,
            "root": str(self.absolute_path),
            "summary": self.summary(),
            "files": [
                file.to_dict()
                for file in self.list_files()
            ],
        }

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
            "Dataset inventory exported to: %s",
            output_path,
        )

        return output_path

    # -----------------------------------------------------------------------
    # Pretty print
    # -----------------------------------------------------------------------

    def print_summary(self) -> None:
        """
        Print human-readable dataset information.
        """

        summary = self.summary()

        print("=" * 70)
        print("Human Skin Atlas")
        print("=" * 70)

        print(f"Path:       {summary['root']}")
        print(f"Exists:     {summary['exists']}")
        print(f"Valid:      {summary['valid']}")
        print(f"Files:      {summary['total_files']}")
        print(f"Size [GB]:  {summary['total_size_gb']}")

        print("\nModalities:")

        modalities = summary["modalities"]

        if not modalities:
            print("  No files detected.")
        else:
            for modality, stats in modalities.items():
                print(
                    f"  {modality}: "
                    f"{int(stats['files'])} files, "
                    f"{stats['size_gb']:.4f} GB"
                )

        print("=" * 70)


# ---------------------------------------------------------------------------
# Utility function
# ---------------------------------------------------------------------------

def get_human_skin_atlas(
    root: Optional[str | Path] = None,
) -> HumanSkinAtlas:
    """
    Factory function returning a HumanSkinAtlas instance.
    """

    return HumanSkinAtlas(root=root)


# ---------------------------------------------------------------------------
# Standalone execution
# ---------------------------------------------------------------------------

def main() -> None:
    """
    Simple command-line diagnostic.
    """

    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s | %(message)s",
    )

    atlas = HumanSkinAtlas()

    atlas.print_summary()

    validation = atlas.validate()

    print("\nValidation:")
    print(
        json.dumps(
            validation,
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()