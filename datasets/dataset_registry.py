"""Central registry for datasets actually available in ``data/raw``.

The registry is deliberately data-driven: planned future datasets are not
registered as required inputs. A missing optional source must never make the
rest of the project unusable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}
WSI_EXTENSIONS = {".svs", ".ndpi", ".mrxs", ".tif", ".tiff", ".dcm"}
RNA_EXTENSIONS = {".h5ad", ".h5", ".csv", ".tsv", ".txt", ".mtx", ".gz", ".tar", ".zip"}


@dataclass
class DatasetInfo:
    name: str
    path: Path
    modality: str
    description: str = ""
    source: str = ""
    url: Optional[str] = None
    task: Optional[str] = None
    license: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    optional: bool = True

    def exists(self) -> bool:
        return self.path.exists()

    def has_data(self) -> bool:
        if not self.path.exists():
            return False
        if self.path.is_file():
            return self.path.stat().st_size > 0
        return any(p.is_file() and p.stat().st_size > 0 for p in self.path.rglob("*"))

    def is_directory(self) -> bool:
        return self.path.is_dir()

    def validate(self) -> Dict[str, object]:
        return {
            "name": self.name,
            "path": str(self.path),
            "exists": self.exists(),
            "has_data": self.has_data(),
            "is_directory": self.is_directory(),
            "valid": self.has_data(),
            "optional": self.optional,
        }

    def summary(self) -> str:
        status = "OK" if self.has_data() else "EMPTY/MISSING"
        return f"[{status}] {self.name} | {self.modality} | {self.path}"


class DatasetRegistry:
    def __init__(self) -> None:
        self._datasets: Dict[str, DatasetInfo] = {}

    def register(self, dataset: DatasetInfo) -> None:
        if dataset.name in self._datasets:
            raise ValueError(f"Dataset '{dataset.name}' is already registered.")
        self._datasets[dataset.name] = dataset

    def get(self, name: str) -> DatasetInfo:
        if name not in self._datasets:
            raise KeyError(f"Dataset '{name}' is not registered.")
        return self._datasets[name]

    def exists(self, name: str) -> bool:
        return name in self._datasets

    def all(self) -> List[DatasetInfo]:
        return list(self._datasets.values())

    def names(self) -> List[str]:
        return list(self._datasets.keys())

    def by_modality(self, modality: str) -> List[DatasetInfo]:
        return [d for d in self._datasets.values() if d.modality.lower() == modality.lower()]

    def by_tag(self, tag: str) -> List[DatasetInfo]:
        tag = tag.lower()
        return [d for d in self._datasets.values() if tag in {t.lower() for t in d.tags}]

    def validate_all(self) -> Dict[str, Dict[str, object]]:
        return {d.name: d.validate() for d in self._datasets.values()}

    def summary(self) -> str:
        lines = ["Dataset Registry", "=" * 80]
        lines.extend(d.summary() for d in self._datasets.values())
        return "\n".join(lines)


def get_project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def get_raw_data_root() -> Path:
    return get_project_root() / "data" / "raw"


def _register_if_data(registry: DatasetRegistry, *, name: str, path: Path,
                      modality: str, description: str, source: str = "",
                      task: str = "", tags: Optional[List[str]] = None,
                      url: Optional[str] = None) -> None:
    """Register a source only when its directory/file contains real data."""
    if path.exists():
        registry.register(DatasetInfo(
            name=name,
            path=path,
            modality=modality,
            description=description,
            source=source,
            url=url,
            task=task,
            tags=tags or [],
        ))


def create_default_registry() -> DatasetRegistry:
    """Create a registry from the datasets currently present in ``data/raw``."""
    raw = get_raw_data_root()
    registry = DatasetRegistry()

    # Images
    _register_if_data(
        registry, name="aging_skin", path=raw / "images" / "aging_skin",
        modality="image", description="Skin images used for aging analysis",
        task="skin aging", tags=["skin", "aging", "image"],
    )
    _register_if_data(
        registry, name="normal_skin", path=raw / "images" / "normal_skin",
        modality="image", description="Normal skin reference images",
        task="normal skin", tags=["skin", "normal", "image"],
    )
    _register_if_data(
        registry, name="skin_lesions_dataset",
        path=raw / "images" / "lesions" / "skin_lesions_dataset",
        modality="image", description="Skin lesion image dataset",
        task="lesion analysis", tags=["skin", "lesion", "image"],
    )
    _register_if_data(
        registry, name="ISIC", path=raw / "images" / "lesions" / "ISIC",
        modality="image", description="ISIC dermatology image collection",
        source="ISIC Archive", url="https://www.isic-archive.com/",
        task="lesion analysis", tags=["skin", "lesion", "dermatology", "image"],
    )
    _register_if_data(
        registry, name="SCIN", path=raw / "images" / "pathology" / "scin",
        modality="image", description="Skin Condition Image Network data",
        source="Google Research", task="dermatology image analysis",
        tags=["skin", "dermatology", "image"],
    )

    # WSI / pathology. DICOM is supported because the current TCGA sample
    # is stored as .dcm rather than SVS/NDPI.
    _register_if_data(
        registry, name="TCGA-SKCM-WP", path=raw / "wsi" / "melanoma" / "TCGA-SKCM",
        modality="wsi", description="TCGA Skin Cutaneous Melanoma pathology data",
        source="TCGA / GDC", url="https://portal.gdc.cancer.gov/",
        task="melanoma pathology", tags=["tcga", "skcm", "melanoma", "pathology", "wsi"],
    )

    # RNA sources that are actually present.
    for accession in ("GSE130973", "GSE226189", "GSE281449"):
        _register_if_data(
            registry, name=accession, path=raw / "rna" / accession,
            modality="rna", description=f"GEO dataset {accession}",
            source="NCBI GEO", url="https://www.ncbi.nlm.nih.gov/geo/",
            task="skin transcriptomics", tags=["geo", "rna", "transcriptomics", "skin"],
        )

    _register_if_data(
        registry, name="spatial_skin_atlas_rna",
        path=raw / "rna" / "spatial_skin_atlas",
        modality="rna", description="Available skin transcriptomic files from the spatial atlas source",
        task="skin transcriptomics", tags=["skin", "rna", "spatial", "transcriptomics"],
    )

    # Hand data.
    _register_if_data(
        registry, name="InterHand2_6M", path=raw / "hand" / "InterHand2_6M",
        modality="hand", description="InterHand2.6M hand pose dataset",
        source="InterHand2.6M", task="3D hand pose estimation",
        tags=["hand", "pose", "3d", "mano"],
    )
    _register_if_data(
        registry, name="own_hand_cohort", path=raw / "hand" / "own_cohort",
        modality="hand", description="Own hand cohort images",
        source="Own cohort", task="hand analysis", tags=["hand", "cohort"],
    )

    return registry


def get_default_registry() -> DatasetRegistry:
    return create_default_registry()


def validate_datasets() -> Dict[str, Dict[str, object]]:
    return get_default_registry().validate_all()


def print_dataset_summary() -> None:
    print(get_default_registry().summary())


if __name__ == "__main__":
    print_dataset_summary()
