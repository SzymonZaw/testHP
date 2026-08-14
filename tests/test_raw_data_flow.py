"""Smoke tests for the datasets that are actually kept in data/raw.

These tests intentionally do not require the complete public datasets. They
validate the small local test samples and, when larger datasets are present,
exercise their file discovery/readability without requiring training.
"""

from __future__ import annotations

import gzip
import json
import tarfile
from pathlib import Path

import pytest
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"


def nonempty_files(path: Path):
    if not path.exists():
        return []
    if path.is_file():
        return [path] if path.stat().st_size else []
    return [p for p in path.rglob("*") if p.is_file() and p.stat().st_size]


def test_raw_modalities_have_data():
    """The current raw tree must expose the four project modalities."""
    expected = [
        RAW / "images",
        RAW / "rna",
        RAW / "hand",
        RAW / "wsi",
    ]
    missing = [str(p) for p in expected if not nonempty_files(p)]
    assert not missing, f"Raw modality directories are empty/missing: {missing}"


def test_image_samples_are_readable():
    """Read representative image samples through Pillow."""
    roots = [
        RAW / "images" / "aging_skin",
        RAW / "images" / "normal_skin",
        RAW / "images" / "lesions" / "skin_lesions_dataset",
        RAW / "images" / "lesions" / "ISIC",
    ]
    candidates = []
    for root in roots:
        candidates.extend(
            p for p in nonempty_files(root)
            if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}
        )
    assert candidates, "No readable image samples were found in data/raw/images."
    for path in candidates[:8]:
        with Image.open(path) as image:
            image.verify()


def test_interhand_samples_are_present_and_json_is_valid():
    root = RAW / "hand" / "InterHand2_6M"
    assert nonempty_files(root), "InterHand2_6M contains no data."

    json_files = list(root.rglob("*.json"))
    assert json_files, "InterHand2_6M sample has no JSON annotations."
    for path in json_files[:2]:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        assert isinstance(data, (dict, list))

    image_files = [p for p in nonempty_files(root) if p.suffix.lower() in {".jpg", ".jpeg", ".png"}]
    assert image_files, "InterHand2_6M sample has no RGB images."


def test_rna_files_are_discoverable():
    root = RAW / "rna"
    files = nonempty_files(root)
    assert files, "No RNA files found in data/raw/rna."

    # Check the compressed formats used by the current GEO samples without
    # assuming one specific accession has to contain a complete matrix.
    gz_files = [p for p in files if p.suffix.lower() == ".gz"]
    if gz_files:
        with gzip.open(gz_files[0], "rb") as handle:
            assert handle.read(1), f"Compressed RNA file is empty: {gz_files[0]}"

    tar_files = [p for p in files if p.name.lower().endswith((".tar", ".tar.gz", ".tgz"))]
    if tar_files:
        assert tarfile.is_tarfile(tar_files[0]), f"Invalid RNA archive: {tar_files[0]}"


def test_tcga_pathology_files_are_present():
    root = RAW / "wsi" / "melanoma" / "TCGA-SKCM"
    files = nonempty_files(root)
    assert files, "No TCGA-SKCM pathology files found."

    dcm_files = [p for p in files if p.suffix.lower() == ".dcm"]
    if not dcm_files:
        pytest.skip("TCGA-SKCM sample is present but currently has no DICOM file.")

    pydicom = pytest.importorskip("pydicom")
    dataset = pydicom.dcmread(dcm_files[0], stop_before_pixels=True)
    assert dataset is not None


def test_dataset_registry_uses_only_current_raw_sources():
    from datasets.dataset_registry import get_default_registry

    registry = get_default_registry()
    names = set(registry.names())

    forbidden_planned = {
        "human_cell_atlas",
        "human_skin_atlas",
        "geo",
        "tcga",
    }
    assert not names.intersection(forbidden_planned)

    assert "InterHand2_6M" in names
    assert "GSE226189" in names or "GSE130973" in names or "GSE281449" in names
