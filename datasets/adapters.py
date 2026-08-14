"""Dataset-specific adapters that normalize real files into Observations.

Adapters are intentionally lightweight: they inspect the data that is actually
present and expose deterministic ingestion facts. They do not invent biological
measurements or require optional heavyweight ML libraries.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from integration.observation_to_twin import Observation

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
WSI_EXTENSIONS = {".svs", ".ndpi", ".mrxs", ".dcm", ".tif", ".tiff"}
RNA_EXTENSIONS = {".h5ad", ".h5", ".mtx", ".csv", ".tsv", ".txt", ".gz", ".zip", ".tar"}


@dataclass(frozen=True)
class AdapterResult:
    dataset: str
    modality: str
    observations: tuple[Observation, ...]
    files: int
    bytes: int
    warnings: tuple[str, ...] = ()


class DatasetAdapter:
    """Small interface shared by every source adapter."""
    def load(self) -> AdapterResult:  # pragma: no cover - interface
        raise NotImplementedError


def _files(path: Path, extensions: set[str] | None = None) -> list[Path]:
    if not path.exists():
        return []
    items = [p for p in path.rglob("*") if p.is_file()]
    if extensions is not None:
        items = [p for p in items if p.suffix.lower() in extensions]
    return sorted(items)


def _base_result(dataset: str, modality: str, path: Path, files: list[Path], observations: list[Observation], warnings: list[str] | None = None) -> AdapterResult:
    total = sum(p.stat().st_size for p in files)
    return AdapterResult(dataset, modality, tuple(observations), len(files), total, tuple(warnings or []))


class ImageAdapter(DatasetAdapter):
    def __init__(self, dataset: str, path: Path, modality: str = "image") -> None:
        self.dataset, self.path, self.modality = dataset, path, modality

    def load(self) -> AdapterResult:
        files = _files(self.path, IMAGE_EXTENSIONS)
        obs = [
            Observation(f"dataset.{self.dataset}.image_count", float(len(files)), 1.0 if files else 0.0, self.modality),
            Observation(f"dataset.{self.dataset}.image_bytes", float(sum(p.stat().st_size for p in files)), 1.0 if files else 0.0, self.modality),
        ]
        return _base_result(self.dataset, self.modality, self.path, files, obs)


class InterHandAdapter(DatasetAdapter):
    def __init__(self, path: Path) -> None:
        self.dataset, self.path = "InterHand2_6M", path

    def load(self) -> AdapterResult:
        files = _files(self.path)
        image_files = _files(self.path, IMAGE_EXTENSIONS)
        json_files = [p for p in files if p.suffix.lower() == ".json"]
        obs = [
            Observation("dataset.InterHand2_6M.image_count", float(len(image_files)), 1.0 if image_files else 0.0, "hand"),
            Observation("dataset.InterHand2_6M.annotation_file_count", float(len(json_files)), 1.0 if json_files else 0.0, "hand"),
        ]
        # Read only small JSON metadata files; never load the large image set.
        annotation_entries = 0
        for p in json_files:
            if p.stat().st_size > 50 * 1024 * 1024:
                continue
            try:
                with p.open("r", encoding="utf-8") as fh:
                    data = json.load(fh)
                if isinstance(data, dict):
                    for key in ("images", "annotations"):
                        value = data.get(key)
                        if isinstance(value, list):
                            annotation_entries += len(value)
            except (OSError, ValueError):
                continue
        if annotation_entries:
            obs.append(Observation("dataset.InterHand2_6M.annotation_entries", float(annotation_entries), 1.0, "hand"))
        return _base_result(self.dataset, "hand", self.path, files, obs)


class WSIAdapter(DatasetAdapter):
    def __init__(self, dataset: str, path: Path) -> None:
        self.dataset, self.path = dataset, path

    def load(self) -> AdapterResult:
        files = _files(self.path, WSI_EXTENSIONS)
        obs = [
            Observation(f"dataset.{self.dataset}.slide_file_count", float(len(files)), 1.0 if files else 0.0, "wsi"),
            Observation(f"dataset.{self.dataset}.slide_bytes", float(sum(p.stat().st_size for p in files)), 1.0 if files else 0.0, "wsi"),
        ]
        return _base_result(self.dataset, "wsi", self.path, files, obs)


class RNAAdapter(DatasetAdapter):
    def __init__(self, dataset: str, path: Path) -> None:
        self.dataset, self.path = dataset, path

    def load(self) -> AdapterResult:
        files = _files(self.path, RNA_EXTENSIONS)
        obs = [
            Observation(f"dataset.{self.dataset}.rna_file_count", float(len(files)), 1.0 if files else 0.0, "rna"),
            Observation(f"dataset.{self.dataset}.rna_bytes", float(sum(p.stat().st_size for p in files)), 1.0 if files else 0.0, "rna"),
        ]
        return _base_result(self.dataset, "rna", self.path, files, obs)


def adapter_for(dataset_name: str, path: Path, modality: str) -> DatasetAdapter:
    if dataset_name == "InterHand2_6M":
        return InterHandAdapter(path)
    if modality == "image":
        return ImageAdapter(dataset_name, path, modality)
    if modality == "wsi":
        return WSIAdapter(dataset_name, path)
    if modality == "rna":
        return RNAAdapter(dataset_name, path)
    return ImageAdapter(dataset_name, path, modality)
