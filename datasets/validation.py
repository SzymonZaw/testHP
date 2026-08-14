"""Validation of the data that is actually present in ``data/raw``.

Validation is structural and conservative. It never claims that a file is
biologically correct; it only checks that the source is readable, non-empty,
and uses a format understood by the corresponding adapter.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from datasets.adapters import IMAGE_EXTENSIONS, RNA_EXTENSIONS, WSI_EXTENSIONS
from datasets.dataset_registry import DatasetInfo


@dataclass(frozen=True)
class ValidationResult:
    dataset: str
    valid: bool
    files: int
    bytes: int
    supported_files: int
    unsupported_files: int
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()


def validate_dataset(dataset: DatasetInfo) -> ValidationResult:
    path = dataset.path
    if not path.exists():
        return ValidationResult(dataset.name, False, 0, 0, 0, 0, ("path does not exist",))

    files = [p for p in path.rglob("*") if p.is_file()] if path.is_dir() else [path]
    total_bytes = sum(p.stat().st_size for p in files)
    extensions = {
        "image": IMAGE_EXTENSIONS,
        "wsi": WSI_EXTENSIONS,
        "rna": RNA_EXTENSIONS,
    }.get(dataset.modality)
    if dataset.modality == "hand":
        supported = [p for p in files if p.suffix.lower() in IMAGE_EXTENSIONS or p.suffix.lower() in {".json", ".txt"}]
    elif extensions is None:
        supported = files
    else:
        supported = [p for p in files if p.suffix.lower() in extensions]

    errors: list[str] = []
    warnings: list[str] = []
    if not files:
        errors.append("dataset contains no files")
    if total_bytes == 0:
        errors.append("dataset contains no non-empty files")
    if files and not supported:
        errors.append(f"no files use a supported {dataset.modality} format")
    if files and len(supported) < len(files):
        warnings.append(f"ignored {len(files) - len(supported)} unsupported file(s)")

    # A zero-byte placeholder is not data and should be reported explicitly.
    empty = sum(1 for p in files if p.stat().st_size == 0)
    if empty:
        warnings.append(f"{empty} empty file(s) present")

    return ValidationResult(
        dataset.name,
        not errors,
        len(files),
        total_bytes,
        len(supported),
        len(files) - len(supported),
        tuple(errors),
        tuple(warnings),
    )


def validate_registry(datasets: list[DatasetInfo]) -> dict[str, ValidationResult]:
    return {dataset.name: validate_dataset(dataset) for dataset in datasets}
