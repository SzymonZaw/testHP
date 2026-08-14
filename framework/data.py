"""Data discovery and readiness checks for the testHP framework.

The framework deliberately discovers what is actually present under data/raw.
It does not require every planned modality to be installed.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable


DEFAULT_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff",
    ".svs", ".ndpi", ".mrxs", ".dcm", ".nii", ".nii.gz",
    ".csv", ".tsv", ".txt", ".json", ".jsonl", ".gz", ".h5", ".h5ad",
    ".mtx", ".tar",
}


@dataclass(frozen=True)
class DatasetStatus:
    name: str
    modality: str
    path: str
    exists: bool
    files: int
    bytes: int
    enabled: bool = True

    @property
    def ready(self) -> bool:
        return self.exists and self.files > 0

    def to_dict(self) -> dict:
        value = asdict(self)
        value["ready"] = self.ready
        return value


def _iter_files(path: Path) -> Iterable[Path]:
    if not path.exists():
        return ()
    return (p for p in path.rglob("*") if p.is_file())


def inspect_path(root: Path, name: str, modality: str, enabled: bool = True) -> DatasetStatus:
    path = root
    files = list(_iter_files(path))
    files = [p for p in files if p.suffix.lower() in DEFAULT_EXTENSIONS or p.name.endswith(".nii.gz")]
    return DatasetStatus(
        name=name,
        modality=modality,
        path=str(path),
        exists=path.exists(),
        files=len(files),
        bytes=sum(p.stat().st_size for p in files),
        enabled=enabled,
    )


def discover_raw(repo_root: Path) -> list[DatasetStatus]:
    """Discover meaningful datasets from the repository's actual raw tree."""
    raw = repo_root / "data" / "raw"
    if not raw.exists():
        return [DatasetStatus("raw", "all", str(raw), False, 0, 0, True)]

    statuses: list[DatasetStatus] = []
    for modality in ("images", "wsi", "rna", "hand"):
        base = raw / modality
        if not base.exists():
            statuses.append(DatasetStatus(modality, modality, str(base), False, 0, 0, True))
            continue
        children = [p for p in sorted(base.iterdir()) if p.is_dir()]
        if not children:
            statuses.append(inspect_path(base, modality, modality))
        else:
            for child in children:
                statuses.append(inspect_path(child, child.name, modality))
    return statuses


def summary(statuses: list[DatasetStatus]) -> dict:
    ready = [s for s in statuses if s.ready]
    return {
        "datasets": len(statuses),
        "ready": len(ready),
        "files": sum(s.files for s in statuses),
        "bytes": sum(s.bytes for s in statuses),
        "modalities": sorted({s.modality for s in ready}),
    }
